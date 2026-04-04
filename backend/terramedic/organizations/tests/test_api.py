import pytest
from django.contrib.gis.geos import Point
from django.test import Client

from terramedic.organizations.models import Category, Organization, Tag


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
        category=Category.DONATE,
        sort_order=1,
        location=Point(-77.0369, 38.9072),
    )
    org.set_current_language("en")
    org.description = "A grassroots advocacy organization."
    org.action_text = "Support Climate Advocacy"
    org.set_current_language("fr")
    org.description = "Une organisation de plaidoyer."
    org.action_text = "Soutenir le plaidoyer"
    org.save()
    org.tags.add(*tags)
    return org


@pytest.fixture
def org_evp() -> Organization:
    org = Organization(
        name="Environmental Voter Project",
        website_url="https://www.environmentalvoter.org/",
        category=Category.VOLUNTEER,
        sort_order=0,
    )
    org.set_current_language("en")
    org.description = "Turning environmentalists into voters."
    org.action_text = "Become a Volunteer"
    org.save()
    return org


@pytest.fixture
def inactive_org() -> Organization:
    org = Organization(
        name="Inactive Org",
        website_url="https://example.com/",
        category=Category.DONATE,
        is_active=False,
    )
    org.set_current_language("en")
    org.description = "This org is inactive."
    org.action_text = "N/A"
    org.save()
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

    def test_includes_category(
        self,
        client: Client,
        org_ccl: Organization,
    ) -> None:
        response = client.get("/api/organizations/")
        data = response.json()
        org = data[0]
        assert org["category"] == "donate"

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
        assert org["action_text"] == "Support Climate Advocacy"


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
        assert org["action_text"] == "Soutenir le plaidoyer"

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
