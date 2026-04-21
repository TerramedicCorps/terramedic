"""Tests for the curation CLI evaluation tool."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from curation.evaluate import (
    _VALID_ACTIVITY_TYPES,
    _VALID_CATEGORIES,
    _build_arg_parser,
    _build_user_message,
    _clean_response,
    _extract_json,
    _extract_subpage_urls,
    _html_to_text,
    _load_schema,
    _save_evaluation,
    _save_to_db,
    _url_to_slug,
    _validate_url,
    evaluate_org,
    main,
)
from curation.prompt import SYSTEM_PROMPT


class TestSchemaSyncWithPrompt:
    """Verify schema.json is the single source of truth for prompt and validation."""

    def test_valid_activity_types_match_schema(self) -> None:
        schema = _load_schema()
        schema_types = set(
            schema["properties"]["evidence_of_work"]["items"]
            ["properties"]["type"]["enum"],
        )
        assert schema_types == _VALID_ACTIVITY_TYPES

    def test_valid_categories_match_schema(self) -> None:
        schema = _load_schema()
        schema_categories = set(
            schema["properties"]["accessibility"]["properties"]
            ["categories"]["items"]["enum"],
        )
        assert schema_categories == _VALID_CATEGORIES

    def test_prompt_contains_schema_json(self) -> None:
        """The prompt should embed the actual JSON schema, not a prose summary."""
        assert '"$schema"' in SYSTEM_PROMPT or '"properties"' in SYSTEM_PROMPT

    def test_prompt_omits_programmatic_fields(self) -> None:
        """Fields injected by evaluate.py should not appear in the schema
        embedded in the prompt, to avoid confusing the model."""
        # These fields are added programmatically after model response
        for field in ("evaluated_at", "evaluated_by", "prompt_version",
                      "evaluation_history"):
            # Should not appear as a JSON property key in the prompt
            assert f'"{field}"' not in SYSTEM_PROMPT

    def test_embedded_schema_is_compact(self) -> None:
        """The schema JSON embedded in the prompt must be compact, not pretty.

        Pretty-printed JSON wastes ~30% on whitespace tokens sent on every
        request. The model parses both forms identically.
        """
        start = SYSTEM_PROMPT.find("```json\n")
        assert start != -1, "prompt must contain a ```json block"
        end = SYSTEM_PROMPT.find("\n```", start + len("```json\n"))
        assert end != -1, "```json block must be closed"
        schema_block = SYSTEM_PROMPT[start + len("```json\n"):end]
        # Round-trip through the canonical compact form — this catches
        # any unnecessary whitespace (spaces, tabs, newlines) regardless
        # of how it was introduced.
        parsed = json.loads(schema_block)
        assert schema_block == json.dumps(parsed, separators=(",", ":"))


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
        "curator_notes": {"recommendation": "include", "confidence": 85},
        "evaluated_at": "2026-04-04T12:00:00+00:00",
        "evaluated_by": "claude-sonnet-4-20250514",
        "prompt_version": "1.0",
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

    def test_categories_flag(self) -> None:
        args = _build_arg_parser().parse_args(
            ["https://example.org", "--categories", "donate", "resource"],
        )
        assert args.categories == ["donate", "resource"]

    def test_categories_default_empty(self) -> None:
        args = _build_arg_parser().parse_args(["https://example.org"])
        assert args.categories == []


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
        block.type = "text"
        block.text = response_text
        message.content = [block]
        message.model = "claude-sonnet-4-20250514"
        client.messages.create.return_value = message
        return client

    def _mock_client_with_blocks(
        self,
        response_text: str,
        extra_block_types: list[str] | None = None,
        usage: dict[str, int] | None = None,
    ) -> MagicMock:
        """Mock a client whose response has non-text blocks before the text.

        Used for tests that exercise mixed content (web search results,
        server tool use) or need a specific ``usage`` object.
        """
        client = MagicMock()
        message = MagicMock()
        blocks: list[MagicMock] = []
        for block_type in extra_block_types or []:
            extra = MagicMock()
            extra.type = block_type
            extra.text = None
            blocks.append(extra)
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = response_text
        blocks.append(text_block)
        message.content = blocks
        if usage is not None:
            message.usage = MagicMock(**usage)
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

    def test_enables_web_search_tool(
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

        call_kwargs = client.messages.create.call_args.kwargs
        assert "tools" in call_kwargs
        tool_types = [t["type"] for t in call_kwargs["tools"]]
        assert "web_search_20250305" in tool_types

    def test_system_prompt_uses_cache_control(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """System prompt must be sent as a cacheable block.

        The SYSTEM_PROMPT is identical across evaluations, so marking it
        with ``cache_control: ephemeral`` lets the API serve subsequent
        evals from cache at ~10% of the input-token cost.
        """
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

        call_kwargs = client.messages.create.call_args.kwargs
        system = call_kwargs["system"]
        assert isinstance(system, list), (
            "system must be a list of blocks to attach cache_control"
        )
        assert system[-1].get("cache_control") == {"type": "ephemeral"}
        assert system[-1]["type"] == "text"
        assert system[-1]["text"] == SYSTEM_PROMPT

    def test_logs_usage_and_search_count(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Token usage and web-search count must be logged per eval.

        Needed to monitor whether cache_control is actually landing cache
        hits and whether the web-search max_uses cap is ever reached.
        """
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]

        client = self._mock_client_with_blocks(
            response_text=json.dumps(evaluation),
            extra_block_types=["server_tool_use", "server_tool_use"],
            usage={
                "input_tokens": 1234,
                "output_tokens": 567,
                "cache_read_input_tokens": 890,
                "cache_creation_input_tokens": 0,
            },
        )

        with caplog.at_level(logging.INFO, logger="curation.evaluate"):
            evaluate_org(
                "https://example.org",
                model="claude-sonnet-4-20250514",
                client=client,
            )

        log_text = "\n".join(r.message for r in caplog.records)
        assert "input=1234" in log_text
        assert "output=567" in log_text
        assert "cache_read=890" in log_text
        assert "server_searches=2" in log_text

    def test_extracts_text_from_mixed_content_blocks(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When web search is used, response has non-text blocks too."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        evaluation = _make_valid_evaluation()
        del evaluation["evaluated_at"]
        del evaluation["evaluated_by"]

        client = self._mock_client_with_blocks(
            response_text=json.dumps(evaluation),
            extra_block_types=["web_search_tool_result"],
        )

        result = evaluate_org(
            "https://example.org",
            model="claude-sonnet-4-20250514",
            client=client,
        )
        assert result["org_metadata"]["name"] == "Test Org"

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


class TestEvaluateOrgViaClaudeCode:
    """Local Claude Code path — uses Max billing, shells out to `claude -p`."""

    def _fake_subprocess_result(
        self,
        payload: dict[str, Any],
        returncode: int = 0,
        is_error: bool = False,
    ) -> MagicMock:
        envelope = {
            "type": "result",
            "subtype": "success",
            "is_error": is_error,
            "result": json.dumps(payload),
            "total_cost_usd": 0.001,
            "duration_ms": 12345,
            "duration_api_ms": 6789,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "server_tool_use": {
                    "web_search_requests": 2,
                    "web_fetch_requests": 1,
                },
            },
        }
        result = MagicMock()
        result.returncode = returncode
        result.stdout = json.dumps(envelope)
        result.stderr = ""
        return result

    def _patch_build_user_message(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "curation.evaluate._build_user_message",
            lambda *_a, **_kw: ("fake user message", 0),
        )

    def test_invokes_claude_cli_with_expected_flags(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        eval_payload = _make_valid_evaluation()
        del eval_payload["evaluated_at"]
        del eval_payload["evaluated_by"]

        captured_cmd: list[str] = []

        def fake_run(cmd: list[str], **_kw: Any) -> MagicMock:
            captured_cmd.extend(cmd)
            return self._fake_subprocess_result(eval_payload)

        monkeypatch.setattr("subprocess.run", fake_run)

        evaluate_org_via_claude_code(
            "https://example.org",
            model="sonnet",
        )

        # Must shell out to the claude CLI in print mode.
        assert captured_cmd[0] == "claude"
        assert "-p" in captured_cmd
        # Must restrict tools to web access only.
        tools_idx = captured_cmd.index("--tools")
        assert captured_cmd[tools_idx + 1] == "WebSearch,WebFetch"
        # Must use JSON envelope.
        fmt_idx = captured_cmd.index("--output-format")
        assert captured_cmd[fmt_idx + 1] == "json"
        # Must pass the system prompt.
        assert "--append-system-prompt" in captured_cmd
        sys_idx = captured_cmd.index("--append-system-prompt")
        assert captured_cmd[sys_idx + 1] == SYSTEM_PROMPT
        # Must pass the model.
        model_idx = captured_cmd.index("--model")
        assert captured_cmd[model_idx + 1] == "sonnet"

    def test_extracts_evaluation_from_envelope(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        eval_payload = _make_valid_evaluation()
        del eval_payload["evaluated_at"]
        del eval_payload["evaluated_by"]

        monkeypatch.setattr(
            "subprocess.run",
            lambda *_a, **_kw: self._fake_subprocess_result(eval_payload),
        )

        result = evaluate_org_via_claude_code(
            "https://example.org",
            model="sonnet",
        )

        assert result["org_metadata"]["name"] == "Test Org"

    def test_stamps_duration_ms_from_envelope(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``duration_ms`` from the CLI envelope must land on the
        stored evaluation so it's queryable later without grepping
        logs."""
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        eval_payload = _make_valid_evaluation()
        del eval_payload["evaluated_at"]
        del eval_payload["evaluated_by"]

        monkeypatch.setattr(
            "subprocess.run",
            lambda *_a, **_kw: self._fake_subprocess_result(eval_payload),
        )

        result = evaluate_org_via_claude_code(
            "https://example.org",
            model="sonnet",
        )

        # _fake_subprocess_result stamps duration_ms=12345.
        assert result["duration_ms"] == 12345

    def test_stamps_evaluated_by_with_claude_code_prefix(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """`evaluated_by` must be distinguishable from the API path."""
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        eval_payload = _make_valid_evaluation()
        del eval_payload["evaluated_at"]
        del eval_payload["evaluated_by"]

        monkeypatch.setattr(
            "subprocess.run",
            lambda *_a, **_kw: self._fake_subprocess_result(eval_payload),
        )

        result = evaluate_org_via_claude_code(
            "https://example.org",
            model="sonnet",
        )

        assert result["evaluated_by"].startswith("claude-code:")
        assert "sonnet" in result["evaluated_by"]

    def test_raises_on_envelope_error(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        eval_payload = _make_valid_evaluation()

        monkeypatch.setattr(
            "subprocess.run",
            lambda *_a, **_kw: self._fake_subprocess_result(
                eval_payload, is_error=True,
            ),
        )

        with pytest.raises(RuntimeError, match="CLI reported error"):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )

    def test_raises_on_nonzero_exit(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)

        def fake_run(*_a: Any, **_kw: Any) -> MagicMock:
            result = MagicMock()
            result.returncode = 2
            result.stdout = ""
            result.stderr = "auth failed"
            return result

        monkeypatch.setattr("subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="exited with code"):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )

    def test_raises_on_malformed_stdout(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Non-JSON stdout must raise ValueError, not propagate JSONDecodeError."""
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)

        def fake_run(*_a: Any, **_kw: Any) -> MagicMock:
            result = MagicMock()
            result.returncode = 0
            result.stdout = "this is not JSON at all {"
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", fake_run)

        with pytest.raises(ValueError, match="not valid JSON"):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )

    def test_raises_on_empty_result_field(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Envelope with empty 'result' must raise ValueError."""
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)

        def fake_run(*_a: Any, **_kw: Any) -> MagicMock:
            envelope = {"is_error": False, "result": "", "usage": {}}
            result = MagicMock()
            result.returncode = 0
            result.stdout = json.dumps(envelope)
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", fake_run)

        with pytest.raises(ValueError, match="no 'result' field"):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )

    def test_propagates_timeout_expired(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """subprocess.TimeoutExpired must propagate so callers can handle it."""
        import subprocess as _subprocess

        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)

        def fake_run(*_a: Any, **_kw: Any) -> MagicMock:
            raise _subprocess.TimeoutExpired(cmd="claude", timeout=1)

        monkeypatch.setattr("subprocess.run", fake_run)

        with pytest.raises(_subprocess.TimeoutExpired):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )

    def test_raises_on_schema_validation_failure(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Invalid Claude Code output must raise with a 'Claude Code' prefix.

        Distinguishes this path from the API-based evaluate_org, whose
        validation failure uses the bare 'Output' prefix.
        """
        from curation.evaluate import evaluate_org_via_claude_code

        self._patch_build_user_message(monkeypatch)
        invalid = {"org_metadata": {"name": "Test"}}  # missing required keys

        monkeypatch.setattr(
            "subprocess.run",
            lambda *_a, **_kw: self._fake_subprocess_result(invalid),
        )

        with pytest.raises(ValueError, match="Claude Code output"):
            evaluate_org_via_claude_code(
                "https://example.org",
                model="sonnet",
            )


class TestValidateAgainstSchema:
    """Error-path coverage for the shared schema validation helper."""

    def test_raises_runtime_error_on_missing_jsonschema(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing jsonschema must raise, not sys.exit.

        sys.exit inside a Django management command mid-batch would
        bypass the CAS rollback that marks the row FAILED.
        """
        import sys as _sys

        from curation.evaluate import _validate_against_schema

        # Force `import jsonschema` inside the helper to raise ImportError.
        monkeypatch.setitem(_sys.modules, "jsonschema", None)

        with pytest.raises(RuntimeError, match="jsonschema"):
            _validate_against_schema({}, source="Output")


class TestCleanResponse:
    def test_known_activity_type_unchanged(self) -> None:
        data = {"evidence_of_work": [{"activity": "x", "type": "conservation"}]}
        _clean_response(data)
        assert data["evidence_of_work"][0]["type"] == "conservation"

    def test_unknown_activity_type_becomes_other(self) -> None:
        data = {"evidence_of_work": [{"activity": "x", "type": "certification"}]}
        _clean_response(data)
        assert data["evidence_of_work"][0]["type"] == "other"

    def test_missing_evidence_of_work_is_noop(self) -> None:
        data: dict[str, Any] = {}
        _clean_response(data)
        assert "evidence_of_work" not in data

    def test_multiple_activity_items(self) -> None:
        data = {
            "evidence_of_work": [
                {"activity": "a", "type": "certification"},
                {"activity": "b", "type": "advocacy"},
                {"activity": "c", "type": "capacity_building"},
            ],
        }
        _clean_response(data)
        assert data["evidence_of_work"][0]["type"] == "other"
        assert data["evidence_of_work"][1]["type"] == "advocacy"
        assert data["evidence_of_work"][2]["type"] == "other"

    def test_known_category_unchanged(self) -> None:
        data: dict[str, Any] = {
            "accessibility": {"categories": ["donate", "volunteer"]},
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert data["accessibility"]["categories"] == ["donate", "volunteer"]

    def test_unknown_category_becomes_other(self) -> None:
        data: dict[str, Any] = {
            "accessibility": {"categories": ["education", "donate"]},
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert data["accessibility"]["categories"] == ["other", "donate"]

    def test_mixed_valid_and_unknown_categories(self) -> None:
        data: dict[str, Any] = {
            "accessibility": {
                "categories": ["volunteer", "education", "donate"],
            },
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert data["accessibility"]["categories"] == [
            "volunteer",
            "other",
            "donate",
        ]

    def test_all_unknown_categories_become_other(self) -> None:
        data: dict[str, Any] = {
            "accessibility": {"categories": ["certification", "awareness"]},
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert data["accessibility"]["categories"] == ["other", "other"]

    def test_missing_accessibility_is_noop(self) -> None:
        data: dict[str, Any] = {"evidence_of_work": []}
        _clean_response(data)
        assert "accessibility" not in data

    def test_accessibility_without_categories_is_noop(self) -> None:
        data: dict[str, Any] = {
            "accessibility": {"donate_url": "https://example.org/donate"},
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert "categories" not in data["accessibility"]

    def test_null_values_removed(self) -> None:
        data: dict[str, Any] = {
            "org_metadata": {
                "name": "Test",
                "website_url": "https://example.org",
                "year_founded": None,
                "region": None,
            },
            "evidence_of_work": [],
        }
        _clean_response(data)
        assert "year_founded" not in data["org_metadata"]
        assert "region" not in data["org_metadata"]
        assert data["org_metadata"]["name"] == "Test"


class TestExtractJson:
    def test_plain_json(self) -> None:
        result = _extract_json('{"name": "test"}')
        assert result == {"name": "test"}

    def test_markdown_fenced_json(self) -> None:
        result = _extract_json('```json\n{"name": "test"}\n```')
        assert result == {"name": "test"}

    def test_json_with_preamble_text(self) -> None:
        text = (
            "Based on my research, here is the evaluation:\n\n"
            '{"name": "test", "score": 4}'
        )
        result = _extract_json(text)
        assert result == {"name": "test", "score": 4}

    def test_json_with_preamble_and_trailing_text(self) -> None:
        text = (
            "Here is my evaluation:\n\n"
            '{"name": "test"}\n\n'
            "Let me know if you need anything else."
        )
        result = _extract_json(text)
        assert result == {"name": "test"}

    def test_no_json_raises(self) -> None:
        with pytest.raises(ValueError, match="JSON"):
            _extract_json("This has no JSON at all")


class TestHtmlToText:
    def test_extracts_text_from_html(self) -> None:
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = _html_to_text(html)
        assert "Hello" in result
        assert "World" in result

    def test_strips_script_and_style(self) -> None:
        html = (
            "<html><body>"
            "<script>var x = 1;</script>"
            "<style>.foo { color: red; }</style>"
            "<p>Content</p>"
            "</body></html>"
        )
        result = _html_to_text(html)
        assert "var x" not in result
        assert "color" not in result
        assert "Content" in result

    def test_truncates_long_content(self) -> None:
        html = f"<html><body><p>{'x' * 20000}</p></body></html>"
        result = _html_to_text(html)
        assert len(result) <= 15000


class TestExtractSubpageUrls:
    def test_finds_volunteer_link(self) -> None:
        html = (
            '<html><body>'
            '<a href="/volunteer">Volunteer</a>'
            '<a href="/blog">Blog</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert "https://example.org/volunteer" in urls

    def test_finds_engagement_patterns(self) -> None:
        html = (
            '<html><body>'
            '<a href="/get-involved">Get Involved</a>'
            '<a href="/events">Events</a>'
            '<a href="/donate">Donate</a>'
            '<a href="/about-us">About</a>'
            '<a href="/careers">Careers</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert "https://example.org/get-involved" in urls
        assert "https://example.org/events" in urls
        assert "https://example.org/donate" in urls
        assert "https://example.org/about-us" in urls
        assert "https://example.org/careers" in urls

    def test_ignores_non_engagement_links(self) -> None:
        html = (
            '<html><body>'
            '<a href="/blog">Blog</a>'
            '<a href="/press">Press</a>'
            '<a href="/login">Login</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert len(urls) == 0

    def test_ignores_external_links(self) -> None:
        html = (
            '<html><body>'
            '<a href="https://other.org/volunteer">Volunteer</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert len(urls) == 0

    def test_handles_absolute_internal_links(self) -> None:
        html = (
            '<html><body>'
            '<a href="https://example.org/volunteer">Volunteer</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert "https://example.org/volunteer" in urls

    def test_deduplicates(self) -> None:
        html = (
            '<html><body>'
            '<a href="/volunteer">Vol 1</a>'
            '<a href="/volunteer">Vol 2</a>'
            '</body></html>'
        )
        urls = _extract_subpage_urls(html, "https://example.org")
        assert urls.count("https://example.org/volunteer") == 1


class TestBuildUserMessage:
    def test_includes_todays_date(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import httpx as _httpx

        html = "<html><body>Hello world</body></html>"

        def fake_get(*args: Any, **kwargs: Any) -> MagicMock:
            resp = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(_httpx, "get", fake_get)
        message, _ = _build_user_message("https://example.org")
        today = datetime.datetime.now(tz=datetime.UTC).date().isoformat()  # type: ignore[attr-defined]
        assert f"Today's date is {today}" in message

    def test_includes_categories_hint(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import httpx as _httpx

        html = "<html><body>Hello</body></html>"

        def fake_get(*args: Any, **kwargs: Any) -> MagicMock:
            resp = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(_httpx, "get", fake_get)
        message, _ = _build_user_message(
            "https://example.org",
            categories=["donate", "resource"],
        )
        assert "donate" in message
        assert "resource" in message
        assert "nominated" in message.lower() or "categor" in message.lower()

    def test_no_categories_no_hint(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import httpx as _httpx

        html = "<html><body>Hello</body></html>"

        def fake_get(*args: Any, **kwargs: Any) -> MagicMock:
            resp = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(_httpx, "get", fake_get)
        message, _ = _build_user_message("https://example.org")
        assert "nominated" not in message.lower()


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

    def test_preserves_evaluation_history(self, tmp_path: Path) -> None:
        output_path = str(tmp_path / "eval.json")
        prior = _make_valid_evaluation()
        prior["prompt_version"] = "0.9"
        _save_evaluation(prior, output_path)

        new_eval = _make_valid_evaluation()
        new_eval["prompt_version"] = "1.0"
        new_eval["evidence_score"]["score"] = 4
        _save_evaluation(new_eval, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert len(loaded["evaluation_history"]) == 1
        assert loaded["evaluation_history"][0]["prompt_version"] == "0.9"
        assert loaded["evaluation_history"][0]["score"] == 3
        assert loaded["evaluation_history"][0]["recommendation"] == "include"

    def test_appends_to_existing_history(self, tmp_path: Path) -> None:
        output_path = str(tmp_path / "eval.json")
        first = _make_valid_evaluation()
        first["prompt_version"] = "0.8"
        _save_evaluation(first, output_path)

        second = _make_valid_evaluation()
        second["prompt_version"] = "0.9"
        _save_evaluation(second, output_path)

        third = _make_valid_evaluation()
        third["prompt_version"] = "1.0"
        _save_evaluation(third, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert len(loaded["evaluation_history"]) == 2
        assert loaded["evaluation_history"][0]["prompt_version"] == "0.8"
        assert loaded["evaluation_history"][1]["prompt_version"] == "0.9"


@pytest.mark.django_db
class TestSaveToDb:
    def test_creates_evaluation_record(self) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        data = _make_valid_evaluation()
        pk = _save_to_db(data)

        obj = OrganizationEvaluation.objects.get(pk=pk)
        assert obj.evaluation_data == data

    def test_populates_ai_model(self) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        data = _make_valid_evaluation()
        pk = _save_to_db(data)

        obj = OrganizationEvaluation.objects.get(pk=pk)
        assert obj.ai_model == "claude-sonnet-4-20250514"

    def test_populates_ai_recommendation(self) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        data = _make_valid_evaluation()
        pk = _save_to_db(data)

        obj = OrganizationEvaluation.objects.get(pk=pk)
        assert obj.ai_recommendation == "include"

    def test_populates_ai_confidence(self) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        data = _make_valid_evaluation()
        pk = _save_to_db(data)

        obj = OrganizationEvaluation.objects.get(pk=pk)
        assert obj.ai_confidence == 85

    def test_status_defaults_to_pending(self) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        data = _make_valid_evaluation()
        pk = _save_to_db(data)

        obj = OrganizationEvaluation.objects.get(pk=pk)
        assert obj.status == "pending"


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

    @pytest.mark.django_db
    def test_db_flag_saves_to_database(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from terramedic.organizations.models import OrganizationEvaluation

        self._mock_evaluate(monkeypatch)

        main(["https://example.org", "--db"])

        assert OrganizationEvaluation.objects.count() == 1
        obj = OrganizationEvaluation.objects.first()
        assert obj is not None
        assert obj.ai_model == "claude-sonnet-4-20250514"
        captured = capsys.readouterr()
        assert "database" in captured.err

    def test_db_flag_parsed(self) -> None:
        args = _build_arg_parser().parse_args(
            ["https://example.org", "--db"],
        )
        assert args.db is True

    def test_db_flag_default_false(self) -> None:
        args = _build_arg_parser().parse_args(["https://example.org"])
        assert args.db is False

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


class TestCategoryAssignmentDiscipline:
    """The prompt must warn the model off over-classifying organizations.

    Reviewers were routinely manually trimming 3-4 category assignments
    down to the 1-2 that actually fit the org.
    """

    def test_prompt_has_assignment_discipline_section(self) -> None:
        assert "Assignment discipline" in SYSTEM_PROMPT

    def test_prompt_calls_out_typical_category_count(self) -> None:
        """The prompt should anchor the model on 1-2 categories as the
        typical count, so it stops routinely assigning 3-5."""
        assert "one or two" in SYSTEM_PROMPT

    def test_prompt_defaults_to_leaving_categories_off_when_unsure(
        self,
    ) -> None:
        assert "When in doubt, leave the category off" in SYSTEM_PROMPT


class TestDescriptionLengthGuidance:
    """Org descriptions must be roughly the same length across orgs so
    card layouts don't jitter — the current cards render the full
    description with no truncation, so raw character count drives
    visual variation.
    """

    def test_prompt_has_description_guidelines_section(self) -> None:
        assert "Description guidelines" in SYSTEM_PROMPT

    def test_prompt_asks_for_one_to_two_sentences(self) -> None:
        assert "one to two sentences" in SYSTEM_PROMPT

    def test_prompt_anchors_on_character_target(self) -> None:
        """The prompt must give the model a concrete character budget
        (120-180) so descriptions land in a narrow band. Assert the
        range as one token so incidental three-digit substrings
        elsewhere in the prompt can't satisfy it."""
        assert "120-180 characters" in SYSTEM_PROMPT
