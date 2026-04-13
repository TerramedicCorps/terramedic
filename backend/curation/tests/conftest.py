"""Skip curation tests when dependencies are not installed."""

import pytest

try:
    import anthropic  # noqa: F401
    import bs4  # type: ignore[import-untyped]  # noqa: F401
    import httpx  # noqa: F401
    import jsonschema  # type: ignore[import-untyped]  # noqa: F401
except ImportError:
    pytest.skip(
        "curation dependencies not installed (poetry install)",
        allow_module_level=True,
    )
