import logging
from typing import Any

from django.contrib import admin, messages
from django.db import connection
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from parler.admin import TranslatableAdmin

from terramedic.organizations.models import (
    SDG,
    Category,
    EngagementOpportunity,
    FocusArea,
    OperatingRegion,
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
    Skill,
    Tag,
)

logger = logging.getLogger(__name__)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["slug", "label"]
    search_fields = ["slug", "label"]


@admin.register(SDG)
class SDGAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["number", "name"]
    search_fields = ["name"]
    ordering = ["number"]


@admin.register(OperatingRegion)
class OperatingRegionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["name", "country_code", "region_code", "continent"]
    list_filter = ["continent"]
    search_fields = ["name", "country_code"]


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["name", "reviewed", "reviewed_by", "reviewed_at"]
    list_filter = ["reviewed"]
    search_fields = ["name"]
    readonly_fields = ["reviewed_by", "reviewed_at"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["name", "reviewed", "reviewed_by", "reviewed_at"]
    list_filter = ["reviewed"]
    search_fields = ["name"]
    readonly_fields = ["reviewed_by", "reviewed_at"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(EngagementOpportunity)
class EngagementOpportunityAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "organization",
        "engagement_type",
        "time_commitment",
        "location_bound",
    ]
    list_filter = ["engagement_type", "time_commitment", "location_bound"]
    search_fields = ["organization__name", "description"]


@admin.register(Organization)
class OrganizationAdmin(TranslatableAdmin):
    list_display = ["name", "categories_display", "sort_order", "is_active"]
    list_filter = ["categories", "is_active"]
    search_fields = ["name"]
    list_editable = ["sort_order", "is_active"]

    def get_queryset(
        self, request: HttpRequest,
    ) -> QuerySet[Organization]:
        # TranslatableAdmin.get_queryset is untyped, so give mypy the
        # concrete type before chaining prefetch_related.
        qs: QuerySet[Organization] = super().get_queryset(request)
        return qs.prefetch_related("categories")

    @admin.display(description="Categories")
    def categories_display(self, obj: Organization) -> str:
        slugs = list(obj.categories.values_list("slug", flat=True))
        return ", ".join(slugs) if slugs else "—"


def _create_org_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> Organization:
    """Create an Organization from evaluation data.

    Assigns every valid category from the evaluation's
    ``accessibility.categories`` array. If none are valid
    (for example, all entries are ``"other"``), the
    organization is filed under ``resource`` as a fallback
    so it still shows up somewhere.
    """
    data = evaluation.evaluation_data
    meta = data.get("org_metadata", {})
    accessibility = data.get("accessibility", {})

    requested = accessibility.get("categories", [])
    valid_categories = list(Category.objects.filter(slug__in=requested))
    if not valid_categories:
        valid_categories = list(Category.objects.filter(slug="resource"))

    org = Organization(
        name=meta.get("name", ""),
        website_url=meta.get("website_url", ""),
        image_url=meta.get("image_url", ""),
        is_active=True,
    )
    org.set_current_language("en")
    org.description = meta.get("description", "")
    action_text = f"Support {meta.get('name', 'this organization')}"
    org.action_text = action_text[:100]
    org.save()
    org.categories.set(valid_categories)
    return org


def _render_sources(sources: list[dict[str, str]]) -> str:
    """Render a sources array as a small HTML list."""
    if not sources:
        return ""
    items: list[str] = []
    for src in sources:
        raw_url = str(src.get("source_url", ""))
        url = escape(raw_url)
        excerpt = escape(str(src.get("excerpt", "")))
        if raw_url.startswith(("http://", "https://")):
            line = f'<a href="{url}">{url}</a>'
        else:
            line = url
        if excerpt:
            line += f" — <em>{excerpt}</em>"
        items.append(f"<li>{line}</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _render_sdg_section(data: dict[str, Any]) -> str:
    """Render SDG alignment as HTML."""
    sdgs = data.get("sdg_alignment", [])
    if not sdgs:
        return ""
    parts = ["<h3>SDG Alignment</h3><ul>"]
    for item in sdgs:
        sdg = escape(str(item.get("sdg", "?")))
        evidence = escape(str(item.get("evidence", "")))
        sources_html = _render_sources(item.get("sources", []))
        parts.append(
            f"<li><strong>SDG {sdg}</strong>: "
            f"{evidence}{sources_html}</li>",
        )
    parts.append("</ul>")
    return "\n".join(parts)


def _render_evidence_section(data: dict[str, Any]) -> str:
    """Render evidence of work as HTML."""
    activities = data.get("evidence_of_work", [])
    if not activities:
        return ""
    parts = ["<h3>Evidence of Work</h3><ul>"]
    for item in activities:
        activity = escape(str(item.get("activity", "")))
        act_type = escape(str(item.get("type", "")))
        sources_html = _render_sources(item.get("sources", []))
        parts.append(
            f"<li><strong>{act_type}</strong>: "
            f"{activity}{sources_html}</li>",
        )
    parts.append("</ul>")
    return "\n".join(parts)


def _render_score_section(data: dict[str, Any]) -> str:
    """Render evidence score as HTML."""
    score_data = data.get("evidence_score", {})
    if not score_data:
        return ""
    score = escape(str(score_data.get("score", "?")))
    rationale = escape(str(score_data.get("rationale", "")))
    return (
        f"<h3>Evidence Score: {score} / 5</h3>"
        f"<p>{rationale}</p>"
    )


def _render_curator_notes(data: dict[str, Any]) -> str:
    """Render curator notes as HTML."""
    notes = data.get("curator_notes", {})
    if not notes:
        return ""
    parts: list[str] = []
    rec = escape(str(notes.get("recommendation", "")))
    note_text = escape(str(notes.get("notes", "")))
    flags = notes.get("flags", [])
    parts.append("<h3>Curator Notes</h3>")
    parts.append(f"<p><strong>Recommendation:</strong> {rec}</p>")
    if note_text:
        parts.append(f"<p>{note_text}</p>")
    if flags:
        escaped = ", ".join(escape(str(f)) for f in flags)
        parts.append(f"<p><strong>Flags:</strong> {escaped}</p>")
    return "\n".join(parts)


def _render_eval_history(data: dict[str, Any]) -> str:
    """Render evaluation history as HTML."""
    history = data.get("evaluation_history", [])
    if not history:
        return ""
    parts = ["<h3>Evaluation History</h3><ul>"]
    for entry in history:
        ver = escape(str(entry.get("prompt_version", "?")))
        sc = escape(str(entry.get("score", "?")))
        rec = escape(str(entry.get("recommendation", "?")))
        at = escape(str(entry.get("evaluated_at", "")))
        parts.append(f"<li>v{ver}: {sc}/5, {rec} ({at})</li>")
    parts.append("</ul>")
    return "\n".join(parts)


class EvidenceScoreFilter(admin.SimpleListFilter):
    title = "evidence score"
    parameter_name = "evidence_score"

    def lookups(
        self,
        _request: HttpRequest,
        _model_admin: Any,
    ) -> list[tuple[str, str]]:
        return [
            ("high", "High (4-5)"),
            ("medium", "Medium (3)"),
            ("low", "Low (1-2)"),
        ]

    def queryset(
        self,
        _request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> QuerySet[OrganizationEvaluation]:
        value = self.value()
        if value == "high":
            return queryset.filter(
                evaluation_data__evidence_score__score__gte=4,
            )
        if value == "medium":
            return queryset.filter(
                evaluation_data__evidence_score__score=3,
            )
        if value == "low":
            return queryset.filter(
                evaluation_data__evidence_score__score__lte=2,
            )
        return queryset


class CategoryFilter(admin.SimpleListFilter):
    title = "category"
    parameter_name = "eval_category"

    def lookups(
        self,
        _request: HttpRequest,
        _model_admin: Any,
    ) -> list[tuple[str, str]]:
        return list(Category.objects.values_list("slug", "label"))

    def queryset(
        self,
        _request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> QuerySet[OrganizationEvaluation]:
        value = self.value()
        if not value:
            return queryset
        if connection.vendor == "postgresql":
            return queryset.filter(
                evaluation_data__accessibility__categories__contains=[value],
            )
        # SpatiaLite does not support __contains on JSONField;
        # fall back to Python-side filtering.  This O(N) scan only
        # runs in local dev (SQLite); production uses PostgreSQL above.
        pks = [
            ev.pk
            for ev in queryset.iterator()
            if value
            in (
                ev.evaluation_data.get("accessibility", {}).get(
                    "categories",
                    [],
                )
            )
        ]
        return queryset.filter(pk__in=pks)


@admin.register(OrganizationEvaluation)
class OrganizationEvaluationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "org_name_display",
        "evidence_score_display",
        "recommendation_display",
        "sdg_display",
        "status",
        "reviewer",
        "reviewed_at",
    ]
    list_filter = ["status", EvidenceScoreFilter, CategoryFilter]
    # search_fields must be non-empty for Django to render the search
    # box.  The default icontains query on "status" is harmless but
    # unused — actual search logic lives in get_search_results below.
    search_fields = ["status"]
    readonly_fields = [
        "evaluation_data",
        "status",
        "created_at",
        "reviewed_at",
        "reviewer",
        "organization",
        "evaluation_detail",
    ]
    fieldsets = (
        (
            "Review",
            {
                "fields": (
                    "status",
                    "reviewer_reasoning",
                ),
                "description": (
                    "Use bulk actions to approve or reject."
                    " Status cannot be changed manually."
                ),
            },
        ),
        (
            "Evaluation Detail",
            {
                "fields": ("evaluation_detail",),
            },
        ),
        (
            "Raw Data",
            {
                "classes": ("collapse",),
                "fields": ("evaluation_data",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "organization",
                    "reviewer",
                    "reviewed_at",
                    "created_at",
                ),
            },
        ),
    )
    actions = ["approve_evaluations", "reject_evaluations"]

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        extra_context = extra_context or {}

        try:
            # Intentionally unfiltered: dashboard shows global stats
            # regardless of any active list filters.
            qs = OrganizationEvaluation.objects.all()
            extra_context["dashboard_stats"] = qs.aggregate(
                pending=Count("id", filter=Q(status=ReviewStatus.PENDING)),
                approved=Count("id", filter=Q(status=ReviewStatus.APPROVED)),
                rejected=Count("id", filter=Q(status=ReviewStatus.REJECTED)),
            )

            growth_qs = (
                qs.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month")
            )
            extra_context["growth_data"] = [
                {
                    "month": row["month"].strftime("%Y-%m"),
                    "count": row["count"],
                }
                for row in growth_qs
                if row["month"] is not None
            ]
        except Exception:  # noqa: BLE001
            logger.exception("Unable to load dashboard data")
            extra_context["dashboard_stats"] = {
                "pending": 0,
                "approved": 0,
                "rejected": 0,
            }
            extra_context["growth_data"] = []
            extra_context["dashboard_error"] = (
                "Unable to load dashboard data"
            )

        return super().changelist_view(request, extra_context)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
        search_term: str,
    ) -> tuple[QuerySet[OrganizationEvaluation], bool]:
        """Search by org name extracted from JSON data."""
        qs, use_distinct = super().get_search_results(
            request,
            queryset,
            search_term,
        )
        if search_term:
            qs |= queryset.filter(
                evaluation_data__org_metadata__name__icontains=search_term,
            )
        return qs, use_distinct

    @admin.display(description="Organization")
    def org_name_display(self, obj: OrganizationEvaluation) -> str:
        return obj.org_name

    @admin.display(description="Score")
    def evidence_score_display(self, obj: OrganizationEvaluation) -> str:
        score = obj.evidence_score_value
        return f"{score} / 5" if score is not None else "—"

    @admin.display(description="Recommendation")
    def recommendation_display(self, obj: OrganizationEvaluation) -> str:
        return obj.recommendation

    @admin.display(description="SDGs")
    def sdg_display(self, obj: OrganizationEvaluation) -> str:
        numbers = obj.sdg_numbers
        return ", ".join(f"SDG {n}" for n in numbers) if numbers else "—"

    @admin.display(description="Evaluation Detail")
    def evaluation_detail(self, obj: OrganizationEvaluation) -> str:
        """Render evaluation data as safe HTML for the detail page."""
        data = obj.evaluation_data or {}
        parts: list[str] = []

        prompt_ver = data.get("prompt_version")
        if prompt_ver:
            parts.append(
                "<p><strong>Prompt version:</strong> "
                f"{escape(str(prompt_ver))}</p>",
            )

        for renderer in (
            _render_sdg_section,
            _render_evidence_section,
            _render_score_section,
            _render_curator_notes,
            _render_eval_history,
        ):
            section = renderer(data)
            if section:
                parts.append(section)

        html = "\n".join(parts) if parts else "<p>No data.</p>"
        return mark_safe(html)  # noqa: S308

    @admin.action(description="Approve selected evaluations")
    def approve_evaluations(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> None:
        approved_count = 0
        for evaluation in queryset:
            if evaluation.status == ReviewStatus.APPROVED:
                continue
            org = evaluation.organization
            if org is None:
                org = _create_org_from_evaluation(evaluation)
            evaluation.organization = org
            evaluation.status = ReviewStatus.APPROVED
            evaluation.reviewer = request.user  # type: ignore[assignment]
            evaluation.reviewed_at = timezone.now()
            evaluation.save()
            approved_count += 1
        self.message_user(
            request,
            f"Approved {approved_count} evaluation(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected evaluations")
    def reject_evaluations(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> None:
        now = timezone.now()
        rejected_count = 0
        for evaluation in queryset:
            if evaluation.status != ReviewStatus.PENDING:
                continue
            evaluation.status = ReviewStatus.REJECTED
            evaluation.reviewer = request.user  # type: ignore[assignment]
            evaluation.reviewed_at = now
            evaluation.save()
            rejected_count += 1
        self.message_user(
            request,
            f"Rejected {rejected_count} evaluation(s).",
            messages.SUCCESS,
        )
