from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from parler.models import TranslatableModel, TranslatedFields

from terramedic.organizations.models.category import Category
from terramedic.organizations.models.organization import Organization

_http_url_validator = URLValidator(schemes=["http", "https"])


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
        # HTTP(S), preventing unsafe browser schemes.
        action_url=models.URLField(blank=True, default="", max_length=500),
    )

    class Meta:
        unique_together = [("organization", "category")]
        ordering = ["sort_order", "category__slug"]
        verbose_name_plural = "organization categories"

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.category.slug}"

    def clean(self) -> None:
        """Enforce safe CTA URLs and 501(c)(3) donate compliance.

        Every non-blank translated CTA URL must be an absolute HTTP(S)
        destination. Parler's translated fields are not covered by Django's
        normal model ``full_clean()``, so this explicit check prevents script
        and data URLs from reaching the public card ``href``.

        Terramedic must not deep-link into another org's donation flow,
        because doing so functionally constitutes fundraising for them.
        ``_normalize_donate_action_url`` in the curation layer rewrites
        donate ``action_url`` to the homepage on every evaluation, but
        this ``clean()`` is the second line of defense — admin saves and
        the curation write path (``_write_category_copy`` calls
        ``full_clean``) get the same enforcement, so a hand-edited deep
        donation link can't slip past the legal check.

        Blank ``action_url`` is permitted; the API serializer falls
        back to ``organization.website_url`` (the homepage), which is
        also compliant. A trailing-slash difference from the homepage is
        tolerated (``https://x.org`` and ``https://x.org/`` are the same
        page); a genuine donation deep link has a path beyond the domain
        and is still rejected.

        ``action_url`` is translated per language and the API serves
        every translation, so *all* translations are checked — saved
        rows and unsaved in-memory edits alike — not just the active
        language. Otherwise a deep link in a non-active translation
        would pass validation while still being served to
        matching-locale clients.
        """
        super().clean()
        if self.pk is None:
            # Querying the reverse translations manager requires a saved
            # master row. New admin forms still have their current unsaved
            # translation in Parler's cache, so validate that language.
            language_codes = [self.get_current_language()]
        else:
            language_codes = self.get_available_languages(
                include_unsaved=True,
            )

        translated_urls: list[tuple[str, str]] = []
        for language_code in language_codes:
            action_url = (
                self.get_translation(language_code).action_url or ""
            )
            if not action_url:
                continue
            try:
                _http_url_validator(action_url)
            except ValidationError as exc:
                raise ValidationError({
                    "action_url": (
                        "CTA URL must use http or https; got "
                        f"{action_url!r} for language {language_code!r}."
                    ),
                }) from exc
            translated_urls.append((language_code, action_url))

        if self.category_id != "donate" or self.organization_id is None:
            # Without an organization there is no homepage to check;
            # clean_fields() reports the missing FK as a normal
            # ValidationError instead of this method crashing with
            # RelatedObjectDoesNotExist on the dereference below.
            return
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
