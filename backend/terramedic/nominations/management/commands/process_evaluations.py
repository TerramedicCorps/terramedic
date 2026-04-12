"""Process queued nominations by running AI evaluations.

Usage:
    # Local
    python manage.py process_evaluations --limit 5

    # Lambda
    zappa manage dev "process_evaluations --limit 5"
"""

import datetime
import logging
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import (
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
)

logger = logging.getLogger(__name__)

_DEFAULT_EVAL_MODEL = "claude-sonnet-4-20250514"
_MAX_RETRY_ATTEMPTS = 2
_REJECTION_COOLDOWN_DAYS = 90


def evaluate_org(
    url: str,
    model: str,
    client: Any = None,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Lazy import wrapper — replaced in tests via mock."""
    from curation.evaluate import evaluate_org as _evaluate_org

    return _evaluate_org(url=url, model=model, client=client, categories=categories)


def create_anthropic_client(**kwargs: Any) -> Any:
    """Lazy import wrapper — replaced in tests via mock."""
    from anthropic import Anthropic

    return Anthropic(**kwargs)


def _should_skip(url: str) -> bool:
    """Check if a URL should be skipped (already evaluated, exists, or in cooldown)."""
    has_active_eval = (
        OrganizationEvaluation.objects.exclude(
            status=ReviewStatus.REJECTED,
        ).filter(
            evaluation_data__org_metadata__website_url=url,
        ).exists()
    )
    if has_active_eval:
        return True

    if Organization.objects.filter(website_url=url).exists():
        return True

    cooldown_cutoff = timezone.now() - datetime.timedelta(
        days=_REJECTION_COOLDOWN_DAYS,
    )
    has_recent_rejection = (
        OrganizationEvaluation.objects.filter(
            status=ReviewStatus.REJECTED,
            created_at__gte=cooldown_cutoff,
            evaluation_data__org_metadata__website_url=url,
        ).exists()
    )
    return has_recent_rejection


class Command(BaseCommand):
    help = "Process queued nominations through AI evaluation."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum nominations to process (default: 10).",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise CommandError("ANTHROPIC_API_KEY is not set.")

        client = create_anthropic_client(api_key=api_key)
        limit: int = options["limit"]

        nominations = list(
            Nomination.objects.filter(
                status=NominationStatus.QUEUED,
            ).order_by("submitted_at")[:limit],
        )

        if not nominations:
            self.stdout.write("No queued nominations to process.")
            return

        processed = 0
        failed = 0
        skipped = 0

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

            if _should_skip(nomination.url):
                nomination.status = NominationStatus.PENDING
                nomination.evaluation_attempts -= 1
                nomination.save(
                    update_fields=["status", "evaluation_attempts"],
                )
                skipped += 1
                continue

            try:
                data = evaluate_org(
                    url=nomination.url,
                    model=_DEFAULT_EVAL_MODEL,
                    client=client,
                    categories=nomination.categories or None,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "evaluate_org failed for %s", nomination.url,
                )
                if nomination.evaluation_attempts >= _MAX_RETRY_ATTEMPTS:
                    nomination.status = NominationStatus.FAILED
                else:
                    nomination.status = NominationStatus.QUEUED
                nomination.save(update_fields=["status"])
                failed += 1
                continue

            curator_notes = data.get("curator_notes", {})
            OrganizationEvaluation.objects.create(
                evaluation_data=data,
                ai_model=data.get("evaluated_by", ""),
                ai_recommendation=curator_notes.get("recommendation", ""),
                ai_confidence=curator_notes.get("confidence"),
                nomination=nomination,
            )
            processed += 1

        self.stdout.write(
            f"Processed {processed}, failed {failed}, skipped {skipped} "
            f"of {len(nominations)} nomination(s).",
        )
