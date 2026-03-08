from __future__ import annotations

from typing import Any

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import HttpRequest
from ninja import Query, Router
from ninja.errors import HttpError

from terramedic.organizations.models import Organization
from terramedic.organizations.schemas import OrganizationOut

router = Router()


def _serialize_org(
    org: Organization,
) -> dict[str, Any]:
    # Manual serialization needed because django-parler translated fields
    # (description, action_text) require accessing the active language on the
    # model instance; django-ninja's ModelSchema cannot resolve these.
    return {
        "id": org.pk,
        "name": org.name,
        "description": org.description,
        "action_text": org.action_text,
        "website_url": org.website_url,
        "image_url": org.image_url,
        "category": org.category,
        "tags": list(org.tags.values_list("name", flat=True)),
        "sort_order": org.sort_order,
    }


@router.get("/", response=list[OrganizationOut], auth=None)
def list_organizations(
    request: HttpRequest,
    category: str | None = Query(None),  # noqa: B008
) -> list[dict[str, Any]]:
    qs = Organization.objects.filter(
        is_active=True,
    ).prefetch_related("tags")

    if category:
        qs = qs.filter(category=category)

    return [_serialize_org(org) for org in qs]


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
        .prefetch_related("tags")
        .order_by("distance")
    )

    return [_serialize_org(org) for org in qs]


@router.get("/{org_id}/", response=OrganizationOut, auth=None)
def get_organization(
    request: HttpRequest,
    org_id: int,
) -> dict[str, Any]:
    try:
        org = (
            Organization.objects.filter(is_active=True)
            .prefetch_related("tags")
            .get(pk=org_id)
        )
    except Organization.DoesNotExist as exc:
        raise HttpError(404, "Organization not found") from exc

    return _serialize_org(org)
