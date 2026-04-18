"""Process queued nominations by running AI evaluations.

Usage:
    # Local
    python manage.py process_evaluations --limit 5

    # Lambda
    zappa manage dev "process_evaluations --limit 5"
"""

import logging
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from terramedic.core.secrets import is_arn, resolve_secret
from terramedic.nominations.claim import (
    DEFAULT_EVAL_MODEL,
    claim_nominations,
    evaluate_org,  # noqa: F401
)
from terramedic.nominations.models import NominationStatus
from terramedic.organizations.models import OrganizationEvaluation

logger = logging.getLogger(__name__)

_MAX_RETRY_ATTEMPTS = 2


def create_anthropic_client(**kwargs: Any) -> Any:
    """Lazy import wrapper — replaced in tests via mock."""
    from anthropic import Anthropic

    return Anthropic(**kwargs)


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
        raw_key = os.environ.get("ANTHROPIC_API_KEY")
        if not raw_key:
            raise CommandError("ANTHROPIC_API_KEY is not set.")

        api_key = resolve_secret(raw_key, "key") if is_arn(raw_key) else raw_key
        client = create_anthropic_client(api_key=api_key)
        limit: int = options["limit"]

        processed = 0
        failed = 0

        for nomination in claim_nominations(limit):
            try:
                data = evaluate_org(
                    url=nomination.url,
                    model=os.environ.get("EVAL_MODEL", DEFAULT_EVAL_MODEL),
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
            f"Processed {processed}, failed {failed} nomination(s).",
        )
