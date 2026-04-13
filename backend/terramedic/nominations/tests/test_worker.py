"""Tests for the refactored worker Lambda handler (dispatch + results)."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)

_EVAL_RESULT: dict[str, Any] = {
    "org_metadata": {
        "name": "Test Org",
        "website_url": "https://example.org",
    },
    "evidence_score": {"score": 3},
    "curator_notes": {
        "recommendation": "include",
        "confidence": 80,
    },
    "evaluated_by": "claude-sonnet-4-20250514",
}

_WORKER_MODULE = "terramedic.nominations.worker"


def _make_queued_nomination(
    url: str = "https://example.org",
) -> Nomination:
    return Nomination.objects.create(
        url=url,
        categories=["volunteer"],
        ip_hash=None,
        status=NominationStatus.QUEUED,
    )


def _make_eventbridge_event(limit: int = 10) -> dict[str, Any]:
    """Simulate an EventBridge scheduled event (via Zappa command envelope)."""
    return {"limit": limit}


def _make_sqs_results_event(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Simulate an SQS event with evaluation results."""
    return {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "body": json.dumps(record),
            }
            for record in records
        ],
    }


# ── Routing ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestEventRouting:
    @patch(f"{_WORKER_MODULE}._handle_dispatch")
    def test_eventbridge_event_routes_to_dispatch(
        self, mock_dispatch: Any,
    ) -> None:
        from terramedic.nominations.worker import process_evaluation_queue

        mock_dispatch.return_value = {"status": "ok"}
        process_evaluation_queue({"limit": 10})
        mock_dispatch.assert_called_once()

    @patch(f"{_WORKER_MODULE}._handle_results")
    def test_sqs_event_routes_to_results(
        self, mock_results: Any,
    ) -> None:
        from terramedic.nominations.worker import process_evaluation_queue

        mock_results.return_value = {"status": "ok"}
        event = _make_sqs_results_event([{"nomination_id": 1}])
        process_evaluation_queue(event)
        mock_results.assert_called_once()

    @patch(f"{_WORKER_MODULE}._handle_dispatch")
    def test_empty_event_routes_to_dispatch(
        self, mock_dispatch: Any,
    ) -> None:
        from terramedic.nominations.worker import process_evaluation_queue

        mock_dispatch.return_value = {"status": "ok"}
        process_evaluation_queue(None)
        mock_dispatch.assert_called_once()


# ── Dispatch ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHandleDispatch:
    @patch(f"{_WORKER_MODULE}.boto3")
    def test_sends_sqs_message_for_queued_nomination(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        nom = _make_queued_nomination()
        _handle_dispatch(_make_eventbridge_event())

        mock_sqs.send_message.assert_called_once()
        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == "https://sqs.test/queue"
        body = json.loads(call_kwargs["MessageBody"])
        assert body["nomination_id"] == nom.pk
        assert body["url"] == "https://example.org"
        assert body["categories"] == ["volunteer"]
        assert body["evaluation_attempts"] == 1

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_claims_nomination_atomically(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_boto3.client.return_value = MagicMock()

        nom = _make_queued_nomination()
        _handle_dispatch(_make_eventbridge_event())

        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING
        assert nom.evaluation_attempts == 1

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_skips_nomination_with_active_eval(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"website_url": "https://example.org"},
            },
            status=ReviewStatus.PENDING,
        )
        nom = _make_queued_nomination(url="https://example.org")
        result = _handle_dispatch(_make_eventbridge_event())

        assert result["skipped"] == 1
        assert result["dispatched"] == 0
        mock_sqs.send_message.assert_not_called()
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING
        assert nom.evaluation_attempts == 0

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_respects_limit(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        _make_queued_nomination(url="https://first.org")
        _make_queued_nomination(url="https://second.org")
        result = _handle_dispatch({"limit": 1})

        assert result["dispatched"] == 1
        assert mock_sqs.send_message.call_count == 1

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_empty_queue_dispatches_nothing(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        result = _handle_dispatch(_make_eventbridge_event())

        assert result["dispatched"] == 0
        mock_sqs.send_message.assert_not_called()

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_dispatches_in_submission_order(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        _make_queued_nomination(url="https://first.org")
        _make_queued_nomination(url="https://second.org")
        _handle_dispatch(_make_eventbridge_event())

        calls = mock_sqs.send_message.call_args_list
        urls = [json.loads(c[1]["MessageBody"])["url"] for c in calls]
        assert urls == ["https://first.org", "https://second.org"]

    @patch(f"{_WORKER_MODULE}.boto3")
    def test_sqs_send_failure_reverts_nomination(
        self, mock_boto3: Any, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.setenv("EVALUATION_REQUESTS_QUEUE_URL", "https://sqs.test/queue")
        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = Exception("SQS throttle")
        mock_boto3.client.return_value = mock_sqs

        nom = _make_queued_nomination()
        result = _handle_dispatch(_make_eventbridge_event())

        assert result["dispatched"] == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED
        assert nom.evaluation_attempts == 0


# ── Results ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHandleResults:
    def test_creates_evaluation_on_success(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = _make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.save(update_fields=["status"])

        event = _make_sqs_results_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": _EVAL_RESULT,
        }])
        result = _handle_results(event)

        assert result["processed"] == 1
        assert OrganizationEvaluation.objects.count() == 1
        ev = OrganizationEvaluation.objects.first()
        assert ev is not None
        assert ev.nomination == nom
        assert ev.ai_model == "claude-sonnet-4-20250514"
        assert ev.ai_recommendation == "include"
        assert ev.ai_confidence == 80

    def test_sets_nomination_evaluated_on_success(self) -> None:
        """Django signal should update nomination status to EVALUATED."""
        from terramedic.nominations.worker import _handle_results

        nom = _make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.save(update_fields=["status"])

        event = _make_sqs_results_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": _EVAL_RESULT,
        }])
        _handle_results(event)

        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATED

    def test_reverts_to_queued_on_first_failure(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = _make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = _make_sqs_results_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": False,
            "error": "evaluate_org failed",
        }])
        result = _handle_results(event)

        assert result["failed"] == 1
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED

    def test_sets_failed_on_second_failure(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = _make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 2
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = _make_sqs_results_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 2,
            "success": False,
            "error": "evaluate_org failed",
        }])
        result = _handle_results(event)

        assert result["failed"] == 1
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_handles_missing_nomination(self) -> None:
        from terramedic.nominations.worker import _handle_results

        event = _make_sqs_results_event([{
            "nomination_id": 99999,
            "evaluation_attempts": 1,
            "success": True,
            "data": _EVAL_RESULT,
        }])
        # Should not raise
        result = _handle_results(event)
        assert result["processed"] == 0
        assert OrganizationEvaluation.objects.count() == 0

    def test_processes_multiple_results(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom1 = _make_queued_nomination(url="https://one.org")
        nom1.status = NominationStatus.EVALUATING
        nom1.save(update_fields=["status"])

        nom2 = _make_queued_nomination(url="https://two.org")
        nom2.status = NominationStatus.EVALUATING
        nom2.save(update_fields=["status"])

        result2 = dict(_EVAL_RESULT)
        result2["org_metadata"] = {
            "name": "Org Two",
            "website_url": "https://two.org",
        }

        event = _make_sqs_results_event([
            {
                "nomination_id": nom1.pk,
                "evaluation_attempts": 1,
                "success": True,
                "data": _EVAL_RESULT,
            },
            {
                "nomination_id": nom2.pk,
                "evaluation_attempts": 1,
                "success": True,
                "data": result2,
            },
        ])
        result = _handle_results(event)

        assert result["processed"] == 2
        assert OrganizationEvaluation.objects.count() == 2

    def test_failure_creates_no_evaluation(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = _make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.save(update_fields=["status"])

        event = _make_sqs_results_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": False,
            "error": "evaluate_org failed",
        }])
        _handle_results(event)

        assert OrganizationEvaluation.objects.count() == 0
