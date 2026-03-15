#!/usr/bin/env python3
"""Pull Google Analytics 4 metrics via the Data API.

Prerequisites:
    1. poetry add google-analytics-data
    2. Enable "Google Analytics Data API" in Google Cloud Console
    3. Authenticate via: gcloud auth application-default login
    4. Set quota project: gcloud auth application-default set-quota-project <PROJECT_ID>
    5. Ensure your Google account has Viewer access on the GA4 property

Usage:
    python scripts/ga_metrics.py --property YOUR_PROPERTY_ID
    python scripts/ga_metrics.py --property YOUR_PROPERTY_ID \
        --start 2026-01-01 --end 2026-03-15
    python scripts/ga_metrics.py --property YOUR_PROPERTY_ID --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any


def parse_report_response(
    name: str, response: Any,
) -> dict[str, Any]:
    """Parse a GA4 RunReportResponse into a simpler dict structure."""
    dimension_headers = [h.name for h in (response.dimension_headers or [])]
    metric_headers = [h.name for h in (response.metric_headers or [])]

    rows: list[dict[str, Any]] = []
    for row in response.rows or []:
        dimensions = {
            dimension_headers[i]: val.value
            for i, val in enumerate(row.dimension_values or [])
        }
        metrics = {
            metric_headers[i]: val.value
            for i, val in enumerate(row.metric_values or [])
        }
        rows.append({"dimensions": dimensions, "metrics": metrics})

    return {"name": name, "rows": rows}


def build_report_requests(
    property_id: str,
    start_date: str = "30daysAgo",
    end_date: str = "today",
) -> list[dict[str, Any]]:
    """Build the report request dicts for our standard metrics suite."""
    date_range = {"start_date": start_date, "end_date": end_date}
    prop = f"properties/{property_id}"

    return [
        {
            "name": "overview",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "metrics": [
                    {"name": "activeUsers"},
                    {"name": "newUsers"},
                    {"name": "sessions"},
                    {"name": "screenPageViews"},
                    {"name": "engagementRate"},
                    {"name": "averageSessionDuration"},
                    {"name": "bounceRate"},
                ],
            },
        },
        {
            "name": "top_pages",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "pagePath"}],
                "metrics": [
                    {"name": "screenPageViews"},
                    {"name": "activeUsers"},
                ],
                "order_bys": [
                    {"metric": {"metric_name": "screenPageViews"}, "desc": True},
                ],
                "limit": 20,
            },
        },
        {
            "name": "traffic_sources",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "activeUsers"},
                ],
                "order_bys": [
                    {"metric": {"metric_name": "sessions"}, "desc": True},
                ],
            },
        },
        {
            "name": "organic_search",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "sessionSource"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "activeUsers"},
                ],
                "dimension_filter": {
                    "filter": {
                        "field_name": "sessionMedium",
                        "string_filter": {"value": "organic"},
                    },
                },
                "order_bys": [
                    {"metric": {"metric_name": "sessions"}, "desc": True},
                ],
            },
        },
        {
            "name": "geography",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "country"}],
                "metrics": [
                    {"name": "activeUsers"},
                    {"name": "sessions"},
                ],
                "order_bys": [
                    {"metric": {"metric_name": "activeUsers"}, "desc": True},
                ],
                "limit": 20,
            },
        },
        {
            "name": "devices",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "deviceCategory"}],
                "metrics": [
                    {"name": "activeUsers"},
                    {"name": "sessions"},
                ],
                "order_bys": [
                    {"metric": {"metric_name": "sessions"}, "desc": True},
                ],
            },
        },
        {
            "name": "custom_events",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "eventName"}],
                "metrics": [{"name": "eventCount"}],
                "dimension_filter": {
                    "filter": {
                        "field_name": "eventName",
                        "in_list_filter": {
                            "values": [
                                "section_view",
                                "newsletter_signup",
                                "contact_form_submit",
                                "donate_click",
                                "volunteer_click",
                                "image_view",
                            ],
                        },
                    },
                },
                "order_bys": [
                    {"metric": {"metric_name": "eventCount"}, "desc": True},
                ],
            },
        },
        {
            "name": "daily_trend",
            "request": {
                "property": prop,
                "date_ranges": [date_range],
                "dimensions": [{"name": "date"}],
                "metrics": [
                    {"name": "activeUsers"},
                    {"name": "sessions"},
                    {"name": "screenPageViews"},
                ],
                "order_bys": [{"dimension": {"dimension_name": "date"}}],
            },
        },
    ]


def _format_metric_value(key: str, value: str) -> str:
    """Format a metric value for human-readable output."""
    if "Rate" in key or "rate" in key:
        return f"{float(value) * 100:.1f}%"
    if "Duration" in key or "duration" in key:
        seconds = float(value)
        mins = int(seconds // 60)
        secs = round(seconds % 60)
        return f"{mins}m {secs}s"
    try:
        num = float(value)
        if num == math.floor(num):
            return f"{int(num):,}"
    except ValueError:
        pass
    return value


def format_reports(reports: list[dict[str, Any]]) -> str:
    """Format reports as a human-readable string."""
    sections: list[str] = []

    for report in reports:
        lines: list[str] = []
        lines.append(f"\n=== {report['name'].upper()} ===")

        rows = report["rows"]
        if not rows:
            lines.append("  No data available")
        elif not rows[0]["dimensions"]:
            for key, value in rows[0]["metrics"].items():
                lines.append(f"  {key}: {_format_metric_value(key, value)}")
        else:
            for row in rows:
                dim_str = " | ".join(row["dimensions"].values())
                metric_str = ", ".join(
                    f"{k}: {_format_metric_value(k, v)}"
                    for k, v in row["metrics"].items()
                )
                lines.append(f"  {dim_str}  —  {metric_str}")

        sections.append("\n".join(lines))

    return "\n".join(sections)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pull Google Analytics 4 metrics via the Data API.",
    )
    parser.add_argument(
        "--property",
        help="GA4 property ID (numeric). Env: GA4_PROPERTY_ID",
    )
    parser.add_argument(
        "--start",
        default="30daysAgo",
        help="Start date (YYYY-MM-DD or relative like 30daysAgo). Default: 30daysAgo",
    )
    parser.add_argument(
        "--end",
        default="today",
        help="End date (YYYY-MM-DD or relative like today). Default: today",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    property_id = args.property or os.environ.get("GA4_PROPERTY_ID")
    if not property_id:
        print(
            "Error: GA4 property ID required. "
            "Use --property <id> or set GA4_PROPERTY_ID env var.",
            file=sys.stderr,
        )
        print(
            "Find it in GA4 Admin > Property Settings (numeric ID, not G-XXXXXXX).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except ImportError:
        print(
            "Error: google-analytics-data package not installed.\n"
            "Install it with: poetry add google-analytics-data",
            file=sys.stderr,
        )
        sys.exit(1)

    client = BetaAnalyticsDataClient()

    report_defs = build_report_requests(
        property_id, start_date=args.start, end_date=args.end,
    )

    if not args.json:
        print(f"Fetching metrics for property {property_id}...")
        print(f"Date range: {args.start} to {args.end}\n")

    reports: list[dict[str, Any]] = []
    for item in report_defs:
        try:
            response = client.run_report(request=item["request"])
            reports.append(parse_report_response(item["name"], response))
        except Exception as exc:  # noqa: BLE001
            print(f"Error fetching {item['name']}: {exc}", file=sys.stderr)
            reports.append({"name": item["name"], "rows": []})

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(format_reports(reports))


if __name__ == "__main__":
    main()
