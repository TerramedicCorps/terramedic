"""Business logic triggered by an OrganizationEvaluation transition.

Kept separate from ``admin.py`` so the post-save signal in
``signals.py`` can share the exact same org-creation logic the bulk
admin actions use, without a circular import through the admin module.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from terramedic.organizations.models import (
    Category,
    Organization,
    OrganizationCategory,
    OrganizationEvaluation,
)

logger = logging.getLogger(__name__)

_DEFAULT_LANGUAGE = "en"


def _resolve_categories(
    evaluation: OrganizationEvaluation,
) -> list[Category]:
    """Resolve the list of Category rows to attach to the Organization.

    Precedence:

    1. ``evaluation.reviewer_categories`` — the reviewer's explicit
       choice. ``NULL`` means "no override" (fall through); an empty
       list means "reviewer cleared all categories" and triggers the
       ``resource`` fallback.
    2. ``accessibility.categories`` from the AI — the legacy / bulk
       approve path.

    If the resolved list contains no valid slugs (for example, all
    entries are ``"other"``), ``resource`` is returned as a fallback
    so the org still surfaces somewhere.
    """
    if evaluation.reviewer_categories is not None:
        requested = evaluation.reviewer_categories
    else:
        data = evaluation.evaluation_data or {}
        requested = data.get("accessibility", {}).get("categories", [])
    valid_categories = list(Category.objects.filter(slug__in=requested))
    if not valid_categories:
        valid_categories = list(Category.objects.filter(slug="resource"))
    return valid_categories


def _category_copy_index(
    evaluation: OrganizationEvaluation,
) -> dict[str, dict[str, str]]:
    """Index ``category_copy`` entries by slug.

    Returns a dict
    ``{slug: {"description": ..., "action_text": ..., "action_url": ...}}``.
    Malformed entries (not a dict, missing/non-string slug) are
    skipped with a WARN log — the through-model row falls back to
    blank copy, but the log makes curation-pipeline bugs visible
    instead of silently invisible.
    """
    data = evaluation.evaluation_data or {}
    entries = data.get("category_copy") or []
    index: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            logger.warning(
                "Skipping malformed category_copy entry "
                "(not a dict) on evaluation %s: %r",
                evaluation.pk, entry,
            )
            continue
        slug = entry.get("slug")
        if not isinstance(slug, str):
            logger.warning(
                "Skipping malformed category_copy entry "
                "(missing/non-string slug) on evaluation %s: %r",
                evaluation.pk, entry,
            )
            continue
        index[slug] = {
            "description": str(entry.get("description") or ""),
            "action_text": str(entry.get("action_text") or ""),
            "action_url": str(entry.get("action_url") or ""),
        }
    return index


def _write_category_copy(
    through: OrganizationCategory,
    copy: dict[str, str],
) -> None:
    """Populate the through row's translated copy for the default lang."""
    through.set_current_language(_DEFAULT_LANGUAGE)
    through.description = copy.get("description", "")
    through.action_text = copy.get("action_text", "")
    through.action_url = copy.get("action_url", "")
    through.save()


def _apply_category_set(
    org: Organization,
    categories: list[Category],
    copy_index: dict[str, dict[str, str]],
) -> None:
    """Reconcile an Organization's through-model rows to ``categories``.

    - Rows for slugs no longer selected are deleted.
    - Rows for newly-selected slugs are created; if
      ``copy_index`` has an entry for that slug, it's written as
      the English translation.
    - Rows for slugs still selected are left alone — they may carry
      curator edits or prior AI drafts we mustn't overwrite.
    """
    desired_slugs = {c.slug for c in categories}
    existing = {
        entry.category_id: entry
        for entry in org.category_entries.all()  # type: ignore[attr-defined]
    }
    existing_slugs = set(existing.keys())

    for slug in existing_slugs - desired_slugs:
        existing[slug].delete()

    for category in categories:
        if category.slug in existing_slugs:
            continue
        through = OrganizationCategory.objects.create(
            organization=org,
            category=category,
            sort_order=0,
        )
        copy = copy_index.get(category.slug)
        if copy:
            _write_category_copy(through, copy)


@transaction.atomic
def create_org_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> Organization:
    """Create an Organization from evaluation data.

    See ``_resolve_categories`` for how the category set is chosen.
    Per-(org, category) description + action_text come from the
    evaluation's ``category_copy`` array (produced by the curation
    pipeline); slugs without an entry start blank and can be filled
    later via the admin "Generate descriptions" action.

    Wrapped in ``transaction.atomic`` so a failure while writing
    per-category copy rolls back the whole create — no half-built
    orgs.
    """
    data: dict[str, Any] = evaluation.evaluation_data or {}
    meta = data.get("org_metadata", {})

    org = Organization(
        name=meta.get("name", ""),
        website_url=meta.get("website_url", ""),
        image_url=meta.get("image_url", ""),
        is_active=True,
    )
    org.set_current_language(_DEFAULT_LANGUAGE)
    org.description = meta.get("description", "")
    org.save()

    _apply_category_set(
        org,
        _resolve_categories(evaluation),
        _category_copy_index(evaluation),
    )
    return org


@transaction.atomic
def sync_org_categories_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> None:
    """Re-apply the resolved category set to the linked Organization.

    Preserves existing per-(org, category) copy for slugs that remain
    selected; re-applies ``category_copy`` for newly-added slugs;
    drops rows for removed slugs.

    Wrapped in ``transaction.atomic`` so a failure partway through
    the delete/create/translation-write reconciliation rolls back —
    either all the category changes land, or none do.

    No-op if no Organization is linked.
    """
    if evaluation.organization is None:
        return
    _apply_category_set(
        evaluation.organization,
        _resolve_categories(evaluation),
        _category_copy_index(evaluation),
    )
