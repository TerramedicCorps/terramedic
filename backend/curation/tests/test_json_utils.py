"""Tests for the shared model-response JSON extractor."""

from __future__ import annotations

import pytest

from curation.json_utils import extract_json


class TestExtractJson:
    def test_plain_json(self) -> None:
        result = extract_json('{"name": "test"}')
        assert result == {"name": "test"}

    def test_markdown_fenced_json(self) -> None:
        result = extract_json('```json\n{"name": "test"}\n```')
        assert result == {"name": "test"}

    def test_json_with_preamble_text(self) -> None:
        text = (
            "Based on my research, here is the evaluation:\n\n"
            '{"name": "test", "score": 4}'
        )
        result = extract_json(text)
        assert result == {"name": "test", "score": 4}

    def test_json_with_preamble_and_trailing_text(self) -> None:
        text = (
            "Here is my evaluation:\n\n"
            '{"name": "test"}\n\n'
            "Let me know if you need anything else."
        )
        result = extract_json(text)
        assert result == {"name": "test"}

    def test_trailing_prose_with_stray_brace_is_handled(self) -> None:
        """``rfind('}')`` would over-shoot and grab the stray ``}``;
        the depth-aware matcher stops at the object's real end."""
        text = '{"name": "test"} then a closing thought }'
        result = extract_json(text)
        assert result == {"name": "test"}

    def test_no_json_raises(self) -> None:
        with pytest.raises(ValueError, match="JSON"):
            extract_json("This has no JSON at all")
