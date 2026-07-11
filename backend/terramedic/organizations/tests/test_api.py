import pytest
from django.contrib.gis.geos import Point
from django.test import Client

from terramedic.organizations.models import (
    Category,
    Organization,
    OrganizationCategory,
    Tag,
)


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def tags() -> list[Tag]:
    return [
        Tag.objects.create(name="Advocacy"),
        Tag.objects.create(name="Bipartisan"),
    ]


@pytest.fixture
def org_ccl(tags: list[Tag]) -> Organization:
    org = Organization(
        name="Citizens' Climate Lobby",
        website_url="https://citizensclimatelobby.org/",
        sort_order=1,
        location=Point(-77.0369, 38.9072),
    )
    org.set_current_language("en")
    org.description = "A grassroots advocacy organization."
    org.set_current_language("fr")
    org.description = "Une organisation de plaidoyer."
    org.save()
    org.tags.add(*tags)
    org.categories.add(Category.objects.get(slug="donate"))
    return org


@pytest.fixture
def org_evp() -> Organization:
    org = Organization(
        name="Environmental Voter Project",
        website_url="https://www.environmentalvoter.org/",
        sort_order=0,
    )
    org.set_current_language("en")
    org.description = "Turning environmentalists into voters."
    org.save()
    org.categories.add(Category.objects.get(slug="volunteer"))
    return org


@pytest.fixture
def inactive_org() -> Organization:
    org = Organization(
        name="Inactive Org",
        website_url="https://example.com/",
        is_active=False,
    )
    org.set_current_language("en")
    org.description = "This org is inactive."
    org.save()
    org.categories.add(Category.objects.get(slug="donate"))
    return org


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check(self, client: Client) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.django_db
class TestListOrganizations:
    def test_list_all(
        self,
        client: Client,
        org_ccl: Organization,
        org_evp: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_by_category(
        self,
        client: Client,
        org_ccl: Organization,
        org_evp: Organization,
    ) -> None:
        response = client.get("/api/organizations/?category=donate")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Citizens' Climate Lobby"

    def test_excludes_inactive(
        self,
        client: Client,
        org_ccl: Organization,
        inactive_org: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        assert response.status_code == 200
        data = response.json()
        names = [org["name"] for org in data]
        assert "Inactive Org" not in names

    def test_includes_tags(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert set(org["tags"]) == {"Advocacy", "Bipartisan"}

    def test_includes_categories(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert org["categories"] == ["donate"]

    def test_org_with_multiple_categories_returns_all_slugs(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        org_ccl.categories.add(Category.objects.get(slug="volunteer"))

        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert set(org["categories"]) == {"donate", "volunteer"}

    def test_filter_by_category_matches_org_with_multiple(
        self,
        client: Client,
        org_ccl: Organization,
        org_evp: Organization,
    ) -> None:
        """An org with ['donate', 'volunteer'] should appear in both filters."""
        org_ccl.categories.add(Category.objects.get(slug="volunteer"))

        donate_response = client.get("/api/organizations/?category=donate")
        volunteer_response = client.get("/api/organizations/?category=volunteer")

        donate_names = {o["name"] for o in donate_response.json()}
        volunteer_names = {o["name"] for o in volunteer_response.json()}
        assert "Citizens' Climate Lobby" in donate_names
        assert "Citizens' Climate Lobby" in volunteer_names
        assert "Environmental Voter Project" in volunteer_names

    def test_listing_does_not_emit_n_plus_one_tag_queries(
        self,
        client: Client,
        tags: list[Tag],
    ) -> None:
        """The listing prefetches ``tags``, but ``_serialize_org`` used
        to call ``org.tags.order_by(...)`` which bypasses the
        prefetch cache and re-queries per row. With SSR rendering
        listings on every request, that's O(N) DB chatter per page
        load. Assert the per-org tag query count is constant."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        # Build several orgs each with multiple tags so a regression
        # would inflate the query count noticeably.
        for i in range(5):
            org = Organization(
                name=f"Org {i}",
                website_url=f"https://example{i}.org/",
                sort_order=i,
            )
            org.set_current_language("en")
            org.description = f"Org {i} description."
            org.save()
            org.tags.add(*tags)
            org.categories.add(Category.objects.get(slug="donate"))

        with CaptureQueriesContext(connection) as ctx:
            response = client.get("/api/organizations/")
        assert response.status_code == 200
        assert len(response.json()) == 5

        tag_queries = [
            q for q in ctx.captured_queries
            if "organizations_tag" in q["sql"].lower()
        ]
        # Pre-fix: 1 prefetch + 5 per-row order_by queries = 6.
        # Post-fix: 1 prefetch only.
        assert len(tag_queries) <= 2, (
            f"Expected ≤2 tag queries, got {len(tag_queries)}:\n"
            + "\n".join(q["sql"] for q in tag_queries)
        )

    def test_response_fields(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert org["name"] == "Citizens' Climate Lobby"
        assert org["website_url"] == "https://citizensclimatelobby.org/"
        assert org["description"] == "A grassroots advocacy organization."


@pytest.mark.django_db
class TestOrganizationDetail:
    def test_get_by_id(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get(f"/api/organizations/{org_ccl.pk}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Citizens' Climate Lobby"

    def test_not_found(self, client: Client) -> None:
        response = client.get("/api/organizations/9999/")
        assert response.status_code == 404

    def test_inactive_not_found(
        self,
        client: Client,
        inactive_org: Organization,
    ) -> None:
        response = client.get(f"/api/organizations/{inactive_org.pk}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestNearbyOrganizations:
    def test_nearby_returns_orgs_within_radius(
        self,
        client: Client,
        org_ccl: Organization,
        org_evp: Organization,
    ) -> None:
        # CCL has location at DC (38.9, -77.0), EVP has no location
        response = client.get(
            "/api/organizations/nearby/?lat=38.9&lng=-77.0&radius=50",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Citizens' Climate Lobby"

    def test_nearby_excludes_distant_orgs(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        # Search far from DC
        response = client.get(
            "/api/organizations/nearby/?lat=34.0&lng=-118.2&radius=10",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_nearby_excludes_inactive(
        self,
        client: Client,
        inactive_org: Organization,
    ) -> None:
        # radius=500 is the API max (500km); large enough to cover
        # the DC-area fixture orgs while staying within validation limits
        response = client.get(
            "/api/organizations/nearby/?lat=38.9&lng=-77.0&radius=500",
        )
        assert response.status_code == 200
        data = response.json()
        names = [org["name"] for org in data]
        assert "Inactive Org" not in names

    def test_nearby_requires_params(self, client: Client) -> None:
        response = client.get("/api/organizations/nearby/")
        assert response.status_code == 422


@pytest.mark.django_db
class TestPerCategoryDescriptionAndActionText:
    """When the API is filtered by ``?category=<slug>``, each card's
    description and action_text come from the matching
    OrganizationCategory row. Unfiltered / nearby responses use the
    org's general description and leave action_text empty."""

    @pytest.fixture
    def two_pathway_org(self) -> Organization:
        org = Organization(
            name="Citizens' Climate Lobby",
            website_url="https://citizensclimatelobby.org/",
        )
        org.set_current_language("en")
        org.description = "General advocacy description."
        org.save()

        donate_entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        donate_entry.set_current_language("en")
        donate_entry.description = "Fund climate lobbying at scale."
        donate_entry.action_text = "Donate to CCL"
        donate_entry.save()

        volunteer_entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="volunteer"),
        )
        volunteer_entry.set_current_language("en")
        volunteer_entry.description = "Join a local lobby day."
        volunteer_entry.action_text = "Find a chapter"
        volunteer_entry.action_url = "https://citizensclimatelobby.org/chapters/"
        volunteer_entry.save()
        # donate_entry.action_url intentionally left blank to exercise the
        # website_url fallback.

        return org

    def test_category_filter_returns_per_category_description(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        response = client.get("/api/organizations/?category=donate")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Fund climate lobbying at scale."
        assert data[0]["action_text"] == "Donate to CCL"

    def test_category_filter_returns_per_category_action_url(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """A populated action_url on the matching row surfaces in the
        response so the CTA card deep-links to the pathway-specific
        page."""
        response = client.get("/api/organizations/?category=volunteer")
        data = response.json()
        assert (
            data[0]["action_url"]
            == "https://citizensclimatelobby.org/chapters/"
        )

    def test_action_url_falls_back_to_website_url_when_blank(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """A blank per-category action_url falls back to the org's
        website_url so the card always has somewhere to send the reader.
        For the donate slug this fallback is also the 501(c)(3)-compliant
        homepage."""
        response = client.get("/api/organizations/?category=donate")
        data = response.json()
        assert data[0]["action_url"] == "https://citizensclimatelobby.org/"
        assert data[0]["action_url"] == two_pathway_org.website_url

    def test_unsafe_stored_action_url_falls_back_to_website_url(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """The API must not expose a script URL even if save bypassed clean."""
        entry = OrganizationCategory.objects.get(
            organization=two_pathway_org,
            category_id="volunteer",
        )
        entry.set_current_language("en")
        entry.action_url = "javascript:alert(document.domain)"
        entry.save()  # Deliberately bypass full_clean to test read defense.

        response = client.get("/api/organizations/?category=volunteer")

        assert response.json()[0]["action_url"] == two_pathway_org.website_url

    def test_cross_site_stored_action_url_falls_back_to_website_url(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """Read defense blocks links that bypassed model ``full_clean``."""
        entry = OrganizationCategory.objects.get(
            organization=two_pathway_org,
            category_id="volunteer",
        )
        entry.set_current_language("en")
        entry.action_url = "https://evil.example/phish"
        entry.save()

        response = client.get("/api/organizations/?category=volunteer")

        assert response.json()[0]["action_url"] == two_pathway_org.website_url

    def test_same_site_deep_donate_link_falls_back_to_homepage(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """501(c)(3) read defense: a same-site *deep* donate link that
        bypassed model ``clean`` (raw ``save``, migration, future write
        path) must not surface as the donate CTA. ``is_same_site_web_url``
        ignores the path, so only slug-aware override catches this — the
        homepage is the sole compliant donate target."""
        entry = OrganizationCategory.objects.get(
            organization=two_pathway_org,
            category_id="donate",
        )
        entry.set_current_language("en")
        entry.action_url = "https://citizensclimatelobby.org/donate/give-now"
        entry.save()  # Deliberately bypass full_clean to test read defense.

        response = client.get("/api/organizations/?category=donate")

        assert response.json()[0]["action_url"] == two_pathway_org.website_url

    def test_unfiltered_list_returns_empty_action_url(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        """Without a category filter there is no pathway context, so
        action_url stays empty even when a through row has one."""
        response = client.get("/api/organizations/")
        data = response.json()
        assert data[0]["action_url"] == ""

    def test_same_org_returns_different_copy_under_different_pathways(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        donate = client.get("/api/organizations/?category=donate").json()
        volunteer = client.get(
            "/api/organizations/?category=volunteer",
        ).json()

        assert donate[0]["description"] != volunteer[0]["description"]
        assert donate[0]["action_text"] != volunteer[0]["action_text"]
        assert donate[0]["description"] == "Fund climate lobbying at scale."
        assert volunteer[0]["description"] == "Join a local lobby day."

    def test_unfiltered_list_returns_general_description_and_empty_action(
        self, client: Client, two_pathway_org: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        assert data[0]["description"] == "General advocacy description."
        assert data[0]["action_text"] == ""

    def test_nearby_returns_general_description_and_empty_action(
        self, client: Client,
    ) -> None:
        from django.contrib.gis.geos import Point as GeoPoint

        org = Organization(
            name="DC Org",
            website_url="https://dc.example.org/",
            location=GeoPoint(-77.0369, 38.9072),
        )
        org.set_current_language("en")
        org.description = "DC-area environmental group."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        entry.set_current_language("en")
        entry.description = "Specific donate pitch."
        entry.action_text = "Give $50"
        entry.save()

        response = client.get(
            "/api/organizations/nearby/?lat=38.9&lng=-77.0&radius=50",
        )
        data = response.json()
        assert data[0]["description"] == "DC-area environmental group."
        assert data[0]["action_text"] == ""

    def test_action_text_falls_back_to_category_default_when_blank(
        self, client: Client,
    ) -> None:
        """A through row with empty action_text should surface the
        Category.default_action_text (seeded by migration 0022)."""
        org = Organization(
            name="Blank-CTA Org",
            website_url="https://example.org/",
        )
        org.set_current_language("en")
        org.description = "General."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        entry.set_current_language("en")
        entry.description = "Donate-specific pitch."
        # action_text intentionally left blank.
        entry.save()

        response = client.get("/api/organizations/?category=donate")
        data = response.json()
        assert data[0]["action_text"] == "Learn more"

    def test_description_falls_back_to_general_when_per_cat_blank(
        self, client: Client,
    ) -> None:
        org = Organization(
            name="Blank-desc Org",
            website_url="https://example.org/",
        )
        org.set_current_language("en")
        org.description = "General description for fallback."
        org.save()
        OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        # No translation row written — per-category description is
        # absent, so the response should fall back to the general one.

        response = client.get("/api/organizations/?category=donate")
        data = response.json()
        assert data[0]["description"] == "General description for fallback."

    def test_per_category_copy_honors_accept_language(
        self, client: Client,
    ) -> None:
        """Per-category description/action_text should honor the
        Accept-Language header when a translation for that language
        exists on the through row."""
        org = Organization(
            name="Bilingual Org",
            website_url="https://example.org/",
        )
        org.set_current_language("en")
        org.description = "General."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        entry.set_current_language("en")
        entry.description = "Fund our work."
        entry.action_text = "Donate"
        entry.set_current_language("fr")
        entry.description = "Financez notre travail."
        entry.action_text = "Faire un don"
        entry.save()

        response = client.get(
            "/api/organizations/?category=donate",
            headers={"Accept-Language": "fr"},
        )
        data = response.json()
        assert data[0]["description"] == "Financez notre travail."
        assert data[0]["action_text"] == "Faire un don"

    def test_blank_localized_action_url_falls_back_to_english(
        self, client: Client,
    ) -> None:
        """A translated label must not discard the default-language URL."""
        org = Organization(
            name="Bilingual Volunteer Org",
            website_url="https://example.org/",
        )
        org.set_current_language("en")
        org.description = "General."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="volunteer"),
        )
        entry.set_current_language("en")
        entry.description = "Join the team."
        entry.action_text = "Sign up"
        entry.action_url = "https://example.org/volunteer/signup"
        entry.set_current_language("fr")
        entry.description = "Rejoignez l'équipe."
        entry.action_text = "S'inscrire"
        entry.action_url = ""
        entry.save()

        response = client.get(
            "/api/organizations/?category=volunteer",
            headers={"Accept-Language": "fr"},
        )

        assert (
            response.json()[0]["action_url"]
            == "https://example.org/volunteer/signup"
        )

    def test_per_category_copy_falls_back_to_english_for_missing_lang(
        self, client: Client,
    ) -> None:
        """When the through row has no translation for the requested
        language, the per-category copy falls back to English rather
        than returning blank — matches the behavior of the general
        org description (see TestTranslationViaAcceptLanguage)."""
        org = Organization(
            name="EN-only Org",
            website_url="https://example.org/",
        )
        org.set_current_language("en")
        org.description = "General."
        org.save()
        entry = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        entry.set_current_language("en")
        entry.description = "Fund our work."
        entry.action_text = "Donate"
        entry.save()

        response = client.get(
            "/api/organizations/?category=donate",
            headers={"Accept-Language": "ja"},
        )
        data = response.json()
        assert data[0]["description"] == "Fund our work."
        assert data[0]["action_text"] == "Donate"


@pytest.mark.django_db
class TestTranslationViaAcceptLanguage:
    def test_french_translation(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get(
            "/api/organizations/",
            headers={"Accept-Language": "fr"},
        )
        data = response.json()
        org = data[0]
        assert org["description"] == "Une organisation de plaidoyer."

    def test_english_default(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert org["description"] == "A grassroots advocacy organization."

    def test_fallback_to_english(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        # Request Japanese - should fall back to English
        response = client.get(
            "/api/organizations/",
            headers={"Accept-Language": "ja"},
        )
        data = response.json()
        org = data[0]
        assert org["description"] == "A grassroots advocacy organization."
