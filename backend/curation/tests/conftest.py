"""Skip curation tests when optional dependencies are not installed."""

import pytest

try:
    import anthropic  # noqa: F401
    import bs4  # type: ignore[import-untyped]  # noqa: F401
    import httpx  # noqa: F401
    import jsonschema  # type: ignore[import-untyped]  # noqa: F401
except ImportError:
    pytest.skip(
        "curation optional dependencies not installed (poetry install --with curation)",
        allow_module_level=True,
    )
