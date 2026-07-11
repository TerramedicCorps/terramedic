from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Prefetch
from django.http import HttpRequest
from django.utils.translation import get_language
from ninja import Query, Router
from ninja.errors import HttpError

from terramedic.organizations.models import (
    Organization,
    OrganizationCategory,
)
from terramedic.organizations.schemas import OrganizationOut

router = Router()


def _safe_web_url(value: str) -> str:
    """Return *value* only when it is an absolute HTTP(S) URL."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return value


def _translated(
    entry: OrganizationCategory, field: str,
) -> str:
    """Pull a translated field off the prefetched through row.

    Prefers the active language (django-parler honors
    ``Accept-Language`` via middleware); falls back to the project's
    ``LANGUAGE_CODE`` when absent so default-language content isn't
    silently dropped for non-matching requests. Following
    ``settings.LANGUAGE_CODE`` (rather than a hardcoded ``"en"``)
    means if the project's default language ever changes, this
    follows along without a code edit.
    """
    active = get_language() or settings.LANGUAGE_CODE
    fallback = settings.LANGUAGE_CODE
    translations = list(entry.translations.all())  # type: ignore[attr-defined]
    for translation in translations:
        if translation.language_code == active:
            return str(getattr(translation, field, "") or "")
    if fallback != active:
        for translation in translations:
            if translation.language_code == fallback:
                return str(getattr(translation, field, "") or "")
    return ""


def _serialize_org(
    org: Organization,
    category_slug: str | None = None,
) -> dict[str, Any]:
    """Serialize an org to the public schema shape.

    When *category_slug* is provided, prefer the per-(org, category)
    translated description, action_text, and action_url. Effective
    action_text precedence:

      1. ``OrganizationCategory.action_text`` (translated).
      2. ``Category.default_action_text``.
      3. empty string — frontend decides.

    ``action_url`` falls back to ``org.website_url`` when the
    per-category row is blank, so cards always have somewhere to send
    the reader. The donate slug is enforced (in curation + admin
    ``clean()``) to be the homepage already, so the fallback
    coincides with the compliance rule.

    When *category_slug* is ``None`` (multi-category contexts like the
    nearby map or unfiltered listing), the general
    ``org.description`` is returned and ``action_text`` /
    ``action_url`` stay empty.
    """
    entries: list[OrganizationCategory] = list(
        org.category_entries.all(),  # type: ignore[attr-defined]
    )
    description = org.description
    action_text = ""
    action_url = ""
    sort_order = org.sort_order

    if category_slug:
        entry = next(
            (e for e in entries if e.category_id == category_slug),
            None,
        )
        if entry is not None:
            per_cat_desc = _translated(entry, "description")
            if per_cat_desc:
                description = per_cat_desc
            action_text = _translated(entry, "action_text")
            if not action_text:
                action_text = entry.category.default_action_text
            action_url = _safe_web_url(_translated(entry, "action_url"))
            if not action_url:
                action_url = _safe_web_url(org.website_url)
            sort_order = entry.sort_order

    return {
        "id": org.pk,
        "name": org.name,
        "description": description,
        "action_text": action_text,
        "action_url": action_url,
        "website_url": org.website_url,
        "image_url": org.image_url,
        "categories": sorted(e.category_id for e in entries),
        # Sort the prefetched cache in Python rather than calling
        # order_by() — order_by re-queries because it builds a fresh
        # queryset that bypasses the prefetch_related result.
        "tags": sorted(tag.name for tag in org.tags.all()),
        "sort_order": sort_order,
    }


def _prefetch_category_entries() -> Prefetch:
    """Prefetch through rows with translations + category so
    ``_serialize_org`` resolves per-category copy and the
    default_action_text fallback without N+1 queries."""
    return Prefetch(
        "category_entries",
        queryset=OrganizationCategory.objects.select_related(
            "category",
        ).prefetch_related("translations"),
    )


@router.get("/", response=list[OrganizationOut], auth=None)
def list_organizations(
    request: HttpRequest,
    category: str | None = Query(None),  # noqa: B008
) -> list[dict[str, Any]]:
    qs = Organization.objects.filter(
        is_active=True,
    ).prefetch_related("tags", _prefetch_category_entries())

    if category:
        # (organization, category) is unique_together on the through
        # model, so the filtered JOIN yields at most one row per org —
        # no .distinct() needed, and the ordering stays deterministic.
        qs = qs.filter(category_entries__category_id=category)
        qs = qs.order_by("category_entries__sort_order", "sort_order", "name")

    return [_serialize_org(org, category_slug=category) for org in qs]


@router.get("/nearby/", response=list[OrganizationOut], auth=None)
def nearby_organizations(
    request: HttpRequest,
    lat: float = Query(..., ge=-90, le=90),  # noqa: B008
    lng: float = Query(..., ge=-180, le=180),  # noqa: B008
    radius: float = Query(..., description="Radius in km", ge=0.1, le=500),  # noqa: B008
) -> list[dict[str, Any]]:
    point = Point(lng, lat, srid=4326)

    qs = (
        Organization.objects.filter(
            is_active=True,
            location__isnull=False,
            location__distance_lte=(point, D(km=radius)),
        )
        .annotate(distance=Distance("location", point))
        .prefetch_related("tags", _prefetch_category_entries())
        .order_by("distance")
    )

    return [_serialize_org(org) for org in qs]


@router.get("/{org_id}/", response=OrganizationOut, auth=None)
def get_organization(
    request: HttpRequest,
    org_id: int,
    category: str | None = Query(None),  # noqa: B008
) -> dict[str, Any]:
    try:
        org = (
            Organization.objects.filter(is_active=True)
            .prefetch_related("tags", _prefetch_category_entries())
            .get(pk=org_id)
        )
    except Organization.DoesNotExist as exc:
        raise HttpError(404, "Organization not found") from exc

    return _serialize_org(org, category_slug=category)
