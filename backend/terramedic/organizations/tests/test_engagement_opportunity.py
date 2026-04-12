import pytest

from terramedic.organizations.models import (
    EngagementOpportunity,
    EngagementType,
    Organization,
    Skill,
)


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
