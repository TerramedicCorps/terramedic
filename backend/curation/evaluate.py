#!/usr/bin/env python3
"""CLI tool to evaluate an environmental organization for Terramedic.

Usage:
    python -m curation.evaluate https://example.org
    python -m curation.evaluate https://example.org --dry-run
    python -m curation.evaluate https://example.org --output /tmp/eval.json
    python -m curation.evaluate https://example.org --model claude-opus-4-20250514
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from curation.prompt import SYSTEM_PROMPT

_SCHEMA_PATH = Path(__file__).parent / "schema.json"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate an environmental organization for Terramedic.",
    )
    parser.add_argument(
        "url",
        help="URL of the organization to evaluate.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path. Defaults to pending dir.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON to stdout only; do not write a file.",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model to use (default: claude-sonnet-4-20250514).",
    )
    return parser


def _validate_url(url: str) -> str:
    """Validate that a URL has an http(s) scheme and a domain."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        msg = f"Invalid URL scheme '{parsed.scheme}': must be http or https"
        raise ValueError(msg)
    if not parsed.netloc:
        msg = "Invalid URL: missing domain"
        raise ValueError(msg)
    return url


def _url_to_slug(url: str) -> str:
    """Convert a URL to a filesystem-safe slug from its domain."""
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.replace(".", "-")


def _default_output_dir() -> str:
    """Return the default output directory for evaluations."""
    return str(
        Path(__file__).parent.parent.parent
        / "terramedic-internal"
        / "curation"
        / "pending",
    )


def _load_schema() -> dict[str, Any]:
    """Load the JSON Schema from schema.json."""
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from model response text."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        result: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"Failed to parse JSON from model response: {exc}"
        raise ValueError(msg) from exc
    return result


def evaluate_org(
    url: str,
    model: str,
    client: Any | None = None,
) -> dict[str, Any]:
    """Evaluate an organization and return a validated evaluation dict."""
    _validate_url(url)

    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(
                "Error: ANTHROPIC_API_KEY environment variable is required.",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            from anthropic import Anthropic
        except ImportError:
            print(
                "Error: anthropic package not installed.\n"
                "Install it with: poetry add anthropic",
                file=sys.stderr,
            )
            sys.exit(1)
        client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Evaluate this organization: {url}",
            },
        ],
    )

    result = _extract_json(response.content[0].text)

    result["evaluated_at"] = (
        datetime.datetime.now(datetime.UTC).isoformat()
    )
    result["evaluated_by"] = model

    try:
        import jsonschema
    except ImportError:
        print(
            "Error: jsonschema package not installed.\n"
            "Install it with: poetry add jsonschema",
            file=sys.stderr,
        )
        sys.exit(1)

    schema = _load_schema()
    try:
        jsonschema.validate(instance=result, schema=schema)
    except jsonschema.ValidationError as exc:
        msg = f"Output failed schema validation: {exc.message}"
        raise ValueError(msg) from exc

    return result


def _save_evaluation(data: dict[str, Any], output_path: str) -> None:
    """Save evaluation data as JSON to the given path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    try:
        result = evaluate_org(args.url, model=args.model)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))

    if not args.dry_run:
        if args.output:
            output_path = args.output
        else:
            slug = _url_to_slug(args.url)
            output_path = os.path.join(
                _default_output_dir(), f"{slug}.json",
            )
        _save_evaluation(result, output_path)
        print(f"Saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
