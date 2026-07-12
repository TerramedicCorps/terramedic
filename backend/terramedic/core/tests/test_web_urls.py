"""Unit tests for the authoritative web-URL safety helpers.

``web_urls`` is the single source of truth for "is this a public,
organization-owned HTTP(S) URL", relied on by the curation validator, the
API serializer, and the ``OrganizationCategory`` model (and mirrored
approximately on the client). These pin the subtle boundaries — credential
stripping, reserved-IP and local-suffix rejection, and same-site vs
parent/look-alike matching — directly rather than only through callers.
"""

import pytest

from terramedic.core.web_urls import (
    is_safe_web_url,
    is_same_site_web_url,
    web_hostname,
)


class TestWebHostname:
    def test_returns_normalized_lowercased_host(self) -> None:
        assert web_hostname("https://Example.ORG/some/path") == "example.org"

    def test_strips_trailing_dot(self) -> None:
        assert web_hostname("https://example.org./x") == "example.org"

    def test_accepts_http_and_https(self) -> None:
        assert web_hostname("http://example.org") == "example.org"
        assert web_hostname("https://example.org") == "example.org"

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.org",
            "javascript:alert(1)",
            "mailto:hi@example.org",
            "data:text/html,x",
        ],
    )
    def test_rejects_non_http_schemes(self, url: str) -> None:
        assert web_hostname(url) is None

    @pytest.mark.parametrize(
        "url",
        [
            "https://user:pass@example.org",
            "https://user@example.org",
            "https://:pass@example.org",
        ],
    )
    def test_rejects_embedded_credentials(self, url: str) -> None:
        assert web_hostname(url) is None

    def test_rejects_bare_localhost(self) -> None:
        assert web_hostname("http://localhost/admin") is None

    def test_rejects_single_label_host(self) -> None:
        # No dot and not an IP: not a routable public domain.
        assert web_hostname("http://intranet/admin") is None

    @pytest.mark.parametrize(
        "host",
        [
            "box.home",
            "site.example",
            "svc.internal",
            "x.invalid",
            "printer.lan",
            "dev.local",
            "api.localhost",
            "unit.test",
        ],
    )
    def test_rejects_local_host_suffixes(self, host: str) -> None:
        assert web_hostname(f"https://{host}/p") is None

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",  # loopback
            "10.0.0.1",  # private
            "192.168.1.1",  # private
            "172.16.0.1",  # private
            "169.254.0.1",  # link-local
            "0.0.0.0",  # unspecified
            "[::1]",  # IPv6 loopback
            "[fd00::1]",  # IPv6 unique-local
            "[fe80::1]",  # IPv6 link-local
        ],
    )
    def test_rejects_reserved_ip_literals(self, ip: str) -> None:
        assert web_hostname(f"http://{ip}/x") is None

    @pytest.mark.parametrize(
        "host",
        [
            "127.1",  # short-form loopback -> 127.0.0.1
            "10.1",  # short-form private -> 10.0.0.1
            "192.168.1",  # 3-part short form -> 192.168.0.1
            "0x7f.0.0.1",  # hex loopback
            "0177.0.0.1",  # octal loopback
        ],
    )
    def test_rejects_disguised_short_form_ip_literals(self, host: str) -> None:
        # Resolvers expand these to loopback/private ranges, but
        # ipaddress.ip_address() only recognizes canonical dotted quads, so
        # the plain "has a dot" heuristic used to let them through as domains.
        assert web_hostname(f"http://{host}/x") is None

    @pytest.mark.parametrize(
        "host",
        [
            "exa mple.org",  # space
            "exam_ple.org",  # underscore
            "-example.org",  # leading hyphen
            "example-.org",  # trailing hyphen
            "ex..ample.org",  # empty label
        ],
    )
    def test_rejects_malformed_dns_labels(self, host: str) -> None:
        # Python's "idna" codec does not reject STD3-invalid ASCII labels,
        # so these must be caught by explicit label validation.
        assert web_hostname(f"https://{host}/p") is None

    def test_accepts_numeric_and_hyphenated_labels(self) -> None:
        # Digits and interior hyphens are valid; only an all-numeric TLD or
        # a malformed label is rejected.
        assert web_hostname("https://1.example.org") == "1.example.org"
        assert web_hostname("https://web3.example.org") == "web3.example.org"
        assert (
            web_hostname("https://rainforest-alliance.org")
            == "rainforest-alliance.org"
        )

    def test_accepts_globally_routable_ip_literal(self) -> None:
        # The rejection above is because those ranges are non-global, not
        # because IP literals are banned outright — a public IP is a valid
        # public host.
        assert web_hostname("http://8.8.8.8/x") == "8.8.8.8"

    def test_rejects_malformed_port(self) -> None:
        assert web_hostname("https://example.org:99999") is None

    def test_rejects_empty_and_schemeless(self) -> None:
        assert web_hostname("") is None
        assert web_hostname("example.org/path") is None


class TestIsSafeWebUrl:
    def test_true_for_public_domain(self) -> None:
        assert is_safe_web_url("https://example.org/x") is True

    def test_false_for_local_host(self) -> None:
        assert is_safe_web_url("http://localhost") is False

    def test_false_for_credentialed_url(self) -> None:
        assert is_safe_web_url("https://user:pass@example.org") is False


class TestIsSameSiteWebUrl:
    def test_exact_host_match(self) -> None:
        assert is_same_site_web_url(
            "https://example.org/give", "https://example.org",
        )

    def test_www_is_presentation_only(self) -> None:
        assert is_same_site_web_url(
            "https://www.example.org/x", "https://example.org",
        )
        assert is_same_site_web_url(
            "https://example.org/x", "https://www.example.org",
        )

    def test_subdomain_allowed(self) -> None:
        assert is_same_site_web_url(
            "https://jobs.example.org/openings", "https://example.org",
        )

    def test_parent_domain_rejected(self) -> None:
        # The nominated site is a subdomain; its parent is a different,
        # broader host and must not be treated as same-site.
        assert not is_same_site_web_url(
            "https://example.org", "https://jobs.example.org",
        )

    def test_lookalike_prefix_rejected(self) -> None:
        # ``notexample.org`` shares a suffix but is a distinct registrable
        # domain; a naive ``endswith("example.org")`` would wrongly accept.
        assert not is_same_site_web_url(
            "https://notexample.org", "https://example.org",
        )

    def test_lookalike_suffix_rejected(self) -> None:
        assert not is_same_site_web_url(
            "https://example.org.evil.com", "https://example.org",
        )

    def test_unrelated_host_rejected(self) -> None:
        assert not is_same_site_web_url(
            "https://evil.com/phish", "https://example.org",
        )

    def test_unsafe_value_rejected(self) -> None:
        assert not is_same_site_web_url(
            "https://user:pass@example.org", "https://example.org",
        )

    def test_unsafe_site_rejected(self) -> None:
        assert not is_same_site_web_url(
            "https://example.org", "http://localhost",
        )
