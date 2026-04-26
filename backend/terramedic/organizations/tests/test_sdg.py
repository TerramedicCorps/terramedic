import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import SDG, Organization


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
