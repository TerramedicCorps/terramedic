import ipaddress
from datetime import datetime
from typing import Annotated
from urllib.parse import urlparse

from ninja import Schema
from pydantic import HttpUrl, StringConstraints, field_validator

from terramedic.organizations.models import Category

MAX_URL_LENGTH = 2048
MAX_NOTES_LENGTH = 2000


def is_private_or_internal_host(hostname: str) -> bool:
    """Return True if a hostname points at a non-public address.

    Catches literal private IPs, loopback, link-local, unspecified,
    multicast, reserved, and the ``localhost`` alias. DNS rebinding
    variants (e.g. ``127.0.0.1.nip.io``) are NOT caught here — that
    requires hostname resolution at fetch time.
    """
    if not hostname:
        return False
    # Strip brackets from IPv6 addresses (e.g. "[::1]" -> "::1")
    if hostname.startswith("[") and hostname.endswith("]"):
        hostname = hostname[1:-1]
    if hostname == "localhost":
        return True
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    # CPython's ``is_global`` returns True for multicast addresses
    # (224.0.0.0/4, ff00::/8), so we can't rely on ``not is_global``
    # alone. Reject every non-public range the evaluator should never
    # fetch.
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_unspecified
        or addr.is_multicast
        or addr.is_reserved
    )


def is_safe_http_url(url: str) -> bool:
    """Return True if ``url`` is a syntactically valid http(s) URL
    whose host is not in a private/internal range."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    return not is_private_or_internal_host(parsed.hostname or "")


class NominationIn(Schema):
    url: HttpUrl
    categories: list[str]
    notes: Annotated[str, StringConstraints(max_length=MAX_NOTES_LENGTH)] = ""
    website: str = ""  # honeypot field — should always be empty

    @field_validator("url")
    @classmethod
    def check_url_not_private(cls, v: HttpUrl) -> HttpUrl:
        # Explicit length check — StringConstraints may not apply to HttpUrl
        if len(str(v)) > MAX_URL_LENGTH:
            msg = f"URL must not exceed {MAX_URL_LENGTH} characters."
            raise ValueError(msg)
        if is_private_or_internal_host(v.host or ""):
            msg = "Private or internal URLs are not allowed."
            raise ValueError(msg)
        return v

    @field_validator("categories")
    @classmethod
    def check_categories(cls, v: list[str]) -> list[str]:
        if not v:
            msg = "At least one category is required."
            raise ValueError(msg)
        valid = set(Category.objects.values_list("slug", flat=True))
        for cat in v:
            if cat not in valid:
                msg = f"Invalid category: {cat}"
                raise ValueError(msg)
        return v


class NominationOut(Schema):
    confirmation_id: str


class NominationStatusOut(Schema):
    confirmation_id: str
    status: str
    display_url: str
    submitted_at: datetime
