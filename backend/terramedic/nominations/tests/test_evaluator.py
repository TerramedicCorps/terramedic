"""Tests for the evaluator Lambda handler (outside VPC)."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

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

_EVALUATOR_MODULE = "terramedic.nominations.evaluator"
_EVALUATE_ORG_PATH = f"{_EVALUATOR_MODULE}.evaluate_org"
_ANTHROPIC_PATH = f"{_EVALUATOR_MODULE}.Anthropic"


def _make_sqs_event(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "body": json.dumps(record),
            }
            for record in records
        ],
    }


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("EVALUATION_RESULTS_QUEUE_URL", "https://sqs.test/results")


class TestHandleEvaluationRequest:
    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, return_value=_EVAL_RESULT)
    @patch(_ANTHROPIC_PATH)
    def test_successful_evaluation_sends_success_result(
        self,
        mock_anthropic: Any,
        mock_eval: Any,
        mock_boto3: Any,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        event = _make_sqs_event([{
            "nomination_id": 42,
            "url": "https://example.org",
            "categories": ["volunteer"],
            "evaluation_attempts": 1,
        }])
        handle_evaluation_request(event)

        mock_sqs.send_message.assert_called_once()
        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == "https://sqs.test/results"
        body = json.loads(call_kwargs["MessageBody"])
        assert body["nomination_id"] == 42
        assert body["success"] is True
        assert body["data"] == _EVAL_RESULT
        assert body["evaluation_attempts"] == 1

    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, side_effect=ValueError("bad URL"))
    @patch(_ANTHROPIC_PATH)
    def test_failed_evaluation_sends_failure_result(
        self,
        mock_anthropic: Any,
        mock_eval: Any,
        mock_boto3: Any,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        event = _make_sqs_event([{
            "nomination_id": 42,
            "url": "https://example.org",
            "categories": None,
            "evaluation_attempts": 1,
        }])
        handle_evaluation_request(event)

        mock_sqs.send_message.assert_called_once()
        body = json.loads(mock_sqs.send_message.call_args[1]["MessageBody"])
        assert body["nomination_id"] == 42
        assert body["success"] is False
        assert "error" in body

    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, return_value=_EVAL_RESULT)
    @patch(_ANTHROPIC_PATH)
    def test_passes_url_and_categories_to_evaluate_org(
        self,
        mock_anthropic: Any,
        mock_eval: Any,
        mock_boto3: Any,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        mock_boto3.client.return_value = MagicMock()

        event = _make_sqs_event([{
            "nomination_id": 1,
            "url": "https://special.org",
            "categories": ["donate", "volunteer"],
            "evaluation_attempts": 1,
        }])
        handle_evaluation_request(event)

        mock_eval.assert_called_once()
        call_kwargs = mock_eval.call_args[1]
        assert call_kwargs["url"] == "https://special.org"
        assert call_kwargs["categories"] == ["donate", "volunteer"]

    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, return_value=_EVAL_RESULT)
    @patch(_ANTHROPIC_PATH)
    def test_processes_multiple_records(
        self,
        mock_anthropic: Any,
        mock_eval: Any,
        mock_boto3: Any,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs

        event = _make_sqs_event([
            {
                "nomination_id": 1,
                "url": "https://one.org",
                "categories": None,
                "evaluation_attempts": 1,
            },
            {
                "nomination_id": 2,
                "url": "https://two.org",
                "categories": ["donate"],
                "evaluation_attempts": 1,
            },
        ])
        handle_evaluation_request(event)

        assert mock_eval.call_count == 2
        assert mock_sqs.send_message.call_count == 2

    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, return_value=_EVAL_RESULT)
    def test_resolves_anthropic_arn(
        self,
        mock_eval: Any,
        mock_boto3: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        arn = "arn:aws:secretsmanager:us-east-1:123:secret:my-key"
        monkeypatch.setenv("ANTHROPIC_API_KEY", arn)
        mock_boto3.client.return_value = MagicMock()

        resolve_path = f"{_EVALUATOR_MODULE}.resolve_secret"
        anthropic_path = _ANTHROPIC_PATH
        with (
            patch(resolve_path, return_value="resolved-key") as mock_resolve,
            patch(anthropic_path) as mock_anthropic,
        ):
            event = _make_sqs_event([{
                "nomination_id": 1,
                "url": "https://example.org",
                "categories": None,
                "evaluation_attempts": 1,
            }])
            handle_evaluation_request(event)

            mock_resolve.assert_called_once_with(arn, "key")
            mock_anthropic.assert_called_once_with(api_key="resolved-key")

    @patch(f"{_EVALUATOR_MODULE}.boto3")
    @patch(_EVALUATE_ORG_PATH, return_value=_EVAL_RESULT)
    @patch(_ANTHROPIC_PATH)
    def test_null_categories_passed_as_none(
        self,
        mock_anthropic: Any,
        mock_eval: Any,
        mock_boto3: Any,
    ) -> None:
        from terramedic.nominations.evaluator import handle_evaluation_request

        mock_boto3.client.return_value = MagicMock()

        event = _make_sqs_event([{
            "nomination_id": 1,
            "url": "https://example.org",
            "categories": None,
            "evaluation_attempts": 1,
        }])
        handle_evaluation_request(event)

        call_kwargs = mock_eval.call_args[1]
        assert call_kwargs["categories"] is None
