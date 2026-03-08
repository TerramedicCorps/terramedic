import json
from pathlib import Path

import pytest

from scripts.configure_zappa import _parse_csv, configure_zappa_settings


class TestParseCsv:
    def test_comma_separated(self) -> None:
        assert _parse_csv("a, b, c") == ["a", "b", "c"]

    def test_empty_string(self) -> None:
        assert _parse_csv("") == []

    def test_strips_whitespace(self) -> None:
        assert _parse_csv("  foo , bar  ") == ["foo", "bar"]

    def test_ignores_empty_segments(self) -> None:
        assert _parse_csv("a,,b,") == ["a", "b"]


class TestConfigureZappaSettings:
    def test_generates_valid_json(self, tmp_path: Path) -> None:
        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert "base" in settings
        assert "dev" in settings
        assert "prod" in settings

    def test_prod_inherits_base_env_vars(
        self, tmp_path: Path,
    ) -> None:
        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        prod_env = settings["prod"]["environment_variables"]
        base_env = settings["base"]["environment_variables"]

        for key in base_env:
            assert key in prod_env, (
                f"Base env var {key!r} missing from prod"
            )

    def test_dev_inherits_base_env_vars(
        self, tmp_path: Path,
    ) -> None:
        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        dev_env = settings["dev"]["environment_variables"]
        base_env = settings["base"]["environment_variables"]

        for key in base_env:
            assert key in dev_env, (
                f"Base env var {key!r} missing from dev"
            )

    def test_dev_uses_lower_memory(
        self, tmp_path: Path,
    ) -> None:
        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert settings["dev"]["memory_size"] < settings["prod"]["memory_size"]

    def test_custom_docker_requires_ecr_registry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("USE_CUSTOM_DOCKER", "true")
        monkeypatch.delenv("ECR_REGISTRY", raising=False)

        with pytest.raises(RuntimeError, match="ECR_REGISTRY"):
            configure_zappa_settings(output_path=tmp_path / "out.json")

    def test_custom_docker_uses_ecr_image(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("USE_CUSTOM_DOCKER", "true")
        monkeypatch.setenv("ECR_REGISTRY", "123.dkr.ecr.us-east-1.amazonaws.com")

        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert "docker_image_uri" in settings["prod"]
        assert "123.dkr.ecr" in settings["prod"]["docker_image_uri"]
        assert "docker_image_uri" in settings["dev"]
        assert "123.dkr.ecr" in settings["dev"]["docker_image_uri"]

    def test_default_uses_public_ecr_image(
        self, tmp_path: Path,
    ) -> None:
        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert "docker_image" in settings["prod"]
        assert "public.ecr.aws" in settings["prod"]["docker_image"]
        assert "docker_image" in settings["dev"]
        assert "public.ecr.aws" in settings["dev"]["docker_image"]

    def test_ci_validation_raises_on_missing_vars(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("CI", "true")
        monkeypatch.delenv("DATABASE_SECRET_ARN", raising=False)
        monkeypatch.delenv("DJANGO_SECRET_ARN", raising=False)
        monkeypatch.delenv("ZAPPA_ROLE_NAME", raising=False)

        with pytest.raises(RuntimeError, match="Missing required"):
            configure_zappa_settings(output_path=tmp_path / "out.json")

    def test_ci_validation_passes_with_required_vars(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv(
            "DATABASE_SECRET_ARN",
            "arn:aws:secretsmanager:us-east-1:123:secret:db",
        )
        monkeypatch.setenv(
            "DJANGO_SECRET_ARN",
            "arn:aws:secretsmanager:us-east-1:123:secret:key",
        )
        monkeypatch.setenv("ZAPPA_ROLE_NAME", "my-role")

        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)
        assert output.exists()

    def test_vpc_config_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("VPC_SUBNET_IDS", "subnet-1, subnet-2")
        monkeypatch.setenv("VPC_SECURITY_GROUP_IDS", "sg-1")

        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        vpc = settings["base"]["vpc_config"]
        assert vpc["SubnetIds"] == ["subnet-1", "subnet-2"]
        assert vpc["SecurityGroupIds"] == ["sg-1"]

    def test_domain_settings_when_env_vars_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cert_arn = "arn:aws:acm:us-east-1:123:cert/abc"
        monkeypatch.setenv("DOMAIN_NAME", "example.org")
        monkeypatch.setenv("ACM_CERTIFICATE_ARN", cert_arn)

        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert settings["prod"]["domain"] == "api.example.org"
        assert settings["dev"]["domain"] == "test-api.example.org"
        assert settings["prod"]["certificate_arn"] == cert_arn
        assert settings["dev"]["certificate_arn"] == cert_arn

    def test_no_domain_settings_without_env_vars(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("DOMAIN_NAME", raising=False)
        monkeypatch.delenv("ACM_CERTIFICATE_ARN", raising=False)

        output = tmp_path / "zappa_settings.json"
        configure_zappa_settings(output_path=output)

        settings = json.loads(output.read_text())
        assert "domain" not in settings["prod"]
        assert "domain" not in settings["dev"]
        assert "certificate_arn" not in settings["prod"]
        assert "certificate_arn" not in settings["dev"]
