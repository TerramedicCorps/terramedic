import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import OperatingRegion


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
