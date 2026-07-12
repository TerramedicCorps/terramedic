"""Behavior tests for evaluation_actions handling category_copy.

Covers the primary path (evaluation approval populates
OrganizationCategory rows with AI-drafted copy) and the
reviewer-edit path (sync preserves curator-edited copy while
syncing the category set)."""

from __future__ import annotations

from typing import Any

import pytest

from terramedic.organizations.evaluation_actions import (
    create_org_from_evaluation,
    sync_org_categories_from_evaluation,
)
from terramedic.organizations.models import (
    Category,
    OrganizationCategory,
    OrganizationEvaluation,
)


def _eval_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "org_metadata": {
            "name": "Citizens' Climate Lobby",
            "website_url": "https://citizensclimatelobby.org/",
            "description": "General grassroots advocacy description.",
        },
        "sdg_alignment": [
            {"sdg": 13, "evidence": "Climate lobbying."},
        ],
        "evidence_of_work": [
            {"activity": "Lobbying Congress.", "type": "advocacy"},
        ],
        "accessibility": {"categories": ["donate", "volunteer"]},
        "category_copy": [
            {
                "slug": "donate",
                "description": "Fund bipartisan climate lobbying.",
                "action_text": "Donate to CCL",
                "action_url": "https://citizensclimatelobby.org/",
            },
            {
                "slug": "volunteer",
                "description": "Join a local lobby day.",
                "action_text": "Find a chapter",
                "action_url": (
                    "https://citizensclimatelobby.org/chapters/"
                ),
            },
        ],
        "evidence_score": {"score": 4, "rationale": "Strong"},
        "curator_notes": {"recommendation": "include", "confidence": 90},
        "evaluated_at": "2026-04-21T00:00:00Z",
        "evaluated_by": "claude-sonnet-4-20250514",
        "prompt_version": "2026.04.13",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestCreateOrgPopulatesCategoryCopy:
    def test_through_rows_carry_description_and_action_text(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
        )

        org = create_org_from_evaluation(ev)

        donate = OrganizationCategory.objects.get(
            organization=org, category__slug="donate",
        )
        donate.set_current_language("en")
        assert donate.description == "Fund bipartisan climate lobbying."
        assert donate.action_text == "Donate to CCL"

        volunteer = OrganizationCategory.objects.get(
            organization=org, category__slug="volunteer",
        )
        volunteer.set_current_language("en")
        assert volunteer.description == "Join a local lobby day."
        assert volunteer.action_text == "Find a chapter"

    def test_through_rows_carry_action_url(self) -> None:
        """``action_url`` from ``category_copy`` lands on the through
        row so the API can render a working CTA link."""
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
        )

        org = create_org_from_evaluation(ev)

        donate = OrganizationCategory.objects.get(
            organization=org, category__slug="donate",
        )
        donate.set_current_language("en")
        assert donate.action_url == "https://citizensclimatelobby.org/"

        volunteer = OrganizationCategory.objects.get(
            organization=org, category__slug="volunteer",
        )
        volunteer.set_current_language("en")
        assert volunteer.action_url == (
            "https://citizensclimatelobby.org/chapters/"
        )

    def test_deep_donate_link_in_evaluation_is_rejected_on_write(
        self,
    ) -> None:
        """501(c)(3) defense in depth on the curation write path. If
        evaluation_data carries a deep donate link (a legacy record or
        hand-edited JSON that bypassed the curation-layer normalization),
        the write must not silently persist it. ``_write_category_copy``
        runs ``full_clean``, so ``OrganizationCategory.clean()`` rejects
        a donate ``action_url`` that isn't the org homepage, and the
        atomic transaction rolls the whole create back."""
        from django.core.exceptions import ValidationError

        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(
                category_copy=[
                    {
                        "slug": "donate",
                        "description": "Fund us.",
                        "action_text": "Donate",
                        "action_url": "https://example.com/donate/give-now",
                    },
                ],
            ),
        )

        with pytest.raises(ValidationError, match="donate"):
            create_org_from_evaluation(ev)

    def test_slug_without_category_copy_entry_starts_blank(self) -> None:
        """Reviewers can add an extra category via reviewer_categories
        that the AI didn't propose. That row should exist but have
        empty translated copy — the admin "Generate descriptions"
        button backfills it."""
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
            reviewer_categories=["donate", "volunteer", "career"],
        )

        org = create_org_from_evaluation(ev)

        career = OrganizationCategory.objects.get(
            organization=org, category__slug="career",
        )
        # Translation row may not exist at all — either way, copy is
        # not the AI draft.
        assert career.translations.count() == 0  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestSyncPreservesExistingCopy:
    def test_editing_reviewer_categories_keeps_copy_for_kept_slugs(
        self,
    ) -> None:
        """When a reviewer removes and re-adds categories after
        approval, rows for slugs that *remain* should keep their
        (possibly curator-edited) per-category copy — we only
        re-apply AI copy for slugs newly added by the edit."""
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
        )
        org = create_org_from_evaluation(ev)
        ev.organization = org
        ev.save()

        # Curator edits donate's copy after approval.
        donate = OrganizationCategory.objects.get(
            organization=org, category__slug="donate",
        )
        donate.set_current_language("en")
        donate.description = "Curator-edited donate pitch."
        donate.action_text = "Chip in"
        donate.save()

        # Reviewer drops volunteer, keeps donate.
        ev.reviewer_categories = ["donate"]
        ev.save()

        sync_org_categories_from_evaluation(ev)

        donate.refresh_from_db()
        donate.set_current_language("en")
        assert donate.description == "Curator-edited donate pitch."
        assert donate.action_text == "Chip in"

    def test_removing_a_slug_deletes_its_through_row(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
        )
        org = create_org_from_evaluation(ev)
        ev.organization = org
        ev.save()

        assert OrganizationCategory.objects.filter(
            organization=org,
        ).count() == 2

        ev.reviewer_categories = ["donate"]
        ev.save()
        sync_org_categories_from_evaluation(ev)

        assert OrganizationCategory.objects.filter(
            organization=org,
        ).count() == 1
        assert OrganizationCategory.objects.filter(
            organization=org, category__slug="volunteer",
        ).count() == 0

    def test_adding_a_new_slug_applies_ai_copy_if_present(self) -> None:
        """If category_copy has an entry for a newly-added slug, the
        sync writes that copy to the new through row."""
        # AI initially proposed only donate (so only donate's through
        # row exists after create), but category_copy carries a
        # volunteer entry too — e.g., the AI drafted copy for a slug
        # the reviewer only later opted in to.
        data = _eval_data(
            accessibility={"categories": ["donate"]},
        )
        data["category_copy"] = [
            {
                "slug": "donate",
                "description": "Fund bipartisan climate lobbying.",
                "action_text": "Donate to CCL",
            },
            {
                "slug": "volunteer",
                "description": "Join a local lobby day.",
                "action_text": "Find a chapter",
            },
        ]
        ev = OrganizationEvaluation.objects.create(evaluation_data=data)
        org = create_org_from_evaluation(ev)
        ev.organization = org
        ev.save()

        # Reviewer adds volunteer. Sync should create the through row
        # and populate it from category_copy.
        ev.reviewer_categories = ["donate", "volunteer"]
        ev.save()
        sync_org_categories_from_evaluation(ev)

        volunteer = OrganizationCategory.objects.get(
            organization=org, category__slug="volunteer",
        )
        volunteer.set_current_language("en")
        assert volunteer.description == "Join a local lobby day."
        assert volunteer.action_text == "Find a chapter"

    def test_noop_when_no_organization_linked(self) -> None:
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=_eval_data(),
        )
        # Not approved; no org link.
        assert ev.organization is None

        sync_org_categories_from_evaluation(ev)  # must not raise


@pytest.mark.django_db
class TestResourceFallback:
    def test_empty_valid_slugs_falls_back_to_resource(self) -> None:
        """If reviewer clears categories and AI only produced 'other',
        the fallback is 'resource' — keeps the org surfaced
        somewhere. category_copy has no entry for 'resource' here,
        so the through row is blank."""
        data = _eval_data()
        data["accessibility"]["categories"] = ["other"]
        data["category_copy"] = []
        ev = OrganizationEvaluation.objects.create(
            evaluation_data=data,
            reviewer_categories=[],
        )

        org = create_org_from_evaluation(ev)

        slugs = list(
            org.categories.values_list("slug", flat=True),
        )
        assert slugs == ["resource"]
        resource = OrganizationCategory.objects.get(
            organization=org, category=Category.objects.get(slug="resource"),
        )
        assert resource.translations.count() == 0  # type: ignore[attr-defined]
