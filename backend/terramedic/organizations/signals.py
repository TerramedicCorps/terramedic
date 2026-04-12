from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from terramedic.nominations.models import NominationStatus
from terramedic.organizations.models.evaluation import (
    OrganizationEvaluation,
    ReviewStatus,
)

# Map evaluation review statuses to nomination statuses.
_EVAL_TO_NOMINATION_STATUS: dict[str, str] = {
    ReviewStatus.APPROVED: NominationStatus.APPROVED,
    ReviewStatus.REJECTED: NominationStatus.REJECTED,
}


@receiver(post_save, sender=OrganizationEvaluation)
def sync_nomination_status(
    sender: type[OrganizationEvaluation],
    instance: OrganizationEvaluation,
    created: bool,
    **kwargs: Any,
) -> None:
    """Keep the linked nomination's status in sync with its evaluation."""
    nomination = instance.nomination
    if nomination is None:
        return

    if created:
        nomination.status = NominationStatus.EVALUATED
        nomination.save(update_fields=["status"])
        return

    new_status = _EVAL_TO_NOMINATION_STATUS.get(instance.status)
    if new_status and nomination.status != new_status:
        nomination.status = new_status
        nomination.save(update_fields=["status"])
