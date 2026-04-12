"""Skip-check logic shared by the admin action and the worker."""

import datetime

from django.utils import timezone

from terramedic.organizations.models import (
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
)

_REJECTION_COOLDOWN_DAYS = 90


def should_skip_url(url: str) -> bool:
    """Return True if the URL should not be evaluated.

    A URL is skipped when:
    - It has a non-rejected OrganizationEvaluation (active eval).
    - It matches an existing Organization.website_url.
    - It was rejected within the last 90 days (cooldown).
    """
    has_active_eval = (
        OrganizationEvaluation.objects.exclude(
            status=ReviewStatus.REJECTED,
        ).filter(
            evaluation_data__org_metadata__website_url=url,
        ).exists()
    )
    if has_active_eval:
        return True

    if Organization.objects.filter(website_url=url).exists():
        return True

    cooldown_cutoff = timezone.now() - datetime.timedelta(
        days=_REJECTION_COOLDOWN_DAYS,
    )
    return OrganizationEvaluation.objects.filter(
        status=ReviewStatus.REJECTED,
        created_at__gte=cooldown_cutoff,
        evaluation_data__org_metadata__website_url=url,
    ).exists()
