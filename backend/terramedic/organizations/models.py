from typing import Any

from django.conf import settings
from django.contrib.gis.db import models
from parler.models import TranslatableModel, TranslatedFields


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


class ReviewStatus(models.TextChoices):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Organization(TranslatableModel):
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    image_url = models.URLField(blank=True, default="")
    categories = models.ManyToManyField(
        Category,
        related_name="organizations",
        blank=True,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="organizations")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    location = models.PointField(null=True, blank=True, geography=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    translations = TranslatedFields(
        description=models.TextField(),
        action_text=models.CharField(max_length=100),
    )

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class OrganizationEvaluation(models.Model):
    evaluation_data: Any = models.JSONField(
        help_text="Full evaluation payload matching curation/schema.json.",
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations",
        help_text="Linked organization (set on approval).",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_evaluations",
    )
    reviewer_reasoning = models.TextField(
        blank=True,
        default="",
        help_text="Reasoning when overriding the AI recommendation.",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.org_name} ({self.status})"

    @property
    def org_name(self) -> str:
        data = self.evaluation_data or {}
        return str(data.get("org_metadata", {}).get("name", "Unknown"))

    @property
    def evidence_score_value(self) -> int | None:
        data = self.evaluation_data or {}
        score = data.get("evidence_score", {}).get("score")
        return int(score) if score is not None else None

    @property
    def recommendation(self) -> str:
        data = self.evaluation_data or {}
        return str(data.get("curator_notes", {}).get("recommendation", ""))

    @property
    def sdg_numbers(self) -> list[int]:
        data = self.evaluation_data or {}
        sdg_numbers: list[int] = []
        for item in data.get("sdg_alignment", []):
            if not isinstance(item, dict) or "sdg" not in item:
                continue
            try:
                sdg_numbers.append(int(item["sdg"]))
            except (TypeError, ValueError):
                continue
        return sdg_numbers
