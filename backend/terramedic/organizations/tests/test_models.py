import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from terramedic.organizations.models import Category, Organization, Tag


@pytest.mark.django_db
class TestTag:
    def test_create_tag(self) -> None:
        tag = Tag.objects.create(name="Advocacy")

        assert tag.pk is not None
        assert tag.name == "Advocacy"

    def test_str_returns_name(self) -> None:
        tag = Tag.objects.create(name="Policy")

        assert str(tag) == "Policy"

    def test_name_is_unique(self) -> None:
        Tag.objects.create(name="Bipartisan")
        with pytest.raises(IntegrityError):
            Tag.objects.create(name="Bipartisan")


@pytest.mark.django_db
class TestOrganization:
    @pytest.fixture
    def org(self) -> Organization:
        o = Organization(
            name="Citizens' Climate Lobby",
            website_url="https://citizensclimatelobby.org/",
            category=Category.DONATE,
            sort_order=1,
        )
        o.set_current_language("en")
        o.description = "A grassroots advocacy organization."
        o.action_text = "Support Climate Advocacy"
        o.save()
        return o

    def test_create_organization(self) -> None:
        org = Organization(
            name="Citizens' Climate Lobby",
            website_url="https://citizensclimatelobby.org/",
            category=Category.DONATE,
            sort_order=1,
        )
        org.set_current_language("en")
        org.description = "A grassroots advocacy organization."
        org.action_text = "Support Climate Advocacy"
        org.save()

        assert org.pk is not None
        assert org.name == "Citizens' Climate Lobby"
        assert org.description == "A grassroots advocacy organization."
        assert org.action_text == "Support Climate Advocacy"
        assert org.category == Category.DONATE

    def test_str_returns_name(self, org: Organization) -> None:
        assert str(org) == "Citizens' Climate Lobby"

    def test_category_choices(self) -> None:
        assert Category.DONATE == "donate"
        assert Category.VOLUNTEER == "volunteer"
        assert Category.RESOURCE == "resource"
        assert Category.ACTION == "action"

    def test_invalid_category(self) -> None:
        org = Organization(
            name="Bad Org",
            website_url="https://example.com/",
            category="invalid",
        )
        org.set_current_language("en")
        org.description = "Test"
        org.action_text = "Test"
        org.save()

        with pytest.raises(ValidationError):
            org.full_clean()

    def test_translations(self) -> None:
        org = Organization(
            name="Give Green",
            website_url="https://givegreen.com/",
            category=Category.DONATE,
        )
        org.set_current_language("en")
        org.description = "Help donors direct political giving."
        org.action_text = "Donate to Candidates"
        org.set_current_language("fr")
        org.description = "Aider les donateurs."
        org.action_text = "Donner aux candidats"
        org.save()

        org.set_current_language("en")
        assert org.description == "Help donors direct political giving."
        org.set_current_language("fr")
        assert org.description == "Aider les donateurs."

    def test_tags_many_to_many(self, org: Organization) -> None:
        tag1 = Tag.objects.create(name="Advocacy")
        tag2 = Tag.objects.create(name="Bipartisan")
        org.tags.add(tag1, tag2)

        assert set(org.tags.all()) == {tag1, tag2}

    def test_location_point_field(self) -> None:
        org = Organization(
            name="Local Org",
            website_url="https://example.com/",
            category=Category.VOLUNTEER,
            location=Point(-77.0369, 38.9072),
        )
        org.set_current_language("en")
        org.description = "Test"
        org.action_text = "Test"
        org.save()

        org.refresh_from_db()
        assert org.location.x == pytest.approx(-77.0369)
        assert org.location.y == pytest.approx(38.9072)

    def test_location_is_optional(self, org: Organization) -> None:
        assert org.location is None

    def test_is_active_default_true(self, org: Organization) -> None:
        assert org.is_active is True

    def test_sort_order_default(self) -> None:
        org = Organization(
            name="Org",
            website_url="https://example.com/",
            category=Category.RESOURCE,
        )
        org.set_current_language("en")
        org.description = "Test"
        org.action_text = "Test"
        org.save()

        assert org.sort_order == 0

    def test_image_url_is_optional(self, org: Organization) -> None:
        assert org.image_url == ""
