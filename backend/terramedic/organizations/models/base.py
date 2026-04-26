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
        related_name="%(class)s_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        user = kwargs.pop("user", None)
        update_fields = kwargs.get("update_fields")
        changed: set[str] = set()

        if self.reviewed and self.reviewed_at is None:
            self.reviewed_at = timezone.now()
            changed.add("reviewed_at")
            if user is not None:
                self.reviewed_by = user
                changed.add("reviewed_by")
        elif not self.reviewed:
            if self.reviewed_at is not None:
                self.reviewed_at = None
                changed.add("reviewed_at")
            if self.reviewed_by is not None:
                self.reviewed_by = None
                changed.add("reviewed_by")

        if update_fields is not None and changed:
            kwargs["update_fields"] = set(update_fields) | changed

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
