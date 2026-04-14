"""Shared nomination-claiming logic used by worker and management command."""

from collections.abc import Generator

from django.db.models import F

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import should_skip_url

DEFAULT_EVAL_MODEL = "claude-sonnet-4-20250514"


def claim_nominations(limit: int) -> Generator[Nomination]:
    """Claim queued nominations atomically and yield non-skipped ones.

    For each queued nomination (up to *limit*):
    1. Atomically set status to EVALUATING and increment attempts.
    2. Revert to PENDING if the URL should be skipped.
    3. Yield the nomination if it passed both checks.
    """
    nominations = list(
        Nomination.objects.filter(
            status=NominationStatus.QUEUED,
        ).order_by("submitted_at")[:limit],
    )

    for nomination in nominations:
        # Atomic claim: only proceed if still queued (prevents
        # duplicate processing by concurrent workers).
        claimed = Nomination.objects.filter(
            pk=nomination.pk,
            status=NominationStatus.QUEUED,
        ).update(
            status=NominationStatus.EVALUATING,
            evaluation_attempts=F("evaluation_attempts") + 1,
        )
        if not claimed:
            continue
        nomination.refresh_from_db()

        if should_skip_url(nomination.url):
            nomination.status = NominationStatus.PENDING
            nomination.evaluation_attempts -= 1
            nomination.save(
                update_fields=["status", "evaluation_attempts"],
            )
            continue

        yield nomination
