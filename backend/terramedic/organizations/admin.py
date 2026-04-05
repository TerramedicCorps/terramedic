from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from parler.admin import TranslatableAdmin

from terramedic.organizations.models import (
    Category,
    Organization,
    OrganizationEvaluation,
    ReviewStatus,
    Tag,
)


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


def _create_org_from_evaluation(
    evaluation: OrganizationEvaluation,
) -> Organization:
    """Create an Organization from evaluation data."""
    data = evaluation.evaluation_data
    meta = data.get("org_metadata", {})
    accessibility = data.get("accessibility", {})

    categories = accessibility.get("categories", [])
    valid_values = set(Category.values)
    first = categories[0] if categories else None
    category = first if first in valid_values else Category.RESOURCE

    org = Organization(
        name=meta.get("name", ""),
        website_url=meta.get("website_url", ""),
        image_url=meta.get("image_url", ""),
        category=category,
        is_active=True,
    )
    org.set_current_language("en")
    org.description = meta.get("description", "")
    action_text = f"Support {meta.get('name', 'this organization')}"
    org.action_text = action_text[:100]
    org.save()
    return org


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
    list_filter = ["status"]
    search_fields: list[str] = []
    readonly_fields = [
        "evaluation_data",
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

        # SDG alignment
        sdgs = data.get("sdg_alignment", [])
        if sdgs:
            parts.append("<h3>SDG Alignment</h3><ul>")
            for item in sdgs:
                sdg = escape(str(item.get("sdg", "?")))
                evidence = escape(str(item.get("evidence", "")))
                parts.append(
                    f"<li><strong>SDG {sdg}</strong>: "
                    f"{evidence}</li>",
                )
            parts.append("</ul>")

        # Evidence of work
        activities = data.get("evidence_of_work", [])
        if activities:
            parts.append("<h3>Evidence of Work</h3><ul>")
            for item in activities:
                activity = escape(str(item.get("activity", "")))
                act_type = escape(str(item.get("type", "")))
                parts.append(
                    f"<li><strong>{act_type}</strong>: "
                    f"{activity}</li>",
                )
            parts.append("</ul>")

        # Evidence score
        score_data = data.get("evidence_score", {})
        if score_data:
            score = escape(str(score_data.get("score", "?")))
            rationale = escape(
                str(score_data.get("rationale", "")),
            )
            parts.append(
                f"<h3>Evidence Score: {score} / 5</h3>"
                f"<p>{rationale}</p>",
            )

        # Curator notes
        notes = data.get("curator_notes", {})
        if notes:
            rec = escape(str(notes.get("recommendation", "")))
            note_text = escape(str(notes.get("notes", "")))
            flags = notes.get("flags", [])
            parts.append("<h3>Curator Notes</h3>")
            parts.append(
                f"<p><strong>Recommendation:</strong> {rec}</p>",
            )
            if note_text:
                parts.append(f"<p>{note_text}</p>")
            if flags:
                escaped = ", ".join(escape(str(f)) for f in flags)
                parts.append(
                    f"<p><strong>Flags:</strong> {escaped}</p>",
                )

        html = "\n".join(parts) if parts else "<p>No data.</p>"
        return mark_safe(html)  # noqa: S308

    @admin.action(description="Approve selected evaluations")
    def approve_evaluations(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> None:
        for evaluation in queryset:
            if evaluation.status == ReviewStatus.APPROVED:
                continue
            org = _create_org_from_evaluation(evaluation)
            evaluation.organization = org
            evaluation.status = ReviewStatus.APPROVED
            evaluation.reviewer = request.user  # type: ignore[assignment]
            evaluation.reviewed_at = timezone.now()
            evaluation.save()
        self.message_user(
            request,
            f"Approved {queryset.count()} evaluation(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected evaluations")
    def reject_evaluations(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> None:
        now = timezone.now()
        for evaluation in queryset:
            if evaluation.status == ReviewStatus.REJECTED:
                continue
            evaluation.status = ReviewStatus.REJECTED
            evaluation.reviewer = request.user  # type: ignore[assignment]
            evaluation.reviewed_at = now
            evaluation.save()
        self.message_user(
            request,
            f"Rejected {queryset.count()} evaluation(s).",
            messages.SUCCESS,
        )
