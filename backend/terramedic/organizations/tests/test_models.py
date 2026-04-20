import pytest
from django.contrib.gis.geos import Point
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
            sort_order=1,
        )
        o.set_current_language("en")
        o.description = "A grassroots advocacy organization."
        o.save()
        o.categories.add(Category.objects.get(slug="donate"))
        return o

    def test_create_organization(self) -> None:
        org = Organization(
            name="Citizens' Climate Lobby",
            website_url="https://citizensclimatelobby.org/",
            sort_order=1,
        )
        org.set_current_language("en")
        org.description = "A grassroots advocacy organization."
        org.save()
        org.categories.add(Category.objects.get(slug="donate"))

        assert org.pk is not None
        assert org.name == "Citizens' Climate Lobby"
        assert org.description == "A grassroots advocacy organization."
        assert list(org.categories.values_list("slug", flat=True)) == ["donate"]

    def test_str_returns_name(self, org: Organization) -> None:
        assert str(org) == "Citizens' Climate Lobby"

    def test_translations(self) -> None:
        org = Organization(
            name="Give Green",
            website_url="https://givegreen.com/",
        )
        org.set_current_language("en")
        org.description = "Help donors direct political giving."
        org.set_current_language("fr")
        org.description = "Aider les donateurs."
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
            location=Point(-77.0369, 38.9072),
        )
        org.set_current_language("en")
        org.description = "Test"
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
        )
        org.set_current_language("en")
        org.description = "Test"
        org.save()

        assert org.sort_order == 0

    def test_image_url_is_optional(self, org: Organization) -> None:
        assert org.image_url == ""

    def test_created_at_auto_set(self, org: Organization) -> None:
        assert org.created_at is not None


@pytest.mark.django_db
class TestCategoryModel:
    """Category is now a model with slug as primary key, not a TextChoices enum.

    Migration 0006 seeds the five canonical categories, so every test
    database starts with them already present.
    """

    def test_five_seeded_categories_exist(self) -> None:
        slugs = set(Category.objects.values_list("slug", flat=True))
        assert slugs == {"donate", "volunteer", "resource", "everyday", "career"}

    def test_category_str_returns_label(self) -> None:
        donate = Category.objects.get(slug="donate")
        assert str(donate) == donate.label

    def test_slug_is_unique(self) -> None:
        with pytest.raises(IntegrityError):
            Category.objects.create(slug="donate", label="Duplicate")


@pytest.mark.django_db
class TestOrganizationCategoriesM2M:
    """An Organization can belong to multiple categories at once."""

    @pytest.fixture
    def org(self) -> Organization:
        o = Organization(
            name="Environmental Voter Project",
            website_url="https://environmentalvoter.org/",
        )
        o.set_current_language("en")
        o.description = "Gets environmentalists to vote."
        o.save()
        return o

    def test_organization_starts_with_no_categories(
        self, org: Organization,
    ) -> None:
        assert org.categories.count() == 0

    def test_assign_single_category(self, org: Organization) -> None:
        donate = Category.objects.get(slug="donate")
        org.categories.add(donate)

        assert list(org.categories.values_list("slug", flat=True)) == ["donate"]

    def test_assign_multiple_categories(self, org: Organization) -> None:
        donate = Category.objects.get(slug="donate")
        volunteer = Category.objects.get(slug="volunteer")
        org.categories.add(donate, volunteer)

        assert set(org.categories.values_list("slug", flat=True)) == {
            "donate",
            "volunteer",
        }

    def test_filter_organizations_by_category_slug(
        self, org: Organization,
    ) -> None:
        org.categories.add(Category.objects.get(slug="donate"))

        results = Organization.objects.filter(categories__slug="donate")
        assert org in results

    def test_filter_matches_org_with_any_assigned_category(
        self, org: Organization,
    ) -> None:
        """An org in both 'donate' and 'volunteer' should appear in both filters."""
        org.categories.add(
            Category.objects.get(slug="donate"),
            Category.objects.get(slug="volunteer"),
        )

        donate_results = Organization.objects.filter(categories__slug="donate")
        volunteer_results = Organization.objects.filter(
            categories__slug="volunteer",
        )
        assert org in donate_results
        assert org in volunteer_results

    def test_reverse_relation_from_category_to_organizations(
        self, org: Organization,
    ) -> None:
        donate = Category.objects.get(slug="donate")
        org.categories.add(donate)

        # django-stubs does not auto-generate reverse M2M accessors,
        # so it cannot see the `organizations` relation set up by
        # `related_name="organizations"` on Organization.categories.
        assert org in donate.organizations.all()  # type: ignore[attr-defined]
