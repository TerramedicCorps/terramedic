"""Load a Django fixture into a Zappa-deployed environment without
a full ``zappa update`` redeploy.

Bridges a local workflow step into the VPC: a curator generates
fixtures on the ``claude``-authenticated laptop (via
``evaluate_urls_to_fixtures``), then runs this command to push them
straight into the target stage's DB. Internally, base64-encodes the
fixture and hands it to ``zappa invoke --raw`` as a small Python
snippet that pipes the decoded JSON to ``loaddata`` over stdin.

Base64 keeps the snippet free of quotes/backslashes/shell
metacharacters, so the encoded payload is safe to embed as a string
literal in the snippet regardless of the fixture's contents.

Example::

    poetry run python manage.py zappa_loaddata dev reeval.json
"""

from __future__ import annotations

import base64
import json
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

# Lambda sync-invoke payload caps at 6 MB. What actually goes over
# the wire is the full invoke payload — the Python snippet we hand to
# ``zappa invoke --raw``, with the fixture embedded as a base64 string
# (~33% expansion) plus snippet scaffolding and zappa's envelope. A
# ~5 MB raw fixture therefore lands at ~6.7 MB on the wire and fails
# the Lambda limit even though the raw bytes would fit. We enforce
# against the encoded payload size and leave ~256 KB for snippet and
# envelope overhead. Fixtures past the limit should go via S3.
_LAMBDA_INVOKE_LIMIT_BYTES = 6 * 1024 * 1024
_SNIPPET_ENVELOPE_OVERHEAD_BYTES = 256 * 1024
_MAX_ENCODED_PAYLOAD_BYTES = (
    _LAMBDA_INVOKE_LIMIT_BYTES - _SNIPPET_ENVELOPE_OVERHEAD_BYTES
)


class Command(BaseCommand):
    help = (
        "Load a Django fixture JSON into a Zappa-deployed environment"
        " without a full redeploy. Base64-encodes the fixture and"
        " ships it to 'zappa invoke --raw' as a Python snippet that"
        " pipes the content into loaddata over stdin."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "stage",
            help="Zappa stage name (e.g. dev, prod).",
        )
        parser.add_argument(
            "fixture",
            help="Path to the fixture JSON file to load.",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        stage: str = options["stage"]
        fixture_path = Path(str(options["fixture"]))

        if not fixture_path.is_file():
            raise CommandError(
                f"Fixture not found: {fixture_path}",
            )

        payload = fixture_path.read_bytes()

        try:
            json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"Fixture is not valid JSON: {exc}",
            ) from exc

        snippet = _build_invoke_snippet(payload)

        # Size-check the snippet that actually goes on the wire, not
        # the raw fixture: base64 expands content ~33%, which can push
        # an innocuous-looking fixture past the Lambda invoke limit.
        encoded_size = len(snippet.encode("utf-8"))
        if encoded_size > _MAX_ENCODED_PAYLOAD_BYTES:
            raise CommandError(
                f"Fixture is {len(payload):,} bytes raw and encodes"
                f" to {encoded_size:,} bytes — too large for inline"
                f" zappa invoke (limit"
                f" {_MAX_ENCODED_PAYLOAD_BYTES:,}). Upload to S3 and"
                " loaddata from there.",
            )

        self.stdout.write(
            f"Loading {fixture_path} into {stage} via zappa invoke"
            f" ({len(payload):,} bytes)...",
        )
        try:
            result = subprocess.run(
                ["zappa", "invoke", stage, snippet, "--raw"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CommandError(
                "Could not find the 'zappa' CLI on PATH — install"
                " it locally (it's in the Poetry dev deps) and"
                " retry.",
            ) from exc

        if result.returncode != 0:
            raise CommandError(
                f"zappa invoke failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}",
            )

        self.stdout.write(result.stdout)
        self.stdout.write(self.style.SUCCESS("Fixture loaded."))


def _build_invoke_snippet(fixture_bytes: bytes) -> str:
    """Build the Python snippet handed to ``zappa invoke --raw``.

    Base64-encoded content + single-quoted string literal keeps the
    snippet safe from shell quoting issues and from any combination
    of characters that might appear inside the fixture JSON.

    ``loaddata`` reads from ``sys.stdin`` directly when given the ``-``
    fixture label; ``call_command``'s ``stdin`` kwarg is ignored by
    ``BaseCommand.execute``, so the snippet reassigns ``sys.stdin``
    in-place to push the decoded fixture in.
    """
    encoded = base64.b64encode(fixture_bytes).decode("ascii")
    return (
        "import base64\n"
        "import sys\n"
        "from io import StringIO\n"
        "from django.core.management import call_command\n"
        f"data = base64.b64decode('{encoded}').decode('utf-8')\n"
        "sys.stdin = StringIO(data)\n"
        "call_command('loaddata', '--format=json', '-')\n"
    )
