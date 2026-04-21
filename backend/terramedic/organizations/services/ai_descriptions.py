"""Admin-triggered AI fallback for drafting per-category org copy.

The curation pipeline produces ``category_copy`` for every category
it proposes (see ``curation/prompt.py`` + ``schema.json``), so the
common path never calls this service. It exists for the case a
curator manually adds a new category to an already-approved org —
the through row would otherwise sit with empty description and
action_text.

Invoked by ``OrganizationAdmin``'s "Generate descriptions" button
(single-org) and bulk action (changelist multi-select). English-only.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from curation.prompt import (
    CTA_LABEL_RULES,
    DESCRIPTION_STYLE_RULES,
    PER_CATEGORY_COPY_GUIDANCE,
)
from terramedic.core.secrets import resolve_secret
from terramedic.organizations.models import Category, Organization

logger = logging.getLogger(__name__)


_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 512

# Composed from the shared voice rules so curation/prompt.py and this
# service stay in lockstep on length, filler, pathway-reader framing,
# and CTA style. Only the framing ("one approved org, one pathway")
# is local.
_SYSTEM_PROMPT = f"""\
You write per-category copy for Terramedic, a platform that connects \
people with vetted environmental organizations. Given one approved \
organization and one pathway, produce a pathway-specific description \
and a CTA label for the card on that pathway's page.

## Pathway reader

{PER_CATEGORY_COPY_GUIDANCE}

## Description style

{DESCRIPTION_STYLE_RULES}

## CTA label

{CTA_LABEL_RULES}

## Output

Return a single raw JSON object with this shape — no markdown, no \
prose around it:

{{"description": "...", "action_text": "..."}}
"""


class AIDescriptionError(RuntimeError):
    """Raised when the AI draft call fails.

    Covers missing API key, malformed response, rate limits, and
    network errors. The admin view catches this and surfaces a
    user-readable message flash.
    """


@dataclass(frozen=True)
class DraftedCopy:
    description: str
    action_text: str


def _get_api_key() -> str:
    raw = os.environ.get("ANTHROPIC_API_KEY", "")
    if not raw:
        msg = (
            "ANTHROPIC_API_KEY is not set. Generate-descriptions "
            "cannot contact the model."
        )
        raise AIDescriptionError(msg)
    try:
        return resolve_secret(raw, "ANTHROPIC_API_KEY")
    except (RuntimeError, KeyError, ValueError) as exc:
        msg = f"Failed to resolve ANTHROPIC_API_KEY: {exc}"
        raise AIDescriptionError(msg) from exc


def _build_user_content(
    org: Organization, category: Category,
) -> str:
    """Build the per-category user turn (org facts + pathway slug)."""
    tags = ", ".join(
        org.tags.order_by("name").values_list("name", flat=True),
    ) or "(none)"
    return (
        f"## Organization\n\n"
        f"- Name: {org.name}\n"
        f"- Website: {org.website_url}\n"
        f"- Tags: {tags}\n"
        f"- General description: {org.description or '(empty)'}\n\n"
        f"## Pathway\n\n"
        f"Draft copy for the **{category.slug}** pathway "
        f"({category.label}). Return the JSON object described in "
        f"the system prompt."
    )


def _parse_response(text: str) -> DraftedCopy:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        msg = f"AI response did not contain a JSON object: {text[:200]!r}"
        raise AIDescriptionError(msg)
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        msg = f"AI response was not valid JSON: {exc}"
        raise AIDescriptionError(msg) from exc
    description = str(data.get("description") or "").strip()
    action_text = str(data.get("action_text") or "").strip()
    if not description:
        msg = "AI response missing 'description'"
        raise AIDescriptionError(msg)
    if not action_text:
        msg = "AI response missing 'action_text'"
        raise AIDescriptionError(msg)
    return DraftedCopy(description=description, action_text=action_text)


def draft_for_category(
    org: Organization,
    category: Category,
    client: Any | None = None,
) -> DraftedCopy:
    """Draft a per-(org, category) description and action_text.

    ``client`` is injectable for tests; in production we build an
    ``anthropic.Anthropic`` client here. The system prompt is marked
    ephemeral so drafting multiple categories for the same org in
    one admin run reuses the prompt cache.
    """
    if client is None:
        api_key = _get_api_key()
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            msg = "anthropic package is not installed"
            raise AIDescriptionError(msg) from exc
        client = Anthropic(api_key=api_key)

    user_content = _build_user_content(org, category)

    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"AI draft call failed: {exc}"
        raise AIDescriptionError(msg) from exc

    text_block = None
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text":
            text_block = block
            break
    if text_block is None:
        msg = "AI response had no text block"
        raise AIDescriptionError(msg)

    return _parse_response(text_block.text)
