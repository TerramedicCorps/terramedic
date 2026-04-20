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


def create_org_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> Organization:
    """Create an Organization from evaluation data.

    Categories are resolved in this order:

    1. ``evaluation.reviewer_categories`` — the reviewer's explicit
       choice. Set via the admin detail form. ``NULL`` means "no
       override" (fall through); an empty list means "reviewer cleared
       all categories" and triggers the ``resource`` fallback.
    2. ``accessibility.categories`` from the AI — the legacy / bulk
       approve path.

    If the resolved list contains no valid slugs (for example, all
    entries are ``"other"``), the organization is filed under
    ``resource`` as a fallback so it still shows up somewhere.
    """
    data = evaluation.evaluation_data
    meta = data.get("org_metadata", {})
    accessibility = data.get("accessibility", {})

    if evaluation.reviewer_categories is not None:
        requested = evaluation.reviewer_categories
    else:
        requested = accessibility.get("categories", [])
    valid_categories = list(Category.objects.filter(slug__in=requested))
    if not valid_categories:
        valid_categories = list(Category.objects.filter(slug="resource"))

    org = Organization(
        name=meta.get("name", ""),
        website_url=meta.get("website_url", ""),
        image_url=meta.get("image_url", ""),
        is_active=True,
    )
    org.set_current_language("en")
    org.description = meta.get("description", "")
    org.save()
    org.categories.set(valid_categories)
    return org
