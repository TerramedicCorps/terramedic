from typing import Any

import pytest
from django.db import IntegrityError

from terramedic.organizations.models import Skill


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
