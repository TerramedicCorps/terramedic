"""Run ``evaluate_org_via_claude_code`` over a list of URLs and write
the results as a Django fixture file suitable for ``loaddata``.

This is the local-only half of the re-evaluation workflow:

1. Get URLs from the DB in the private subnet (remote):
   ``zappa manage <env> "list_reevaluation_candidates" > urls.txt``
2. Evaluate locally via the authenticated ``claude`` CLI (this
   command) — writes ``out.json``, no DB access needed.
3. Ship the fixture back (``zappa update`` to package it, or copy
   to S3 / the Zappa working tree) and load with
   ``zappa manage <env> "loaddata out.json"``.

Requires the shell to be logged into Claude Code (``claude auth``).
"""

from __future__ import annotations

import json
import logging
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from curation.evaluate import evaluate_org_via_claude_code
from terramedic.organizations.models import ReviewStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Evaluate a list of URLs via the local claude CLI and write a"
        " Django fixture JSON that loaddata can consume into"
        " OrganizationEvaluation rows with status=PENDING."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "urls_file",
            help="Path to a file with one URL per line. Blank lines"
                 " and lines starting with # are ignored.",
        )
        parser.add_argument(
            "--out",
            help="Path to write the fixture JSON file. Required"
                 " unless --dry-run is set.",
        )
        parser.add_argument(
            "--model",
            default="sonnet",
            help="Claude Code model alias (default: sonnet).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List URLs that would be evaluated without calling"
                 " the claude CLI or writing the fixture file.",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        urls_file = Path(str(options["urls_file"]))
        dry_run: bool = options["dry_run"]
        model = str(options["model"])
        out_arg = options.get("out")
        out_path = Path(str(out_arg)) if out_arg else None

        if not urls_file.is_file():
            raise CommandError(f"{urls_file} is not a file.")
        if not dry_run and out_path is None:
            raise CommandError("--out is required unless --dry-run.")

        urls = _read_urls(urls_file)

        if dry_run:
            self.stdout.write(
                f"[dry-run] Would evaluate {len(urls)} URL(s) via"
                " claude-code:",
            )
            for url in urls:
                self.stdout.write(f"  {url}")
            self.stdout.write(
                "[dry-run] No claude CLI calls made, no fixture"
                " written.",
            )
            return

        self.stdout.write(
            f"Evaluating {len(urls)} URL(s) via claude-code...",
        )
        fixtures: list[dict[str, Any]] = []
        for url in urls:
            fixture = self._evaluate_one(url, model=model)
            if fixture is not None:
                fixtures.append(fixture)

        assert out_path is not None  # narrowed by the guard above
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(fixtures, indent=2) + "\n")
        self.stdout.write(
            f"Wrote {len(fixtures)} fixture row(s) to {out_path}.",
        )

    def _evaluate_one(
        self,
        url: str,
        *,
        model: str,
    ) -> dict[str, Any] | None:
        self.stdout.write(f"  {url} ...")
        try:
            data = evaluate_org_via_claude_code(url, model=model)
        except Exception as exc:  # noqa: BLE001
            # Any failure — CLI timeout, schema validation,
            # subprocess error — is reported and skipped so the
            # rest of the batch continues.
            self.stderr.write(f"    FAILED {url}: {exc}")
            logger.exception(
                "evaluate_org_via_claude_code failed for %s", url,
            )
            return None

        curator_notes = data.get("curator_notes") or {}
        # loaddata bypasses auto_now_add, so created_at must appear
        # in the fixture or the NOT NULL constraint blocks the insert.
        # ISO 8601 UTC is what Django's date/time parser expects.
        now = datetime.now(tz=UTC).isoformat()
        return {
            "model": "organizations.organizationevaluation",
            "fields": {
                "evaluation_data": data,
                "ai_model": data.get("evaluated_by", ""),
                "ai_recommendation": curator_notes.get(
                    "recommendation", "",
                ),
                "ai_confidence": curator_notes.get("confidence"),
                "status": ReviewStatus.PENDING,
                "reviewer_categories": None,
                "reviewer_reasoning": "",
                "created_at": now,
            },
        }


def _read_urls(path: Path) -> list[str]:
    """Read URLs from a plain-text file, one per line.

    Blank lines and lines whose first non-space character is ``#`` are
    skipped so the file can carry human-readable comments without
    confusing downstream processing.
    """
    urls: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls
