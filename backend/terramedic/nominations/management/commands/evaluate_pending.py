"""Evaluate PENDING nominations locally via Claude Code (Max billing).

Shells out to the ``claude`` CLI for each claimed nomination, so the
cost hits the operator's Max subscription rather than the per-token
Anthropic API used by the SQS/Lambda pipeline.

Usage:
    SECRET_KEY=... DEBUG=true \\
        poetry run python manage.py evaluate_pending --limit 10

Notes:
- Only touches ``PENDING`` nominations. The AWS pipeline claims
  ``QUEUED``, so the two pools are disjoint — no race.
- Pre-filters duplicate URLs via ``build_skip_urls`` and reports them;
  those nominations stay in ``PENDING`` for the curator to triage.
- Requires an interactive Claude Code login (``claude auth``). Not
  usable from a headless server.
"""

import logging
from typing import Any

from django.core.management.base import BaseCommand

from curation.evaluate import evaluate_org_via_claude_code
from terramedic.nominations.claim import claim_nominations
from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import build_skip_urls
from terramedic.organizations.models import OrganizationEvaluation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Evaluate PENDING nominations locally via Claude Code "
        "(uses Max subscription, not API credits)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum nominations to evaluate (default: 10).",
        )
        parser.add_argument(
            "--model",
            default="sonnet",
            help=(
                "Claude Code model alias or full name "
                "(default: sonnet)."
            ),
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        limit: int = options["limit"]
        model: str = options["model"]

        self._report_skips(limit)

        processed = 0
        failed = 0

        for nomination in claim_nominations(
            limit, from_status=NominationStatus.PENDING,
        ):
            self.stdout.write(f"Evaluating {nomination.url} ...")
            try:
                data = evaluate_org_via_claude_code(
                    url=nomination.url,
                    model=model,
                    categories=nomination.categories or None,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "evaluate_org_via_claude_code failed for %s",
                    nomination.url,
                )
                # Conditional CAS on (status, evaluation_attempts) so a
                # concurrent change — sweep_stuck_claims retiring the
                # row, a manual admin edit, or a parallel run — isn't
                # stomped. Mirrors worker._handle_results.
                updated = Nomination.objects.filter(
                    pk=nomination.pk,
                    status=NominationStatus.EVALUATING,
                    evaluation_attempts=nomination.evaluation_attempts,
                ).update(status=NominationStatus.FAILED)
                if updated == 0:
                    logger.warning(
                        "Skipping FAILED update for nomination %s; "
                        "row changed concurrently",
                        nomination.pk,
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"  skipped FAILED update for {nomination.url}: "
                            "row changed concurrently",
                        ),
                    )
                    continue
                self.stdout.write(
                    self.style.ERROR(f"  FAILED: {exc}"),
                )
                failed += 1
                continue

            curator_notes = data.get("curator_notes", {})
            OrganizationEvaluation.objects.create(
                evaluation_data=data,
                ai_model=data.get("evaluated_by", ""),
                ai_recommendation=curator_notes.get(
                    "recommendation", "",
                ),
                ai_confidence=curator_notes.get("confidence"),
                nomination=nomination,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  saved evaluation for {nomination.url}",
                ),
            )
            processed += 1

        self.stdout.write(
            f"Done. Evaluated {processed}, failed {failed}.",
        )

    def _report_skips(self, limit: int) -> None:
        """Report PENDING URLs that are duplicates and will be skipped."""
        pending_urls = list(
            Nomination.objects.filter(
                status=NominationStatus.PENDING,
            ).order_by("submitted_at").values_list(
                "url", flat=True,
            )[:limit],
        )
        if not pending_urls:
            return
        skip_urls = build_skip_urls(set(pending_urls))
        if not skip_urls:
            return
        # Count nominations, not URLs: Nomination.url is not unique,
        # so multiple PENDING rows may share a skipworthy URL.
        skipped_count = sum(url in skip_urls for url in pending_urls)
        self.stdout.write(
            self.style.WARNING(
                f"Skipping {skipped_count} PENDING nomination(s) "
                "(already evaluated, already an organization, "
                "or in 90-day cooldown):",
            ),
        )
        for url in sorted(skip_urls):
            self.stdout.write(f"  - {url}")
