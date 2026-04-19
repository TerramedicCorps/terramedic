"""Tests for the refactored worker Lambda handler (dispatch + results)."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from terramedic.nominations.models import NominationStatus
from terramedic.nominations.tests.conftest import (
    EVAL_RESULT,
    make_queued_nomination,
    make_sqs_event,
)
from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)

_WORKER_MODULE = "terramedic.nominations.worker"


def _make_eventbridge_event(limit: int = 10) -> dict[str, Any]:
    """Simulate an EventBridge scheduled event (via Zappa command envelope)."""
    return {"limit": limit}


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
        event = make_sqs_event([{"nomination_id": 1}])
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

        nom = make_queued_nomination()
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

        nom = make_queued_nomination()
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
        nom = make_queued_nomination(url="https://example.org")
        result = _handle_dispatch(_make_eventbridge_event())

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

        make_queued_nomination(url="https://first.org")
        make_queued_nomination(url="https://second.org")
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

        make_queued_nomination(url="https://first.org")
        make_queued_nomination(url="https://second.org")
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

        nom = make_queued_nomination()
        result = _handle_dispatch(_make_eventbridge_event())

        assert result["dispatched"] == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED
        assert nom.evaluation_attempts == 0

    def test_raises_when_queue_url_missing(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.worker import _handle_dispatch

        monkeypatch.delenv("EVALUATION_REQUESTS_QUEUE_URL", raising=False)

        with pytest.raises(
            RuntimeError, match="EVALUATION_REQUESTS_QUEUE_URL is not set",
        ):
            _handle_dispatch(_make_eventbridge_event())


# ── Results ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHandleResults:
    def test_creates_evaluation_on_success(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
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
        """Worker explicitly sets nomination status to EVALUATED."""
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
        }])
        _handle_results(event)

        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATED

    def test_reverts_to_queued_on_first_failure(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
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

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 2
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
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

        event = make_sqs_event([{
            "nomination_id": 99999,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
        }])
        # Should not raise
        result = _handle_results(event)
        assert result["processed"] == 0
        assert OrganizationEvaluation.objects.count() == 0

    def test_processes_multiple_results(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom1 = make_queued_nomination(url="https://one.org")
        nom1.status = NominationStatus.EVALUATING
        nom1.evaluation_attempts = 1
        nom1.save(update_fields=["status", "evaluation_attempts"])

        nom2 = make_queued_nomination(url="https://two.org")
        nom2.status = NominationStatus.EVALUATING
        nom2.evaluation_attempts = 1
        nom2.save(update_fields=["status", "evaluation_attempts"])

        result2 = dict(EVAL_RESULT)
        result2["org_metadata"] = {
            "name": "Org Two",
            "website_url": "https://two.org",
        }

        event = make_sqs_event([
            {
                "nomination_id": nom1.pk,
                "evaluation_attempts": 1,
                "success": True,
                "data": EVAL_RESULT,
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

    def test_duplicate_result_is_idempotent(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        record = {
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
        }
        # Process the same result twice (SQS at-least-once delivery)
        _handle_results(make_sqs_event([record]))
        result = _handle_results(make_sqs_event([record]))

        assert result["processed"] == 0  # second delivery is a no-op
        assert OrganizationEvaluation.objects.count() == 1

    def test_failure_creates_no_evaluation(self) -> None:
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": False,
            "error": "evaluate_org failed",
        }])
        _handle_results(event)

        assert OrganizationEvaluation.objects.count() == 0

    def test_late_success_does_not_resurrect_swept_nomination(self) -> None:
        """If sweep_stuck_claims has already marked a nomination
        FAILED, a late success result must not create an evaluation
        or flip the status back to EVALUATED."""
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.FAILED  # swept earlier
        nom.save(update_fields=["status"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
        }])
        result = _handle_results(event)

        assert result["processed"] == 0
        assert OrganizationEvaluation.objects.count() == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_late_failure_does_not_resurrect_swept_nomination(self) -> None:
        """If sweep_stuck_claims has already marked a nomination
        FAILED, a late failure result must not revert it to QUEUED."""
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.FAILED  # swept earlier
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": False,
            "error": "evaluate_org failed",
        }])
        result = _handle_results(event)

        assert result["failed"] == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_ignores_stale_attempt_success(self) -> None:
        """SQS is at-least-once: a delayed attempt-1 success must
        not create an evaluation while attempt-2 is in progress."""
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING  # attempt 2 running
        nom.evaluation_attempts = 2
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,  # stale — from attempt 1
            "success": True,
            "data": EVAL_RESULT,
        }])
        result = _handle_results(event)

        assert result["processed"] == 0
        assert OrganizationEvaluation.objects.count() == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING

    def test_ignores_stale_attempt_failure(self) -> None:
        """A delayed attempt-1 failure must not revert a nomination
        whose attempt-2 is still in progress."""
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING  # attempt 2 running
        nom.evaluation_attempts = 2
        nom.save(update_fields=["status", "evaluation_attempts"])

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,  # stale
            "success": False,
            "error": "evaluate_org failed",
        }])
        result = _handle_results(event)

        assert result["failed"] == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING
        assert nom.evaluation_attempts == 2

    def test_atomic_update_loses_race_to_concurrent_sweep(self) -> None:
        """If the row is flipped to FAILED between the fetch and the
        conditional update (simulating a concurrent sweep or worker),
        the atomic compare-and-swap affects 0 rows and the result is
        ignored — no evaluation created, no status overwrite."""
        from terramedic.nominations.worker import Nomination as WorkerNom
        from terramedic.nominations.worker import _handle_results

        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.evaluation_attempts = 1
        nom.save(update_fields=["status", "evaluation_attempts"])

        real_filter = WorkerNom.objects.filter

        def racing_filter(*args: object, **kwargs: object) -> object:
            # Simulate a concurrent sweep flipping the row to FAILED
            # after the conditional UPDATE's filter is built but
            # before it runs.
            real_filter(pk=nom.pk).update(
                status=NominationStatus.FAILED,
            )
            # Restore the original filter so the UPDATE itself runs
            # normally against the now-FAILED row.
            WorkerNom.objects.filter = real_filter  # type: ignore[assignment,method-assign]
            return real_filter(*args, **kwargs)

        event = make_sqs_event([{
            "nomination_id": nom.pk,
            "evaluation_attempts": 1,
            "success": True,
            "data": EVAL_RESULT,
        }])
        try:
            WorkerNom.objects.filter = racing_filter  # type: ignore[assignment,method-assign]
            result = _handle_results(event)
        finally:
            WorkerNom.objects.filter = real_filter  # type: ignore[assignment,method-assign]

        assert result["processed"] == 0
        assert OrganizationEvaluation.objects.count() == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED
