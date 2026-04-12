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

    class Meta:
        ordering = ["slug"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.label
