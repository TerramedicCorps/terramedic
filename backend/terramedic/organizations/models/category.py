from django.db import models


class Category(models.Model):
    """A Terramedic engagement pathway an organization can fit into.

    The five canonical slugs (donate, volunteer, resource, everyday, career)
    are seeded by migration 0006; new categories should be added via
    migrations rather than at runtime so the curation schema and frontend
    routes stay in sync.
    """

    slug = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=100)
    default_action_text = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text=(
            "Fallback CTA label used when an OrganizationCategory row"
            " has no per-(org, category) action_text. Empty string means"
            " the frontend decides."
        ),
    )

    class Meta:
        ordering = ["slug"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.label
