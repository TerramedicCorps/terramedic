from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass
class CsvParseResult:
    rows: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


REQUIRED_COLUMNS = {"url", "category"}


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
    existing_urls: set[str],
    valid_categories: set[str],
) -> str | dict[str, Any]:
    """Return a parsed row dict on success, or an error string on failure."""
    if not url:
        return f"Row {row_num}: URL is empty."
    if not _is_valid_url(url):
        return f"Row {row_num}: Invalid URL '{url}'."
    if url in seen_urls:
        return f"Row {row_num}: Duplicate URL '{url}'."
    if url in existing_urls:
        return f"Row {row_num}: URL '{url}' already exists as a nomination."

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
    check_existing: bool = False,
) -> CsvParseResult:
    result = CsvParseResult()

    reader = csv.DictReader(file)
    if reader.fieldnames is None:
        result.errors.append("Empty file or missing header row.")
        return result

    # Normalize headers to lowercase
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

    existing_urls: set[str] = set()
    if check_existing:
        from terramedic.nominations.models import Nomination

        existing_urls = set(Nomination.objects.values_list("url", flat=True))

    from terramedic.organizations.models import Category

    valid_categories: set[str] = {c.value for c in Category}
    seen_urls: set[str] = set()

    for row_num, row in enumerate(reader, start=2):
        url = (row.get(url_col) or "").strip()
        raw_category = (row.get(category_col) or "").strip()

        validated = _validate_row(
            row_num, url, raw_category, seen_urls, existing_urls, valid_categories,
        )
        if isinstance(validated, str):
            result.errors.append(validated)
        else:
            seen_urls.add(url)
            result.rows.append(validated)

    return result
