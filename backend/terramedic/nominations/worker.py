"""Lambda handler for processing the evaluation queue.

Invoked asynchronously by the admin action via boto3, or directly
via ``zappa invoke``.
"""

from typing import Any

from django.core.management import call_command


def process_evaluation_queue(
    event: dict[str, Any] | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """Process queued nominations.

    Accepts an optional ``limit`` key in the event payload.
    """
    event = event or {}
    limit = max(1, min(int(event.get("limit", 10)), 50))
    call_command("process_evaluations", "--limit", str(limit))
    return {"status": "ok", "limit": limit}
