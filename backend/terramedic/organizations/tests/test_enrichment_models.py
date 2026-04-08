import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import (
    EngagementOpportunity,
    EngagementType,
    FocusArea,
    GeographicScope,
    OperatingRegion,
    Organization,
    TimeCommitment,
)

# -- FocusArea ---------------------------------------------------------


@pytest.mark.django_db
class TestFocusArea:
    def test_create_focus_area(self) -> None:
        fa = FocusArea.objects.create(name="ocean_conservation")
        assert fa.pk is not None
        assert fa.name == "ocean_conservation"

    def test_str_returns_name(self) -> None:
        fa = FocusArea.objects.create(name="reforestation")
        assert str(fa) == "reforestation"

    def test_name_is_unique(self) -> None:
        FocusArea.objects.create(name="climate_policy")
        with pytest.raises(IntegrityError):
            FocusArea.objects.create(name="climate_policy")

    def test_reviewed_defaults_to_false(self) -> None:
        fa = FocusArea.objects.create(name="urban_ecology")
        assert fa.reviewed is False

    def test_reviewed_can_be_set_true(self) -> None:
        fa = FocusArea.objects.create(
            name="climate_policy", reviewed=True,
        )
        fa.refresh_from_db()
        assert fa.reviewed is True

    def test_ordering_by_name(self) -> None:
        FocusArea.objects.create(name="wildlife_protection")
        FocusArea.objects.create(name="biodiversity_monitoring")
        names = list(
            FocusArea.objects.values_list("name", flat=True),
        )
        assert names == [
            "biodiversity_monitoring",
            "wildlife_protection",
        ]


# -- OperatingRegion ---------------------------------------------------


@pytest.mark.django_db
class TestOperatingRegion:
    def test_create_with_country_only(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        assert r.pk is not None
        assert r.country_code == "US"
        assert r.region_code == ""

    def test_create_with_country_and_region(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="US",
            region_code="US-CA",
            name="California",
        )
        assert r.region_code == "US-CA"

    def test_str_returns_name(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="GB", name="United Kingdom",
        )
        assert str(r) == "United Kingdom"

    def test_unique_together_country_and_region(self) -> None:
        OperatingRegion.objects.create(
            country_code="US",
            region_code="US-CA",
            name="California",
        )
        with pytest.raises(IntegrityError):
            OperatingRegion.objects.create(
                country_code="US",
                region_code="US-CA",
                name="CA duplicate",
            )

    def test_same_country_different_regions_allowed(self) -> None:
        OperatingRegion.objects.create(
            country_code="US",
            region_code="US-CA",
            name="California",
        )
        r2 = OperatingRegion.objects.create(
            country_code="US",
            region_code="US-NY",
            name="New York",
        )
        assert r2.pk is not None

    def test_invalid_country_code_rejected(self) -> None:
        r = OperatingRegion(
            country_code="zz", name="Invalid",
        )
        with pytest.raises(ValidationError):
            r.full_clean()

    def test_ordering_by_country_then_name(self) -> None:
        OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        OperatingRegion.objects.create(
            country_code="GB", name="United Kingdom",
        )
        codes = list(
            OperatingRegion.objects.values_list(
                "country_code", flat=True,
            ),
        )
        assert codes == ["GB", "US"]


# -- Enums -------------------------------------------------------------


class TestGeographicScope:
    def test_choices_exist(self) -> None:
        assert GeographicScope.LOCAL == "local"
        assert GeographicScope.STATE == "state"
        assert GeographicScope.REGIONAL == "regional"
        assert GeographicScope.NATIONAL == "national"
        assert GeographicScope.MULTINATIONAL == "multinational"
        assert GeographicScope.GLOBAL == "global"


class TestTimeCommitment:
    def test_choices_exist(self) -> None:
        assert TimeCommitment.MINUTES == "minutes"
        assert TimeCommitment.HOURS_PER_WEEK == "hours_per_week"
        assert TimeCommitment.DAYS_PER_MONTH == "days_per_month"
        assert TimeCommitment.FLEXIBLE == "flexible"
        assert TimeCommitment.EVENT_BASED == "event_based"


class TestEngagementType:
    def test_choices_exist(self) -> None:
        assert EngagementType.VOLUNTEER_IN_PERSON == "volunteer_in_person"
        assert EngagementType.VOLUNTEER_REMOTE == "volunteer_remote"
        assert EngagementType.DONATE_ONE_TIME == "donate_one_time"
        assert EngagementType.DONATE_RECURRING == "donate_recurring"
        assert EngagementType.ADVOCACY == "advocacy"
        assert EngagementType.EDUCATION == "education"
        assert EngagementType.CAREER == "career"
        assert EngagementType.CITIZEN_SCIENCE == "citizen_science"


# -- Organization enrichment fields ------------------------------------


@pytest.fixture
def org() -> Organization:
    o = Organization(
        name="Test Org",
        website_url="https://example.com",
    )
    o.set_current_language("en")
    o.description = "A test organization."
    o.action_text = "Donate"
    o.save()
    return o


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


# -- EngagementOpportunity ---------------------------------------------


@pytest.mark.django_db
class TestEngagementOpportunity:
    def test_create(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Beach cleanup",
        )
        assert eo.pk is not None

    def test_str(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_ONE_TIME,
            description="One-time donation",
        )
        assert "Test Org" in str(eo)
        assert "donate_one_time" in str(eo)

    def test_time_commitment_blank_by_default(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.ADVOCACY,
            description="Sign petition",
        )
        assert eo.time_commitment == ""

    def test_skills_helpful_default_empty(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CITIZEN_SCIENCE,
            description="Bird count",
        )
        assert eo.skills_helpful == []

    def test_skills_helpful_stores_list(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Data entry",
            skills_helpful=["data_entry", "GIS"],
        )
        eo.refresh_from_db()
        assert eo.skills_helpful == ["data_entry", "GIS"]

    def test_cascade_delete_with_org(
        self, org: Organization,
    ) -> None:
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CAREER,
            description="Conservation officer",
        )
        org.delete()
        assert EngagementOpportunity.objects.count() == 0

    def test_ordering_by_engagement_type(
        self, org: Organization,
    ) -> None:
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Cleanup",
        )
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.ADVOCACY,
            description="Sign petition",
        )
        types = list(
            EngagementOpportunity.objects.values_list(
                "engagement_type", flat=True,
            ),
        )
        assert types == ["advocacy", "volunteer_in_person"]


# -- location_bound auto-detection ------------------------------------


@pytest.mark.django_db
class TestLocationBound:
    def test_volunteer_in_person_defaults_true(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Beach cleanup",
        )
        assert eo.location_bound is True

    def test_career_defaults_true(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CAREER,
            description="Park ranger",
        )
        assert eo.location_bound is True

    def test_donate_defaults_false(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_ONE_TIME,
            description="Donate",
        )
        assert eo.location_bound is False

    def test_remote_volunteer_defaults_false(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Data entry",
        )
        assert eo.location_bound is False

    def test_override_to_true(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_RECURRING,
            description="Monthly donor",
            location_bound=True,
        )
        assert eo.location_bound is True

    def test_override_to_false(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Remote-friendly cleanup coord",
            location_bound=False,
        )
        assert eo.location_bound is False
