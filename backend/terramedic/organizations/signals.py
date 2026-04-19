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
    """Reconcile the linked Organization on APPROVED transitions.

    Three cases, chosen to keep the APPROVE → REJECT → APPROVE cycle
    producing exactly one Organization row:

    * **Already linked and active** — no-op (prevents duplicate creation
      on idempotent saves).
    * **Already linked but deactivated** — reactivate the existing
      Organization (this is the re-approve path, after ``save_model``
      deactivated the org on a prior REJECT/PENDING transition).
    * **No org linked** — create a fresh Organization and link it via
      a conditional ``UPDATE`` that requires the row still has
      ``organization IS NULL`` and ``status = APPROVED``. If a
      concurrent save won the race, delete the orphan we just created
      so we don't leak rows.
    """
    if created:
        return
    if instance.status != ReviewStatus.APPROVED:
        return

    if instance.organization is not None:
        if not instance.organization.is_active:
            instance.organization.is_active = True
            instance.organization.save(update_fields=["is_active"])
        return

    org = create_org_from_evaluation(instance)
    # Conditional update: only link if the row still has no org and
    # is still APPROVED. filter().update() bypasses save() so this
    # receiver doesn't re-fire on itself.
    linked = sender.objects.filter(
        pk=instance.pk,
        organization__isnull=True,
        status=ReviewStatus.APPROVED,
    ).update(organization=org)
    if not linked:
        # Concurrent save linked a different org or flipped status
        # before we got here. Clean up the orphan we just created.
        org.delete()
        return
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
