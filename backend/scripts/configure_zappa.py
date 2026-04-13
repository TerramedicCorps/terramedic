#!/usr/bin/env python3
"""Generate zappa_settings.json from environment variables.

This allows the deployment workflow to inject Terraform-provisioned
resource IDs without committing them to the repository.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _parse_csv(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def configure_zappa_settings(
    output_path: Path | None = None,
) -> None:
    aws_region = get_env("AWS_REGION", "us-east-1")
    ecr_registry = get_env("ECR_REGISTRY")
    zappa_bucket = get_env(
        "ZAPPA_S3_BUCKET",
        "terramedic-prod-zappa-deployments",
    )
    zappa_role_name = get_env("ZAPPA_ROLE_NAME", "")

    vpc_subnet_ids = _parse_csv(get_env("VPC_SUBNET_IDS", ""))
    vpc_sg_ids = _parse_csv(get_env("VPC_SECURITY_GROUP_IDS", ""))

    db_secret_arn = get_env("DATABASE_SECRET_ARN", "")
    django_secret_arn = get_env("DJANGO_SECRET_ARN", "")

    domain_name = get_env("DOMAIN_NAME", "")
    certificate_arn = get_env("ACM_CERTIFICATE_ARN", "")
    anthropic_secret_arn = get_env("ANTHROPIC_SECRET_ARN", "")

    use_custom_docker = (
        get_env("USE_CUSTOM_DOCKER", "false").lower() == "true"
    )

    # Fail fast in CI if required env vars are missing
    if os.environ.get("CI"):
        missing = [
            name
            for name, value in (
                ("DATABASE_SECRET_ARN", db_secret_arn),
                ("DJANGO_SECRET_ARN", django_secret_arn),
                ("ZAPPA_ROLE_NAME", zappa_role_name),
            )
            if not value
        ]
        if missing:
            msg = (
                "Missing required env var(s) in CI: "
                + ", ".join(missing)
            )
            raise RuntimeError(msg)

    if use_custom_docker:
        if not ecr_registry:
            msg = "ECR_REGISTRY is required when USE_CUSTOM_DOCKER is true"
            raise RuntimeError(msg)
        docker_image_key = "docker_image_uri"
        docker_image_prod = f"{ecr_registry}/terramedic-prod:latest"
        docker_image_dev = f"{ecr_registry}/terramedic-dev:latest"
    else:
        docker_image_key = "docker_image"
        docker_image_prod = "public.ecr.aws/lambda/python:3.14"
        docker_image_dev = "public.ecr.aws/lambda/python:3.14"

    # Shared settings — Zappa's "extends" does a shallow merge, so
    # nested dicts like environment_variables are replaced, not merged.
    # We merge them explicitly here to avoid silent key loss.
    base_env_vars = {
        "IS_LAMBDA": "true",
        "GDAL_DATA": "/opt/share/gdal",
        "PROJ_LIB": "/opt/share/proj",
        "LD_LIBRARY_PATH": "/opt/lib:/opt/lib64",
    }

    settings: dict[str, dict[str, Any]] = {
        "base": {
            "aws_region": aws_region,
            "django_settings": "terramedic.core.settings",
            "project_name": "terramedic",
            "s3_bucket": zappa_bucket,
            "runtime": "python3.14",
            "vpc_config": {
                "SubnetIds": vpc_subnet_ids,
                "SecurityGroupIds": vpc_sg_ids,
            },
            "manage_roles": False,
            "role_name": (
                zappa_role_name
                or "terramedic-prod-zappa-deployment"
            ),
            "timeout_seconds": 30,
            "slim_handler": False,
            "use_precompiled_packages": False,
            "environment_variables": base_env_vars,
            "exclude": [
                "*.gz", "*.rar", "*.zip", "*.tar",
                ".git/*", "tests/*", "*.pyc",
                "docker/*", "scripts/*",
                "node_modules/*", ".pytest_cache/*",
                "__pycache__/*", "*.egg-info/*",
                ".coverage", "htmlcov/*",
            ],
            "cors": True,
            "cors_allow_headers": [
                "Content-Type",
                "X-CSRFToken",
                "Authorization",
                "X-Requested-With",
                "Accept-Language",
            ],
            "apigateway_settings": {
                "throttle_burst_limit": 100,
                "throttle_rate_limit": 50,
            },
        },
        "dev": {
            "extends": "base",
            "stage": "dev",
            docker_image_key: docker_image_dev,
            "memory_size": 512,
            "keep_warm": True,
            "keep_warm_expression": "rate(4 minutes)",
            "environment_variables": {
                **base_env_vars,
                "ENVIRONMENT": "development",
                "DEBUG": "false",
            },
            "aws_environment_variables": {
                "DATABASE_URL": db_secret_arn,
                "SECRET_KEY": django_secret_arn,
            },
            "xray_tracing": False,
            **(
                {
                    "domain": f"test-api.{domain_name}",
                    "certificate_arn": certificate_arn,
                }
                if domain_name and certificate_arn
                else {}
            ),
        },
        "prod": {
            "extends": "base",
            "stage": "prod",
            docker_image_key: docker_image_prod,
            "memory_size": 1024,
            "keep_warm": True,
            "keep_warm_expression": "rate(4 minutes)",
            "environment_variables": {
                **base_env_vars,
                "ENVIRONMENT": "production",
                "DEBUG": "false",
            },
            # ARNs resolved at runtime by secrets.py
            "aws_environment_variables": {
                "DATABASE_URL": db_secret_arn,
                "SECRET_KEY": django_secret_arn,
            },
            "xray_tracing": True,
            **(
                {
                    "domain": f"api.{domain_name}",
                    "certificate_arn": certificate_arn,
                }
                if domain_name and certificate_arn
                else {}
            ),
        },
        "dev-worker": {
            "extends": "dev",
            "stage": "dev-worker",
            "timeout_seconds": 300,
            "memory_size": 512,
            "keep_warm": False,
            "apigateway_enabled": False,
            "aws_environment_variables": {
                "DATABASE_URL": db_secret_arn,
                "SECRET_KEY": django_secret_arn,
                **(
                    {"ANTHROPIC_API_KEY": anthropic_secret_arn}
                    if anthropic_secret_arn
                    else {}
                ),
            },
        },
        "prod-worker": {
            "extends": "prod",
            "stage": "prod-worker",
            "timeout_seconds": 300,
            "memory_size": 512,
            "keep_warm": False,
            "apigateway_enabled": False,
            "aws_environment_variables": {
                "DATABASE_URL": db_secret_arn,
                "SECRET_KEY": django_secret_arn,
                **(
                    {"ANTHROPIC_API_KEY": anthropic_secret_arn}
                    if anthropic_secret_arn
                    else {}
                ),
            },
        },
    }

    config_path = (
        output_path
        or Path(__file__).parent.parent / "zappa_settings.json"
    )
    with open(config_path, "w") as f:  # noqa: PTH123
        json.dump(settings, f, indent=2)
        f.write("\n")

    sys.stdout.write(
        f"Generated zappa_settings.json at {config_path}\n"
        f"  AWS Region: {aws_region}\n"
        f"  Zappa Bucket: {zappa_bucket}\n"
        f"  Custom Docker: {use_custom_docker}\n",
    )
    if vpc_subnet_ids:
        sys.stdout.write(
            f"  VPC Subnets: {', '.join(vpc_subnet_ids)}\n",
        )


def main() -> None:
    try:
        configure_zappa_settings()
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
