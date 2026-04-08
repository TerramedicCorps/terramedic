from typing import Any

from django.conf import settings
from django.contrib.gis.db import models

from terramedic.organizations.models.enums import ReviewStatus
from terramedic.organizations.models.organization import Organization


class OrganizationEvaluation(models.Model):
    evaluation_data: Any = models.JSONField(
        help_text=(
            "Full evaluation payload matching curation/schema.json."
        ),
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
        help_text=(
            "Reasoning when overriding the AI recommendation."
        ),
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
        return str(
            data.get("org_metadata", {}).get("name", "Unknown"),
        )

    @property
    def evidence_score_value(self) -> int | None:
        data = self.evaluation_data or {}
        score = data.get("evidence_score", {}).get("score")
        return int(score) if score is not None else None

    @property
    def recommendation(self) -> str:
        data = self.evaluation_data or {}
        return str(
            data.get("curator_notes", {}).get(
                "recommendation", "",
            ),
        )

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
