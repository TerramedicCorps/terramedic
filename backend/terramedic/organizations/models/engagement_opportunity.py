from django.contrib.gis.db import models

from terramedic.organizations.models.enums import EngagementType, TimeCommitment
from terramedic.organizations.models.organization import Organization

LOCATION_BOUND_TYPES = frozenset({
    EngagementType.VOLUNTEER_IN_PERSON,
    EngagementType.CAREER,
})


class EngagementOpportunity(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="engagement_opportunities",
    )
    engagement_type = models.CharField(
        max_length=30,
        choices=EngagementType.choices,
    )
    description = models.TextField()
    time_commitment = models.CharField(
        max_length=20,
        choices=TimeCommitment.choices,
        blank=True,
        default="",
    )
    url = models.URLField(blank=True, default="")
    skills_helpful = models.JSONField(default=list, blank=True)
    location_bound = models.BooleanField(default=False)

    class Meta:
        ordering = ["engagement_type"]

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.pk and not self.location_bound:
            self.location_bound = (
                self.engagement_type in LOCATION_BOUND_TYPES
            )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.engagement_type}"
