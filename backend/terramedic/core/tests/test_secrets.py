import json
from unittest.mock import MagicMock, patch

import pytest

from terramedic.core.secrets import _get_client, is_arn, resolve_secret


class TestIsArn:
    def test_valid_arn(self) -> None:
        arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret"
        assert is_arn(arn) is True

    def test_plain_value(self) -> None:
        assert is_arn("my-plain-secret-value") is False

    def test_empty_string(self) -> None:
        assert is_arn("") is False

    def test_partial_arn_prefix(self) -> None:
        assert is_arn("arn:aws:secretsmanager") is False

    def test_other_aws_arn(self) -> None:
        assert is_arn("arn:aws:s3:::my-bucket") is False


class TestResolveSecret:
    def setup_method(self) -> None:
        _get_client.cache_clear()

    @patch("terramedic.core.secrets._get_client")
    def test_non_arn_returns_unchanged(self, mock_client: MagicMock) -> None:
        result = resolve_secret("plain-value", "key")
        assert result == "plain-value"
        mock_client.assert_not_called()

    @patch("terramedic.core.secrets._get_client")
    def test_resolves_arn_with_json_key(
        self, mock_get_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"url": "postgres://db:5432/app"}),
        }

        arn = "arn:aws:secretsmanager:us-east-1:123:secret:db-creds"
        result = resolve_secret(arn, "url")

        assert result == "postgres://db:5432/app"
        mock_client.get_secret_value.assert_called_once_with(SecretId=arn)

    @patch("terramedic.core.secrets._get_client")
    def test_invalid_json_raises_value_error(
        self, mock_get_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": "not-json",
        }

        arn = "arn:aws:secretsmanager:us-east-1:123:secret:bad-secret"
        with pytest.raises(ValueError, match="valid JSON"):
            resolve_secret(arn, "key")

    @patch("terramedic.core.secrets._get_client")
    def test_missing_key_raises_key_error(
        self, mock_get_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"other": "value"}),
        }

        arn = "arn:aws:secretsmanager:us-east-1:123:secret:my-secret"
        with pytest.raises(KeyError, match="key"):
            resolve_secret(arn, "key")
