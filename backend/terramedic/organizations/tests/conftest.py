import pytest

from terramedic.organizations.models import Organization


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
