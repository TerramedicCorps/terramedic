from django.contrib import admin

from terramedic.nominations.models import Nomination


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "url",
        "status",
        "confirmation_id",
        "submitted_at",
    ]
    list_filter = ["status"]
    search_fields = ["url", "confirmation_id"]
    readonly_fields = [
        "confirmation_id",
        "ip_hash",
        "submitted_at",
    ]
