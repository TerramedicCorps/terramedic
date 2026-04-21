"""Tests for the ``zappa_loaddata`` command.

Loads a Django fixture JSON into a Zappa-deployed environment without
a full ``zappa update`` redeploy, by base64-encoding the fixture and
handing it to ``zappa invoke --raw`` as a small Python snippet. Lets
a curator re-evaluate orgs locally (via claude-code) and push results
straight into the dev DB in one shot.
"""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

_CMD_MODULE = (
    "terramedic.organizations.management.commands.zappa_loaddata"
)


def _valid_fixture_bytes() -> bytes:
    """A minimal two-row fixture that mirrors what
    ``evaluate_urls_to_fixtures`` emits."""
    return json.dumps([
        {
            "model": "organizations.organizationevaluation",
            "fields": {
                "evaluation_data": {"org_metadata": {"name": "A"}},
                "status": "pending",
                "created_at": "2026-04-20T21:00:00+00:00",
            },
        },
        {
            "model": "organizations.organizationevaluation",
            "fields": {
                "evaluation_data": {"org_metadata": {"name": "B"}},
                "status": "pending",
                "created_at": "2026-04-20T21:00:00+00:00",
            },
        },
    ]).encode("utf-8")


def _mock_run_ok() -> MagicMock:
    """A ``subprocess.run`` mock that reports zappa success."""
    result = MagicMock()
    result.returncode = 0
    result.stdout = "Installed 2 object(s) from 1 fixture(s)\n"
    result.stderr = ""
    return result


class TestZappaLoaddata:
    def test_invokes_zappa_invoke_with_raw_flag(
        self,
        tmp_path: Path,
    ) -> None:
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(_valid_fixture_bytes())

        with patch(
            f"{_CMD_MODULE}.subprocess.run",
            return_value=_mock_run_ok(),
        ) as mock_run:
            call_command("zappa_loaddata", "dev", str(fixture))

        mock_run.assert_called_once()
        argv = mock_run.call_args.args[0]
        # argv is a list passed to subprocess (no shell invocation).
        assert argv[:3] == ["zappa", "invoke", "dev"]
        assert "--raw" in argv

    def test_embeds_fixture_as_base64_in_python_snippet(
        self,
        tmp_path: Path,
    ) -> None:
        """Base64 keeps the snippet free of quotes/backslashes so
        shell-escape bugs can't corrupt the fixture content."""
        fixture_bytes = _valid_fixture_bytes()
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(fixture_bytes)
        expected_b64 = base64.b64encode(fixture_bytes).decode("ascii")

        with patch(
            f"{_CMD_MODULE}.subprocess.run",
            return_value=_mock_run_ok(),
        ) as mock_run:
            call_command("zappa_loaddata", "dev", str(fixture))

        argv = mock_run.call_args.args[0]
        # argv is ["zappa", "invoke", stage, snippet, "--raw"] — the
        # snippet sits before --raw, so match it by content.
        snippet = next(
            arg for arg in argv
            if isinstance(arg, str) and "base64" in arg
        )
        assert expected_b64 in snippet
        assert "loaddata" in snippet

    def test_passes_stage_argument_through_to_zappa(
        self,
        tmp_path: Path,
    ) -> None:
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(_valid_fixture_bytes())

        with patch(
            f"{_CMD_MODULE}.subprocess.run",
            return_value=_mock_run_ok(),
        ) as mock_run:
            call_command("zappa_loaddata", "prod", str(fixture))

        argv = mock_run.call_args.args[0]
        assert "prod" in argv
        assert "dev" not in argv

    def test_missing_fixture_file_errors_clearly(
        self,
        tmp_path: Path,
    ) -> None:
        missing = tmp_path / "nope.json"

        with pytest.raises(CommandError, match="nope.json"):
            call_command("zappa_loaddata", "dev", str(missing))

    def test_invalid_json_errors_before_invoking_zappa(
        self,
        tmp_path: Path,
    ) -> None:
        """Sanity-check parsing locally so a malformed fixture fails
        in ~1 ms rather than after a Lambda round-trip."""
        fixture = tmp_path / "bad.json"
        fixture.write_text("{ not valid json")

        with (
            patch(f"{_CMD_MODULE}.subprocess.run") as mock_run,
            pytest.raises(CommandError, match="JSON"),
        ):
            call_command("zappa_loaddata", "dev", str(fixture))

        mock_run.assert_not_called()

    def test_fixture_exceeding_size_limit_errors(
        self,
        tmp_path: Path,
    ) -> None:
        """Lambda sync-invoke payload tops out at 6 MB; we refuse
        fixtures over ~5 MB to leave headroom for the snippet."""
        huge_rows = [
            {
                "model": "organizations.organizationevaluation",
                "fields": {
                    "evaluation_data": {"blob": "x" * 10_000},
                    "status": "pending",
                    "created_at": "2026-04-20T21:00:00+00:00",
                },
            }
            for _ in range(600)
        ]
        fixture = tmp_path / "big.json"
        fixture.write_bytes(json.dumps(huge_rows).encode("utf-8"))

        with (
            patch(f"{_CMD_MODULE}.subprocess.run") as mock_run,
            pytest.raises(CommandError, match="too large"),
        ):
            call_command("zappa_loaddata", "dev", str(fixture))

        mock_run.assert_not_called()

    def test_zappa_nonzero_exit_becomes_command_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Surface zappa's stderr in the exception so a failed run
        gives the curator enough info to diagnose without hunting
        through subprocess output."""
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(_valid_fixture_bytes())

        failed = MagicMock(returncode=1, stdout="", stderr="boom")
        with (
            patch(
                f"{_CMD_MODULE}.subprocess.run", return_value=failed,
            ),
            pytest.raises(CommandError, match="boom"),
        ):
            call_command("zappa_loaddata", "dev", str(fixture))

    def test_missing_zappa_binary_gives_actionable_error(
        self,
        tmp_path: Path,
    ) -> None:
        """``FileNotFoundError`` from subprocess is cryptic; translate
        it to a message that names the missing binary."""
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(_valid_fixture_bytes())

        with (
            patch(
                f"{_CMD_MODULE}.subprocess.run",
                side_effect=FileNotFoundError(2, "not found", "zappa"),
            ),
            pytest.raises(CommandError, match="zappa"),
        ):
            call_command("zappa_loaddata", "dev", str(fixture))

    def test_subprocess_called_without_shell_interpolation(
        self,
        tmp_path: Path,
    ) -> None:
        """Double-check that we never hand a command string to a
        shell — argv must be a list. Prevents shell-injection if a
        future fixture path or stage ends up reflecting user input."""
        fixture = tmp_path / "reeval.json"
        fixture.write_bytes(_valid_fixture_bytes())

        with patch(
            f"{_CMD_MODULE}.subprocess.run",
            return_value=_mock_run_ok(),
        ) as mock_run:
            call_command("zappa_loaddata", "dev", str(fixture))

        _, kwargs = mock_run.call_args
        assert kwargs.get("shell", False) is False
        assert isinstance(mock_run.call_args.args[0], list)


@pytest.mark.parametrize("_fixture", [_valid_fixture_bytes()])
def test_subprocess_module_is_the_real_one(_fixture: Any) -> None:
    """Guard rail: the tests patch ``subprocess.run`` on the command
    module's namespace. If the import path changes, the patch falls
    through to the real subprocess and tests would hit the zappa
    binary for real. This test fails loudly in that case."""
    from terramedic.organizations.management.commands import (
        zappa_loaddata,
    )
    assert zappa_loaddata.subprocess is subprocess
