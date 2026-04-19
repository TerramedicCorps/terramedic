"""Shared helpers used by the worker, evaluator, and management command."""

import logging
from collections.abc import Generator
from datetime import timedelta
from typing import Any

from django.db.models import F, Q
from django.utils import timezone

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import should_skip_url

logger = logging.getLogger(__name__)

DEFAULT_EVAL_MODEL = "claude-sonnet-4-20250514"

# Nominations claimed longer than this without a result are stuck —
# typically because the evaluator swallowed the message silently
# (e.g., Zappa's "Cannot find a function" path returns success) or
# crashed before sending a result. Safely past the SQS retry window
# (2 × 360s visibility timeout = 12 min for the requests queue).
_STUCK_CLAIM_THRESHOLD = timedelta(minutes=15)


def sweep_stuck_claims() -> int:
    """Mark nominations stuck in EVALUATING as FAILED.

    Returns the count swept. Rows with a null ``claimed_at`` (either
    pre-migration leftovers or an unexpected code path that skipped
    the claim update) are also swept so the pipeline doesn't silently
    leak them.
    """
    cutoff = timezone.now() - _STUCK_CLAIM_THRESHOLD
    swept: int = (
        Nomination.objects.filter(
            status=NominationStatus.EVALUATING,
        )
        .filter(
            Q(claimed_at__lt=cutoff) | Q(claimed_at__isnull=True),
        )
        .update(status=NominationStatus.FAILED)
    )
    if swept:
        logger.warning(
            "Swept %d stuck EVALUATING nomination(s) to FAILED.",
            swept,
        )
    return swept


def evaluate_org(
    url: str,
    model: str,
    client: Any = None,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Lazy-import wrapper — replaced in tests via mock."""
    from curation.evaluate import evaluate_org as _evaluate_org

    return _evaluate_org(url=url, model=model, client=client, categories=categories)


def claim_nominations(
    limit: int,
    from_status: str = NominationStatus.QUEUED,
) -> Generator[Nomination]:
    """Claim nominations atomically and yield non-skipped ones.

    The AWS worker claims from ``QUEUED`` (the default). A local
    curator-run command can claim from ``PENDING`` to bypass the SQS
    pipeline — the two pools are disjoint so the worker and a local
    run can't race for the same row.

    For each nomination in ``from_status`` (up to *limit*):
    1. Atomically set status to EVALUATING and increment attempts.
    2. Revert to ``PENDING`` if the URL should be skipped — always
       PENDING, regardless of ``from_status``, so skipworthy rows
       exit the active ``QUEUED`` pool (prevents the worker's
       claim-skip-revert loop).
    3. Yield the nomination if it passed both checks.
    """
    nominations = list(
        Nomination.objects.filter(
            status=from_status,
        ).order_by("submitted_at")[:limit],
    )

    for nomination in nominations:
        # Atomic claim: only proceed if still in the source status
        # (prevents duplicate processing by concurrent workers).
        claimed = Nomination.objects.filter(
            pk=nomination.pk,
            status=from_status,
        ).update(
            status=NominationStatus.EVALUATING,
            evaluation_attempts=F("evaluation_attempts") + 1,
            claimed_at=timezone.now(),
        )
        if not claimed:
            continue
        nomination.refresh_from_db()

        if should_skip_url(nomination.url):
            # Always revert to PENDING so skipworthy rows exit the
            # active queue. For QUEUED → this breaks the worker's
            # claim-skip-revert loop. For PENDING → the local command
            # pre-filters via build_skip_urls so this path is a rare
            # race fallback; staying in PENDING is fine because the
            # pre-filter will exclude it again on the next run.
            nomination.status = NominationStatus.PENDING
            nomination.evaluation_attempts -= 1
            nomination.save(
                update_fields=["status", "evaluation_attempts"],
            )
            continue

        yield nomination
