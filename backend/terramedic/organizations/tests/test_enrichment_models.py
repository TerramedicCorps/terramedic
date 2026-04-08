import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import (
    Category,
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

    def test_ordering_by_name(self) -> None:
        FocusArea.objects.create(name="wildlife_protection")
        FocusArea.objects.create(name="biodiversity_monitoring")
        names = list(FocusArea.objects.values_list("name", flat=True))
        assert names == sorted(names)


# -- OperatingRegion ---------------------------------------------------


@pytest.mark.django_db
class TestOperatingRegion:
    def test_create_with_country_only(self) -> None:
        region = OperatingRegion.objects.create(
            country_code="KE",
            name="Kenya",
        )
        assert region.pk is not None
        assert region.country_code == "KE"
        assert region.region_code == ""

    def test_create_with_country_and_region(self) -> None:
        region = OperatingRegion.objects.create(
            country_code="US",
            region_code="US-CA",
            name="California",
        )
        assert region.country_code == "US"
        assert region.region_code == "US-CA"
        assert region.name == "California"

    def test_str_returns_name(self) -> None:
        region = OperatingRegion.objects.create(
            country_code="GB",
            name="United Kingdom",
        )
        assert str(region) == "United Kingdom"

    def test_unique_together_country_and_region(self) -> None:
        OperatingRegion.objects.create(
            country_code="US",
            region_code="US-OR",
            name="Oregon",
        )
        with pytest.raises(IntegrityError):
            OperatingRegion.objects.create(
                country_code="US",
                region_code="US-OR",
                name="Oregon duplicate",
            )

    def test_same_country_different_regions_allowed(self) -> None:
        OperatingRegion.objects.create(
            country_code="US",
            region_code="US-CA",
            name="California",
        )
        region2 = OperatingRegion.objects.create(
            country_code="US",
            region_code="US-OR",
            name="Oregon",
        )
        assert region2.pk is not None

    def test_ordering_by_country_then_name(self) -> None:
        OperatingRegion.objects.create(
            country_code="US",
            name="United States",
        )
        OperatingRegion.objects.create(
            country_code="GB",
            name="United Kingdom",
        )
        codes = list(
            OperatingRegion.objects.values_list("country_code", flat=True),
        )
        assert codes == ["GB", "US"]


# -- GeographicScope & TimeCommitment enums ----------------------------


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
        website_url="https://example.com/",
        category=Category.VOLUNTEER,
    )
    o.set_current_language("en")
    o.description = "Test description."
    o.action_text = "Get involved"
    o.save()
    return o


@pytest.mark.django_db
class TestOrganizationEnrichmentFields:
    def test_geographic_scope(self, org: Organization) -> None:
        org.geographic_scope = GeographicScope.NATIONAL
        org.save()
        org.refresh_from_db()
        assert org.geographic_scope == GeographicScope.NATIONAL

    def test_geographic_scope_blank_by_default(self, org: Organization) -> None:
        assert org.geographic_scope == ""

    def test_invalid_geographic_scope(self, org: Organization) -> None:
        org.geographic_scope = "interplanetary"
        org.save()
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_year_founded(self, org: Organization) -> None:
        org.year_founded = 1970
        org.save()
        org.refresh_from_db()
        assert org.year_founded == 1970

    def test_year_founded_nullable(self, org: Organization) -> None:
        assert org.year_founded is None

    def test_legal_status(self, org: Organization) -> None:
        org.legal_status = "501(c)(3)"
        org.save()
        org.refresh_from_db()
        assert org.legal_status == "501(c)(3)"

    def test_legal_status_blank_by_default(self, org: Organization) -> None:
        assert org.legal_status == ""

    def test_evidence_score(self, org: Organization) -> None:
        org.evidence_score = 4
        org.save()
        org.refresh_from_db()
        assert org.evidence_score == 4

    def test_evidence_score_nullable(self, org: Organization) -> None:
        assert org.evidence_score is None

    def test_donate_url(self, org: Organization) -> None:
        org.donate_url = "https://example.com/donate"
        org.save()
        org.refresh_from_db()
        assert org.donate_url == "https://example.com/donate"

    def test_donate_url_blank_by_default(self, org: Organization) -> None:
        assert org.donate_url == ""

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


# -- Organization M2M relationships ------------------------------------


@pytest.mark.django_db
class TestOrganizationFocusAreas:
    def test_add_focus_areas(self, org: Organization) -> None:
        fa1 = FocusArea.objects.create(name="ocean_conservation")
        fa2 = FocusArea.objects.create(name="reforestation")
        org.focus_areas.add(fa1, fa2)
        assert set(org.focus_areas.all()) == {fa1, fa2}

    def test_focus_areas_empty_by_default(self, org: Organization) -> None:
        assert org.focus_areas.count() == 0

    def test_focus_area_shared_across_orgs(self, org: Organization) -> None:
        fa = FocusArea.objects.create(name="climate_policy")
        org.focus_areas.add(fa)

        org2 = Organization(
            name="Other Org",
            website_url="https://other.com/",
            category=Category.DONATE,
        )
        org2.set_current_language("en")
        org2.description = "Another org."
        org2.action_text = "Donate"
        org2.save()
        org2.focus_areas.add(fa)

        assert fa.organizations.count() == 2  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestOrganizationOperatingRegions:
    def test_add_operating_regions(self, org: Organization) -> None:
        r1 = OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        r2 = OperatingRegion.objects.create(
            country_code="KE", name="Kenya",
        )
        org.operating_regions.add(r1, r2)
        assert set(org.operating_regions.all()) == {r1, r2}

    def test_operating_regions_empty_by_default(
        self, org: Organization,
    ) -> None:
        assert org.operating_regions.count() == 0

    def test_filter_orgs_by_country(self, org: Organization) -> None:
        r = OperatingRegion.objects.create(
            country_code="KE", name="Kenya",
        )
        org.operating_regions.add(r)

        orgs = Organization.objects.filter(
            operating_regions__country_code="KE",
        )
        assert org in orgs


# -- EngagementOpportunity ---------------------------------------------


@pytest.mark.django_db
class TestEngagementOpportunity:
    def test_create_engagement(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Beach cleanup events every Saturday.",
            time_commitment=TimeCommitment.HOURS_PER_WEEK,
        )
        assert eo.pk is not None
        assert eo.organization == org
        assert eo.engagement_type == EngagementType.VOLUNTEER_IN_PERSON

    def test_str_representation(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.ADVOCACY,
            description="Contact your representatives.",
        )
        assert str(eo) == "Test Org - advocacy"

    def test_url_optional(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_ONE_TIME,
            description="One-time donation.",
        )
        assert eo.url == ""

    def test_time_commitment_optional(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_RECURRING,
            description="Monthly giving.",
        )
        assert eo.time_commitment == ""

    def test_skills_helpful_default_empty(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CITIZEN_SCIENCE,
            description="Classify camera trap images.",
        )
        assert eo.skills_helpful == []

    def test_skills_helpful_stores_list(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="GIS data analysis for habitat mapping.",
            skills_helpful=["GIS", "data_analysis", "python"],
        )
        eo.refresh_from_db()
        assert eo.skills_helpful == ["GIS", "data_analysis", "python"]

    def test_cascade_delete_with_org(self, org: Organization) -> None:
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.EDUCATION,
            description="Online course.",
        )
        org_pk = org.pk
        org.delete()
        assert (
            EngagementOpportunity.objects.filter(
                organization_id=org_pk,
            ).count()
            == 0
        )

    def test_multiple_engagements_per_org(self, org: Organization) -> None:
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Fieldwork.",
        )
        EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_ONE_TIME,
            description="Donate.",
        )
        assert org.engagement_opportunities.count() == 2

    def test_invalid_engagement_type(self, org: Organization) -> None:
        eo = EngagementOpportunity(
            organization=org,
            engagement_type="invalid_type",
            description="Bad type.",
        )
        eo.save()
        with pytest.raises(ValidationError):
            eo.full_clean()

    def test_invalid_time_commitment(self, org: Organization) -> None:
        eo = EngagementOpportunity(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Remote work.",
            time_commitment="all_the_time",
        )
        eo.save()
        with pytest.raises(ValidationError):
            eo.full_clean()

    def test_location_bound_defaults_true_for_in_person(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="Beach cleanup.",
        )
        assert eo.location_bound is True

    def test_location_bound_defaults_true_for_career(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CAREER,
            description="Full-time role.",
        )
        assert eo.location_bound is True

    def test_location_bound_defaults_false_for_donate(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.DONATE_ONE_TIME,
            description="One-time donation.",
        )
        assert eo.location_bound is False

    def test_location_bound_defaults_false_for_remote(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Remote data entry.",
        )
        assert eo.location_bound is False

    def test_location_bound_defaults_false_for_advocacy(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.ADVOCACY,
            description="Sign petition.",
        )
        assert eo.location_bound is False

    def test_location_bound_defaults_false_for_citizen_science(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CITIZEN_SCIENCE,
            description="Classify images.",
        )
        assert eo.location_bound is False

    def test_location_bound_override_to_true(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Remote role requiring US timezone.",
            location_bound=True,
        )
        eo.refresh_from_db()
        assert eo.location_bound is True

    def test_location_bound_override_to_false(self, org: Organization) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_IN_PERSON,
            description="In-person role with no location requirement.",
            location_bound=False,
        )
        eo.refresh_from_db()
        assert eo.location_bound is False
