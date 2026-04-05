from typing import Any

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import Client

from terramedic.organizations.admin import OrganizationEvaluationAdmin
from terramedic.organizations.models import (
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
)


def _make_evaluation_data(**overrides: Any) -> dict[str, Any]:
    """Build a valid evaluation payload matching curation/schema.json."""
    data: dict[str, Any] = {
        "org_metadata": {
            "name": "Rainforest Alliance",
            "website_url": "https://www.rainforest-alliance.org/",
            "country": "US",
            "description": "Working to conserve biodiversity.",
            "image_url": "https://example.com/logo.png",
        },
        "sdg_alignment": [
            {
                "sdg": 15,
                "evidence": "Protects forest ecosystems.",
                "evidence_urls": ["https://example.com/evidence"],
            },
        ],
        "evidence_of_work": [
            {
                "activity": "Certified 5 million hectares of forest.",
                "type": "conservation",
                "source_url": "https://example.com/source",
            },
        ],
        "accessibility": {
            "donate_url": "https://www.rainforest-alliance.org/donate/",
            "categories": ["donate", "volunteer"],
        },
        "evidence_score": {
            "score": 4,
            "rationale": "Strong evidence of conservation work.",
        },
        "curator_notes": {
            "recommendation": "include",
            "notes": "Well-established org with strong track record.",
        },
        "evaluated_at": "2026-03-15T10:30:00Z",
        "evaluated_by": "claude-opus-4-6",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestOrganizationEvaluationModel:
    def test_create_evaluation(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.pk is not None
        assert ev.status == ReviewStatus.PENDING
        assert ev.organization is None

    def test_str_returns_org_name_and_status(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert str(ev) == "Rainforest Alliance (pending)"

    def test_org_name_property(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.org_name == "Rainforest Alliance"

    def test_evidence_score_value_property(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.evidence_score_value == 4

    def test_recommendation_property(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.recommendation == "include"

    def test_sdg_numbers_property(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.sdg_numbers == [15]

    def test_default_status_is_pending(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.status == ReviewStatus.PENDING

    def test_reviewed_at_initially_none(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.reviewed_at is None

    def test_reviewer_initially_none(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.reviewer is None


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="testpass123",
    )


@pytest.fixture
def admin_client(admin_user: User) -> Client:
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def pending_evaluation() -> OrganizationEvaluation:
    return OrganizationEvaluation.objects.create(
        evaluation_data=_make_evaluation_data(),
    )


@pytest.mark.django_db
class TestOrganizationEvaluationAdminList:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.status_code == 200

    def test_changelist_shows_pending(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert b"Rainforest Alliance" in response.content

    def test_changelist_shows_evidence_score(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        # Score 4 should appear in the list
        content = response.content.decode()
        assert "4 / 5" in content

    def test_changelist_shows_recommendation(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        content = response.content.decode()
        assert "include" in content.lower()


@pytest.mark.django_db
class TestOrganizationEvaluationAdminDetail:
    def test_detail_page_loads(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            f"/admin/organizations/organizationevaluation/"
            f"{pending_evaluation.pk}/change/",
        )
        assert response.status_code == 200

    def test_detail_shows_sdg_alignment(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            f"/admin/organizations/organizationevaluation/"
            f"{pending_evaluation.pk}/change/",
        )
        content = response.content.decode()
        assert "SDG 15" in content

    def test_detail_shows_curator_notes(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            f"/admin/organizations/organizationevaluation/"
            f"{pending_evaluation.pk}/change/",
        )
        content = response.content.decode()
        assert "Well-established org" in content


@pytest.mark.django_db
class TestApproveAction:
    def test_approve_creates_organization(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.status == ReviewStatus.APPROVED
        assert pending_evaluation.organization is not None
        assert pending_evaluation.organization.name == "Rainforest Alliance"
        assert pending_evaluation.organization.is_active is True
        assert pending_evaluation.reviewed_at is not None

    def test_approve_sets_reviewer(
        self,
        admin_client: Client,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.reviewer == admin_user

    def test_approve_maps_categories_from_accessibility(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        org = pending_evaluation.organization
        assert org is not None
        # First category from the accessibility.categories list
        assert org.category == "donate"

    def test_approve_sets_org_description(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        org = pending_evaluation.organization
        assert org is not None
        org.set_current_language("en")
        assert org.description == "Working to conserve biodiversity."

    def test_approve_skips_already_approved(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        # Approve once
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        org_count_after_first = Organization.objects.count()

        # Approve again — should not create a duplicate
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        assert Organization.objects.count() == org_count_after_first


@pytest.mark.django_db
class TestRejectAction:
    def test_reject_sets_status(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "reject_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.status == ReviewStatus.REJECTED
        assert pending_evaluation.organization is None
        assert pending_evaluation.reviewed_at is not None

    def test_reject_sets_reviewer(
        self,
        admin_client: Client,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "reject_evaluations",
                "_selected_action": [pending_evaluation.pk],
            },
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.reviewer == admin_user


@pytest.mark.django_db
class TestReviewerReasoning:
    def test_can_save_reviewer_reasoning(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        """Reviewer can record reasoning when overriding AI recommendation."""
        pending_evaluation.reviewer_reasoning = (
            "Score too low for immediate inclusion."
        )
        pending_evaluation.save()
        pending_evaluation.refresh_from_db()
        assert (
            pending_evaluation.reviewer_reasoning
            == "Score too low for immediate inclusion."
        )


@pytest.mark.django_db
class TestEvaluationAdminReadonlyPresentation:
    """The admin should present evaluation data as read-only for review."""

    def test_evaluation_data_is_readonly(self) -> None:
        site = AdminSite()
        admin = OrganizationEvaluationAdmin(OrganizationEvaluation, site)
        assert "evaluation_data" in admin.readonly_fields

    def test_status_is_readonly(self) -> None:
        site = AdminSite()
        admin = OrganizationEvaluationAdmin(OrganizationEvaluation, site)
        assert "status" in admin.readonly_fields

    def test_status_choices(self) -> None:
        assert ReviewStatus.PENDING == "pending"
        assert ReviewStatus.APPROVED == "approved"
        assert ReviewStatus.REJECTED == "rejected"
