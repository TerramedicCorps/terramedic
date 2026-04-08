from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import TypedDict
from urllib.parse import urlparse

from terramedic.nominations.models import Nomination


class ParsedRow(TypedDict):
    url: str
    categories: list[str]


@dataclass
class CsvParseResult:
    """Callers must check ``errors`` before consuming ``rows``.

    When errors is non-empty, rows may contain partial results
    that should NOT be persisted.
    """

    rows: list[ParsedRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


REQUIRED_COLUMNS = ("url", "category")
MAX_ROWS = 500


def _is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _validate_row(
    row_num: int,
    url: str,
    raw_category: str,
    seen_urls: set[str],
    valid_categories: set[str],
) -> str | ParsedRow:
    """Return a parsed row dict on success, or an error string on failure."""
    if not url:
        return f"Row {row_num}: URL is empty."
    if not _is_valid_url(url):
        return f"Row {row_num}: Invalid URL '{url}'."
    if len(url) > 2048:
        return f"Row {row_num}: URL exceeds 2048 characters."
    if url in seen_urls:
        return f"Row {row_num}: Duplicate URL '{url}'."

    categories = [c.strip() for c in raw_category.split(",") if c.strip()]
    if not categories:
        return f"Row {row_num}: Category is empty."

    invalid = [c for c in categories if c not in valid_categories]
    if invalid:
        return f"Row {row_num}: Invalid category: {', '.join(invalid)}."

    return {"url": url, "categories": categories}


def parse_nominations_csv(
    file: io.StringIO,
    *,
    valid_categories: set[str],
    check_existing: bool = False,
) -> CsvParseResult:
    result = CsvParseResult()

    reader = csv.DictReader(file)
    if reader.fieldnames is None:
        result.errors.append("Empty file or missing header row.")
        return result

    normalized = {name.strip().lower(): name for name in reader.fieldnames}
    for required in REQUIRED_COLUMNS:
        if required not in normalized:
            result.errors.append(
                f"Missing required column: '{required}'. "
                f"Found columns: {', '.join(reader.fieldnames)}",
            )
            return result

    url_col = normalized["url"]
    category_col = normalized["category"]

    seen_urls: set[str] = set()

    for row_num, row in enumerate(reader, start=2):
        if row_num - 1 > MAX_ROWS:
            result.errors.append(
                f"CSV exceeds the maximum of {MAX_ROWS} rows.",
            )
            result.rows.clear()
            return result

        url = (row.get(url_col) or "").strip()
        raw_category = (row.get(category_col) or "").strip()

        validated = _validate_row(
            row_num, url, raw_category, seen_urls, valid_categories,
        )
        if isinstance(validated, str):
            result.errors.append(validated)
        else:
            seen_urls.add(url)
            result.rows.append(validated)

    if check_existing and result.rows:
        parsed_urls = {row["url"] for row in result.rows}
        existing_urls = set(
            Nomination.objects.filter(url__in=parsed_urls).values_list(
                "url", flat=True,
            ),
        )
        if existing_urls:
            result.errors.extend(
                f"URL '{url}' already exists as a nomination."
                for url in sorted(existing_urls)
            )
            result.rows = [
                row for row in result.rows if row["url"] not in existing_urls
            ]

    return result
