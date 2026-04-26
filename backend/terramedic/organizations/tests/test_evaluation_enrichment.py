import pytest
from django.core.exceptions import ValidationError

from terramedic.organizations.models import (
    AIRecommendation,
    OrganizationEvaluation,
    ReviewStatus,
)

SAMPLE_EVAL_DATA = {
    "org_metadata": {"name": "Test Org"},
    "evidence_score": {"score": 3},
}


@pytest.mark.django_db
class TestEvaluationEnrichmentFields:
    def test_ai_model_stored(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_model="claude-sonnet-4-5-20250514",
        )
        ev.refresh_from_db()
        assert ev.ai_model == "claude-sonnet-4-5-20250514"

    def test_ai_model_defaults_blank(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        assert ev.ai_model == ""

    def test_ai_recommendation_stored(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_recommendation=AIRecommendation.INCLUDE,
        )
        ev.refresh_from_db()
        assert ev.ai_recommendation == AIRecommendation.INCLUDE

    def test_ai_recommendation_defaults_blank(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        assert ev.ai_recommendation == ""

    def test_override_without_reasoning_rejected(self) -> None:
        """Status differs from AI recommendation but no reasoning given."""
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_recommendation=AIRecommendation.INCLUDE,
            status=ReviewStatus.REJECTED,
            reviewer_reasoning="",
        )
        with pytest.raises(ValidationError):
            ev.full_clean()

    def test_override_with_reasoning_accepted(self) -> None:
        """Status differs from AI recommendation with reasoning provided."""
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_recommendation=AIRecommendation.INCLUDE,
            status=ReviewStatus.REJECTED,
            reviewer_reasoning="Org has deceptive financial practices.",
        )
        ev.full_clean()  # should not raise

    def test_agreement_needs_no_reasoning(self) -> None:
        """Status matches AI recommendation — reasoning is optional."""
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_recommendation=AIRecommendation.INCLUDE,
            status=ReviewStatus.APPROVED,
        )
        ev.full_clean()  # should not raise

    def test_pending_status_needs_no_reasoning(self) -> None:
        """Pending evaluations haven't been reviewed yet."""
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_recommendation=AIRecommendation.INCLUDE,
            status=ReviewStatus.PENDING,
        )
        ev.full_clean()  # should not raise

    def test_ai_confidence_stored(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_confidence=85,
        )
        ev.refresh_from_db()
        assert ev.ai_confidence == 85

    def test_ai_confidence_defaults_null(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        assert ev.ai_confidence is None

    def test_ai_confidence_rejects_over_100(self) -> None:
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_confidence=101,
        )
        with pytest.raises(ValidationError):
            ev.full_clean()

    def test_ai_confidence_rejects_negative(self) -> None:
        ev = OrganizationEvaluation(
            evaluation_data=SAMPLE_EVAL_DATA,
            ai_confidence=-1,
        )
        with pytest.raises(ValidationError):
            ev.full_clean()
