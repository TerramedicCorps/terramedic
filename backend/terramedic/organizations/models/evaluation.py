from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from terramedic.organizations.models.enums import AIRecommendation, ReviewStatus
from terramedic.organizations.models.organization import Organization

# Map AI recommendations to the review status that agrees.
_AI_RECOMMENDATION_TO_STATUS: dict[str, str] = {
    AIRecommendation.INCLUDE: ReviewStatus.APPROVED,
    AIRecommendation.EXCLUDE: ReviewStatus.REJECTED,
}


class OrganizationEvaluation(models.Model):
    evaluation_data: Any = models.JSONField(
        help_text=(
            "Full evaluation payload matching curation/schema.json."
        ),
    )
    ai_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Model ID that produced this evaluation.",
    )
    ai_recommendation = models.CharField(
        max_length=20,
        choices=AIRecommendation.choices,
        blank=True,
        default="",
        help_text="The AI's inclusion recommendation.",
    )
    ai_confidence = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI confidence in its recommendation (0–100).",
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    nomination = models.ForeignKey(
        "nominations.Nomination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations",
        help_text="Source nomination that triggered this evaluation.",
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
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="eval_status_created",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        agreed_status = _AI_RECOMMENDATION_TO_STATUS.get(
            self.ai_recommendation,
        )
        is_override = (
            self.ai_recommendation
            and self.status != ReviewStatus.PENDING
            and self.status != agreed_status
        )
        if is_override and not self.reviewer_reasoning.strip():
            raise ValidationError(
                {
                    "reviewer_reasoning": (
                        "Reasoning is required when overriding"
                        " the AI recommendation."
                    ),
                },
            )

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
        """Recommendation from the raw evaluation JSON payload.

        Prefer ``ai_recommendation`` for the canonical value; this
        property exists for reading directly from the evaluation data.
        """
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
