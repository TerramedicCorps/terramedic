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
_MAX_PAGE_CHARS = 12000
_FETCH_TIMEOUT = 15


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


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text, stripping scripts/styles."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return text[:_MAX_PAGE_CHARS]


_SUBPAGE_PATTERNS = (
    "volunteer", "get-involved", "get_involved", "getinvolved",
    "event", "action", "donate", "giving", "support",
    "about", "mission", "team", "staff", "leadership",
    "career", "job", "work-with", "program", "project",
    "what-we-do", "our-work", "impact", "conservation",
    "community", "chapter", "local", "visit",
)
_MAX_SUBPAGES = 5


def _extract_subpage_urls(html: str, base_url: str) -> list[str]:
    """Extract internal links that likely contain engagement info."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    base_origin = f"{parsed_base.scheme}://{base_domain}"

    seen: set[str] = set()
    results: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]

        if href.startswith("/"):
            full_url = base_origin + href
        elif href.startswith(("http://", "https://")):
            if urlparse(href).netloc != base_domain:
                continue
            full_url = href
        else:
            continue

        full_url = full_url.rstrip("/").split("?")[0].split("#")[0]

        path_lower = urlparse(full_url).path.lower()
        if not any(p in path_lower for p in _SUBPAGE_PATTERNS):
            continue

        if full_url in seen:
            continue
        seen.add(full_url)
        results.append(full_url)

    return results[:_MAX_SUBPAGES]


def _fetch_page_text(url: str) -> str | None:
    """Fetch a URL and return its text content, or None on failure."""
    import httpx

    try:
        resp = httpx.get(
            url,
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Terramedic-Curator/1.0"},
        )
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.InvalidURL):
        return None
    return _html_to_text(resp.text)


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


_VALID_ACTIVITY_TYPES = frozenset({
    "advocacy",
    "conservation",
    "education",
    "litigation",
    "policy",
    "research",
    "restoration",
    "other",
})

_VALID_CATEGORIES = frozenset({
    "donate",
    "volunteer",
    "resource",
    "action",
    "career",
})


def _clean_response(data: dict[str, Any]) -> None:
    """Fix common model output issues before schema validation."""
    for item in data.get("evidence_of_work", []):
        if item.get("type") not in _VALID_ACTIVITY_TYPES:
            item["type"] = "other"

    accessibility = data.get("accessibility")
    if accessibility and "categories" in accessibility:
        accessibility["categories"] = [
            c for c in accessibility["categories"]
            if c in _VALID_CATEGORIES
        ]

    # Remove null values for optional fields — the schema uses
    # type-specific validation, so null isn't valid; omission is.
    _strip_nulls(data)


def _strip_nulls(obj: Any) -> None:
    """Recursively remove keys with None values from dicts."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if obj[key] is None:
                del obj[key]
            else:
                _strip_nulls(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            _strip_nulls(item)


def _build_user_message(url: str) -> str:
    """Fetch the org's website and build the user message for the model."""
    import httpx

    print(f"Fetching {url} ...", file=sys.stderr)
    homepage_html = None
    try:
        resp = httpx.get(
            url,
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Terramedic-Curator/1.0"},
        )
        resp.raise_for_status()
        homepage_html = resp.text
    except (httpx.HTTPError, httpx.InvalidURL):
        pass

    page_text = _html_to_text(homepage_html) if homepage_html else None

    subpage_texts: list[str] = []
    if homepage_html:
        subpage_urls = _extract_subpage_urls(homepage_html, url)
        for sub_url in subpage_urls:
            print(f"  Fetching {sub_url} ...", file=sys.stderr)
            sub_text = _fetch_page_text(sub_url)
            if sub_text:
                subpage_texts.append(f"### {sub_url}\n\n{sub_text}")

    message = f"Evaluate this organization: {url}"
    if page_text:
        message += (
            "\n\n## Homepage content\n\n"
            "Below is text extracted from the organization's website. "
            "Use this as primary evidence — do not fabricate information "
            "that contradicts what is shown here.\n\n"
            f"{page_text}"
        )
        if subpage_texts:
            message += (
                "\n\n## Additional pages\n\n"
                + "\n\n".join(subpage_texts)
            )
    else:
        message += (
            "\n\nNote: the homepage could not be fetched. "
            "Evaluate based on your training data and flag "
            "that the website was unreachable in curator_notes.flags."
        )
    return message


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

    user_content = _build_user_message(url)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_content,
            },
        ],
    )

    result = _extract_json(response.content[0].text)  # type: ignore[union-attr]

    _clean_response(result)

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
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    try:
        validator.validate(result)
    except jsonschema.ValidationError as exc:
        msg = f"Output failed schema validation: {exc.message}"
        raise ValueError(msg) from exc

    return result


def _save_evaluation(data: dict[str, Any], output_path: str) -> None:
    """Save evaluation data as JSON to the given path."""
    output_parent = Path(output_path).parent
    if output_parent != Path("."):
        output_parent.mkdir(parents=True, exist_ok=True)
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
