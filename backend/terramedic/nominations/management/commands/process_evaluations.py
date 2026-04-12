"""Process queued nominations by running AI evaluations.

Usage:
    # Local
    python manage.py process_evaluations --limit 5

    # Lambda
    zappa manage dev "process_evaluations --limit 5"
"""

import logging
import os
import sys
from typing import Any

from django.core.management.base import BaseCommand

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import OrganizationEvaluation

logger = logging.getLogger(__name__)

_DEFAULT_EVAL_MODEL = "claude-sonnet-4-20250514"
_MAX_RETRY_ATTEMPTS = 2


def evaluate_org(
    url: str,
    model: str,
    client: Any = None,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Lazy import wrapper — replaced in tests via mock."""
    from curation.evaluate import evaluate_org as _evaluate_org

    return _evaluate_org(url=url, model=model, client=client, categories=categories)


def Anthropic(**kwargs: Any) -> Any:  # noqa: N802
    """Lazy import wrapper — replaced in tests via mock."""
    from anthropic import Anthropic as _Anthropic

    return _Anthropic(**kwargs)


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
            self.stderr.write("ANTHROPIC_API_KEY is not set.")
            sys.exit(1)

        client = Anthropic(api_key=api_key)
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

        for nomination in nominations:
            nomination.status = NominationStatus.EVALUATING
            nomination.evaluation_attempts += 1
            nomination.save(
                update_fields=["status", "evaluation_attempts"],
            )

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
            f"Processed {processed}, failed {failed} "
            f"of {len(nominations)} nomination(s).",
        )
