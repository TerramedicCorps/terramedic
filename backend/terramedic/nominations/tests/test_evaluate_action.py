from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client

from terramedic.nominations.models import Nomination, NominationStatus

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
class TestEvaluateActionMessages:
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


_INVOKE_PATH = "terramedic.nominations.admin.invoke_worker_lambda"


@pytest.mark.django_db
class TestEvaluateActionWorkerInvocation:
    @patch(_INVOKE_PATH)
    def test_invokes_worker_after_queuing(
        self,
        mock_invoke: MagicMock,
        admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        _post_action(admin_client, [nom.pk])
        mock_invoke.assert_called_once()

    @patch(_INVOKE_PATH)
    def test_does_not_invoke_worker_when_nothing_queued(
        self,
        mock_invoke: MagicMock,
        admin_client: Client,
    ) -> None:
        nom = _make_nomination(status=NominationStatus.APPROVED)
        _post_action(admin_client, [nom.pk])
        mock_invoke.assert_not_called()

    @patch(_INVOKE_PATH, side_effect=Exception("boto3 error"))
    def test_graceful_fallback_on_invoke_failure(
        self,
        mock_invoke: MagicMock,
        admin_client: Client,
    ) -> None:
        nom = _make_nomination()
        response = _post_action(admin_client, [nom.pk])
        nom.refresh_from_db()
        # Nomination should still be queued even if invoke fails
        assert nom.status == NominationStatus.QUEUED
        # Should show a warning message
        content = response.content.decode()
        assert "manually" in content.lower() or "process_evaluations" in content
