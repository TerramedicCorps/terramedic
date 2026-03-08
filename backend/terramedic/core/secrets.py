"""Resolve AWS Secrets Manager ARNs to their actual values at Lambda startup."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_ARN_PREFIX = "arn:aws:secretsmanager:"


def is_arn(value: str) -> bool:
    """Check if a value is a Secrets Manager ARN."""
    return value.startswith(_ARN_PREFIX)


@lru_cache(maxsize=1)
def _get_client() -> Any:
    return boto3.client("secretsmanager")


def resolve_secret(value: str, json_key: str) -> str:
    """Resolve a value that may be a Secrets Manager ARN.

    If the value is an ARN, fetch the secret and extract the
    specified JSON key. Otherwise, return the value unchanged.
    """
    if not is_arn(value):
        return value

    secret_name = value.rsplit(":", 1)[-1] if ":" in value else "<unknown>"
    client = _get_client()
    try:
        resp = client.get_secret_value(SecretId=value)
    except ClientError as exc:
        msg = f"Failed to retrieve secret '{secret_name}' from Secrets Manager: {exc}"
        raise RuntimeError(msg) from exc
    try:
        secret = json.loads(resp["SecretString"])
    except json.JSONDecodeError as exc:
        msg = f"Secret '{secret_name}' must contain valid JSON in SecretString"
        raise ValueError(msg) from exc
    try:
        resolved = secret[json_key]
    except KeyError as exc:
        msg = f"Secret '{secret_name}' does not contain expected key {json_key!r}"
        raise KeyError(msg) from exc
    logger.info("Resolved secret successfully")
    return str(resolved)
