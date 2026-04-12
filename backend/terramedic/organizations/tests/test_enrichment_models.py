import json
from pathlib import Path
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import (
    SDG,
    AIRecommendation,
    EngagementOpportunity,
    EngagementType,
    FocusArea,
    GeographicScope,
    OperatingRegion,
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
    Skill,
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

    def test_reviewed_by_defaults_null(self) -> None:
        fa = FocusArea.objects.create(name="wetland_restoration")
        assert fa.reviewed_by is None

    def test_reviewed_at_defaults_null(self) -> None:
        fa = FocusArea.objects.create(name="pollinator_habitat")
        assert fa.reviewed_at is None

    def test_save_with_user_sets_reviewed_by(
        self, django_user_model: Any,
    ) -> None:
        reviewer = django_user_model.objects.create_user(username="reviewer")
        fa = FocusArea.objects.create(name="riparian_buffer")
        fa.reviewed = True
        fa.save(user=reviewer)
        fa.refresh_from_db()
        assert fa.reviewed_by == reviewer

    def test_save_without_user_leaves_reviewed_by_null(self) -> None:
        fa = FocusArea.objects.create(name="urban_canopy")
        fa.reviewed = True
        fa.save()
        fa.refresh_from_db()
        assert fa.reviewed_by is None

    def test_reviewed_at_auto_set_when_reviewed_toggled_true(self) -> None:
        fa = FocusArea.objects.create(name="carbon_sequestration")
        assert fa.reviewed_at is None
        fa.reviewed = True
        fa.save()
        fa.refresh_from_db()
        assert fa.reviewed_at is not None

    def test_reviewed_at_cleared_when_reviewed_toggled_false(self) -> None:
        fa = FocusArea.objects.create(
            name="soil_health", reviewed=True,
        )
        assert fa.reviewed_at is not None
        fa.reviewed = False
        fa.save()
        fa.refresh_from_db()
        assert fa.reviewed_at is None
        assert fa.reviewed_by is None

    def test_reviewed_at_not_overwritten_on_re_save(self) -> None:
        fa = FocusArea.objects.create(
            name="agroforestry", reviewed=True,
        )
        original_at = fa.reviewed_at
        fa.name = "agroforestry_updated"
        fa.save()
        fa.refresh_from_db()
        assert fa.reviewed_at == original_at


# -- CuratorProposedTerm audit fields on Skill -------------------------


@pytest.mark.django_db
class TestSkillAuditFields:
    def test_reviewed_by_defaults_null(self) -> None:
        s = Skill.objects.create(name="water_testing")
        assert s.reviewed_by is None

    def test_reviewed_at_defaults_null(self) -> None:
        s = Skill.objects.create(name="public_speaking")
        assert s.reviewed_at is None

    def test_save_with_user_sets_reviewed_by(
        self, django_user_model: Any,
    ) -> None:
        reviewer = django_user_model.objects.create_user(username="skill_reviewer")
        s = Skill.objects.create(name="data_analysis")
        s.reviewed = True
        s.save(user=reviewer)
        s.refresh_from_db()
        assert s.reviewed_by == reviewer

    def test_save_without_user_leaves_reviewed_by_null(self) -> None:
        s = Skill.objects.create(name="first_aid")
        s.reviewed = True
        s.save()
        s.refresh_from_db()
        assert s.reviewed_by is None

    def test_reviewed_at_auto_set_when_reviewed_toggled_true(self) -> None:
        s = Skill.objects.create(name="grant_writing")
        assert s.reviewed_at is None
        s.reviewed = True
        s.save()
        s.refresh_from_db()
        assert s.reviewed_at is not None

    def test_reviewed_at_cleared_when_reviewed_toggled_false(self) -> None:
        s = Skill.objects.create(
            name="fundraising", reviewed=True,
        )
        assert s.reviewed_at is not None
        s.reviewed = False
        s.save()
        s.refresh_from_db()
        assert s.reviewed_at is None
        assert s.reviewed_by is None

    def test_reviewed_at_not_overwritten_on_re_save(self) -> None:
        s = Skill.objects.create(
            name="project_management", reviewed=True,
        )
        original_at = s.reviewed_at
        s.name = "project_management_updated"
        s.save()
        s.refresh_from_db()
        assert s.reviewed_at == original_at


# -- SDG ---------------------------------------------------------------


@pytest.mark.django_db
class TestSDG:
    def test_create_sdg(self) -> None:
        sdg = SDG.objects.create(number=13, name="Climate Action")
        assert sdg.pk == 13
        assert sdg.name == "Climate Action"

    def test_number_is_primary_key(self) -> None:
        sdg = SDG.objects.create(number=14, name="Life Below Water")
        assert sdg.pk == 14

    def test_str_returns_number_and_name(self) -> None:
        sdg = SDG.objects.create(number=15, name="Life on Land")
        assert str(sdg) == "SDG 15: Life on Land"

    def test_duplicate_number_rejected(self) -> None:
        SDG.objects.create(number=13, name="Climate Action")
        with pytest.raises(IntegrityError):
            SDG.objects.create(number=13, name="Duplicate")

    def test_ordering_by_number(self) -> None:
        SDG.objects.create(number=15, name="Life on Land")
        SDG.objects.create(number=13, name="Climate Action")
        SDG.objects.create(number=14, name="Life Below Water")
        numbers = list(SDG.objects.values_list("number", flat=True))
        assert numbers == [13, 14, 15]

    def test_org_sdg_m2m(self, org: Organization) -> None:
        sdg13 = SDG.objects.create(number=13, name="Climate Action")
        sdg15 = SDG.objects.create(number=15, name="Life on Land")
        org.sdgs.add(sdg13, sdg15)
        assert set(org.sdgs.all()) == {sdg13, sdg15}

    def test_sdg_shared_across_orgs(self) -> None:
        sdg = SDG.objects.create(number=14, name="Life Below Water")
        org1 = Organization.objects.create(
            name="Ocean Conservancy", website_url="https://example.com/oc",
        )
        org2 = Organization.objects.create(
            name="Surfrider", website_url="https://example.com/sr",
        )
        org1.sdgs.add(sdg)
        org2.sdgs.add(sdg)
        assert Organization.objects.filter(sdgs=sdg).count() == 2

    def test_number_rejects_below_1(self) -> None:
        sdg = SDG(number=0, name="Invalid")
        with pytest.raises(ValidationError):
            sdg.full_clean()

    def test_number_rejects_above_17(self) -> None:
        sdg = SDG(number=18, name="Invalid")
        with pytest.raises(ValidationError):
            sdg.full_clean()


# -- Skill -------------------------------------------------------------


@pytest.mark.django_db
class TestSkill:
    def test_create_skill(self) -> None:
        s = Skill.objects.create(name="GIS")
        assert s.pk is not None
        assert s.name == "GIS"

    def test_str_returns_name(self) -> None:
        s = Skill.objects.create(name="data_analysis")
        assert str(s) == "data_analysis"

    def test_name_is_unique(self) -> None:
        Skill.objects.create(name="communications")
        with pytest.raises(IntegrityError):
            Skill.objects.create(name="communications")

    def test_reviewed_defaults_to_false(self) -> None:
        s = Skill.objects.create(name="legal")
        assert s.reviewed is False

    def test_reviewed_can_be_set_true(self) -> None:
        s = Skill.objects.create(name="fundraising", reviewed=True)
        s.refresh_from_db()
        assert s.reviewed is True

    def test_ordering_by_name(self) -> None:
        Skill.objects.create(name="writing")
        Skill.objects.create(name="data_entry")
        names = list(Skill.objects.values_list("name", flat=True))
        assert names == ["data_entry", "writing"]


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

    def test_continent_auto_set_on_save(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="KE", name="Kenya",
        )
        assert r.continent == "Africa"

    def test_continent_set_for_each_continent(self) -> None:
        cases = [
            ("US", "North America"),
            ("BR", "South America"),
            ("DE", "Europe"),
            ("JP", "Asia"),
            ("AU", "Oceania"),
            ("KE", "Africa"),
        ]
        for code, expected in cases:
            r = OperatingRegion.objects.create(
                country_code=code, name=code,
            )
            assert r.continent == expected, (
                f"{code} should be {expected}, got {r.continent}"
            )

    def test_continent_updates_on_country_change(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        assert r.continent == "North America"
        r.country_code = "JP"
        r.save()
        r.refresh_from_db()
        assert r.continent == "Asia"

    def test_continent_blank_for_unknown_code(self) -> None:
        r = OperatingRegion(
            country_code="XX", name="Unknown",
        )
        r.save()
        assert r.continent == ""

    def test_continent_persisted_to_db(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="GB", name="United Kingdom",
        )
        r.refresh_from_db()
        assert r.continent == "Europe"

    def test_continent_included_in_update_fields(self) -> None:
        r = OperatingRegion.objects.create(
            country_code="US", name="United States",
        )
        assert r.continent == "North America"
        r.country_code = "JP"
        r.name = "Japan"
        r.save(update_fields=["country_code", "name"])
        r.refresh_from_db()
        assert r.continent == "Asia"

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


# -- Enum ↔ schema sync ------------------------------------------------

_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[3] / "curation" / "schema.json")
    .read_text(),
)


class TestEnumSchemaSync:
    """Enum values stay in sync with curation/schema.json."""

    def test_geographic_scope_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"]["geographic_coverage"][
            "properties"
        ]["scope"]["enum"]
        model_values = [c.value for c in GeographicScope]
        assert set(model_values) == set(schema_values)

    def test_engagement_type_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"][
            "engagement_opportunities"
        ]["items"]["properties"]["engagement_type"]["enum"]
        model_values = [c.value for c in EngagementType]
        assert set(model_values) == set(schema_values)

    def test_time_commitment_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"][
            "engagement_opportunities"
        ]["items"]["properties"]["time_commitment"]["enum"]
        model_values = [c.value for c in TimeCommitment]
        assert set(model_values) == set(schema_values)


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

    def test_skills_empty_by_default(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.CITIZEN_SCIENCE,
            description="Bird count",
        )
        assert eo.skills.count() == 0

    def test_add_skills(
        self, org: Organization,
    ) -> None:
        eo = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.VOLUNTEER_REMOTE,
            description="Data entry",
        )
        s1 = Skill.objects.create(name="data_entry")
        s2 = Skill.objects.create(name="GIS")
        eo.skills.add(s1, s2)
        assert set(eo.skills.all()) == {s1, s2}

    def test_skill_shared_across_opportunities(
        self, org: Organization,
    ) -> None:
        s = Skill.objects.create(name="communications")
        eo1 = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.ADVOCACY,
            description="Outreach",
        )
        eo2 = EngagementOpportunity.objects.create(
            organization=org,
            engagement_type=EngagementType.EDUCATION,
            description="Workshops",
        )
        eo1.skills.add(s)
        eo2.skills.add(s)
        assert EngagementOpportunity.objects.filter(skills=s).count() == 2

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


# -- OrganizationEvaluation (enrichment fields) -------------------------


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
