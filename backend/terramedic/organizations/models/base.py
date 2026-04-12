from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


class CuratorProposedTerm(models.Model):
    """Abstract base for AI-proposed taxonomy terms that need human review."""

    name = models.CharField(max_length=100, unique=True)
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.reviewed and self.reviewed_at is None:
            self.reviewed_at = timezone.now()
        elif not self.reviewed:
            self.reviewed_at = None
            self.reviewed_by = None
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
