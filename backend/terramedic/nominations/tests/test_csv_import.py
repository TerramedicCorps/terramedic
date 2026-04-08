import io

import pytest

from terramedic.nominations.csv_import import CsvParseResult, parse_nominations_csv
from terramedic.nominations.models import Nomination


def _make_csv(lines: list[str]) -> io.StringIO:
    return io.StringIO("\n".join(lines))


class TestParseNominationsCsvValid:
    def test_single_valid_row(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 1
        assert result.rows[0]["url"] == "https://example.org/"
        assert result.rows[0]["categories"] == ["volunteer"]
        assert result.errors == []

    def test_multiple_valid_rows(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,volunteer",
            "https://donate.org/,donate",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 2
        assert result.errors == []

    def test_multiple_categories_comma_separated(self) -> None:
        f = _make_csv([
            "url,category",
            'https://example.org/,"volunteer,donate"',
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 1
        assert set(result.rows[0]["categories"]) == {"volunteer", "donate"}
        assert result.errors == []

    def test_whitespace_trimmed(self) -> None:
        f = _make_csv([
            "url,category",
            "  https://example.org/  ,  volunteer  ",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 1
        assert result.rows[0]["url"] == "https://example.org/"
        assert result.rows[0]["categories"] == ["volunteer"]

    def test_returns_result_dataclass(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert isinstance(result, CsvParseResult)


class TestParseNominationsCsvErrors:
    def test_missing_url_column(self) -> None:
        f = _make_csv([
            "website,category",
            "https://example.org/,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "url" in result.errors[0].lower()

    def test_missing_category_column(self) -> None:
        f = _make_csv([
            "url,type",
            "https://example.org/,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "category" in result.errors[0].lower()

    def test_empty_file(self) -> None:
        f = _make_csv([""])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) >= 1

    def test_header_only(self) -> None:
        f = _make_csv(["url,category"])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert result.errors == []

    def test_invalid_url(self) -> None:
        f = _make_csv([
            "url,category",
            "not-a-url,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "row 2" in result.errors[0].lower()

    def test_invalid_category(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,invalid_cat",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "row 2" in result.errors[0].lower()

    def test_empty_url(self) -> None:
        f = _make_csv([
            "url,category",
            ",volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1

    def test_empty_category(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1

    def test_mixed_valid_and_invalid_rows(self) -> None:
        f = _make_csv([
            "url,category",
            "https://good.org/,volunteer",
            "bad-url,donate",
            "https://also-good.org/,career",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 2
        assert len(result.errors) == 1

    def test_duplicate_urls_reported(self) -> None:
        f = _make_csv([
            "url,category",
            "https://example.org/,volunteer",
            "https://example.org/,donate",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 1
        assert len(result.errors) == 1
        assert "duplicate" in result.errors[0].lower()

    def test_url_exceeding_max_length(self) -> None:
        long_url = "https://example.org/" + "a" * 2040
        f = _make_csv([
            "url,category",
            f"{long_url},volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "2048" in result.errors[0]

    def test_missing_cell_value_does_not_crash(self) -> None:
        """A row missing the trailing column should report an error, not 500."""
        f = _make_csv([
            "url,category",
            "https://example.org/",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1

    def test_one_valid_one_invalid_category_in_multi(self) -> None:
        """If a row has 'volunteer,bogus', it should error."""
        f = _make_csv([
            "url,category",
            'https://example.org/,"volunteer,bogus"',
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) == 1

    def test_case_insensitive_headers(self) -> None:
        f = _make_csv([
            "URL,Category",
            "https://example.org/,volunteer",
        ])
        result = parse_nominations_csv(f)
        assert len(result.rows) == 1
        assert result.errors == []


class TestParseNominationsCsvRowLimit:
    def test_exceeding_max_rows_returns_error(self) -> None:
        lines = ["url,category"] + [
            f"https://example{i}.org/,volunteer" for i in range(501)
        ]
        f = _make_csv(lines)
        result = parse_nominations_csv(f)
        assert len(result.rows) == 0
        assert len(result.errors) >= 1
        assert "500" in result.errors[0]

    def test_exactly_max_rows_succeeds(self) -> None:
        lines = ["url,category"] + [
            f"https://example{i}.org/,volunteer" for i in range(500)
        ]
        f = _make_csv(lines)
        result = parse_nominations_csv(f)
        assert len(result.rows) == 500
        assert result.errors == []


@pytest.mark.django_db
class TestParseNominationsCsvDbDuplicates:
    def test_duplicate_of_existing_nomination_reported(self) -> None:
        Nomination.objects.create(
            url="https://existing.org/",
            categories=["volunteer"],
            ip_hash="somehash",
        )
        f = _make_csv([
            "url,category",
            "https://existing.org/,donate",
        ])
        result = parse_nominations_csv(f, check_existing=True)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "already exists" in result.errors[0].lower()
