#!/usr/bin/env python3
"""CLI tool to evaluate an environmental organization for Terramedic.

Usage:
    python -m curation.evaluate https://example.org
    python -m curation.evaluate https://example.org --categories donate resource
    python -m curation.evaluate https://example.org --dry-run
    python -m curation.evaluate https://example.org --output /tmp/eval.json
    python -m curation.evaluate https://example.org --model claude-opus-4-20250514
"""

from __future__ import annotations

import argparse
import datetime
import functools
import ipaddress
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from curation.json_utils import extract_json
from curation.prompt import PROMPT_VERSION, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.json"
_MAX_PAGE_CHARS = 12000
_FETCH_TIMEOUT = 15
_CLAUDE_CLI_TIMEOUT = 600
_CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
_MAX_REDIRECT_HOPS = 5


def _url_resolves_to_public(url: str) -> bool:
    """Return True iff *url* parses to an http(s) scheme and every IP
    its hostname resolves to is a public address.

    Catches DNS-rebinding-style attacks where a public hostname maps to
    a private IP at fetch time (AWS IMDS, internal services). Used as a
    pre-flight check before httpx fetches and re-checked on every
    redirect hop.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    host = parsed.hostname
    if host == "localhost":
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_unspecified
            or addr.is_multicast
            or addr.is_reserved
        ):
            return False
    return True


@functools.cache
def _read_settings_effort() -> str:
    """Read ``effortLevel`` from the user's ``~/.claude/settings.json``
    once per process. Batch runs (e.g. ``evaluate_urls_to_fixtures``
    with N URLs) hit this on every call; the file changes only when
    the user re-runs ``claude config``."""
    try:
        with open(_CLAUDE_SETTINGS_PATH) as f:
            settings = json.load(f)
    except (OSError, json.JSONDecodeError):
        return "default"
    level = settings.get("effortLevel")
    return level if isinstance(level, str) and level else "default"


def _resolve_effort(explicit: str | None) -> str:
    """Return the effort level for metadata stamping.

    Priority: ``--effort`` arg > ``effortLevel`` from the user's
    ``~/.claude/settings.json`` > ``"default"`` sentinel. The CLI
    envelope doesn't surface the resolved effort, so we re-derive it
    from the same source the CLI does — close enough for provenance.
    """
    if explicit:
        return explicit
    return _read_settings_effort()


def _resolve_model(envelope: dict[str, Any], fallback: str) -> str:
    """Return the resolved model ID from a CLI envelope.

    Claude Code uses a small orchestrator model (Haiku) for routing
    before handing off to the requested model, so ``modelUsage``
    typically contains multiple entries. The metadata stamp picks the
    one with the highest ``outputTokens`` — the model that actually
    produced the response — so long Opus runs aren't misattributed to
    the orchestrator. Falls back to the input alias when an older CLI
    omits ``modelUsage`` or all entries lack ``outputTokens``.
    """
    usage = envelope.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        return fallback

    def _output_tokens(entry: Any) -> int:
        if not isinstance(entry, dict):
            return 0
        tokens = entry.get("outputTokens")
        return tokens if isinstance(tokens, int) else 0

    return max(usage, key=lambda model_id: _output_tokens(usage[model_id]))


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
    parser.add_argument(
        "--categories",
        nargs="*",
        default=[],
        help="Nominated categories (e.g. donate volunteer resource everyday career).",
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Save to database instead of file. Requires Django.",
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
        result: dict[str, Any] = json.load(f)
        return result


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


def _safe_get(url: str) -> Any:
    """``httpx.get`` with manual redirect handling that re-validates
    every hop's hostname against private/internal IP ranges.

    Returns the final ``httpx.Response`` on success, or ``None`` if any
    hop resolves to a non-public address or the request errors. Raises
    no exceptions to the caller — the curation pipeline treats fetch
    failures as missing pages and proceeds.
    """
    import httpx

    current = url
    for _hop in range(_MAX_REDIRECT_HOPS + 1):
        if not _url_resolves_to_public(current):
            return None
        try:
            resp = httpx.get(
                current,
                timeout=_FETCH_TIMEOUT,
                follow_redirects=False,
                headers={"User-Agent": "Terramedic-Curator/1.0"},
            )
        except (httpx.HTTPError, httpx.InvalidURL):
            return None
        if resp.is_redirect:
            location = resp.headers.get("location")
            if not location:
                return None
            current = urljoin(current, location)
            continue
        try:
            resp.raise_for_status()
        except httpx.HTTPError:
            return None
        return resp
    return None


def _fetch_page_text(url: str) -> str | None:
    """Fetch a URL and return its text content, or None on failure."""
    resp = _safe_get(url)
    if resp is None:
        return None
    return _html_to_text(resp.text)


def _enum_from_schema(
    schema: dict[str, Any], *path: str,
) -> frozenset[str]:
    """Extract an enum array from a nested schema path."""
    node = schema
    for key in path:
        node = node[key]
    return frozenset(node)


_SCHEMA = _load_schema()

# Fields the curation layer stamps onto the response after the model
# replies. The model has no way to produce them correctly, so they're
# stripped from ``required`` in the schema we hand to the CLI's
# ``--json-schema`` flag — otherwise the CLI would reject every valid
# response for missing them.
_PROGRAMMATIC_FIELDS: frozenset[str] = frozenset({
    "evaluated_at", "evaluated_by", "prompt_version",
    "duration_ms", "evaluation_history",
})


@functools.cache
def _model_output_schema_json() -> str:
    """Return the JSON Schema string passed to ``claude --json-schema``.

    Drops fields the curation layer injects post-call from ``required``
    so the CLI's structured-output validator only enforces what the
    model can actually produce. Compact form to keep the embedded
    string under any CLI argv length limits.
    """
    schema = json.loads(json.dumps(_SCHEMA))
    schema["required"] = [
        r for r in schema.get("required", [])
        if r not in _PROGRAMMATIC_FIELDS
    ]
    return json.dumps(schema, separators=(",", ":"))


_VALID_ACTIVITY_TYPES: frozenset[str] = _enum_from_schema(
    _SCHEMA,
    "properties", "evidence_of_work", "items",
    "properties", "type", "enum",
)

_VALID_CATEGORIES: frozenset[str] = _enum_from_schema(
    _SCHEMA,
    "properties", "accessibility", "properties",
    "categories", "items", "enum",
)


def _clean_response(data: dict[str, Any]) -> None:
    """Fix common model output issues before schema validation."""
    for item in data.get("evidence_of_work", []):
        if item.get("type") not in _VALID_ACTIVITY_TYPES:
            item["type"] = "other"

    accessibility = data.get("accessibility")
    if accessibility and "categories" in accessibility:
        accessibility["categories"] = [
            c if c in _VALID_CATEGORIES else "other"
            for c in accessibility["categories"]
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


def _build_user_message(
    url: str,
    categories: list[str] | None = None,
) -> tuple[str, int]:
    """Fetch the org's website and build the user message for the model.

    Returns ``(message, pages_fetched)`` — the count tracks every page
    the curation layer attempted to fetch via ``httpx`` (homepage +
    subpages) regardless of whether each fetch succeeded, so it lines
    up 1:1 with the ``Fetching ...`` lines written to stderr. This is
    distinct from any ``server_tool_use`` web fetches Claude might do
    on top; callers log both.
    """
    print(f"Fetching {url} ...", file=sys.stderr)
    pages_fetched = 1
    homepage_html = None
    resp = _safe_get(url)
    if resp is not None:
        homepage_html = resp.text

    page_text = _html_to_text(homepage_html) if homepage_html else None

    subpage_texts: list[str] = []
    if homepage_html:
        subpage_urls = _extract_subpage_urls(homepage_html, url)
        pages_fetched += len(subpage_urls)
        for sub_url in subpage_urls:
            print(f"  Fetching {sub_url} ...", file=sys.stderr)
            sub_text = _fetch_page_text(sub_url)
            if sub_text:
                subpage_texts.append(f"### {sub_url}\n\n{sub_text}")

    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    message = f"Today's date is {today}.\n\nEvaluate this organization: {url}"
    if categories:
        cats = ", ".join(categories)
        message += (
            f"\n\nThis organization was nominated under these categories: "
            f"{cats}. Pay special attention to evidence supporting these "
            f"categories during your evaluation."
        )
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
    return message, pages_fetched


def _validate_against_schema(
    data: dict[str, Any], source: str = "Output",
) -> None:
    """Validate *data* against ``schema.json``.

    Raises ``ValueError`` on mismatch with a message prefixed by
    *source* (e.g. ``"Claude Code output"``). Raises ``RuntimeError``
    if ``jsonschema`` isn't installed — avoids ``sys.exit`` so callers
    inside a Django management command can catch the failure and roll
    the row back via CAS instead of hard-exiting mid-batch.
    """
    try:
        import jsonschema
    except ImportError as exc:
        msg = (
            "jsonschema package not installed. "
            "Install it with: poetry install"
        )
        raise RuntimeError(msg) from exc

    validator = jsonschema.Draft202012Validator(
        _load_schema(),
        format_checker=jsonschema.FormatChecker(),
    )
    try:
        validator.validate(data)
    except jsonschema.ValidationError as exc:
        msg = f"{source} failed schema validation: {exc.message}"
        raise ValueError(msg) from exc


def evaluate_org(
    url: str,
    model: str,
    client: Any | None = None,
    categories: list[str] | None = None,
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
                "Install it with: poetry install",
                file=sys.stderr,
            )
            sys.exit(1)
        client = Anthropic(api_key=api_key)

    user_content, pages_fetched = _build_user_message(
        url, categories=categories,
    )

    t0 = time.monotonic()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": user_content,
            },
        ],
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            },
        ],
    )

    # With web search, response may contain non-text blocks.
    # Find the last text block which contains the JSON output.
    text_block = None
    search_count = 0
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_block = block
        elif block_type == "server_tool_use":
            search_count += 1

    elapsed = time.monotonic() - t0
    usage = getattr(response, "usage", None)
    # ``pages_fetched`` counts homepage + subpages the curation layer
    # pulled inline via httpx. ``server_searches`` counts the
    # Claude-side web_search tool calls. They're separate cost
    # drivers, so log both.
    logger.info(
        "eval usage url=%s elapsed_s=%.1f input=%s output=%s "
        "cache_read=%s cache_creation=%s pages_fetched=%s "
        "server_searches=%s",
        url,
        elapsed,
        getattr(usage, "input_tokens", None),
        getattr(usage, "output_tokens", None),
        getattr(usage, "cache_read_input_tokens", None),
        getattr(usage, "cache_creation_input_tokens", None),
        pages_fetched,
        search_count,
    )

    if text_block is None:
        msg = "No text block found in model response"
        raise ValueError(msg)

    result = extract_json(text_block.text)  # type: ignore[union-attr]

    _clean_response(result)

    result["evaluated_at"] = (
        datetime.datetime.now(datetime.UTC).isoformat()
    )
    result["evaluated_by"] = model
    result["prompt_version"] = PROMPT_VERSION
    result["duration_ms"] = int(elapsed * 1000)
    # Preserve the nominated URL verbatim. The model tends to
    # normalize ``website_url`` to the domain root, which would
    # collapse subpages (local chapter pages, specific program
    # landing pages) into a single Organization record.
    result.setdefault("org_metadata", {})["website_url"] = url

    _validate_against_schema(result, source="Output")

    return result


def _invoke_claude_cli(
    cmd: list[str],
    timeout: int,
    url: str,
    pages_fetched: int = 0,
    model_fallback: str = "",
) -> tuple[str, int | None, str]:
    """Run the ``claude`` CLI and return ``(text, duration_ms, model)``.

    ``duration_ms`` is wall-clock for the whole call including tool
    turns. ``model`` is the resolved model ID from ``modelUsage``,
    falling back to ``model_fallback`` (the input alias) when an older
    CLI omits the field. Handles exit code, JSON envelope parsing,
    ``is_error`` handling, and per-call usage logging. Raises
    ``RuntimeError`` on non-zero exit or ``is_error: true``;
    ``ValueError`` on malformed stdout or missing ``result`` field.
    """
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        msg = (
            f"claude CLI exited with code {proc.returncode}: "
            f"{proc.stderr[:500] or proc.stdout[:500]}"
        )
        raise RuntimeError(msg)

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        msg = f"claude CLI stdout was not valid JSON: {exc}"
        raise ValueError(msg) from exc

    if envelope.get("is_error"):
        msg = (
            f"claude CLI reported error: "
            f"{envelope.get('result', 'unknown')}"
        )
        raise RuntimeError(msg)

    text = envelope.get("result", "")
    if not text:
        msg = "claude CLI envelope had no 'result' field"
        raise ValueError(msg)

    tool_use = envelope.get("usage", {}).get("server_tool_use", {})
    # total_cost_usd is 0 on Max subscriptions (no per-token billing);
    # kept for parity with the API-path usage log so the two sources
    # can be grepped the same way.
    # ``duration_ms`` is wall-clock for the whole call including tool
    # turns; ``duration_api_ms`` is just Anthropic API time. The gap
    # between them is where WebFetch / WebSearch latency lives, so
    # log both when diagnosing slow evaluations.
    logger.info(
        "eval via claude-code url=%s duration_ms=%s duration_api_ms=%s "
        "cost_usd=%s pages_fetched=%s server_searches=%s "
        "server_fetches=%s",
        url,
        envelope.get("duration_ms"),
        envelope.get("duration_api_ms"),
        envelope.get("total_cost_usd"),
        pages_fetched,
        tool_use.get("web_search_requests"),
        tool_use.get("web_fetch_requests"),
    )
    duration_ms = envelope.get("duration_ms")
    return (
        text,
        duration_ms if isinstance(duration_ms, int) else None,
        _resolve_model(envelope, model_fallback),
    )


def _build_claude_cli_cmd(
    user_content: str, model: str, effort: str | None,
) -> list[str]:
    cmd = [
        "claude",
        "-p", user_content,
        "--append-system-prompt", SYSTEM_PROMPT,
        "--tools", "WebSearch,WebFetch",
        "--output-format", "json",
        "--permission-mode", "dontAsk",
        "--model", model,
        "--json-schema", _model_output_schema_json(),
    ]
    if effort:
        cmd.extend(["--effort", effort])
    return cmd


def _parse_and_stamp_response(
    text: str,
    *,
    url: str,
    duration_ms: int | None,
    resolved_model: str,
    effort: str | None,
) -> dict[str, Any]:
    """Extract JSON, clean, stamp programmatic fields, and validate.

    Raises ``ValueError`` from ``extract_json`` or
    ``_validate_against_schema`` — both are model-output issues that the
    retry path can recover from by feeding the error back to the model.
    """
    data = extract_json(text)
    _clean_response(data)
    data["evaluated_at"] = (
        datetime.datetime.now(datetime.UTC).isoformat()
    )
    data["evaluated_by"] = (
        f"claude-code:{resolved_model}@{_resolve_effort(effort)}"
    )
    data["prompt_version"] = PROMPT_VERSION
    if duration_ms is not None:
        data["duration_ms"] = duration_ms
    # Preserve the nominated URL verbatim. The model tends to
    # normalize ``website_url`` to the domain root, which would
    # collapse subpages (local chapter pages, specific program
    # landing pages) into a single Organization record.
    data.setdefault("org_metadata", {})["website_url"] = url

    _validate_against_schema(data, source="Claude Code output")
    return data


def evaluate_org_via_claude_code(
    url: str,
    model: str = "sonnet",
    categories: list[str] | None = None,
    timeout: int = _CLAUDE_CLI_TIMEOUT,
    effort: str | None = None,
) -> dict[str, Any]:
    """Evaluate an organization by shelling out to the ``claude`` CLI.

    Uses the caller's Claude Code session, so billing hits the Max
    subscription rather than the per-token Anthropic API. Requires the
    shell to be logged into Claude Code (``claude auth``). Not usable
    from Lambda — Claude Code has no service-account mode.

    Returns a schema-validated evaluation dict, just like ``evaluate_org``.
    ``evaluated_by`` is stamped with a ``claude-code:`` prefix so the two
    paths are distinguishable in stored records.

    On a model-output failure (unparseable JSON or schema validation
    error) the call is retried once with the validator's error fed back
    to the model. CLI / network / auth failures (``RuntimeError``,
    ``TimeoutExpired``) propagate without retry — those are not things
    the model can fix.
    """
    _validate_url(url)
    user_content, pages_fetched = _build_user_message(
        url, categories=categories,
    )

    cmd = _build_claude_cli_cmd(user_content, model, effort)
    text, duration_ms, resolved_model = _invoke_claude_cli(
        cmd,
        timeout=timeout,
        url=url,
        pages_fetched=pages_fetched,
        model_fallback=model,
    )
    try:
        return _parse_and_stamp_response(
            text,
            url=url,
            duration_ms=duration_ms,
            resolved_model=resolved_model,
            effort=effort,
        )
    except ValueError as exc:
        logger.warning(
            "Claude Code output invalid for %s; retrying once: %s",
            url, exc,
        )
        retry_error = str(exc)

    retry_content = (
        f"{user_content}\n\n## Retry\n\nYour previous response could "
        f"not be used. Validation error: {retry_error}\n\nReturn ONLY "
        "a single JSON object that conforms to the schema. No prose, "
        "no markdown fences, no commentary."
    )
    retry_cmd = _build_claude_cli_cmd(retry_content, model, effort)
    text, duration_ms, resolved_model = _invoke_claude_cli(
        retry_cmd,
        timeout=timeout,
        url=url,
        pages_fetched=pages_fetched,
        model_fallback=model,
    )
    return _parse_and_stamp_response(
        text,
        url=url,
        duration_ms=duration_ms,
        resolved_model=resolved_model,
        effort=effort,
    )


def _save_evaluation(data: dict[str, Any], output_path: str) -> None:
    """Save evaluation data as JSON to the given path.

    If a prior evaluation exists at the same path, its metadata is
    appended to the ``evaluation_history`` array so reviewers can
    compare scores across prompt versions.
    """
    output_parent = Path(output_path).parent
    if output_parent != Path("."):
        output_parent.mkdir(parents=True, exist_ok=True)

    path = Path(output_path)
    if path.exists():
        with open(path) as f:
            prior = json.load(f)
        history: list[dict[str, Any]] = prior.get(
            "evaluation_history", [],
        )
        history.append({
            "prompt_version": prior.get("prompt_version", "unknown"),
            "evaluated_at": prior.get("evaluated_at", ""),
            "evaluated_by": prior.get("evaluated_by", ""),
            "score": prior.get("evidence_score", {}).get("score", 0),
            "recommendation": prior.get(
                "curator_notes", {},
            ).get("recommendation", ""),
        })
        data["evaluation_history"] = history

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _save_to_db(data: dict[str, Any]) -> int:
    """Save evaluation data as an OrganizationEvaluation record.

    Returns the ID of the created record.
    """
    try:
        import django
    except ImportError:
        msg = (
            "Django is not installed. "
            "Use --output to save to a file instead."
        )
        raise RuntimeError(msg) from None

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "terramedic.core.settings",
    )
    django.setup()

    from terramedic.organizations.models import OrganizationEvaluation

    curator_notes = data.get("curator_notes", {})
    obj = OrganizationEvaluation.objects.create(
        evaluation_data=data,
        ai_model=data.get("evaluated_by", ""),
        ai_recommendation=curator_notes.get("recommendation", ""),
        ai_confidence=curator_notes.get("confidence"),
    )
    return obj.pk


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    try:
        result = evaluate_org(
            args.url,
            model=args.model,
            categories=args.categories or None,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))

    if not args.dry_run:
        if args.db:
            pk = _save_to_db(result)
            print(
                f"Saved to database (OrganizationEvaluation pk={pk})",
                file=sys.stderr,
            )
        else:
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
