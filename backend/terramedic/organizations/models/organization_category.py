from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from parler.models import TranslatableModel, TranslatedFields

from terramedic.core.web_urls import (
    is_safe_web_url,
    is_same_site_web_url,
)
from terramedic.organizations.models.category import Category
from terramedic.organizations.models.organization import Organization

_ACTION_URL_MAX_LENGTH = 500
_http_url_validator = URLValidator(schemes=["http", "https"])


def _validate_action_url(
    action_url: str,
    language_code: str,
    website_url: str | None,
) -> None:
    """Validate one translated CTA URL against storage and site rules."""
    if len(action_url) > _ACTION_URL_MAX_LENGTH:
        raise ValidationError({
            "action_url": (
                "CTA URL must be at most "
                f"{_ACTION_URL_MAX_LENGTH} characters; got "
                f"{len(action_url)} for language {language_code!r}."
            ),
        })
    try:
        _http_url_validator(action_url)
    except ValidationError as exc:
        raise ValidationError({
            "action_url": (
                "CTA URL must use http or https; got "
                f"{action_url!r} for language {language_code!r}."
            ),
        }) from exc
    if not is_safe_web_url(action_url):
        raise ValidationError({
            "action_url": (
                "CTA URL must be a public http or https URL "
                f"without credentials; got {action_url!r} for "
                f"language {language_code!r}."
            ),
        })
    if website_url and not is_same_site_web_url(action_url, website_url):
        raise ValidationError({
            "action_url": (
                "CTA URL must belong to the organization's website; "
                f"got {action_url!r} for language {language_code!r}."
            ),
        })


class OrganizationCategory(TranslatableModel):
    """Through model carrying per-(org, category) copy.

    One Organization can appear under multiple Terramedic pathways
    (donate, volunteer, resource, everyday, career). The "why donate"
    pitch rarely reads the same as the "why volunteer" pitch, so each
    join row carries its own translated description and action_text.
    ``Organization.description`` remains the general fallback used in
    multi-category contexts (nearby, unfiltered listing).
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="category_entries",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="organization_entries",
    )
    sort_order = models.IntegerField(default=0)

    translations = TranslatedFields(
        description=models.TextField(blank=True, default=""),
        action_text=models.CharField(max_length=80, blank=True, default=""),
        # action_url is the page the action_text CTA links to. Per
        # 501(c)(3) compliance, when ``category.slug == "donate"`` this
        # must equal ``organization.website_url`` (the homepage); the
        # curation layer normalizes that and ``clean()`` enforces it on
        # admin saves. ``clean()`` also restricts every pathway URL to
        # the organization's public HTTP(S) site, preventing unsafe
        # browser schemes, local destinations, and unrelated hosts.
        action_url=models.URLField(
            blank=True,
            default="",
            max_length=_ACTION_URL_MAX_LENGTH,
        ),
    )

    class Meta:
        unique_together = [("organization", "category")]
        ordering = ["sort_order", "category__slug"]
        verbose_name_plural = "organization categories"

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.category.slug}"

    def clean(self) -> None:
        """Enforce safe CTA URLs and 501(c)(3) donate compliance.

        Two responsibilities, one per helper: validate every translated
        CTA URL as a public, same-site HTTP(S) destination, then — for
        donate rows — require the homepage so Terramedic never deep-links
        into another org's donation flow. This runs on admin saves and on
        the curation write path (``_write_category_copy`` calls
        ``full_clean``), the second line of defense behind
        ``_normalize_donate_action_url`` in the curation layer.
        """
        super().clean()
        translated_urls = self._validated_translated_action_urls()
        # Without an organization there is no homepage to check;
        # clean_fields() reports the missing FK as a normal
        # ValidationError instead of this method crashing with
        # RelatedObjectDoesNotExist on the dereference below.
        if self.category_id == "donate" and self.organization_id is not None:
            self._enforce_donate_homepage(translated_urls)

    def _validated_translated_action_urls(self) -> list[tuple[str, str]]:
        """Validate every non-blank translated CTA URL; return (lang, url).

        Parler's translated fields are not covered by Django's normal
        model ``full_clean()``, so each translation is checked explicitly —
        saved rows and unsaved in-memory edits alike, not just the active
        language — preventing script/data URLs, local hosts, unrelated
        destinations, and overlong values from reaching the card. Blank
        ``action_url`` is permitted; the API serializer falls back to
        ``organization.website_url`` (the compliant homepage).
        """
        if self.pk is None:
            # Querying the reverse translations manager requires a saved
            # master row. New admin forms still have their current unsaved
            # translation in Parler's cache, so validate that language.
            language_codes = [self.get_current_language()]
        else:
            language_codes = self.get_available_languages(
                include_unsaved=True,
            )
        website_url = (
            self.organization.website_url
            if self.organization_id is not None
            else None
        )
        translated_urls: list[tuple[str, str]] = []
        for language_code in language_codes:
            action_url = (
                self.get_translation(language_code).action_url or ""
            )
            if not action_url:
                continue
            _validate_action_url(action_url, language_code, website_url)
            translated_urls.append((language_code, action_url))
        return translated_urls

    def _enforce_donate_homepage(
        self, translated_urls: list[tuple[str, str]],
    ) -> None:
        """Reject any donate CTA that is not the org's homepage.

        A trailing-slash difference is tolerated (``https://x.org`` and
        ``https://x.org/`` are the same page); a genuine donation deep
        link has a path beyond the domain and is rejected in every
        translation, so a link in a non-active language can't slip past.
        """
        homepage = self.organization.website_url or ""
        for language_code, action_url in translated_urls:
            if action_url.rstrip("/") != homepage.rstrip("/"):
                raise ValidationError({
                    "action_url": (
                        "donate CTA must link to the org's homepage, "
                        "not a deep donation page (Terramedic "
                        f"501(c)(3) compliance). Expected {homepage!r}"
                        f", got {action_url!r} for language "
                        f"{language_code!r}."
                    ),
                })
