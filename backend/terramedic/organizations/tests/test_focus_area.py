from typing import Any

import pytest
from django.db import IntegrityError

from terramedic.organizations.models import FocusArea


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

    def test_update_fields_includes_mutated_audit_fields(self) -> None:
        fa = FocusArea.objects.create(name="wetland_mgmt")
        fa.reviewed = True
        fa.save(update_fields=["reviewed"])
        fa.refresh_from_db()
        assert fa.reviewed is True
        assert fa.reviewed_at is not None

    def test_update_fields_clears_audit_fields_on_uncheck(
        self, django_user_model: Any,
    ) -> None:
        reviewer = django_user_model.objects.create_user(username="rev2")
        fa = FocusArea.objects.create(name="mangrove_mgmt", reviewed=True)
        fa.reviewed_by = reviewer
        fa.save(update_fields=["reviewed_by"])
        fa.refresh_from_db()
        assert fa.reviewed_by == reviewer
        fa.reviewed = False
        fa.save(update_fields=["reviewed"])
        fa.refresh_from_db()
        assert fa.reviewed_at is None
        assert fa.reviewed_by is None
