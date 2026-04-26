"""Shared helpers used by the worker, evaluator, and management command."""

import logging
from collections.abc import Generator
from datetime import timedelta
from typing import Any

from django.db.models import F, Q
from django.utils import timezone

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import build_skip_urls

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

    # Snapshot the skip set once for the whole batch — three
    # batched queries instead of three per row. The race window
    # between this snapshot and each atomic claim is microseconds;
    # any row that becomes skipworthy in that window is caught on
    # the next sweep, which is fine.
    skip_urls = build_skip_urls({n.url for n in nominations})

    # In-batch dedup: two pending rows for the same URL would both
    # pass the skip check (no eval/org exists yet for either) and
    # both get evaluated, wasting Claude budget and creating
    # duplicate OrganizationEvaluation rows. Track URLs already
    # claimed in this batch and skip repeats — they stay in the
    # source status; the next dispatch's build_skip_urls will catch
    # them once the first row's evaluation lands.
    claimed_urls: set[str] = set()

    for nomination in nominations:
        if nomination.url in claimed_urls:
            continue

        if nomination.url in skip_urls:
            # Skipworthy rows must exit the active QUEUED pool so the
            # worker stops re-encountering them on every dispatch.
            # PENDING is the resting state for skipworthy rows: the
            # pre-filter in any subsequent run will exclude them
            # again. Conditional UPDATE on the source status keeps
            # this safe against concurrent transitions.
            if from_status != NominationStatus.PENDING:
                Nomination.objects.filter(
                    pk=nomination.pk,
                    status=from_status,
                ).update(status=NominationStatus.PENDING)
            continue

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

        claimed_urls.add(nomination.url)
        yield nomination
