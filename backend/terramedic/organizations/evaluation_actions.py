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

    Assigns every valid category from the evaluation's
    ``accessibility.categories`` array. If none are valid
    (for example, all entries are ``"other"``), the
    organization is filed under ``resource`` as a fallback
    so it still shows up somewhere.
    """
    data = evaluation.evaluation_data
    meta = data.get("org_metadata", {})
    accessibility = data.get("accessibility", {})

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
    action_text = f"Support {meta.get('name', 'this organization')}"
    org.action_text = action_text[:100]
    org.save()
    org.categories.set(valid_categories)
    return org
