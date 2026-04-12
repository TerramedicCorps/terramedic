import io
import logging

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import URLPattern, path, reverse

from terramedic.nominations.csv_import import parse_nominations_csv
from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.skip_checks import build_skip_urls
from terramedic.organizations.models import Category

logger = logging.getLogger(__name__)


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
    change_list_template = "admin/nominations/nomination/change_list.html"
    actions = ["evaluate_nominations"]

    @admin.action(
        description="Queue selected nominations for AI evaluation",
    )
    def evaluate_nominations(
        self,
        request: HttpRequest,
        queryset: QuerySet[Nomination],
    ) -> None:
        to_queue: list[Nomination] = []
        skipped_count = 0

        pending = [
            n for n in queryset
            if n.status == NominationStatus.PENDING
        ]
        skipped_count += len(queryset) - len(pending)

        skip_urls = build_skip_urls({n.url for n in pending})

        for nomination in pending:
            if nomination.url in skip_urls:
                skipped_count += 1
                continue

            nomination.status = NominationStatus.QUEUED
            nomination.evaluation_attempts = 0
            to_queue.append(nomination)

        if to_queue:
            Nomination.objects.bulk_update(
                to_queue, ["status", "evaluation_attempts"],
            )
            self.message_user(
                request,
                f"Queued {len(to_queue)} nomination(s) for evaluation. "
                "Processing will begin within a few minutes.",
                messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Skipped {skipped_count} nomination(s) "
                "(not pending, already evaluated, or in cooldown).",
                messages.INFO,
            )

    def get_urls(self) -> list[URLPattern]:
        custom_urls = [
            path(
                "upload-csv/",
                self.admin_site.admin_view(self.upload_csv_view),
                name="nominations_nomination_upload_csv",
            ),
        ]
        return custom_urls + super().get_urls()

    def upload_csv_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_add_permission(request):
            raise PermissionDenied
        if request.method == "POST":
            return self._handle_csv_upload(request)

        context = {
            **self.admin_site.each_context(request),
            "title": "Upload CSV",
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/nominations/nomination/upload_csv.html",
            context,
        )

    def _handle_csv_upload(self, request: HttpRequest) -> HttpResponse:
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            return self._render_with_errors(request, ["No file was uploaded."])

        if not (csv_file.name or "").lower().endswith(".csv"):
            return self._render_with_errors(
                request,
                ["Please upload a CSV file."],
            )

        max_size = 256 * 1024  # 256 KB
        if csv_file.size and csv_file.size > max_size:
            return self._render_with_errors(
                request,
                ["CSV file exceeds the 256 KB size limit."],
            )

        try:
            text = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return self._render_with_errors(
                request,
                [
                    "Could not read the file. "
                    "Please save it as UTF-8 encoded CSV.",
                ],
            )
        valid_categories = set(
            Category.objects.values_list("slug", flat=True),
        )
        result = parse_nominations_csv(
            io.StringIO(text),
            valid_categories=valid_categories,
            check_existing=True,
        )

        if result.errors:
            return self._render_with_errors(request, result.errors)

        nominations = [
            Nomination(
                url=row["url"],
                categories=row["categories"],
                ip_hash=None,
                notes=(
                    "Imported via CSV upload by "
                    f"{getattr(request.user, 'username', 'unknown')}."
                ),
            )
            for row in result.rows
        ]
        Nomination.objects.bulk_create(nominations)

        messages.success(
            request,
            f"Successfully imported {len(nominations)} nomination(s).",
        )
        return HttpResponseRedirect(
            reverse("admin:nominations_nomination_changelist"),
        )

    def _render_with_errors(
        self,
        request: HttpRequest,
        errors: list[str],
    ) -> TemplateResponse:
        context = {
            **self.admin_site.each_context(request),
            "title": "Upload CSV",
            "opts": self.model._meta,
            "errors": errors,
        }
        return TemplateResponse(
            request,
            "admin/nominations/nomination/upload_csv.html",
            context,
        )
