from typing import Any
from unittest.mock import patch

import pytest
from django.core.management import call_command

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import OrganizationEvaluation

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

_COMMAND = "process_evaluations"


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_EVAL_ORG_PATH = (
    "terramedic.nominations.management.commands"
    ".process_evaluations.evaluate_org"
)
_ANTHROPIC_PATH = (
    "terramedic.nominations.management.commands"
    ".process_evaluations.create_anthropic_client"
)


def _make_queued_nomination(
    url: str = "https://example.org",
) -> Nomination:
    return Nomination.objects.create(
        url=url,
        categories=["volunteer"],
        ip_hash=None,
        status=NominationStatus.QUEUED,
    )


@pytest.mark.django_db
class TestProcessEvaluationsSuccess:
    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_processes_queued_nomination(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom = _make_queued_nomination()
        call_command(_COMMAND)
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATED

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_creates_evaluation_record(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom = _make_queued_nomination()
        call_command(_COMMAND)
        assert OrganizationEvaluation.objects.count() == 1
        ev = OrganizationEvaluation.objects.first()
        assert ev is not None
        assert ev.nomination_id == nom.pk

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_evaluation_stores_correct_fields(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        _make_queued_nomination()
        call_command(_COMMAND)
        ev = OrganizationEvaluation.objects.first()
        assert ev is not None
        assert ev.ai_model == "claude-sonnet-4-20250514"
        assert ev.ai_recommendation == "include"
        assert ev.ai_confidence == 80

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_passes_url_and_categories(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        _make_queued_nomination(url="https://special.org")
        call_command(_COMMAND)
        mock_eval.assert_called_once()
        call_kwargs = mock_eval.call_args
        assert call_kwargs[1]["url"] == "https://special.org"
        assert call_kwargs[1]["categories"] == ["volunteer"]

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_sets_evaluating_during_processing(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom = _make_queued_nomination()
        statuses_during: list[str] = []

        def capture_status(**kwargs: Any) -> dict[str, Any]:
            nom.refresh_from_db()
            statuses_during.append(nom.status)
            return _EVAL_RESULT

        mock_eval.side_effect = capture_status
        call_command(_COMMAND)
        assert statuses_during == [NominationStatus.EVALUATING]

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_processes_in_submission_order(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom1 = _make_queued_nomination(url="https://first.org")
        nom2 = _make_queued_nomination(url="https://second.org")
        call_command(_COMMAND)
        urls = [c[1]["url"] for c in mock_eval.call_args_list]
        assert urls == [nom1.url, nom2.url]

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_respects_limit(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        _make_queued_nomination(url="https://first.org")
        _make_queued_nomination(url="https://second.org")
        call_command(_COMMAND, "--limit", "1")
        assert mock_eval.call_count == 1


@pytest.mark.django_db
class TestProcessEvaluationsFailure:
    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, side_effect=ValueError("bad URL"))
    def test_first_failure_reverts_to_queued(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom = _make_queued_nomination()
        call_command(_COMMAND)
        nom.refresh_from_db()
        assert nom.status == NominationStatus.QUEUED
        assert nom.evaluation_attempts == 1

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, side_effect=ValueError("bad URL"))
    def test_second_failure_marks_failed(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        nom = _make_queued_nomination()
        nom.evaluation_attempts = 1
        nom.save(update_fields=["evaluation_attempts"])
        call_command(_COMMAND)
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED
        assert nom.evaluation_attempts == 2

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, side_effect=ValueError("bad URL"))
    def test_failure_creates_no_evaluation(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        _make_queued_nomination()
        call_command(_COMMAND)
        assert OrganizationEvaluation.objects.count() == 0

    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH)
    def test_failure_continues_to_next(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        mock_eval.side_effect = [ValueError("bad"), _EVAL_RESULT]
        nom1 = _make_queued_nomination(url="https://bad.org")
        nom2 = _make_queued_nomination(url="https://good.org")
        call_command(_COMMAND)
        nom1.refresh_from_db()
        nom2.refresh_from_db()
        assert nom1.status == NominationStatus.QUEUED
        assert nom2.status == NominationStatus.EVALUATED


@pytest.mark.django_db
class TestProcessEvaluationsEdgeCases:
    @patch(_ANTHROPIC_PATH)
    @patch(_EVAL_ORG_PATH, return_value=_EVAL_RESULT)
    def test_empty_queue_exits_cleanly(
        self,
        mock_eval: Any,
        mock_anthropic: Any,
    ) -> None:
        call_command(_COMMAND)
        mock_eval.assert_not_called()

    def test_missing_api_key_raises_command_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from django.core.management.base import CommandError

        monkeypatch.delenv("ANTHROPIC_API_KEY")
        with pytest.raises(CommandError, match="ANTHROPIC_API_KEY"):
            call_command(_COMMAND)
