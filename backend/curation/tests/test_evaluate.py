"""Tests for the curation CLI evaluation tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from curation.evaluate import (
    _build_arg_parser,
    _coerce_enums,
    _save_evaluation,
    _url_to_slug,
    _validate_url,
    evaluate_org,
    main,
)


def _make_valid_evaluation() -> dict[str, Any]:
    """Return a minimal valid evaluation dict."""
    return {
        "org_metadata": {
            "name": "Test Org",
            "website_url": "https://example.org",
        },
        "sdg_alignment": [
            {"sdg": 13, "evidence": "Climate action programs"},
        ],
        "evidence_of_work": [
            {"activity": "Tree planting", "type": "conservation"},
        ],
        "accessibility": {},
        "evidence_score": {"score": 3, "rationale": "Moderate evidence"},
        "curator_notes": {"recommendation": "include"},
        "evaluated_at": "2026-04-04T12:00:00+00:00",
        "evaluated_by": "claude-sonnet-4-20250514",
    }


class TestArgParser:
    def test_url_required(self) -> None:
        with pytest.raises(SystemExit):
            _build_arg_parser().parse_args([])

    def test_url_parsed(self) -> None:
        args = _build_arg_parser().parse_args(["https://example.org"])
        assert args.url == "https://example.org"

    def test_default_model(self) -> None:
        args = _build_arg_parser().parse_args(["https://example.org"])
        assert args.model == "claude-sonnet-4-20250514"

    def test_custom_model(self) -> None:
        args = _build_arg_parser().parse_args(
            ["https://example.org", "--model", "claude-opus-4-20250514"],
        )
        assert args.model == "claude-opus-4-20250514"

    def test_dry_run_flag(self) -> None:
        args = _build_arg_parser().parse_args(
            ["https://example.org", "--dry-run"],
        )
        assert args.dry_run is True

    def test_dry_run_default_false(self) -> None:
        args = _build_arg_parser().parse_args(["https://example.org"])
        assert args.dry_run is False

    def test_output_override(self) -> None:
        args = _build_arg_parser().parse_args(
            ["https://example.org", "--output", "/tmp/out.json"],
        )
        assert args.output == "/tmp/out.json"


class TestValidateUrl:
    def test_valid_https_url(self) -> None:
        assert _validate_url("https://example.org") == "https://example.org"

    def test_valid_http_url(self) -> None:
        assert _validate_url("http://example.org") == "http://example.org"

    def test_missing_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("example.org")

    def test_missing_netloc_raises(self) -> None:
        with pytest.raises(ValueError, match="domain"):
            _validate_url("https://")

    def test_non_http_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("ftp://example.org")


class TestUrlToSlug:
    def test_simple_domain(self) -> None:
        result = _url_to_slug("https://rainforest-alliance.org")
        assert result == "rainforest-alliance-org"

    def test_www_stripped(self) -> None:
        assert _url_to_slug("https://www.wwf.org") == "wwf-org"

    def test_subdomain_preserved(self) -> None:
        assert _url_to_slug("https://act.greenpeace.org") == "act-greenpeace-org"

    def test_trailing_slash_ignored(self) -> None:
        assert _url_to_slug("https://example.org/") == "example-org"


class TestEvaluateOrg:
    def _mock_client(self, response_text: str) -> MagicMock:
        client = MagicMock()
        message = MagicMock()
        block = MagicMock()
        block.text = response_text
        message.content = [block]
        message.model = "claude-sonnet-4-20250514"
        client.messages.create.return_value = message
        return client

    def test_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SystemExit):
            evaluate_org("https://example.org", model="claude-sonnet-4-20250514")

    def test_calls_api_with_correct_params(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]
        client = self._mock_client(json.dumps(evaluation))

        evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )

        client.messages.create.assert_called_once()
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert "example.org" in call_kwargs["messages"][0]["content"]

    def test_parses_json_response(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]
        client = self._mock_client(json.dumps(evaluation))

        result = evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )

        assert result["org_metadata"]["name"] == "Test Org"

    def test_strips_markdown_fences(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]
        wrapped = f"```json\n{json.dumps(evaluation)}\n```"
        client = self._mock_client(wrapped)

        result = evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )

        assert result["org_metadata"]["name"] == "Test Org"

    def test_adds_evaluated_at(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]
        client = self._mock_client(json.dumps(evaluation))

        result = evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )

        assert "evaluated_at" in result
        assert "T" in result["evaluated_at"]  # ISO format

    def test_adds_evaluated_by(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]
        client = self._mock_client(json.dumps(evaluation))

        result = evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )

        assert result["evaluated_by"] == "claude-sonnet-4-20250514"

    def test_invalid_json_raises(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = self._mock_client("This is not JSON at all")

        with pytest.raises(ValueError, match="JSON"):
            evaluate_org(
                "https://example.org",
                model="claude-sonnet-4-20250514",
                client=client,
            )

    def test_schema_validation_failure(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        invalid = {"org_metadata": {"name": "Test"}}  # missing required fields
        client = self._mock_client(json.dumps(invalid))

        with pytest.raises(ValueError, match="schema"):
            evaluate_org(
                "https://example.org",
                model="claude-sonnet-4-20250514",
                client=client,
            )


class TestCoerceEnums:
    def test_known_activity_type_unchanged(self) -> None:
        data = {"evidence_of_work": [{"activity": "x", "type": "conservation"}]}
        _coerce_enums(data)
        assert data["evidence_of_work"][0]["type"] == "conservation"

    def test_unknown_activity_type_becomes_other(self) -> None:
        data = {"evidence_of_work": [{"activity": "x", "type": "certification"}]}
        _coerce_enums(data)
        assert data["evidence_of_work"][0]["type"] == "other"

    def test_missing_evidence_of_work_is_noop(self) -> None:
        data: dict[str, Any] = {}
        _coerce_enums(data)
        assert "evidence_of_work" not in data

    def test_multiple_activity_items(self) -> None:
        data = {
            "evidence_of_work": [
                {"activity": "a", "type": "certification"},
                {"activity": "b", "type": "advocacy"},
                {"activity": "c", "type": "capacity_building"},
            ],
        }
        _coerce_enums(data)
        assert data["evidence_of_work"][0]["type"] == "other"
        assert data["evidence_of_work"][1]["type"] == "advocacy"
        assert data["evidence_of_work"][2]["type"] == "other"

    def test_known_category_unchanged(self) -> None:
        data = {"accessibility": {"categories": ["donate", "volunteer"]}}
        _coerce_enums(data)
        assert data["accessibility"]["categories"] == ["donate", "volunteer"]

    def test_unknown_category_removed(self) -> None:
        data = {"accessibility": {"categories": ["donate", "education"]}}
        _coerce_enums(data)
        assert data["accessibility"]["categories"] == ["donate"]

    def test_missing_accessibility_is_noop(self) -> None:
        data: dict[str, Any] = {}
        _coerce_enums(data)
        assert "accessibility" not in data

    def test_missing_categories_is_noop(self) -> None:
        data: dict[str, Any] = {"accessibility": {}}
        _coerce_enums(data)
        assert "categories" not in data["accessibility"]


class TestSaveEvaluation:
    def test_creates_directory(self, tmp_path: Path) -> None:
        output_path = str(tmp_path / "sub" / "dir" / "eval.json")
        data = _make_valid_evaluation()

        _save_evaluation(data, output_path)

        assert Path(output_path).exists()

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        output_path = str(tmp_path / "eval.json")
        data = _make_valid_evaluation()

        _save_evaluation(data, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_json_is_indented(self, tmp_path: Path) -> None:
        output_path = str(tmp_path / "eval.json")
        data = _make_valid_evaluation()

        _save_evaluation(data, output_path)

        content = Path(output_path).read_text()
        assert "  " in content  # indented


class TestMain:
    def _mock_evaluate(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> dict[str, Any]:
        evaluation = _make_valid_evaluation()
        monkeypatch.setattr(
            "curation.evaluate.evaluate_org",
            lambda *_args, **_kwargs: evaluation,
        )
        return evaluation

    def test_dry_run_no_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        self._mock_evaluate(monkeypatch)
        output_path = str(tmp_path / "should_not_exist.json")

        main(["https://example.org", "--dry-run", "--output", output_path])

        assert not Path(output_path).exists()
        captured = capsys.readouterr()
        assert "Test Org" in captured.out

    def test_prints_to_stdout(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        self._mock_evaluate(monkeypatch)
        output_path = str(tmp_path / "eval.json")

        main(["https://example.org", "--output", output_path])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["org_metadata"]["name"] == "Test Org"

    def test_saves_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        self._mock_evaluate(monkeypatch)
        output_path = str(tmp_path / "eval.json")

        main(["https://example.org", "--output", output_path])

        assert Path(output_path).exists()

    def test_api_error_exits_1(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "curation.evaluate.evaluate_org",
            MagicMock(side_effect=RuntimeError("API connection failed")),
        )

        with pytest.raises(SystemExit) as exc_info:
            main(["https://example.org", "--dry-run"])

        assert exc_info.value.code == 1

    def test_default_output_path_uses_slug(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        self._mock_evaluate(monkeypatch)
        default_dir = tmp_path / "curation" / "pending"
        monkeypatch.setattr(
            "curation.evaluate._default_output_dir",
            lambda: str(default_dir),
        )

        main(["https://www.example.org"])

        expected = default_dir / "example-org.json"
        assert expected.exists()
