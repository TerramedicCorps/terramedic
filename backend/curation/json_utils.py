"""JSON extraction for free-form model responses."""

from __future__ import annotations

import json
from typing import Any


def _find_json_end(text: str, start: int) -> int | None:
    """Find the closing brace of a top-level JSON object.

    Walks the text tracking brace depth while respecting strings and
    backslash escapes — ``text.rfind("}")`` would misbehave when
    trailing prose contains a stray ``}``.
    """
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from model response text.

    Handles plain JSON, markdown-fenced JSON, and JSON embedded in
    surrounding prose (common with web-search-enabled responses).
    Raises ``ValueError`` when no valid JSON *object* is found —
    arrays, scalars, and ``null`` at the top level all fail loudly so
    callers don't blow up later doing ``.get(...)`` on a non-dict.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    parsed_top: Any = None
    top_parse_succeeded = False
    try:
        parsed_top = json.loads(text)
        top_parse_succeeded = True
    except json.JSONDecodeError:
        pass

    if top_parse_succeeded:
        if isinstance(parsed_top, dict):
            return parsed_top
        # Whole text parsed cleanly but isn't an object — don't fall
        # through to substring extraction, the model emitted a list or
        # scalar and the caller should know.
        msg = (
            "Failed to parse JSON object from model response: "
            f"top-level value is {type(parsed_top).__name__}, not object"
        )
        raise ValueError(msg)

    start = text.find("{")
    if start != -1:
        end = _find_json_end(text, start)
        if end is not None:
            try:
                parsed = json.loads(text[start:end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

    msg = "Failed to parse JSON object from model response: no valid JSON object found"
    raise ValueError(msg)
