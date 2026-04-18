"""Tests for scripts/inject_event_mapping.py."""

import importlib.util
from pathlib import Path

import pytest

from scripts.configure_zappa import configure_zappa_settings
from scripts.inject_event_mapping import (
    EVALUATOR_HANDLER,
    WORKER_HANDLER,
    append_event_mapping,
    build_event_mapping,
    require_mapping_in_ci,
    sqs_url_to_arn,
)


class TestSqsUrlToArn:
    def test_standard_url(self) -> None:
        url = (
            "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
        )
        assert (
            sqs_url_to_arn(url)
            == "arn:aws:sqs:us-east-1:123456789012:my-queue"
        )

    def test_different_region(self) -> None:
        url = "https://sqs.eu-west-2.amazonaws.com/1/queue-name"
        assert (
            sqs_url_to_arn(url)
            == "arn:aws:sqs:eu-west-2:1:queue-name"
        )

    def test_fifo_queue_url(self) -> None:
        url = "https://sqs.us-east-1.amazonaws.com/1/my-queue.fifo"
        assert (
            sqs_url_to_arn(url)
            == "arn:aws:sqs:us-east-1:1:my-queue.fifo"
        )


class TestBuildEventMapping:
    def test_both_queues(self) -> None:
        mapping = build_event_mapping(
            "https://sqs.us-east-1.amazonaws.com/1/requests",
            "https://sqs.us-east-1.amazonaws.com/1/results",
        )
        assert mapping == {
            "arn:aws:sqs:us-east-1:1:requests": EVALUATOR_HANDLER,
            "arn:aws:sqs:us-east-1:1:results": WORKER_HANDLER,
        }

    def test_empty_urls_yields_empty_mapping(self) -> None:
        assert build_event_mapping("", "") == {}

    def test_only_requests_queue(self) -> None:
        mapping = build_event_mapping(
            "https://sqs.us-east-1.amazonaws.com/1/requests",
            "",
        )
        assert mapping == {
            "arn:aws:sqs:us-east-1:1:requests": EVALUATOR_HANDLER,
        }

    def test_only_results_queue(self) -> None:
        mapping = build_event_mapping(
            "",
            "https://sqs.us-east-1.amazonaws.com/1/results",
        )
        assert mapping == {
            "arn:aws:sqs:us-east-1:1:results": WORKER_HANDLER,
        }


class TestAppendEventMapping:
    def test_appends_valid_python_to_existing_file(
        self,
        tmp_path: Path,
    ) -> None:
        settings = tmp_path / "zappa_settings.py"
        settings.write_text(
            "# existing content\nENVIRONMENT_VARIABLES = {}\n",
        )
        mapping = {
            "arn:aws:sqs:us-east-1:1:foo": "module.func",
        }

        append_event_mapping(settings, mapping)

        content = settings.read_text()
        assert "ENVIRONMENT_VARIABLES = {}" in content
        assert "AWS_EVENT_MAPPING" in content

        # The appended block must be valid Python that defines the
        # exact dict we expect.
        namespace: dict[str, object] = {}
        exec(content, namespace)  # noqa: S102
        assert namespace["AWS_EVENT_MAPPING"] == mapping

    def test_empty_mapping_is_noop(self, tmp_path: Path) -> None:
        settings = tmp_path / "zappa_settings.py"
        original = "SOME_SETTING = 1\n"
        settings.write_text(original)

        append_event_mapping(settings, {})

        assert settings.read_text() == original

    def test_second_call_does_not_duplicate(
        self,
        tmp_path: Path,
    ) -> None:
        settings = tmp_path / "zappa_settings.py"
        settings.write_text("SOME_SETTING = 1\n")
        mapping = {
            "arn:aws:sqs:us-east-1:1:foo": "module.func",
        }

        append_event_mapping(settings, mapping)
        after_first = settings.read_text()

        append_event_mapping(settings, mapping)
        after_second = settings.read_text()

        assert after_first == after_second


class TestRequireMappingInCi:
    def test_ci_with_nonempty_mapping_passes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("CI", "true")
        require_mapping_in_ci({"arn:aws:sqs:us-east-1:1:q": "fn"})

    def test_no_ci_with_empty_mapping_passes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("CI", raising=False)
        require_mapping_in_ci({})

    def test_ci_with_empty_mapping_exits_nonzero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setenv("CI", "true")
        with pytest.raises(SystemExit) as exc:
            require_mapping_in_ci({})
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "EVALUATION_REQUESTS_QUEUE_URL" in err


class TestPipelineIntegration:
    """End-to-end: simulate the deploy pipeline and import the result.

    Verifies that configure_zappa.py + (a stub of `zappa
    save-python-settings-file`) + inject_event_mapping.py produce a
    Python module that, when imported, exposes ``AWS_EVENT_MAPPING``
    with the ARNs Zappa's handler will look up at runtime.
    """

    def test_produces_importable_settings_with_event_mapping(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv(
            "DATABASE_SECRET_ARN",
            "arn:aws:secretsmanager:us-east-1:1:secret:db",
        )
        monkeypatch.setenv(
            "DJANGO_SECRET_ARN",
            "arn:aws:secretsmanager:us-east-1:1:secret:key",
        )
        monkeypatch.setenv("ZAPPA_ROLE_NAME", "my-role")
        requests_url = "https://sqs.us-east-1.amazonaws.com/1/req"
        results_url = "https://sqs.us-east-1.amazonaws.com/1/res"
        monkeypatch.setenv(
            "EVALUATION_REQUESTS_QUEUE_URL", requests_url,
        )
        monkeypatch.setenv(
            "EVALUATION_RESULTS_QUEUE_URL", results_url,
        )

        json_path = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=json_path)
        assert json_path.exists()

        # Stub what `zappa save-python-settings-file` would produce.
        # Zappa's own generator isn't invoked here — we just need a
        # valid Python file for the inject step to append to.
        settings_py = tmp_path / "zappa_settings.py"
        settings_py.write_text(
            "API_STAGE = 'dev'\nENVIRONMENT_VARIABLES = {}\n",
        )

        mapping = build_event_mapping(requests_url, results_url)
        append_event_mapping(settings_py, mapping)

        spec = importlib.util.spec_from_file_location(
            "pipeline_test_zappa_settings", settings_py,
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.API_STAGE == "dev"
        assert module.AWS_EVENT_MAPPING == {
            "arn:aws:sqs:us-east-1:1:req": EVALUATOR_HANDLER,
            "arn:aws:sqs:us-east-1:1:res": WORKER_HANDLER,
        }
