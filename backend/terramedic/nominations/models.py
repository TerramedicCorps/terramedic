import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from terramedic.organizations.models import Category


class NominationStatus(models.TextChoices):
    PENDING = "pending"
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
    APPROVED = "approved"
    REJECTED = "rejected"


class Nomination(models.Model):
    url = models.URLField(max_length=2048)
    categories: Any = models.JSONField(
        help_text="List of category strings (e.g. volunteer, donate).",
    )
    notes = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
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

    MAX_NOTES_LENGTH = 2000

    def clean(self) -> None:
        super().clean()
        if self.notes and len(self.notes) > self.MAX_NOTES_LENGTH:
            raise ValidationError(
                {"notes": f"Notes must not exceed {self.MAX_NOTES_LENGTH} characters."},
            )
        cats = self.categories
        if not isinstance(cats, list) or not all(isinstance(c, str) for c in cats):
            raise ValidationError(
                {"categories": "Must be a list of strings."},
            )
        valid = set(Category.values)
        invalid = [c for c in cats if c not in valid]
        if invalid:
            raise ValidationError(
                {"categories": f"Invalid categories: {', '.join(invalid)}"},
            )

    def __str__(self) -> str:
        return f"{self.url} ({self.status})"
