import pytest
from django.core.cache import cache

from terramedic.organizations.models import Organization


@pytest.fixture(autouse=True)
def _clear_parler_cache() -> None:
    """Clear Django's cache between tests.

    pytest-django rolls back the DB between tests but does not clear
    LocMemCache. django-parler stores translations there keyed by
    (model, pk, language); since SQLite reuses primary keys after a
    rollback, the stale cache can return a rolled-back test's
    translation for the next test's fresh row.
    """
    cache.clear()


@pytest.fixture
def org() -> Organization:
    o = Organization(
        name="Test Org",
        website_url="https://example.com",
    )
    o.set_current_language("en")
    o.description = "A test organization."
    o.save()
    return o
