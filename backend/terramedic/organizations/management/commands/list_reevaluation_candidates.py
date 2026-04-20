"""Print website URLs of evaluations that predate the current
``PROMPT_VERSION``.

Lambda-safe (pure DB query, no external process). Intended to be run
via ``zappa manage <env> "list_reevaluation_candidates"`` from a
laptop that can't reach the private-subnet RDS directly — the stdout
feeds into the local ``evaluate_urls_to_fixtures`` command, which
shells out to the ``claude`` CLI.

``--status`` selects which review states to include (default:
``rejected``). Typical use:

- ``rejected`` (default): revisit rejections that may have been
  driven by the older prompt's weaknesses — most common flow after
  a prompt bump, since reruns here can surface orgs that now qualify
  without disturbing already-live approvals.
- ``approved``: re-run live orgs if the prompt changes something
  that should flow through (e.g. description wording).
- ``pending``: supersede still-unreviewed evaluations with fresh
  ones before a reviewer gets to them.
- ``all``: every evaluation with a stale ``prompt_version``.
"""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from curation.prompt import PROMPT_VERSION
from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)

_STATUS_CHOICES = ("pending", "approved", "rejected", "all")
_DEFAULT_STATUS = "rejected"


class Command(BaseCommand):
    help = (
        "Print website URLs of evaluations whose stored prompt_version"
        f" lags the current {PROMPT_VERSION}. One URL per line,"
        " pk-ascending for determinism. Filter by --status"
        f" (default: {_DEFAULT_STATUS})."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--status",
            choices=_STATUS_CHOICES,
            default=_DEFAULT_STATUS,
            help="Review state to include. 'all' matches every status"
                 f" (default: {_DEFAULT_STATUS}).",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        status_filter: str = options["status"]
        qs = OrganizationEvaluation.objects.all().order_by("pk")
        if status_filter != "all":
            # Choice is validated to a ReviewStatus member; map
            # explicitly so the enum stays the source of truth.
            status_map = {
                "pending": ReviewStatus.PENDING,
                "approved": ReviewStatus.APPROVED,
                "rejected": ReviewStatus.REJECTED,
            }
            qs = qs.filter(status=status_map[status_filter])

        for ev in qs:
            data = ev.evaluation_data or {}
            if data.get("prompt_version") == PROMPT_VERSION:
                continue
            url = (data.get("org_metadata") or {}).get("website_url")
            if not url:
                continue
            self.stdout.write(url)
