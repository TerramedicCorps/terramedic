from __future__ import annotations

import hashlib
import uuid
from datetime import timedelta

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from terramedic.nominations.models import Nomination
from terramedic.nominations.schemas import (
    NominationIn,
    NominationOut,
    NominationStatusOut,
)

router = Router()

RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = timedelta(hours=1)


def _hash_ip(ip: str) -> str:
    """Hash an IP address with salted SHA-256 for privacy-preserving rate limiting."""
    from django.conf import settings

    return hashlib.sha256(f"{settings.SECRET_KEY}{ip}".encode()).hexdigest()


def _get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request, respecting X-Forwarded-For.

    Assumes the app is behind a trusted reverse proxy (AWS API Gateway)
    that sets X-Forwarded-For. If accessed directly, this header can be
    spoofed to bypass rate limiting.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _is_rate_limited(ip_hash: str) -> bool:
    """Check if this IP hash has exceeded the rate limit."""
    cutoff = timezone.now() - RATE_LIMIT_WINDOW
    recent_count = Nomination.objects.filter(
        ip_hash=ip_hash,
        submitted_at__gte=cutoff,
    ).count()
    return recent_count >= RATE_LIMIT_MAX


@router.post("/", response={201: NominationOut}, auth=None)
def create_nomination(
    request: HttpRequest,
    payload: NominationIn,
) -> tuple[int, NominationOut]:
    # Rate limiting (before honeypot so bots can't bypass it)
    client_ip = _get_client_ip(request)
    ip_hash = _hash_ip(client_ip)

    if _is_rate_limited(ip_hash):
        response = JsonResponse(
            {"detail": "Rate limit exceeded. Try again later."},
            status=429,
        )
        response["Retry-After"] = str(int(RATE_LIMIT_WINDOW.total_seconds()))
        return response

    # Honeypot check: if the hidden field is filled, silently discard
    if payload.website:
        fake_id = str(uuid.uuid4())
        return 201, NominationOut(confirmation_id=fake_id)

    nomination = Nomination.objects.create(
        url=str(payload.url),
        categories=payload.categories,
        notes=payload.notes,
        ip_hash=ip_hash,
    )

    return 201, NominationOut(
        confirmation_id=str(nomination.confirmation_id),
    )


@router.get(
    "/{confirmation_id}/status/",
    response=NominationStatusOut,
    auth=None,
)
def get_nomination_status(
    request: HttpRequest,
    confirmation_id: uuid.UUID,
) -> NominationStatusOut:
    try:
        nomination = Nomination.objects.get(confirmation_id=confirmation_id)
    except Nomination.DoesNotExist as exc:
        raise HttpError(404, "Nomination not found") from exc

    return NominationStatusOut(
        confirmation_id=str(nomination.confirmation_id),
        status=nomination.status,
    )
