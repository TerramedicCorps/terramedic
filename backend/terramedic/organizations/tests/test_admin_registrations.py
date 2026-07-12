"""Tests for admin registrations of all organization models."""

from typing import Any

import pytest
from django.contrib import admin
from django.test import Client

from terramedic.organizations.admin import OrganizationCategoryInline
from terramedic.organizations.models import (
    SDG,
    Category,
    EngagementOpportunity,
    FocusArea,
    OperatingRegion,
    Organization,
    OrganizationCategory,
    OrganizationEvaluation,
    Skill,
    Tag,
)


@pytest.mark.django_db
class TestAdminRegistrations:
    """Every concrete model should be registered in the admin."""

    @pytest.mark.parametrize(
        "model",
        [
            Category,
            EngagementOpportunity,
            FocusArea,
            OperatingRegion,
            SDG,
            Skill,
            # Already registered — included for completeness
            Organization,
            OrganizationEvaluation,
            Tag,
        ],
    )
    def test_model_is_registered(self, model: type) -> None:
        assert admin.site.is_registered(model), (
            f"{model.__name__} is not registered in the admin"
        )

    def test_org_category_inline_exposes_action_url(self) -> None:
        assert "action_url" in OrganizationCategoryInline.fields

    def test_org_change_form_renders_action_url_field(
        self, admin_client: Client,
    ) -> None:
        org = Organization(
            name="Admin URL Org",
            website_url="https://example.org",
        )
        org.set_current_language("en")
        org.description = "General."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="volunteer"),
        )
        entry.set_current_language("en")
        entry.action_url = "https://example.org/volunteer"
        entry.save()

        response = admin_client.get(
            f"/admin/organizations/organization/{org.pk}/change/",
        )

        assert response.status_code == 200
        assert b"action_url" in response.content


@pytest.mark.django_db
class TestCategoryAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/category/")
        assert response.status_code == 200

    def test_search_by_label(self, admin_client: Client) -> None:
        Category.objects.get_or_create(
            slug="test-cat", defaults={"label": "Test Category"},
        )
        Category.objects.get_or_create(
            slug="other-cat", defaults={"label": "Other Category"},
        )
        response = admin_client.get(
            "/admin/organizations/category/?q=Test",
        )
        assert response.status_code == 200
        assert b"Test Category" in response.content
        assert b"Other Category" not in response.content


@pytest.mark.django_db
class TestSDGAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/sdg/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestOperatingRegionAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/operatingregion/")
        assert response.status_code == 200

    def test_search_by_name(self, admin_client: Client) -> None:
        OperatingRegion.objects.get_or_create(
            country_code="US",
            region_code="",
            defaults={"name": "United States"},
        )
        OperatingRegion.objects.get_or_create(
            country_code="CA",
            region_code="",
            defaults={"name": "Canada"},
        )
        response = admin_client.get(
            "/admin/organizations/operatingregion/?q=United",
        )
        assert response.status_code == 200
        assert b"United States" in response.content
        assert b"Canada" not in response.content


@pytest.mark.django_db
class TestFocusAreaAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/focusarea/")
        assert response.status_code == 200

    def test_filter_by_reviewed(self, admin_client: Client) -> None:
        FocusArea.objects.create(name="Reviewed Focus Area", reviewed=True)
        FocusArea.objects.create(name="Unreviewed Focus Area", reviewed=False)
        response = admin_client.get(
            "/admin/organizations/focusarea/?reviewed__exact=1",
        )
        assert response.status_code == 200
        assert b"Reviewed Focus Area" in response.content
        assert b"Unreviewed Focus Area" not in response.content

    def test_save_sets_reviewed_by_to_current_user(
        self, admin_client: Client, django_user_model: Any,
    ) -> None:
        fa = FocusArea.objects.create(name="test_term")
        response = admin_client.post(
            f"/admin/organizations/focusarea/{fa.pk}/change/",
            {"name": "test_term", "reviewed": "on"},
        )
        assert response.status_code == 302
        fa.refresh_from_db()
        admin_user = django_user_model.objects.get(username="admin")
        assert fa.reviewed is True
        assert fa.reviewed_by == admin_user
        assert fa.reviewed_at is not None


@pytest.mark.django_db
class TestSkillAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/skill/")
        assert response.status_code == 200

    def test_filter_by_reviewed(self, admin_client: Client) -> None:
        Skill.objects.create(name="Reviewed Skill", reviewed=True)
        Skill.objects.create(name="Unreviewed Skill", reviewed=False)
        response = admin_client.get(
            "/admin/organizations/skill/?reviewed__exact=1",
        )
        assert response.status_code == 200
        assert b"Reviewed Skill" in response.content
        assert b"Unreviewed Skill" not in response.content


@pytest.mark.django_db
class TestEngagementOpportunityAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get(
            "/admin/organizations/engagementopportunity/",
        )
        assert response.status_code == 200

    def test_filter_by_engagement_type(
        self, admin_client: Client,
    ) -> None:
        org = Organization.objects.create(name="Test Org")
        matching = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type="donate_one_time",
            description="Donate once",
        )
        non_matching = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type="volunteer_remote",
            description="Volunteer remotely",
        )
        response = admin_client.get(
            "/admin/organizations/engagementopportunity/"
            "?engagement_type__exact=donate_one_time",
        )
        assert response.status_code == 200
        result_pks = list(
            response.context["cl"].queryset.values_list("pk", flat=True),
        )
        assert matching.pk in result_pks
        assert non_matching.pk not in result_pks
