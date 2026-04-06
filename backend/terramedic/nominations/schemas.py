import ipaddress
from urllib.parse import urlparse

from ninja import Schema

from terramedic.organizations.models import Category

MAX_URL_LENGTH = 2048
MAX_NOTES_LENGTH = 2000


class NominationIn(Schema):
    url: str
    categories: list[str]
    notes: str = ""
    website: str = ""  # honeypot field — should always be empty

    def validate_url(self) -> str | None:
        """Return an error message if the URL is invalid, else None."""
        if not self.url:
            return "URL is required."
        if len(self.url) > MAX_URL_LENGTH:
            return f"URL must not exceed {MAX_URL_LENGTH} characters."
        if not (
            self.url.startswith("http://") or self.url.startswith("https://")
        ):
            return "URL must start with http:// or https://."
        parsed = urlparse(self.url)
        hostname = parsed.hostname or ""
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return "Private or internal URLs are not allowed."
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local:
                return "Private or internal URLs are not allowed."
        except ValueError:
            pass  # hostname is a domain name, not an IP
        return None

    def validate_categories(self) -> str | None:
        """Return an error message if categories are invalid, else None."""
        if not self.categories:
            return "At least one category is required."
        valid = set(Category.values)
        for cat in self.categories:
            if cat not in valid:
                return f"Invalid category: {cat}"
        return None

    def validate_notes(self) -> str | None:
        """Return an error message if notes exceed max length, else None."""
        if len(self.notes) > MAX_NOTES_LENGTH:
            return f"Notes must not exceed {MAX_NOTES_LENGTH} characters."
        return None


class NominationOut(Schema):
    confirmation_id: str


class NominationStatusOut(Schema):
    confirmation_id: str
    status: str
