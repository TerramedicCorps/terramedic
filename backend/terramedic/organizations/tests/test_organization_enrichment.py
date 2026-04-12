import pytest
from django.core.exceptions import ValidationError

from terramedic.organizations.models import (
    FocusArea,
    GeographicScope,
    OperatingRegion,
    Organization,
)


@pytest.mark.django_db
class TestOrganizationEnrichmentFields:
    def test_geographic_scope(self, org: Organization) -> None:
        org.geographic_scope = GeographicScope.NATIONAL
        org.save()
        org.refresh_from_db()
        assert org.geographic_scope == GeographicScope.NATIONAL

    def test_geographic_scope_blank_by_default(
        self, org: Organization,
    ) -> None:
        assert org.geographic_scope == ""

    def test_year_founded(self, org: Organization) -> None:
        org.year_founded = 1985
        org.save()
        org.refresh_from_db()
        assert org.year_founded == 1985

    def test_year_founded_null_by_default(
        self, org: Organization,
    ) -> None:
        assert org.year_founded is None

    def test_year_founded_rejects_negative(
        self, org: Organization,
    ) -> None:
        org.year_founded = -500
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_year_founded_rejects_far_future(
        self, org: Organization,
    ) -> None:
        org.year_founded = 99999
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_legal_status(self, org: Organization) -> None:
        org.legal_status = "501(c)(3)"
        org.save()
        org.refresh_from_db()
        assert org.legal_status == "501(c)(3)"

    def test_evidence_score(self, org: Organization) -> None:
        org.evidence_score = 4
        org.save()
        org.refresh_from_db()
        assert org.evidence_score == 4

    def test_evidence_score_rejects_out_of_range(
        self, org: Organization,
    ) -> None:
        org.evidence_score = 6
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_donate_url(self, org: Organization) -> None:
        org.donate_url = "https://example.com/donate"
        org.save()
        org.refresh_from_db()
        assert org.donate_url == "https://example.com/donate"

    def test_volunteer_url(self, org: Organization) -> None:
        org.volunteer_url = "https://example.com/volunteer"
        org.save()
        org.refresh_from_db()
        assert org.volunteer_url == "https://example.com/volunteer"

    def test_toolkit_url(self, org: Organization) -> None:
        org.toolkit_url = "https://example.com/toolkit"
        org.save()
        org.refresh_from_db()
        assert org.toolkit_url == "https://example.com/toolkit"


@pytest.mark.django_db
class TestOrganizationFocusAreas:
    def test_add_focus_areas(self, org: Organization) -> None:
        fa1 = FocusArea.objects.create(name="ocean_conservation")
        fa2 = FocusArea.objects.create(name="reforestation")
        org.focus_areas.add(fa1, fa2)
        assert set(org.focus_areas.all()) == {fa1, fa2}

    def test_focus_areas_empty_by_default(
        self, org: Organization,
    ) -> None:
        assert org.focus_areas.count() == 0

    def test_focus_area_shared_across_orgs(
        self, org: Organization,
    ) -> None:
        fa = FocusArea.objects.create(name="climate_policy")
        org.focus_areas.add(fa)

        org2 = Organization(
            name="Other Org",
            website_url="https://example2.com",
        )
        org2.set_current_language("en")
        org2.description = "Another org."
        org2.action_text = "Donate"
        org2.save()
        org2.focus_areas.add(fa)

        assert fa.organizations.count() == 2  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestOrganizationOperatingRegions:
    def test_add_operating_regions(
        self, org: Organization,
    ) -> None:
        r = OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        org.operating_regions.add(r)
        assert org.operating_regions.count() == 1

    def test_operating_regions_empty_by_default(
        self, org: Organization,
    ) -> None:
        assert org.operating_regions.count() == 0
