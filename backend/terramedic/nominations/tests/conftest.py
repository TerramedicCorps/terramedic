"""Shared fixtures and constants for nominations tests."""

import json
from typing import Any

EVAL_RESULT: dict[str, Any] = {
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


def make_sqs_event(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a synthetic SQS event payload for testing."""
    return {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "body": json.dumps(record),
            }
            for record in records
        ],
    }
