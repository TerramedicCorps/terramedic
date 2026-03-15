"""Tests for the GA4 Data API metrics script."""

from __future__ import annotations

from unittest.mock import MagicMock

from scripts.ga_metrics import (
    build_report_requests,
    format_reports,
    parse_report_response,
)


class TestParseReportResponse:
    def test_parses_dimensions_and_metrics(self) -> None:
        response = MagicMock()
        response.dimension_headers = [MagicMock(name="pagePath")]
        # MagicMock uses `name` internally, so set it explicitly
        response.dimension_headers[0].name = "pagePath"
        response.metric_headers = [
            MagicMock(name="screenPageViews"),
            MagicMock(name="activeUsers"),
        ]
        response.metric_headers[0].name = "screenPageViews"
        response.metric_headers[1].name = "activeUsers"

        row = MagicMock()
        row.dimension_values = [MagicMock(value="/")]
        row.metric_values = [MagicMock(value="150"), MagicMock(value="80")]
        response.rows = [row]

        result = parse_report_response("topPages", response)

        assert result["name"] == "topPages"
        assert len(result["rows"]) == 1
        assert result["rows"][0]["dimensions"] == {"pagePath": "/"}
        assert result["rows"][0]["metrics"] == {
            "screenPageViews": "150",
            "activeUsers": "80",
        }

    def test_handles_no_dimensions(self) -> None:
        response = MagicMock()
        response.dimension_headers = []
        response.metric_headers = [MagicMock(), MagicMock()]
        response.metric_headers[0].name = "activeUsers"
        response.metric_headers[1].name = "sessions"

        row = MagicMock()
        row.dimension_values = []
        row.metric_values = [MagicMock(value="200"), MagicMock(value="350")]
        response.rows = [row]

        result = parse_report_response("overview", response)

        assert result["rows"][0]["dimensions"] == {}
        assert result["rows"][0]["metrics"] == {"activeUsers": "200", "sessions": "350"}

    def test_handles_empty_rows(self) -> None:
        response = MagicMock()
        response.dimension_headers = [MagicMock()]
        response.dimension_headers[0].name = "country"
        response.metric_headers = [MagicMock()]
        response.metric_headers[0].name = "activeUsers"
        response.rows = []

        result = parse_report_response("geography", response)
        assert result["rows"] == []

    def test_handles_none_rows(self) -> None:
        response = MagicMock()
        response.dimension_headers = []
        response.metric_headers = []
        response.rows = None

        result = parse_report_response("empty", response)
        assert result["rows"] == []


class TestBuildReportRequests:
    def test_default_date_range(self) -> None:
        requests = build_report_requests("123456")

        assert len(requests) > 0
        for item in requests:
            dr = item["request"]["date_ranges"]
            assert dr == [{"start_date": "30daysAgo", "end_date": "today"}]
            assert item["request"]["property"] == "properties/123456"

    def test_custom_date_range(self) -> None:
        requests = build_report_requests(
            "123456", start_date="2026-01-01", end_date="2026-03-15",
        )

        for item in requests:
            dr = item["request"]["date_ranges"]
            assert dr == [{"start_date": "2026-01-01", "end_date": "2026-03-15"}]

    def test_includes_all_report_names(self) -> None:
        requests = build_report_requests("123456")
        names = [r["name"] for r in requests]

        assert "overview" in names
        assert "top_pages" in names
        assert "traffic_sources" in names
        assert "organic_search" in names
        assert "geography" in names
        assert "devices" in names
        assert "custom_events" in names
        assert "daily_trend" in names


class TestFormatReports:
    def test_formats_overview(self) -> None:
        reports = [
            {
                "name": "overview",
                "rows": [
                    {
                        "dimensions": {},
                        "metrics": {"activeUsers": "200", "sessions": "350"},
                    },
                ],
            },
        ]
        output = format_reports(reports)

        assert "OVERVIEW" in output
        assert "activeUsers" in output
        assert "200" in output

    def test_formats_table_report(self) -> None:
        reports = [
            {
                "name": "top_pages",
                "rows": [
                    {
                        "dimensions": {"pagePath": "/"},
                        "metrics": {"screenPageViews": "150"},
                    },
                    {
                        "dimensions": {"pagePath": "/about"},
                        "metrics": {"screenPageViews": "50"},
                    },
                ],
            },
        ]
        output = format_reports(reports)

        assert "TOP_PAGES" in output
        assert "/" in output
        assert "/about" in output

    def test_formats_rate_as_percentage(self) -> None:
        reports = [
            {
                "name": "overview",
                "rows": [{"dimensions": {}, "metrics": {"engagementRate": "0.75"}}],
            },
        ]
        output = format_reports(reports)
        assert "75.0%" in output

    def test_formats_duration(self) -> None:
        reports = [
            {
                "name": "overview",
                "rows": [
                    {"dimensions": {}, "metrics": {"averageSessionDuration": "125"}},
                ],
            },
        ]
        output = format_reports(reports)
        assert "2m 5s" in output

    def test_handles_empty_report(self) -> None:
        reports = [{"name": "geography", "rows": []}]
        output = format_reports(reports)

        assert "GEOGRAPHY" in output
        assert "No data available" in output
