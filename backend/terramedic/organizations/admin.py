from django.contrib import admin
from parler.admin import TranslatableAdmin

from terramedic.organizations.models import Organization, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Organization)
class OrganizationAdmin(TranslatableAdmin):
    list_display = ["name", "category", "sort_order", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name"]
    list_editable = ["sort_order", "is_active"]
