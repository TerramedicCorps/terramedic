import uuid
from typing import Any

from django.db import models


class NominationStatus(models.TextChoices):
    PENDING = "pending"
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
    APPROVED = "approved"
    REJECTED = "rejected"


class Nomination(models.Model):
    url = models.URLField()
    categories: Any = models.JSONField(
        help_text="List of category strings (e.g. volunteer, donate).",
    )
    notes = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of submitter IP for rate limiting.",
    )
    status = models.CharField(
        max_length=20,
        choices=NominationStatus.choices,
        default=NominationStatus.PENDING,
    )
    confirmation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.url} ({self.status})"
