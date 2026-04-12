import ipaddress
from datetime import datetime
from typing import Annotated

from ninja import Schema
from pydantic import HttpUrl, StringConstraints, field_validator

from terramedic.organizations.models import Category

MAX_URL_LENGTH = 2048
MAX_NOTES_LENGTH = 2000


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
        # Blocks literal private IPs and "localhost". DNS rebinding variants
        # (e.g. 127.0.0.1.nip.io) are not caught — acceptable for a nomination
        # form since the URL is not fetched server-side at submission time.
        hostname = v.host or ""
        # Strip brackets from IPv6 addresses (e.g. "[::1]" -> "::1")
        if hostname.startswith("[") and hostname.endswith("]"):
            hostname = hostname[1:-1]
        if hostname in ("localhost",):
            msg = "Private or internal URLs are not allowed."
            raise ValueError(msg)
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local:
                msg = "Private or internal URLs are not allowed."
                raise ValueError(msg)
        except ValueError as exc:
            if "Private or internal" in str(exc):
                raise
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
