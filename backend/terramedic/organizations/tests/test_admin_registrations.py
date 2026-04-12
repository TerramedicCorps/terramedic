"""Tests for admin registrations of all organization models."""

import pytest
from django.contrib import admin
from django.test import Client

from terramedic.organizations.models import (
    SDG,
    Category,
    EngagementOpportunity,
    FocusArea,
    OperatingRegion,
    Organization,
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
            Tag,
        ],
    )
    def test_model_is_registered(self, model: type) -> None:
        assert admin.site.is_registered(model), (
            f"{model.__name__} is not registered in the admin"
        )


@pytest.mark.django_db
class TestCategoryAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/category/")
        assert response.status_code == 200

    def test_search_by_label(self, admin_client: Client) -> None:
        Category.objects.get_or_create(
            slug="test-cat", defaults={"label": "Test Category"},
        )
        response = admin_client.get(
            "/admin/organizations/category/?q=Test",
        )
        assert response.status_code == 200


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
        response = admin_client.get(
            "/admin/organizations/operatingregion/?q=United",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestFocusAreaAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/focusarea/")
        assert response.status_code == 200

    def test_filter_by_reviewed(self, admin_client: Client) -> None:
        response = admin_client.get(
            "/admin/organizations/focusarea/?reviewed__exact=1",
        )
        assert response.status_code == 200

    def test_save_sets_reviewed_by_to_current_user(
        self, admin_client: Client,
    ) -> None:
        fa = FocusArea.objects.create(name="test_term")
        response = admin_client.post(
            f"/admin/organizations/focusarea/{fa.pk}/change/",
            {"name": "test_term", "reviewed": "on"},
        )
        assert response.status_code == 302
        fa.refresh_from_db()
        assert fa.reviewed is True
        assert fa.reviewed_by is not None
        assert fa.reviewed_at is not None


@pytest.mark.django_db
class TestSkillAdmin:
    def test_changelist_loads(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/organizations/skill/")
        assert response.status_code == 200

    def test_filter_by_reviewed(self, admin_client: Client) -> None:
        response = admin_client.get(
            "/admin/organizations/skill/?reviewed__exact=1",
        )
        assert response.status_code == 200


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
        response = admin_client.get(
            "/admin/organizations/engagementopportunity/"
            "?engagement_type=donate",
        )
        assert response.status_code == 200
