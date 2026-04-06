import uuid

import pytest
from django.test import Client

from terramedic.nominations.models import Nomination


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.mark.django_db
class TestCreateNomination:
    def test_create_valid_nomination(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["volunteer", "donate"],
                "notes": "Great org for reef conservation.",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert "confirmation_id" in data
        # Should be a valid UUID
        uuid.UUID(data["confirmation_id"])

    def test_nomination_saved_to_db(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        nom = Nomination.objects.get(confirmation_id=data["confirmation_id"])
        assert nom.url == "https://example.org/"
        assert nom.categories == ["volunteer"]

    def test_ip_hash_is_stored(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        nom = Nomination.objects.get(confirmation_id=data["confirmation_id"])
        assert nom.ip_hash != ""
        # Should be a hash, not a raw IP
        assert "." not in nom.ip_hash
        assert ":" not in nom.ip_hash

    def test_notes_optional(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_invalid_url_rejected(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "not-a-url",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_empty_url_rejected(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_invalid_category_rejected(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["invalid_category"],
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_empty_categories_rejected(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": [],
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_honeypot_rejects_bots(self, client: Client) -> None:
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example.org/",
                "categories": ["volunteer"],
                "website": "I am a bot filling hidden fields",
            },
            content_type="application/json",
        )
        # Honeypot should silently reject: return 201 with a fake
        # confirmation_id so bots don't know they were caught
        assert response.status_code == 201
        data = response.json()
        assert "confirmation_id" in data
        # But nothing should be saved
        assert Nomination.objects.count() == 0

    def test_rate_limit_5_per_hour(self, client: Client) -> None:
        for i in range(5):
            response = client.post(
                "/api/nominations/",
                data={
                    "url": f"https://example{i}.org/",
                    "categories": ["volunteer"],
                },
                content_type="application/json",
            )
            assert response.status_code == 201

        # 6th request should be rate limited
        response = client.post(
            "/api/nominations/",
            data={
                "url": "https://example99.org/",
                "categories": ["volunteer"],
            },
            content_type="application/json",
        )
        assert response.status_code == 429

    def test_valid_categories_accepted(self, client: Client) -> None:
        for cat in ["donate", "volunteer", "resource", "everyday", "career"]:
            response = client.post(
                "/api/nominations/",
                data={
                    "url": f"https://example-{cat}.org/",
                    "categories": [cat],
                },
                content_type="application/json",
            )
            assert response.status_code == 201, f"Category '{cat}' should be valid"


@pytest.mark.django_db
class TestNominationStatus:
    def test_get_status_by_confirmation_id(self, client: Client) -> None:
        # Create a nomination first
        nom = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer"],
            ip_hash="testhash",
        )
        response = client.get(
            f"/api/nominations/{nom.confirmation_id}/status/",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["confirmation_id"] == str(nom.confirmation_id)
        assert data["status"] == "pending"

    def test_status_not_found(self, client: Client) -> None:
        fake_id = uuid.uuid4()
        response = client.get(f"/api/nominations/{fake_id}/status/")
        assert response.status_code == 404

    def test_status_does_not_expose_ip_hash(self, client: Client) -> None:
        nom = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer"],
            ip_hash="testhash",
        )
        response = client.get(
            f"/api/nominations/{nom.confirmation_id}/status/",
        )
        data = response.json()
        assert "ip_hash" not in data

    def test_status_does_not_expose_url(self, client: Client) -> None:
        nom = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer"],
            ip_hash="testhash",
        )
        response = client.get(
            f"/api/nominations/{nom.confirmation_id}/status/",
        )
        data = response.json()
        # Public status endpoint should only show status and confirmation_id
        assert "url" not in data
