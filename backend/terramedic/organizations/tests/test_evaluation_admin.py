from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

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
            "name": "Test Organization",
            "website_url": "https://example.com",
            "country": "US",
            "description": "Working to conserve biodiversity.",
            "image_url": "https://example.com/logo.png",
        },
        "sdg_alignment": [
            {
                "sdg": 15,
                "evidence": "Protects forest ecosystems.",
                "sources": [
                    {
                        "source_url": "https://example.com/evidence",
                        "date_accessed": "2026-03-15",
                        "excerpt": "Forest certification program.",
                    },
                ],
            },
        ],
        "evidence_of_work": [
            {
                "activity": "Certified 5 million hectares of forest.",
                "type": "conservation",
                "sources": [
                    {"source_url": "https://example.com/source"},
                ],
            },
        ],
        "accessibility": {
            "donate_url": "https://example.com/donate/",
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
        "prompt_version": "2026.04.1",
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
        assert str(ev) == "Test Organization (pending)"

    def test_org_name_property(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        assert ev.org_name == "Test Organization"

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
        assert b"Test Organization" in response.content

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
        assert pending_evaluation.organization.name == "Test Organization"
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
        # Both categories from accessibility.categories should be assigned
        # (the default fixture uses ["donate", "volunteer"]).
        assert set(org.categories.values_list("slug", flat=True)) == {
            "donate",
            "volunteer",
        }

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

    def test_status_is_editable(self) -> None:
        """Curators change status directly on the detail page; the
        post_save signal handles the downstream side effects."""
        site = AdminSite()
        admin = OrganizationEvaluationAdmin(OrganizationEvaluation, site)
        assert "status" not in admin.readonly_fields

    def test_status_choices(self) -> None:
        assert ReviewStatus.PENDING == "pending"
        assert ReviewStatus.APPROVED == "approved"
        assert ReviewStatus.REJECTED == "rejected"


@pytest.mark.django_db
class TestApproveFromDetailPage:
    """Curator flips status to Approved on the change form and saves.

    save_model stamps reviewer + reviewed_at; the post_save signal
    creates and links an Organization.
    """

    def _post_change(
        self,
        client: Client,
        evaluation: OrganizationEvaluation,
        status: str,
        reasoning: str = "",
    ) -> Any:
        url = (
            "/admin/organizations/organizationevaluation/"
            f"{evaluation.pk}/change/"
        )
        return client.post(
            url,
            {
                "status": status,
                "reviewer_reasoning": reasoning,
                "_save": "Save",
            },
        )

    def test_approve_via_detail_creates_organization(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.status == ReviewStatus.APPROVED
        assert pending_evaluation.organization is not None
        assert pending_evaluation.organization.name == "Test Organization"

    def test_approve_via_detail_stamps_reviewer_and_time(
        self,
        admin_client: Client,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.reviewer == admin_user
        assert pending_evaluation.reviewed_at is not None

    def test_reject_via_detail_sets_status_without_creating_org(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.REJECTED,
        )
        pending_evaluation.refresh_from_db()
        assert pending_evaluation.status == ReviewStatus.REJECTED
        assert pending_evaluation.organization is None
        assert Organization.objects.count() == 0

    def test_save_without_status_change_does_not_restamp_reviewer(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        # First save: approves and stamps reviewer/time.
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        original_time = pending_evaluation.reviewed_at
        assert original_time is not None

        # Second save: status unchanged, only reasoning edited.
        self._post_change(
            admin_client,
            pending_evaluation,
            ReviewStatus.APPROVED,
            reasoning="Updated notes",
        )
        pending_evaluation.refresh_from_db()
        # reviewed_at preserved because status didn't change.
        assert pending_evaluation.reviewed_at == original_time

    def test_repeat_approve_does_not_create_second_org(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        # First approval creates the org.
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        first_org = pending_evaluation.organization
        assert first_org is not None

        # Saving again should not create a second Organization.
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        assert Organization.objects.count() == 1
        assert pending_evaluation.organization == first_org

    def test_reject_after_approve_deactivates_but_preserves_fk(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        """Transitioning APPROVED → REJECTED keeps the FK (audit trail)
        but deactivates the linked Organization so it disappears from
        the public frontend."""
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        org = pending_evaluation.organization
        assert org is not None
        assert org.is_active is True

        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.REJECTED,
        )
        pending_evaluation.refresh_from_db()
        org.refresh_from_db()
        assert pending_evaluation.status == ReviewStatus.REJECTED
        assert pending_evaluation.organization == org  # FK preserved
        assert org.is_active is False

    def test_approve_reject_reapprove_does_not_duplicate_org(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        """A full APPROVE → REJECT → APPROVE cycle ends with exactly
        one Organization, reactivated, linked to the evaluation."""
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )
        pending_evaluation.refresh_from_db()
        original_org = pending_evaluation.organization
        assert original_org is not None

        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.REJECTED,
        )
        self._post_change(
            admin_client, pending_evaluation, ReviewStatus.APPROVED,
        )

        pending_evaluation.refresh_from_db()
        original_org.refresh_from_db()
        assert Organization.objects.count() == 1
        assert pending_evaluation.organization == original_org
        assert original_org.is_active is True
        assert pending_evaluation.status == ReviewStatus.APPROVED


@pytest.mark.django_db
class TestCreateOrgOnApprovalSignal:
    """The post_save signal enforces org creation regardless of the
    code path that flipped status to APPROVED."""

    def test_signal_fires_for_direct_save(
        self,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        # Simulate any non-admin code path (shell, migration, etc.)
        # that transitions status directly.
        pending_evaluation.status = ReviewStatus.APPROVED
        pending_evaluation.reviewer = admin_user
        pending_evaluation.reviewed_at = timezone.now()
        pending_evaluation.save()

        pending_evaluation.refresh_from_db()
        assert pending_evaluation.organization is not None

    def test_signal_skips_when_org_already_linked(
        self,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        existing = Organization.objects.create(
            name="Pre-linked Org", website_url="https://pre.example",
        )
        pending_evaluation.organization = existing
        pending_evaluation.status = ReviewStatus.APPROVED
        pending_evaluation.reviewer = admin_user
        pending_evaluation.reviewed_at = timezone.now()
        pending_evaluation.save()

        pending_evaluation.refresh_from_db()
        # No new org created; existing link preserved.
        assert Organization.objects.count() == 1
        assert pending_evaluation.organization == existing

    def test_signal_skips_on_rejection(
        self,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        pending_evaluation.status = ReviewStatus.REJECTED
        pending_evaluation.reviewer = admin_user
        pending_evaluation.reviewed_at = timezone.now()
        pending_evaluation.save()

        assert Organization.objects.count() == 0

    def test_signal_reactivates_deactivated_org_on_reapproval(
        self,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        """Re-approving an evaluation whose Organization was
        deactivated (by a prior REJECT transition) flips the org back
        to is_active=True instead of creating a new one."""
        existing = Organization.objects.create(
            name="Previously Approved Org",
            website_url="https://prev.example",
            is_active=False,
        )
        pending_evaluation.organization = existing
        pending_evaluation.status = ReviewStatus.APPROVED
        pending_evaluation.reviewer = admin_user
        pending_evaluation.reviewed_at = timezone.now()
        pending_evaluation.save()

        pending_evaluation.refresh_from_db()
        existing.refresh_from_db()
        assert pending_evaluation.organization == existing
        assert existing.is_active is True
        assert Organization.objects.count() == 1

    def test_signal_cleans_up_orphan_on_race(
        self,
        admin_user: User,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        """If a concurrent saver links an org between this receiver's
        check and its conditional UPDATE, the newly-created Org is
        deleted so we don't leak rows."""
        from terramedic.organizations import signals as sig

        winning_org = Organization.objects.create(
            name="Winning Org", website_url="https://winner.example",
        )

        real_create = sig.create_org_from_evaluation

        def create_with_race(evaluation: OrganizationEvaluation) -> Organization:
            # Simulate a concurrent saver linking a different org
            # right after we've started creating ours but before the
            # conditional UPDATE runs. The UPDATE's filter requires
            # organization__isnull=True, so it will return 0.
            OrganizationEvaluation.objects.filter(
                pk=evaluation.pk,
            ).update(organization=winning_org)
            return real_create(evaluation)

        pending_evaluation.status = ReviewStatus.APPROVED
        pending_evaluation.reviewer = admin_user
        pending_evaluation.reviewed_at = timezone.now()

        with patch.object(
            sig, "create_org_from_evaluation", side_effect=create_with_race,
        ):
            pending_evaluation.save()

        pending_evaluation.refresh_from_db()
        # Orphan was cleaned up; only the winning org remains.
        assert Organization.objects.count() == 1
        assert pending_evaluation.organization == winning_org


@pytest.mark.django_db
class TestApproveWithOtherCategory:
    """Evaluations with 'other' entries skip them and keep the valid ones;
    if none remain, the org falls back to 'resource'."""

    def test_skips_other_assigns_remaining_valid(
        self,
        admin_client: Client,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                accessibility={
                    "categories": ["other", "volunteer"],
                },
            ),
        )
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [ev.pk],
            },
        )
        ev.refresh_from_db()
        assert ev.organization is not None
        assert list(
            ev.organization.categories.values_list("slug", flat=True),
        ) == ["volunteer"]

    def test_all_other_defaults_to_resource(
        self,
        admin_client: Client,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                accessibility={"categories": ["other"]},
            ),
        )
        admin_client.post(
            "/admin/organizations/organizationevaluation/",
            {
                "action": "approve_evaluations",
                "_selected_action": [ev.pk],
            },
        )
        ev.refresh_from_db()
        assert ev.organization is not None
        assert list(
            ev.organization.categories.values_list("slug", flat=True),
        ) == ["resource"]


@pytest.mark.django_db
class TestDetailShowsNewSchemaFields:
    def test_detail_shows_prompt_version(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            f"/admin/organizations/organizationevaluation/"
            f"{pending_evaluation.pk}/change/",
        )
        content = response.content.decode()
        assert "2026.04.1" in content

    def test_detail_shows_source_excerpt(
        self,
        admin_client: Client,
        pending_evaluation: OrganizationEvaluation,
    ) -> None:
        response = admin_client.get(
            f"/admin/organizations/organizationevaluation/"
            f"{pending_evaluation.pk}/change/",
        )
        content = response.content.decode()
        assert "Forest certification program." in content


@pytest.mark.django_db
class TestDashboardStats:
    """The changelist should show counts of pending, approved, rejected."""

    def test_changelist_shows_pending_count(
        self,
        admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.context["dashboard_stats"]["pending"] == 2

    def test_changelist_shows_approved_count(
        self,
        admin_client: Client,
        admin_user: User,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
            status=ReviewStatus.APPROVED,
            reviewer=admin_user,
        )
        # Also one pending — should not be counted as approved
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.context["dashboard_stats"]["approved"] == 1

    def test_changelist_shows_rejected_count(
        self,
        admin_client: Client,
        admin_user: User,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
            status=ReviewStatus.REJECTED,
            reviewer=admin_user,
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.context["dashboard_stats"]["rejected"] == 1

    def test_dashboard_stats_all_zero_when_empty(
        self,
        admin_client: Client,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        stats = response.context["dashboard_stats"]
        assert stats["pending"] == 0
        assert stats["approved"] == 0
        assert stats["rejected"] == 0

    def test_dashboard_handles_database_error(
        self,
        admin_client: Client,
    ) -> None:
        with (
            patch(
                "terramedic.organizations.admin.OrganizationEvaluation.objects",
            ) as mock_objects,
            patch(
                "terramedic.organizations.admin.logger",
            ) as mock_logger,
        ):
            mock_objects.all.side_effect = Exception("DB connection lost")
            response = admin_client.get(
                "/admin/organizations/organizationevaluation/",
            )
        assert response.status_code == 200
        assert response.context["dashboard_error"] == (
            "Unable to load dashboard data"
        )
        mock_logger.exception.assert_called_once()


@pytest.mark.django_db
class TestGrowthOverTime:
    """The changelist should include monthly growth data."""

    def test_changelist_includes_growth_data(
        self,
        admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        growth = response.context["growth_data"]
        assert len(growth) == 1
        expected_month = timezone.now().strftime("%Y-%m")
        assert growth[0]["month"] == expected_month
        assert growth[0]["count"] == 2

    def test_growth_data_empty_when_no_evaluations(
        self,
        admin_client: Client,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.context["growth_data"] == []


@pytest.mark.django_db
class TestEvidenceScoreFilter:
    """Filter evaluations by evidence score range."""

    def test_filter_high_score(
        self,
        admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 5, "rationale": "Excellent"},
            ),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 2, "rationale": "Weak"},
            ),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/?evidence_score=high",
        )
        content = response.content.decode()
        # Score 5 should be visible, score 2 should not
        assert "5 / 5" in content
        assert "2 / 5" not in content

    def test_filter_low_score(
        self,
        admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 5, "rationale": "Excellent"},
            ),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 2, "rationale": "Weak"},
            ),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/?evidence_score=low",
        )
        content = response.content.decode()
        assert "2 / 5" in content
        assert "5 / 5" not in content

    def test_filter_medium_score(
        self,
        admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 3, "rationale": "Average"},
            ),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                evidence_score={"score": 5, "rationale": "Excellent"},
            ),
        )
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/"
            "?evidence_score=medium",
        )
        content = response.content.decode()
        assert "3 / 5" in content
        assert "5 / 5" not in content


@pytest.mark.django_db
class TestAnonymousAccess:
    """Non-staff users should be redirected to login."""

    def test_anonymous_user_redirected(self) -> None:
        client = Client()
        response = client.get(
            "/admin/organizations/organizationevaluation/",
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestCategoryFilter:
    """Filter evaluations by accessibility category from JSON data."""

    @pytest.fixture(autouse=True)
    def _create_category_evaluations(self) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                accessibility={"categories": ["donate"]},
            ),
        )
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_evaluation_data(
                accessibility={"categories": ["volunteer"]},
                org_metadata={
                    "name": "Volunteer Corps",
                    "website_url": "https://example.com",
                    "country": "US",
                    "description": "Volunteering org.",
                    "image_url": "",
                },
            ),
        )

    def test_filter_by_donate(
        self,
        admin_client: Client,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/?eval_category=donate",
        )
        content = response.content.decode()
        assert "Test Organization" in content
        assert "Volunteer Corps" not in content

    def test_filter_by_volunteer(
        self,
        admin_client: Client,
    ) -> None:
        response = admin_client.get(
            "/admin/organizations/organizationevaluation/"
            "?eval_category=volunteer",
        )
        content = response.content.decode()
        assert "Volunteer Corps" in content
        assert "Test Organization" not in content
