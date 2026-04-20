"""Tests for the ``evaluate_urls_to_fixtures`` command.

Local-only command that wraps ``evaluate_org_via_claude_code`` over a
URL list and emits a single Django fixture JSON file. The output is
designed to be loaded via ``loaddata`` through ``zappa manage`` —
letting re-evaluations produce PENDING rows in the dev DB without
sharing the DB with the laptop that ran the ``claude`` CLI.
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from django.core.management import call_command

from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)

_EVAL_CMD_MODULE = (
    "terramedic.organizations.management.commands."
    "evaluate_urls_to_fixtures"
)


def _fake_eval(url: str, **_: Any) -> dict[str, Any]:
    """Minimal valid-enough evaluation payload for fixture tests."""
    return {
        "org_metadata": {
            "name": f"Org for {url}",
            "website_url": url,
            "description": "Testing org description.",
        },
        "sdg_alignment": [
            {"sdg": 15, "evidence": "Habitat work."},
        ],
        "evidence_of_work": [
            {"activity": "Tree planting.", "type": "restoration"},
        ],
        "accessibility": {"categories": ["volunteer"]},
        "evidence_score": {"score": 3, "rationale": "Moderate."},
        "curator_notes": {
            "recommendation": "include",
            "confidence": 80,
        },
        "evaluated_at": "2026-04-20T21:00:00+00:00",
        "evaluated_by": "claude-code:sonnet",
        "prompt_version": "2026.04.10",
    }


@pytest.mark.django_db
class TestEvaluateUrlsToFixtures:
    def test_writes_one_fixture_row_per_input_url(
        self,
        tmp_path: Path,
    ) -> None:
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "https://a.example\nhttps://b.example\n",
        )
        out_path = tmp_path / "out.json"

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=lambda url, **kw: _fake_eval(url, **kw),
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )

        data = json.loads(out_path.read_text())
        assert len(data) == 2
        for row in data:
            assert row["model"] == "organizations.organizationevaluation"
            assert row["fields"]["status"] == ReviewStatus.PENDING

    def test_fixture_output_is_loaddata_compatible(
        self,
        tmp_path: Path,
    ) -> None:
        """End-to-end: the command's output round-trips through
        Django's ``loaddata`` and produces a PENDING row whose
        evaluation_data matches what claude-code returned."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://a.example\n")
        out_path = tmp_path / "out.json"

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=lambda url, **kw: _fake_eval(url, **kw),
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )
        call_command("loaddata", str(out_path))

        assert OrganizationEvaluation.objects.count() == 1
        ev = OrganizationEvaluation.objects.first()
        assert ev is not None
        assert ev.status == ReviewStatus.PENDING
        assert ev.ai_recommendation == "include"
        assert ev.ai_confidence == 80
        assert ev.ai_model == "claude-code:sonnet"
        assert (
            ev.evaluation_data["org_metadata"]["website_url"]
            == "https://a.example"
        )

    def test_skips_blank_lines_and_comments(
        self,
        tmp_path: Path,
    ) -> None:
        """Real-world URL lists include blanks and `#` comments —
        both should be ignored so a ``zappa manage list_... > f`` +
        manual edits flow stays ergonomic."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "\n".join([
                "https://a.example",
                "",
                "   ",
                "# a comment",
                "  # indented comment",
                "https://b.example",
                "",
            ]),
        )
        out_path = tmp_path / "out.json"

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=lambda url, **kw: _fake_eval(url, **kw),
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )

        data = json.loads(out_path.read_text())
        urls = [
            row["fields"]["evaluation_data"]["org_metadata"]["website_url"]
            for row in data
        ]
        assert urls == ["https://a.example", "https://b.example"]

    def test_eval_failure_is_logged_and_does_not_abort_batch(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A single URL's evaluation can fail (CLI timeout, schema
        validation, etc.) without dropping the rest of the batch."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "https://broken.example\nhttps://ok.example\n",
        )
        out_path = tmp_path / "out.json"

        def fake(url: str, **kw: Any) -> dict[str, Any]:
            if "broken" in url:
                raise RuntimeError("simulated CLI failure")
            return _fake_eval(url, **kw)

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=fake,
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )

        captured = capsys.readouterr()
        assert "broken.example" in captured.err
        assert "simulated CLI failure" in captured.err

        data = json.loads(out_path.read_text())
        urls = [
            row["fields"]["evaluation_data"]["org_metadata"]["website_url"]
            for row in data
        ]
        assert urls == ["https://ok.example"]

    def test_empty_url_list_produces_empty_fixture(
        self,
        tmp_path: Path,
    ) -> None:
        """An empty candidates list — the common case right after a
        prompt bump once everything is already caught up — writes an
        empty fixture rather than erroring."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("\n# nothing here\n")
        out_path = tmp_path / "out.json"

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=lambda url, **kw: _fake_eval(url, **kw),
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )

        assert json.loads(out_path.read_text()) == []

    def test_dry_run_lists_urls_without_calling_claude_or_writing(
        self,
        tmp_path: Path,
    ) -> None:
        """``--dry-run`` lets a curator preview the URL list before
        committing to a 10+ minute claude-code batch. It must skip
        the CLI call entirely and must not write a fixture file."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "https://a.example\n# comment\nhttps://b.example\n",
        )
        out_path = tmp_path / "should-not-exist.json"

        stdout = StringIO()
        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
        ) as mock_eval:
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
                "--dry-run",
                stdout=stdout,
            )

        # The CLI wrapper was never called.
        mock_eval.assert_not_called()
        # No fixture file written.
        assert not out_path.exists()
        # Preview output mentions each URL.
        output = stdout.getvalue()
        assert "https://a.example" in output
        assert "https://b.example" in output
        assert "[dry-run]" in output

    def test_dry_run_does_not_require_out_argument(
        self,
        tmp_path: Path,
    ) -> None:
        """Previewing shouldn't force the caller to pick an output
        path they don't plan to use."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://a.example\n")

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
        ) as mock_eval:
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--dry-run",
            )

        mock_eval.assert_not_called()

    def test_skips_non_http_lines_so_zappa_log_wrapping_survives(
        self,
        tmp_path: Path,
    ) -> None:
        """``zappa manage ... "list_reevaluation_candidates"`` wraps
        the command's stdout with Lambda log lines (START/END/REPORT,
        ``Important! A new version of Zappa ...``, etc.). A curator
        redirecting that straight to a file shouldn't have to strip
        it by hand — only lines starting with http:// or https://
        count as candidate URLs."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("\n".join([
            "Important! A new version of Zappa is available!",
            "START RequestId: abc Version: $LATEST",
            "DEBUG handler Zappa Event: {...}",
            "https://a.example",
            "https://b.example",
            "END RequestId: abc",
            "REPORT Duration: 220ms",
            "ftp://not-an-http-url.example",
            "plain text that isn't a URL",
        ]))
        out_path = tmp_path / "out.json"

        with patch(
            f"{_EVAL_CMD_MODULE}.evaluate_org_via_claude_code",
            side_effect=lambda url, **kw: _fake_eval(url, **kw),
        ):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
                "--out",
                str(out_path),
            )

        data = json.loads(out_path.read_text())
        urls = [
            row["fields"]["evaluation_data"]["org_metadata"][
                "website_url"
            ]
            for row in data
        ]
        assert urls == ["https://a.example", "https://b.example"]

    def test_non_dry_run_requires_out_argument(
        self,
        tmp_path: Path,
    ) -> None:
        """A real run without ``--out`` is almost certainly a user
        mistake — fail loudly rather than silently do nothing."""
        from django.core.management.base import CommandError

        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://a.example\n")

        with pytest.raises(CommandError, match="--out"):
            call_command(
                "evaluate_urls_to_fixtures",
                str(urls_file),
            )
