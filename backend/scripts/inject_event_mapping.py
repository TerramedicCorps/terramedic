#!/usr/bin/env python3
"""Append AWS_EVENT_MAPPING to the generated Zappa settings file.

Zappa's handler routes non-API events (SQS, SNS, DynamoDB, Kinesis) by
looking up the event source ARN in ``settings.AWS_EVENT_MAPPING``. That
dict is only populated when a stage declares ``events`` in its Zappa
config, which in turn makes Zappa manage the event source mapping —
conflicting with Terraform, which owns the mapping for the nomination
evaluation pipeline.

This script sidesteps the conflict by populating ``AWS_EVENT_MAPPING``
directly in the ``zappa_settings.py`` baked into the Docker image. The
same image serves the API (``dev``), the worker (``dev-worker``), and
the evaluator (``dev-evaluator``), so the mapping includes both queues
and each Lambda routes the events it actually receives.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

EVALUATOR_HANDLER = (
    "terramedic.nominations.evaluator.handle_evaluation_request"
)
WORKER_HANDLER = (
    "terramedic.nominations.worker.process_evaluation_queue"
)


def sqs_url_to_arn(queue_url: str) -> str:
    """Convert an SQS queue URL to its ARN.

    URL: https://sqs.{region}.amazonaws.com/{account}/{queue-name}
    ARN: arn:aws:sqs:{region}:{account}:{queue-name}
    """
    host_and_path = queue_url.split("://", 1)[-1]
    host, account, name = host_and_path.split("/", 2)
    region = host.split(".")[1]
    return f"arn:aws:sqs:{region}:{account}:{name}"


def build_event_mapping(
    requests_queue_url: str,
    results_queue_url: str,
) -> dict[str, str]:
    """Build AWS_EVENT_MAPPING from queue URLs.

    Skips empty URLs so local builds without the pipeline configured
    produce an empty mapping (and a no-op append).
    """
    mapping: dict[str, str] = {}
    if requests_queue_url:
        mapping[sqs_url_to_arn(requests_queue_url)] = EVALUATOR_HANDLER
    if results_queue_url:
        mapping[sqs_url_to_arn(results_queue_url)] = WORKER_HANDLER
    return mapping


def append_event_mapping(
    settings_path: Path,
    mapping: dict[str, str],
) -> None:
    """Append an ``AWS_EVENT_MAPPING = {...}`` block to the file.

    Idempotent: returns early if the file already contains an
    ``AWS_EVENT_MAPPING`` assignment, so re-runs don't accumulate
    duplicate blocks.
    """
    if not mapping:
        return
    if "AWS_EVENT_MAPPING" in settings_path.read_text():
        return
    lines = [
        "",
        "# Injected by scripts/inject_event_mapping.py for SQS routing.",
        "AWS_EVENT_MAPPING = {",
    ]
    for arn, handler in mapping.items():
        lines.append(f"    {arn!r}: {handler!r},")
    lines.append("}")
    lines.append("")
    with settings_path.open("a") as f:
        f.write("\n".join(lines))


def require_mapping_in_ci(mapping: dict[str, str]) -> None:
    """In CI, refuse to deploy without any SQS routing entries.

    Silently skipping would reproduce the exact runtime failure this
    script is designed to prevent ("Cannot find a function to process
    the triggered event") the next time an SQS event arrives.
    """
    if not os.environ.get("CI"):
        return
    if mapping:
        return
    sys.stderr.write(
        "Error: CI is set but neither EVALUATION_REQUESTS_QUEUE_URL "
        "nor EVALUATION_RESULTS_QUEUE_URL is defined. The worker and "
        "evaluator Lambdas would fail SQS routing at runtime.\n",
    )
    sys.exit(1)


def main() -> None:
    settings_path = (
        Path(__file__).parent.parent / "zappa_settings.py"
    )
    if not settings_path.exists():
        sys.stderr.write(
            f"Error: {settings_path} not found. "
            "Run `zappa save-python-settings-file` first.\n",
        )
        sys.exit(1)

    mapping = build_event_mapping(
        os.environ.get("EVALUATION_REQUESTS_QUEUE_URL", ""),
        os.environ.get("EVALUATION_RESULTS_QUEUE_URL", ""),
    )
    require_mapping_in_ci(mapping)
    append_event_mapping(settings_path, mapping)
    if mapping:
        sys.stdout.write(
            f"Injected AWS_EVENT_MAPPING with {len(mapping)} entries "
            f"into {settings_path}\n",
        )
    else:
        sys.stdout.write(
            "No queue URLs set; skipping AWS_EVENT_MAPPING injection.\n",
        )


if __name__ == "__main__":
    main()
