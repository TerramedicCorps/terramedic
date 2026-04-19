"""Lambda handler for the evaluation worker (in VPC).

Handles two triggers:

- **EventBridge** (scheduled): queries DB for queued nominations,
  claims them, runs skip checks, and dispatches to the
  evaluation-requests SQS queue.
- **SQS** (evaluation-results): writes evaluation results to the
  database and updates nomination status.
"""

import json
import logging
import os
from typing import Any

import boto3
from django.db import transaction

from terramedic.nominations.claim import claim_nominations, sweep_stuck_claims
from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.organizations.models import OrganizationEvaluation

logger = logging.getLogger(__name__)

_MAX_RETRY_ATTEMPTS = 2


def process_evaluation_queue(
    event: dict[str, Any] | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """Route to dispatch or results handler based on event source."""
    event = event or {}

    if "Records" in event and event["Records"]:
        source = event["Records"][0].get("eventSource", "")
        if source == "aws:sqs":
            return _handle_results(event)

    return _handle_dispatch(event)


def _handle_dispatch(event: dict[str, Any]) -> dict[str, Any]:
    """Query DB for queued nominations and send to SQS."""
    limit = max(1, min(int(event.get("limit", 10)), 50))
    queue_url = os.environ.get("EVALUATION_REQUESTS_QUEUE_URL", "")
    if not queue_url:
        msg = "EVALUATION_REQUESTS_QUEUE_URL is not set"
        raise RuntimeError(msg)
    sqs = boto3.client("sqs")

    sweep_stuck_claims()

    dispatched = 0

    for nomination in claim_nominations(limit):
        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    "nomination_id": nomination.pk,
                    "url": nomination.url,
                    "categories": nomination.categories,
                    "evaluation_attempts": nomination.evaluation_attempts,
                }),
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to dispatch nomination %s to SQS.",
                nomination.pk,
            )
            nomination.status = NominationStatus.QUEUED
            nomination.evaluation_attempts -= 1
            nomination.save(
                update_fields=["status", "evaluation_attempts"],
            )
            continue
        dispatched += 1

    logger.info("Dispatched %d nomination(s).", dispatched)
    return {"status": "ok", "dispatched": dispatched}


def _handle_results(event: dict[str, Any]) -> dict[str, Any]:
    """Process evaluation results from SQS."""
    processed = 0
    failed = 0

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        nomination_id = body["nomination_id"]
        evaluation_attempts = body.get("evaluation_attempts", 1)

        is_success = bool(body.get("success"))
        if is_success:
            new_status = NominationStatus.EVALUATED
        elif evaluation_attempts >= _MAX_RETRY_ATTEMPTS:
            new_status = NominationStatus.FAILED
        else:
            new_status = NominationStatus.QUEUED

        # Atomic compare-and-swap: only transition if the row is still
        # in the expected EVALUATING state for this attempt. A single
        # conditional UPDATE catches all races with sweep_stuck_claims
        # and stale/duplicate SQS deliveries (including messages from
        # earlier attempts). Zero rows affected → skip.
        with transaction.atomic():
            updated = Nomination.objects.filter(
                pk=nomination_id,
                status=NominationStatus.EVALUATING,
                evaluation_attempts=evaluation_attempts,
            ).update(status=new_status)
            if not updated:
                current = Nomination.objects.filter(
                    pk=nomination_id,
                ).values("status", "evaluation_attempts").first()
                logger.warning(
                    "Ignoring %s result for nomination %s: row changed "
                    "(current=%s, message_attempt=%s).",
                    "success" if is_success else "failure",
                    nomination_id,
                    current,
                    evaluation_attempts,
                )
                continue

            if is_success:
                data = body["data"]
                curator_notes = data.get("curator_notes", {})
                _, created = OrganizationEvaluation.objects.get_or_create(
                    nomination_id=nomination_id,
                    defaults={
                        "evaluation_data": data,
                        "ai_model": data.get("evaluated_by", ""),
                        "ai_recommendation": curator_notes.get(
                            "recommendation", "",
                        ),
                        "ai_confidence": curator_notes.get("confidence"),
                    },
                )
                if created:
                    processed += 1
                else:
                    logger.info(
                        "Evaluation already exists for nomination %s; "
                        "skipping duplicate result.",
                        nomination_id,
                    )
            else:
                failed += 1

    logger.info("Processed %d, failed %d result(s).", processed, failed)
    return {"status": "ok", "processed": processed, "failed": failed}
