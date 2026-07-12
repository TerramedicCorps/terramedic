"""Pure helpers for validating public, organization-owned web URLs.

This is the authoritative implementation. A deliberately-approximate
client-side mirror lives in
``terramedic/src/lib/components/OrganizationCard.svelte``
(``isLocalHostname`` / ``safeActionUrl``) for defense in depth on the
raw ``website_url`` the API returns unsanitized; keep the local-suffix
list and reserved-IP ranges in sync when either changes.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_LOCAL_HOST_SUFFIXES = (
    ".home",
    ".example",
    ".internal",
    ".invalid",
    ".lan",
    ".local",
    ".localhost",
    ".test",
)

# One LDH label: letters/digits/hyphen, 1-63 chars, no leading/trailing hyphen.
_DNS_LABEL = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")


def _is_dns_hostname(hostname: str) -> bool:
    """Return whether *hostname* is a valid multi-label domain name.

    Requires at least two LDH labels and a non-numeric top-level label.
    The all-numeric-TLD rule rejects legacy short-form IPv4 addresses such
    as ``127.1`` or ``10.1`` that resolvers expand to loopback/private
    ranges (``ipaddress`` only recognizes canonical dotted quads); the LDH
    rule rejects spaces, underscores, and edge hyphens that Python's
    ``idna`` codec passes through but browsers reject.
    """
    labels = hostname.split(".")
    if len(labels) < 2 or labels[-1].isdigit():
        return False
    return all(_DNS_LABEL.match(label) for label in labels)


def web_hostname(value: str) -> str | None:
    """Return a normalized hostname for a safe HTTP(S) destination.

    Credentials and hosts that are explicitly local/private are rejected.
    Domain names are checked syntactically here; callers that fetch a URL must
    still resolve DNS immediately before the request to defend against DNS
    rebinding.
    """
    try:
        parsed = urlsplit(value)
        # Accessing ``port`` raises for malformed/out-of-range values.
        _ = parsed.port
    except (TypeError, ValueError):
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None

    try:
        hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None
    if hostname == "localhost" or hostname.endswith(_LOCAL_HOST_SUFFIXES):
        return None

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return hostname if _is_dns_hostname(hostname) else None
    return hostname if address.is_global else None


def is_safe_web_url(value: str) -> bool:
    """Return whether *value* is an absolute, non-local HTTP(S) URL."""
    return web_hostname(value) is not None


def is_same_site_web_url(value: str, site_url: str) -> bool:
    """Return whether *value* belongs to *site_url* or its subdomains.

    A leading ``www.`` is treated as presentation-only. Subdomains of the
    nominated host are allowed so an org can use destinations such as
    ``jobs.example.org`` while unrelated hosts and parent domains remain
    blocked.
    """
    value_host = web_hostname(value)
    site_host = web_hostname(site_url)
    if value_host is None or site_host is None:
        return False

    value_site = value_host.removeprefix("www.")
    expected_site = site_host.removeprefix("www.")
    return value_site == expected_site or value_site.endswith(f".{expected_site}")
