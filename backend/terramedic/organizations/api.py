from __future__ import annotations

from typing import Any

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


def _translated(
    entry: OrganizationCategory, field: str,
) -> str:
    """Pull a translated field off the prefetched through row.

    Prefers the active language (django-parler honors
    ``Accept-Language`` via middleware); falls back to English when
    absent so English defaults aren't silently dropped for non-en
    requests.
    """
    language = get_language() or "en"
    translations = list(entry.translations.all())  # type: ignore[attr-defined]
    for translation in translations:
        if translation.language_code == language:
            return str(getattr(translation, field, "") or "")
    for translation in translations:
        if translation.language_code == "en":
            return str(getattr(translation, field, "") or "")
    return ""


def _serialize_org(
    org: Organization,
    category_slug: str | None = None,
) -> dict[str, Any]:
    """Serialize an org to the public schema shape.

    When *category_slug* is provided, prefer the per-(org, category)
    translated description and action_text. Effective action_text
    precedence:

      1. ``OrganizationCategory.action_text`` (translated).
      2. ``Category.default_action_text``.
      3. empty string — frontend decides.

    When *category_slug* is ``None`` (multi-category contexts like the
    nearby map or unfiltered listing), the general
    ``org.description`` is returned and ``action_text`` stays empty.
    """
    entries: list[OrganizationCategory] = list(
        org.category_entries.all(),  # type: ignore[attr-defined]
    )
    description = org.description
    action_text = ""
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
            sort_order = entry.sort_order

    return {
        "id": org.pk,
        "name": org.name,
        "description": description,
        "action_text": action_text,
        "website_url": org.website_url,
        "image_url": org.image_url,
        "categories": sorted(e.category_id for e in entries),
        "tags": list(org.tags.order_by("name").values_list("name", flat=True)),
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
        qs = qs.filter(category_entries__category_id=category).distinct()
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
