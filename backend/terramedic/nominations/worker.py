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
from django.db.models import F

from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import should_skip_url
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
    queue_url = os.environ["EVALUATION_REQUESTS_QUEUE_URL"]
    sqs = boto3.client("sqs")

    nominations = list(
        Nomination.objects.filter(
            status=NominationStatus.QUEUED,
        ).order_by("submitted_at")[:limit],
    )

    dispatched = 0
    skipped = 0

    for nomination in nominations:
        # Atomic claim: only proceed if still queued.
        claimed = Nomination.objects.filter(
            pk=nomination.pk,
            status=NominationStatus.QUEUED,
        ).update(
            status=NominationStatus.EVALUATING,
            evaluation_attempts=F("evaluation_attempts") + 1,
        )
        if not claimed:
            continue
        nomination.refresh_from_db()

        if should_skip_url(nomination.url):
            nomination.status = NominationStatus.PENDING
            nomination.evaluation_attempts -= 1
            nomination.save(
                update_fields=["status", "evaluation_attempts"],
            )
            skipped += 1
            continue

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

    logger.info(
        "Dispatched %d, skipped %d of %d nomination(s).",
        dispatched, skipped, len(nominations),
    )
    return {"status": "ok", "dispatched": dispatched, "skipped": skipped}


def _handle_results(event: dict[str, Any]) -> dict[str, Any]:
    """Process evaluation results from SQS."""
    processed = 0
    failed = 0

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        nomination_id = body["nomination_id"]
        evaluation_attempts = body.get("evaluation_attempts", 1)

        try:
            nomination = Nomination.objects.get(pk=nomination_id)
        except Nomination.DoesNotExist:
            logger.warning("Nomination %s not found, skipping", nomination_id)
            continue

        if body.get("success"):
            data = body["data"]
            curator_notes = data.get("curator_notes", {})
            _, created = OrganizationEvaluation.objects.get_or_create(
                nomination=nomination,
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
            if evaluation_attempts >= _MAX_RETRY_ATTEMPTS:
                nomination.status = NominationStatus.FAILED
            else:
                nomination.status = NominationStatus.QUEUED
            nomination.save(update_fields=["status"])
            failed += 1

    logger.info("Processed %d, failed %d result(s).", processed, failed)
    return {"status": "ok", "processed": processed, "failed": failed}
