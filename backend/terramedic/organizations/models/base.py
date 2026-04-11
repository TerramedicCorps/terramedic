from django.db import models


class CuratorProposedTerm(models.Model):
    """Abstract base for AI-proposed taxonomy terms that need human review."""

    name = models.CharField(max_length=100, unique=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
