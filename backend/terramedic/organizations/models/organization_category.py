from django.db import models
from parler.models import TranslatableModel, TranslatedFields

from terramedic.organizations.models.category import Category
from terramedic.organizations.models.organization import Organization


class OrganizationCategory(TranslatableModel):
    """Through model carrying per-(org, category) copy.

    One Organization can appear under multiple Terramedic pathways
    (donate, volunteer, resource, everyday, career). The "why donate"
    pitch rarely reads the same as the "why volunteer" pitch, so each
    join row carries its own translated description and action_text.
    ``Organization.description`` remains the general fallback used in
    multi-category contexts (nearby, unfiltered listing).
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="category_entries",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="organization_entries",
    )
    sort_order = models.IntegerField(default=0)

    translations = TranslatedFields(
        description=models.TextField(blank=True, default=""),
        action_text=models.CharField(max_length=80, blank=True, default=""),
    )

    class Meta:
        unique_together = [("organization", "category")]
        ordering = ["sort_order", "category__slug"]
        verbose_name_plural = "organization categories"

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.category.slug}"
