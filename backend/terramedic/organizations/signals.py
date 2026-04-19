from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from terramedic.nominations.models import NominationStatus
from terramedic.organizations.evaluation_actions import (
    create_org_from_evaluation,
)
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
def create_org_on_approval(
    sender: type[OrganizationEvaluation],
    instance: OrganizationEvaluation,
    created: bool,
    **kwargs: Any,
) -> None:
    """Create and link an Organization when an evaluation is APPROVED.

    This fires on any save — from the admin change form, the bulk
    approve action, a management command, or a test — so the
    org-creation side-effect of approval is enforced in one place.
    Skipped on creation (the initial save by the worker) and when an
    organization is already linked.
    """
    if created:
        return
    if instance.status != ReviewStatus.APPROVED:
        return
    if instance.organization is not None:
        return
    org = create_org_from_evaluation(instance)
    # filter().update() bypasses save() so this receiver doesn't
    # re-fire on itself (and reviewer/reviewed_at stay intact).
    type(instance).objects.filter(pk=instance.pk).update(organization=org)
    instance.organization = org


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
