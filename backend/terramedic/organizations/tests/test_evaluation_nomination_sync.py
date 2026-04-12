import pytest

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)

SAMPLE_EVAL_DATA = {
    "org_metadata": {"name": "Test Org", "website_url": "https://example.com"},
    "evidence_score": {"score": 3},
    "curator_notes": {"recommendation": "include", "confidence": 80},
}


@pytest.fixture
def nomination() -> Nomination:
    return Nomination.objects.create(
        url="https://example.com",
        categories=["volunteer"],
        ip_hash=None,
    )


@pytest.mark.django_db
class TestEvaluationNominationFK:
    def test_fk_exists_and_nullable(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        assert ev.nomination is None

    def test_fk_links_to_nomination(
        self, nomination: Nomination,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        ev.refresh_from_db()
        assert ev.nomination_id == nomination.pk

    def test_nomination_set_null_on_delete(
        self, nomination: Nomination,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        nomination.delete()
        ev.refresh_from_db()
        assert ev.nomination is None

    def test_reverse_relation(
        self, nomination: Nomination,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        assert ev in nomination.evaluations.all()


@pytest.mark.django_db
class TestEvaluationNominationSignalOnCreate:
    def test_creation_sets_nomination_evaluated(
        self, nomination: Nomination,
    ) -> None:
        nomination.status = NominationStatus.EVALUATING
        nomination.save(update_fields=["status"])

        OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        nomination.refresh_from_db()
        assert nomination.status == NominationStatus.EVALUATED

    def test_creation_without_nomination_no_error(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        assert ev.pk is not None


@pytest.mark.django_db
class TestEvaluationNominationSignalOnStatusChange:
    def test_approval_sets_nomination_approved(
        self, nomination: Nomination,
    ) -> None:
        nomination.status = NominationStatus.EVALUATED
        nomination.save(update_fields=["status"])

        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        ev.status = ReviewStatus.APPROVED
        ev.save(update_fields=["status"])

        nomination.refresh_from_db()
        assert nomination.status == NominationStatus.APPROVED

    def test_rejection_sets_nomination_rejected(
        self, nomination: Nomination,
    ) -> None:
        nomination.status = NominationStatus.EVALUATED
        nomination.save(update_fields=["status"])

        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
            nomination=nomination,
        )
        ev.status = ReviewStatus.REJECTED
        ev.save(update_fields=["status"])

        nomination.refresh_from_db()
        assert nomination.status == NominationStatus.REJECTED

    def test_no_update_without_nomination(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=SAMPLE_EVAL_DATA,
        )
        ev.status = ReviewStatus.APPROVED
        ev.save(update_fields=["status"])
        # Should not raise — no nomination to update
        assert ev.nomination is None
