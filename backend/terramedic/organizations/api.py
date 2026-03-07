from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.http import HttpRequest
from ninja import Query, Router

from terramedic.organizations.models import Organization
from terramedic.organizations.schemas import OrganizationOut

router = Router()


def _serialize_org(
    org: Organization,
) -> dict:
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
) -> list[dict]:
    qs = Organization.objects.filter(
        is_active=True,
    ).prefetch_related("tags")

    if category:
        qs = qs.filter(category=category)

    return [_serialize_org(org) for org in qs]


@router.get("/nearby/", response=list[OrganizationOut], auth=None)
def nearby_organizations(
    request: HttpRequest,
    lat: float = Query(...),  # noqa: B008
    lng: float = Query(...),  # noqa: B008
    radius: float = Query(..., description="Radius in km"),  # noqa: B008
) -> list[dict]:
    point = Point(lng, lat, srid=4326)
    radius_m = radius * 1000

    qs = (
        Organization.objects.filter(
            is_active=True,
            location__isnull=False,
            location__distance_lte=(point, radius_m),
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
) -> dict:
    try:
        org = (
            Organization.objects.filter(is_active=True)
            .prefetch_related("tags")
            .get(pk=org_id)
        )
    except Organization.DoesNotExist as exc:
        from ninja.errors import HttpError

        raise HttpError(404, "Organization not found") from exc

    return _serialize_org(org)
