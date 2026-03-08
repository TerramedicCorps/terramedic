"""URL configuration for terramedic project."""

from django.contrib import admin
from django.urls import path

from terramedic.core.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
