"""Business logic triggered by an OrganizationEvaluation transition.

Kept separate from ``admin.py`` so the post-save signal in
``signals.py`` can share the exact same org-creation logic the bulk
admin actions use, without a circular import through the admin module.
"""

from __future__ import annotations

from terramedic.organizations.models import (
    Category,
    Organization,
    OrganizationEvaluation,
)


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


def create_org_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> Organization:
    """Create an Organization from evaluation data.

    See ``_resolve_categories`` for how the category set is chosen.
    """
    data = evaluation.evaluation_data or {}
    meta = data.get("org_metadata", {})

    org = Organization(
        name=meta.get("name", ""),
        website_url=meta.get("website_url", ""),
        image_url=meta.get("image_url", ""),
        is_active=True,
    )
    org.set_current_language("en")
    org.description = meta.get("description", "")
    org.save()
    org.categories.set(_resolve_categories(evaluation))
    return org


def sync_org_categories_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> None:
    """Re-apply the resolved category set to the linked Organization.

    For already-approved evaluations whose ``reviewer_categories`` was
    edited on the admin form. The post_save signal short-circuits when
    an org is already linked (it only handles the APPROVED transition),
    so changes to ``reviewer_categories`` after approval would silently
    desync the Organization's categories without this sync.

    No-op if no Organization is linked.
    """
    if evaluation.organization is None:
        return
    evaluation.organization.categories.set(_resolve_categories(evaluation))
