"""Lambda handler for the evaluator (outside VPC).

Triggered by SQS messages on the evaluation-requests queue.
Fetches org websites, calls the Anthropic API, and sends
results to the evaluation-results queue.  Has no database access.
"""

import json
import logging
import os
from typing import Any

import boto3

from terramedic.core.secrets import is_arn, resolve_secret
from terramedic.nominations.claim import DEFAULT_EVAL_MODEL, evaluate_org  # noqa: F401

logger = logging.getLogger(__name__)


def Anthropic(**kwargs: Any) -> Any:  # noqa: N802
    """Lazy-import wrapper — replaced in tests via mock."""
    from anthropic import Anthropic as _Anthropic

    return _Anthropic(**kwargs)


def handle_evaluation_request(
    event: dict[str, Any],
    context: Any = None,
) -> dict[str, Any]:
    """Process SQS messages containing evaluation requests."""
    raw_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not raw_key:
        msg = "ANTHROPIC_API_KEY is not set"
        raise RuntimeError(msg)
    api_key = resolve_secret(raw_key, "key") if is_arn(raw_key) else raw_key
    client = Anthropic(api_key=api_key)

    results_queue_url = os.environ["EVALUATION_RESULTS_QUEUE_URL"]
    sqs = boto3.client("sqs")

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        nomination_id = body["nomination_id"]
        url = body["url"]
        categories = body.get("categories") or None
        evaluation_attempts = body.get("evaluation_attempts", 1)

        try:
            data = evaluate_org(
                url=url,
                model=os.environ.get("EVAL_MODEL", DEFAULT_EVAL_MODEL),
                client=client,
                categories=categories,
            )
            result_message: dict[str, Any] = {
                "nomination_id": nomination_id,
                "evaluation_attempts": evaluation_attempts,
                "success": True,
                "data": data,
            }
        except Exception:  # noqa: BLE001
            logger.exception("evaluate_org failed for %s", url)
            result_message = {
                "nomination_id": nomination_id,
                "evaluation_attempts": evaluation_attempts,
                "success": False,
                "error": f"evaluate_org failed for {url}",
            }

        sqs.send_message(
            QueueUrl=results_queue_url,
            MessageBody=json.dumps(result_message),
        )

    return {"status": "ok"}
