import pytest
from django.core.management import call_command

from terramedic.organizations.models import Category, Organization, Tag


@pytest.fixture
def seed_data(db: None) -> None:
    call_command("loaddata", "seed_data")


@pytest.mark.django_db
class TestSeedDataFixture:
    @pytest.fixture(autouse=True)
    def _load_seed_data(self, seed_data: None) -> None:
        pass

    def test_organizations_loaded(self) -> None:
        assert Organization.objects.count() > 0

    def test_tags_loaded(self) -> None:
        assert Tag.objects.count() > 0

    def test_category_counts(self) -> None:
        assert Organization.objects.filter(category=Category.DONATE).count() == 5
        assert Organization.objects.filter(category=Category.VOLUNTEER).count() == 3
        assert Organization.objects.filter(category=Category.RESOURCE).count() == 6
        assert Organization.objects.filter(category=Category.ACTION).count() == 2

    def test_all_orgs_have_translations(self) -> None:
        for org in Organization.objects.all():
            org.set_current_language("en")
            assert org.description != "", f"{org.name} missing description"
            assert org.action_text != "", f"{org.name} missing action_text"

    def test_org_has_tags(self) -> None:
        org = Organization.objects.get(name="Give Green")
        tag_names = set(org.tags.values_list("name", flat=True))
        assert tag_names == {
            "Political Giving",
            "Electoral Impact",
            "Climate Champions",
        }

    def test_sort_order_preserved(self) -> None:
        donate_orgs = list(
            Organization.objects.filter(category=Category.DONATE)
            .order_by("sort_order")
            .values_list("name", flat=True),
        )
        assert donate_orgs[0] == "Climate Cabinet"
        assert donate_orgs[-1] == "Citizens' Climate Lobby"

    def test_all_orgs_active(self) -> None:
        assert Organization.objects.filter(is_active=False).count() == 0
