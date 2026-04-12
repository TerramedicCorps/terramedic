import datetime
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import (
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
)

CHANGELIST_URL = "/admin/nominations/nomination/"


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="testpass123",
    )


@pytest.fixture
def admin_client(admin_user: User) -> Client:
    client = Client()
    client.force_login(admin_user)
    return client


def _make_nomination(
    url: str = "https://example.org",
    status: str = NominationStatus.PENDING,
) -> Nomination:
    return Nomination.objects.create(
        url=url,
        categories=["volunteer"],
        ip_hash=None,
        status=status,
    )


def _post_action(
    admin_client: Client,
    nomination_ids: list[int],
) -> Any:
    return admin_client.post(
        CHANGELIST_URL,
        {
            "action": "evaluate_nominations",
            "_selected_action": nomination_ids,
        },
        follow=True,
    )


@pytest.mark.django_db
class TestEvaluateActionQueues:
    def test_pending_nomination_gets_queued(
        self, admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED

    def test_attempts_reset_to_zero(
        self, admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        nom.evaluation_attempts = 1
        nom.save(update_fields=["evaluation_attempts"])
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.evaluation_attempts == 0

    def test_queued_count_in_message(
        self, admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        response = _post_action(admin_client, [nom.pk])
        content = response.content.decode()
        assert "1" in content
        assert "queued" in content.lower()


@pytest.mark.django_db
class TestEvaluateActionSkipsNonPending:
    @pytest.mark.parametrize("status", [
        NominationStatus.QUEUED,
        NominationStatus.EVALUATING,
        NominationStatus.EVALUATED,
        NominationStatus.APPROVED,
        NominationStatus.REJECTED,
        NominationStatus.FAILED,
    ])
    def test_skips_non_pending(
        self,
        admin_client: Client,
        status: str,
    ) -> None:
        nom = _make_nomination(status=status)
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == status


@pytest.mark.django_db
class TestEvaluateActionSkipsActiveEvaluation:
    def test_skips_url_with_pending_evaluation(
        self, admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.PENDING,
        )
        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING

    def test_skips_url_with_approved_evaluation(
        self, admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.APPROVED,
        )
        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING

    def test_allows_url_with_only_rejected_evaluation_past_cooldown(
        self, admin_client: Client,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.REJECTED,
        )
        OrganizationEvaluation.objects.filter(pk=ev.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=91),
        )
        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED


@pytest.mark.django_db
class TestEvaluateActionSkipsExistingOrg:
    def test_skips_url_matching_existing_org(
        self, admin_client: Client,
    ) -> None:
        org = Organization(
            name="Example Org",
            website_url="https://example.org",
        )
        org.set_current_language("en")
        org.description = "An org."
        org.action_text = "Support"
        org.save()

        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING


@pytest.mark.django_db
class TestEvaluateActionCooldown:
    def test_skips_recently_rejected_url(
        self, admin_client: Client,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.REJECTED,
        )
        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING

    def test_allows_old_rejected_url(
        self, admin_client: Client,
    ) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.REJECTED,
        )
        OrganizationEvaluation.objects.filter(pk=ev.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=91),
        )
        nom = _make_nomination(url="https://example.org")
        _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED


@pytest.mark.django_db
class TestEvaluateActionMessages:
    def test_skip_reasons_reported(
        self, admin_client: Client,
    ) -> None:
        pending = _make_nomination(url="https://new.org")
        already_eval = _make_nomination(url="https://evaluated.org")
        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://evaluated.org"},
            },
            status=ReviewStatus.PENDING,
        )
        response = _post_action(
            admin_client, [pending.pk, already_eval.pk],
        )
        content = response.content.decode()
        assert "1" in content  # 1 queued
        assert "skip" in content.lower()

    def test_mixed_pending_and_non_pending(
        self, admin_client: Client,
    ) -> None:
        pending = _make_nomination(url="https://new.org")
        approved = _make_nomination(
            url="https://approved.org",
            status=NominationStatus.APPROVED,
        )
        _post_action(admin_client, [pending.pk, approved.pk])
        pending.refresh_from_db()
        approved.refresh_from_db()
        assert pending.status == NominationStatus.QUEUED
        assert approved.status == NominationStatus.APPROVED


@pytest.mark.django_db
class TestEvaluateActionScheduledProcessing:
    def test_success_message_mentions_processing(
        self, admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        response = _post_action(admin_client, [nom.pk])
        content = response.content.decode()
        assert "within a few minutes" in content.lower()
