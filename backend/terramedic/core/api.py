from django.http import HttpRequest
from ninja import NinjaAPI

from terramedic.organizations.api import router as organizations_router

api = NinjaAPI()

api.add_router("/organizations/", organizations_router)


@api.get("/health", auth=None)
def health_check(request: HttpRequest) -> dict:
    return {"status": "ok"}
