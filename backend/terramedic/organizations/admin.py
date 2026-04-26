import logging
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.db import connection, transaction
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import URLPattern, path
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from parler.admin import TranslatableAdmin, TranslatableTabularInline

from terramedic.organizations.evaluation_actions import (
    sync_org_categories_from_evaluation,
)
from terramedic.organizations.models import (
    SDG,
    Category,
    EngagementOpportunity,
    FocusArea,
    OperatingRegion,
    Organization,
    OrganizationCategory,
    OrganizationEvaluation,
    ReviewStatus,
    Skill,
    Tag,
)
from terramedic.organizations.services.ai_descriptions import (
    AIDescriptionError,
    draft_for_category,
)

logger = logging.getLogger(__name__)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["slug", "label", "default_action_text"]
    search_fields = ["slug", "label"]
    fields = ["slug", "label", "default_action_text"]


class OrganizationCategoryInline(TranslatableTabularInline):
    """Per-(org, category) editor for the Organization change form.

    Carries the pathway-specific description and action_text that the
    curation pipeline drafts for each category. Curators pick
    categories and edit their copy in the same place.
    """

    model = OrganizationCategory
    extra = 0
    fields = ["category", "sort_order", "description", "action_text"]
    autocomplete_fields = ["category"]


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


class CuratorTermAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Base admin for CuratorProposedTerm subclasses."""

    list_display = ["name", "reviewed", "reviewed_by", "reviewed_at"]
    list_filter = ["reviewed"]
    search_fields = ["name"]
    readonly_fields = ["reviewed_by", "reviewed_at"]

    def save_model(
        self,
        request: HttpRequest,
        obj: Any,
        _form: Any,
        _change: bool,
    ) -> None:
        obj.save(user=request.user)


@admin.register(FocusArea)
class FocusAreaAdmin(CuratorTermAdmin):
    pass


@admin.register(Skill)
class SkillAdmin(CuratorTermAdmin):
    pass


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
    inlines = [OrganizationCategoryInline]
    actions = ["generate_missing_descriptions"]
    change_form_template = (
        "admin/organizations/organization/change_form.html"
    )

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

    def get_urls(self) -> list[URLPattern]:
        # TranslatableAdmin.get_urls is untyped in django-stubs, so
        # pin the list type locally before concatenating.
        urls: list[URLPattern] = super().get_urls()
        custom: list[URLPattern] = [
            path(
                "<int:object_id>/generate-descriptions/",
                self.admin_site.admin_view(
                    require_POST(self.generate_descriptions_view),
                ),
                name="organizations_organization_generate_descriptions",
            ),
        ]
        return custom + urls

    def generate_descriptions_view(
        self, request: HttpRequest, object_id: int,
    ) -> HttpResponse:
        """Fill blank per-category copy on ``object_id`` via the AI.

        For each row, only the blank field(s) (in English) are
        overwritten — partial curator edits (e.g., a hand-written
        description with a blank action_text) are preserved. Rows
        with both fields populated are skipped entirely. The curation
        pipeline drafts ``category_copy`` on the initial evaluation,
        so for freshly-approved orgs this view typically reports
        "nothing to draft". Useful when a curator adds a new category
        manually after approval.
        """
        try:
            org = Organization.objects.get(pk=object_id)
        except Organization.DoesNotExist:
            messages.error(request, "Organization not found.")
            return redirect("admin:organizations_organization_changelist")

        drafted, skipped, errored = self._draft_blank_entries(org)

        if errored:
            messages.error(
                request,
                f"AI draft failed: {errored}",
            )
        elif drafted:
            messages.success(
                request,
                f"Drafted copy for {drafted} categor"
                f"{'y' if drafted == 1 else 'ies'}"
                f" ({skipped} already had copy).",
            )
        else:
            messages.info(
                request,
                "Nothing to draft — every category already has copy.",
            )

        return redirect(
            "admin:organizations_organization_change", object_id,
        )

    def _draft_blank_entries(
        self, org: Organization,
    ) -> tuple[int, int, str]:
        """Return ``(drafted, skipped, error_message)``.

        ``error_message`` is empty on success. An AIDescriptionError
        short-circuits the loop — admins get one clear flash instead
        of N noisy ones.
        """
        drafted = 0
        skipped = 0
        entries = (
            OrganizationCategory.objects.filter(organization=org)
            .select_related("category")
            .prefetch_related("translations")
        )
        for entry in entries:
            entry.set_current_language("en")
            desc = entry.safe_translation_getter(
                "description", default="", language_code="en",
            )
            action = entry.safe_translation_getter(
                "action_text", default="", language_code="en",
            )
            has_desc = bool((desc or "").strip())
            has_action = bool((action or "").strip())
            if has_desc and has_action:
                skipped += 1
                continue
            try:
                copy = draft_for_category(org, entry.category)
            except AIDescriptionError as exc:
                return drafted, skipped, str(exc)
            if not has_desc:
                entry.description = copy.description
            if not has_action:
                entry.action_text = copy.action_text
            entry.save()
            drafted += 1
        return drafted, skipped, ""

    @admin.action(description="Generate missing per-category descriptions")
    def generate_missing_descriptions(
        self,
        request: HttpRequest,
        queryset: QuerySet[Organization],
    ) -> None:
        """Changelist bulk action: draft blank copy across selected orgs."""
        total_drafted = 0
        total_skipped = 0
        failures: list[str] = []
        for org in queryset:
            drafted, skipped, err = self._draft_blank_entries(org)
            total_drafted += drafted
            total_skipped += skipped
            if err:
                failures.append(f"{org.name}: {err}")

        self.message_user(
            request,
            f"Drafted {total_drafted} row(s), skipped "
            f"{total_skipped} already populated.",
            messages.SUCCESS,
        )
        if failures:
            self.message_user(
                request,
                "Some orgs failed: " + "; ".join(failures),
                messages.ERROR,
            )


# Scoped CSS for the Evaluation Detail readonly field. Visually hides
# the redundant field label (the fieldset header already says
# "Evaluation Detail") while keeping it in the accessibility tree for
# screen readers via the standard "visually hidden" pattern. Flattens
# list nesting so sources sit one indent-level under their parent item
# instead of stacking three deep, and lets long URLs wrap inside the
# content column.
_EV_DETAIL_STYLE = """<style>
.field-evaluation_detail label {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.ev-detail { font-size: 13px; line-height: 1.45; }
.ev-detail h3 {
  margin: 1em 0 0.3em 0;
  padding-left: 0;
  font-size: 16px;
  font-weight: 600;
}
.ev-detail h3:first-of-type { margin-top: 0.25em; }
.ev-detail p { margin: 0.25em 0; }
.ev-detail .ev-meta { margin-bottom: 0.75em; }
.ev-detail .ev-item { margin: 0.4em 0 0.6em; }
.ev-detail .ev-sources { margin: 0.2em 0 0 1.25em; padding: 0; font-size: 0.88em; }
.ev-detail .ev-sources li {
  list-style: disc inside; margin: 0.1em 0;
  word-break: break-word; overflow-wrap: anywhere;
}
.ev-detail .ev-history { margin: 0.2em 0 0 1.25em; padding: 0; }
.ev-detail .ev-history li { list-style: disc inside; margin: 0.1em 0; }
</style>"""


def _render_sources(sources: list[dict[str, str]]) -> str:
    """Render a sources array as a small flat bulleted list."""
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
    return '<ul class="ev-sources">' + "".join(items) + "</ul>"


def _render_sdg_section(data: dict[str, Any]) -> str:
    """Render SDG alignment as HTML (flat items, no nested lists)."""
    sdgs = data.get("sdg_alignment", [])
    if not sdgs:
        return ""
    parts = ["<h3>SDG Alignment</h3>"]
    for item in sdgs:
        sdg = escape(str(item.get("sdg", "?")))
        evidence = escape(str(item.get("evidence", "")))
        sources_html = _render_sources(item.get("sources", []))
        parts.append(
            '<div class="ev-item">'
            f"<p><strong>SDG {sdg}</strong>: {evidence}</p>"
            f"{sources_html}"
            "</div>",
        )
    return "\n".join(parts)


def _render_evidence_section(data: dict[str, Any]) -> str:
    """Render evidence of work as HTML (flat items, no nested lists)."""
    activities = data.get("evidence_of_work", [])
    if not activities:
        return ""
    parts = ["<h3>Evidence of Work</h3>"]
    for item in activities:
        activity = escape(str(item.get("activity", "")))
        act_type = escape(str(item.get("type", "")))
        sources_html = _render_sources(item.get("sources", []))
        parts.append(
            '<div class="ev-item">'
            f"<p><strong>{act_type}</strong>: {activity}</p>"
            f"{sources_html}"
            "</div>",
        )
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
    parts = ['<h3>Evaluation History</h3><ul class="ev-history">']
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


class EvaluationReviewForm(forms.ModelForm):  # type: ignore[type-arg]
    """Admin detail form with per-category checkboxes.

    Prefilled with the AI's ``accessibility.categories`` the first time
    a reviewer opens the form, so unchecking is the reviewer's only
    action when the AI over-classified. On save:

    * **Edited away from the AI list** — the reviewer's selection is
      persisted to ``reviewer_categories`` as an explicit override.
    * **Confirmed unchanged (still matches the AI list)** —
      ``clean_reviewer_categories`` returns ``None`` so the field
      stays ``NULL``, and the evaluation keeps tracking the AI list
      rather than freezing today's list as a snapshot.

    Either way, ``OrganizationEvaluationAdmin.save_model`` resyncs the
    linked ``Organization.categories`` to the evaluation's effective
    set — ``reviewer_categories`` when present, else the AI list —
    so the admin form is authoritative for the linked org's
    categories on every save.
    """

    reviewer_categories = forms.MultipleChoiceField(
        choices=(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categories to assign on approval",
        help_text=(
            "Prefilled with the AI's proposed list. Edits here flow"
            " to the linked Organization — before approval via the"
            " create path, and after approval via re-sync. Uncheck"
            " any that don't fit."
        ),
    )

    class Meta:
        model = OrganizationEvaluation
        fields = (
            "status",
            "reviewer_reasoning",
            "reviewer_categories",
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["reviewer_categories"].choices = list(  # type: ignore[attr-defined]
            Category.objects.values_list("slug", "label"),
        )
        # Use self.instance (populated by ModelForm.__init__ whether
        # the caller passed instance positionally or by keyword) and
        # gate on pk so unbound forms — e.g. the admin's "add" view —
        # skip prefill cleanly.
        if self.instance.pk is None:
            return
        if self.instance.reviewer_categories is not None:
            self.initial["reviewer_categories"] = list(
                self.instance.reviewer_categories,
            )
            return
        # 'other' is in the schema as an AI escape hatch but isn't a
        # real Category row — don't pre-check a box that maps to
        # nothing on approval.
        self.initial["reviewer_categories"] = self._ai_fallback_slugs()

    def _ai_fallback_slugs(self) -> list[str]:
        """Slugs the AI proposed, filtered to ones that map to a real
        Category row. Used both for prefill and for NULL-preservation
        in ``clean_reviewer_categories``."""
        ai_categories = (
            (self.instance.evaluation_data or {})
            .get("accessibility", {})
            .get("categories", [])
        )
        return [slug for slug in ai_categories if slug != "other"]

    def clean_reviewer_categories(self) -> list[str] | None:
        """Preserve NULL when the reviewer confirms the AI defaults.

        The field prefills from the AI list when
        ``instance.reviewer_categories`` is ``NULL``, so a reviewer
        opening the form sees the AI-proposed categories as checked
        boxes. If they save without toggling any box, the submission
        equals the prefilled list — but that's "I accept the AI
        defaults," not "I'm explicitly choosing this exact list."
        Returning ``None`` in that case keeps the DB value ``NULL``,
        so the evaluation continues to follow the AI list (which can
        evolve) rather than freezing a snapshot of today's list as
        an explicit override.
        """
        submitted = self.cleaned_data.get("reviewer_categories") or []
        if self.instance.pk is None:
            return submitted
        if self.instance.reviewer_categories is not None:
            # Existing override — respect whatever the reviewer submits,
            # including the AI list if that's what they chose.
            return submitted
        if set(submitted) == set(self._ai_fallback_slugs()):
            return None
        return submitted


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
    form = EvaluationReviewForm
    # search_fields must be non-empty for Django to render the search
    # box.  The default icontains query on "status" is harmless but
    # unused — actual search logic lives in get_search_results below.
    search_fields = ["status"]
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
                    "reviewer_categories",
                    "reviewer_reasoning",
                ),
                "description": (
                    "Change status to Approved or Rejected and click"
                    " Save. Reviewer, timestamp, and (on approval) a"
                    " linked Organization are set automatically."
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
                '<p class="ev-meta"><strong>Prompt version:</strong> '
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

        body = "\n".join(parts) if parts else "<p>No data.</p>"
        html = (
            f'{_EV_DETAIL_STYLE}<div class="ev-detail">{body}</div>'
        )
        return mark_safe(html)  # noqa: S308

    def save_model(
        self,
        request: HttpRequest,
        obj: OrganizationEvaluation,
        form: Any,
        change: bool,
    ) -> None:
        """Stamp reviewer/time and keep linked-org visibility in sync.

        Org creation (or reactivation) on the APPROVED transition is
        handled by the post_save signal in ``signals.py`` — keeping it
        there means the same logic applies whether the transition
        happens via the change form, a bulk action, or any other
        saver.

        Going *the other way* — transitioning a previously approved
        evaluation to REJECTED or PENDING — is only reachable through
        the change form. We deactivate the linked Organization here
        (keeping the FK intact) so it disappears from the public
        frontend without losing the audit trail. Re-approving the
        evaluation later reactivates the same org rather than creating
        a duplicate.
        """
        # Wrap status flip + super().save_model() + category resync in
        # one atomic block so a failure in the resync doesn't leave the
        # evaluation in its new status while the org is half-updated.
        with transaction.atomic():
            if change and "status" in form.changed_data:
                obj.reviewer = request.user  # type: ignore[assignment]
                obj.reviewed_at = timezone.now()
                if (
                    obj.status != ReviewStatus.APPROVED
                    and obj.organization is not None
                    and obj.organization.is_active
                ):
                    obj.organization.is_active = False
                    obj.organization.save(update_fields=["is_active"])
            super().save_model(request, obj, form, change)

            # Admin form saves are authoritative: whenever the
            # reviewer submits the change form for an approved, linked
            # evaluation, align the org's categories with the
            # evaluation's resolved set. This covers every relevant
            # case — explicit category edits, no-op saves (sync is
            # idempotent), and APPROVED→PENDING→APPROVED cycles where
            # the signal only reactivates is_active. The alternative
            # — triggering on form.changed_data — misses the
            # NULL-preservation path from clean_reviewer_categories
            # (which surfaces the cleaned value, while has_changed
            # works off raw form data).
            if (
                change
                and obj.status == ReviewStatus.APPROVED
                and obj.organization is not None
            ):
                sync_org_categories_from_evaluation(obj)

    @admin.action(description="Approve selected evaluations")
    def approve_evaluations(
        self,
        request: HttpRequest,
        queryset: QuerySet[OrganizationEvaluation],
    ) -> None:
        # Per-row save inside its own atomic block so a single failure
        # (e.g., a downstream signal-handler error) doesn't leave a
        # row half-updated, but also doesn't roll back already-approved
        # rows. Errors are accumulated and surfaced to the curator.
        now = timezone.now()
        approved_count = 0
        failure_count = 0
        for evaluation in queryset.exclude(status=ReviewStatus.APPROVED):
            try:
                with transaction.atomic():
                    evaluation.status = ReviewStatus.APPROVED
                    evaluation.reviewer = request.user  # type: ignore[assignment]
                    evaluation.reviewed_at = now
                    evaluation.save()
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Failed to approve evaluation %s",
                    evaluation.pk,
                )
                failure_count += 1
                continue
            approved_count += 1
        if failure_count:
            self.message_user(
                request,
                (
                    f"Approved {approved_count} evaluation(s); "
                    f"{failure_count} failed (see server log)."
                ),
                messages.WARNING,
            )
        else:
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
        skipped_count = 0
        for evaluation in queryset:
            if evaluation.status != ReviewStatus.PENDING:
                skipped_count += 1
                continue
            evaluation.status = ReviewStatus.REJECTED
            evaluation.reviewer = request.user  # type: ignore[assignment]
            evaluation.reviewed_at = now
            evaluation.save()
            rejected_count += 1
        if skipped_count:
            self.message_user(
                request,
                (
                    f"Rejected {rejected_count} evaluation(s); "
                    f"skipped {skipped_count} non-pending row(s) — "
                    "use the change form to reject approved rows so "
                    "the linked organization is also deactivated."
                ),
                messages.WARNING,
            )
        else:
            self.message_user(
                request,
                f"Rejected {rejected_count} evaluation(s).",
                messages.SUCCESS,
            )
