import uuid

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from terramedic.nominations.models import Nomination, NominationStatus


@pytest.mark.django_db
class TestNominationStatus:
    def test_status_choices(self) -> None:
        assert NominationStatus.PENDING == "pending"
        assert NominationStatus.EVALUATED == "evaluated"
        assert NominationStatus.APPROVED == "approved"
        assert NominationStatus.REJECTED == "rejected"


@pytest.mark.django_db
class TestNomination:
    @pytest.fixture
    def nomination(self) -> Nomination:
        return Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer", "donate"],
            notes="Great organization for reef conservation.",
            ip_hash="abc123hash",
        )

    def test_create_nomination(self, nomination: Nomination) -> None:
        assert nomination.pk is not None
        assert nomination.url == "https://example.org/"
        assert nomination.categories == ["volunteer", "donate"]
        assert nomination.notes == "Great organization for reef conservation."
        assert nomination.ip_hash == "abc123hash"

    def test_default_status_is_pending(self, nomination: Nomination) -> None:
        assert nomination.status == NominationStatus.PENDING

    def test_submitted_at_auto_set(self, nomination: Nomination) -> None:
        assert nomination.submitted_at is not None
        # Should be recent (within last 10 seconds)
        delta = timezone.now() - nomination.submitted_at
        assert delta.total_seconds() < 10

    def test_confirmation_id_is_uuid(self, nomination: Nomination) -> None:
        assert isinstance(nomination.confirmation_id, uuid.UUID)

    def test_confirmation_id_is_unique(self) -> None:
        n1 = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer"],
            ip_hash="hash1",
        )
        n2 = Nomination.objects.create(
            url="https://example2.org/",
            categories=["donate"],
            ip_hash="hash2",
        )
        assert n1.confirmation_id != n2.confirmation_id

    def test_notes_is_optional(self) -> None:
        nom = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer"],
            ip_hash="abc123hash",
        )
        assert nom.notes == ""

    def test_str_representation(self, nomination: Nomination) -> None:
        expected = f"https://example.org/ ({nomination.status})"
        assert str(nomination) == expected

    def test_invalid_status_fails_validation(self, nomination: Nomination) -> None:
        nomination.status = "invalid_status"
        with pytest.raises(ValidationError):
            nomination.full_clean()

    def test_ordering_is_newest_first(self) -> None:
        n1 = Nomination.objects.create(
            url="https://first.org/",
            categories=["volunteer"],
            ip_hash="hash1",
        )
        n2 = Nomination.objects.create(
            url="https://second.org/",
            categories=["donate"],
            ip_hash="hash2",
        )
        noms = list(Nomination.objects.all())
        assert noms[0] == n2
        assert noms[1] == n1

    def test_categories_is_json_list(self) -> None:
        nom = Nomination.objects.create(
            url="https://example.org/",
            categories=["volunteer", "career", "donate"],
            ip_hash="hash1",
        )
        nom.refresh_from_db()
        assert nom.categories == ["volunteer", "career", "donate"]
