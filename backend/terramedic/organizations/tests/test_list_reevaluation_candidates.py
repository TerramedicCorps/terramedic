"""Tests for the ``list_reevaluation_candidates`` command.

Runs against the dev DB via ``zappa manage`` to dump URLs of approved
evaluations whose stored ``prompt_version`` lags the live one —
input for the split re-evaluation workflow (evaluate locally via
claude-code, loaddata fixtures back via zappa).
"""

from __future__ import annotations

from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command

from curation.prompt import PROMPT_VERSION
from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)


def _make_eval_data(
    url: str = "https://example.org",
    prompt_version: str = "2026.01.1",
    name: str = "Example Org",
) -> dict[str, Any]:
    return {
        "org_metadata": {"name": name, "website_url": url},
        "prompt_version": prompt_version,
    }


@pytest.mark.django_db
class TestListReevaluationCandidates:
    def test_prints_urls_of_rejected_evals_with_stale_prompt_version(
        self,
    ) -> None:
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_eval_data(
                url="https://a.example", prompt_version="2026.01.1",
            ),
            status=ReviewStatus.REJECTED,
        )
        out = StringIO()
        call_command("list_reevaluation_candidates", stdout=out)
        assert out.getvalue().strip() == "https://a.example"

    def test_excludes_evals_at_current_prompt_version(self) -> None:
        """An eval already at the live PROMPT_VERSION has nothing to
        re-run, regardless of its review state."""
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_eval_data(
                url="https://a.example", prompt_version=PROMPT_VERSION,
            ),
            status=ReviewStatus.REJECTED,
        )
        out = StringIO()
        call_command("list_reevaluation_candidates", stdout=out)
        assert out.getvalue().strip() == ""

    def test_default_status_is_rejected_only(self) -> None:
        """Default is 'rejected' because a prompt bump most commonly
        surfaces orgs that previously didn't qualify — re-running the
        rejection pool is the highest-yield first pass, and it
        doesn't churn already-live approvals."""
        for status, slug in (
            (ReviewStatus.PENDING, "p"),
            (ReviewStatus.APPROVED, "a"),
        ):
            OrganizationEvaluation.objects.create(
                evaluation_data=_make_eval_data(
                    url=f"https://{slug}.example",
                    prompt_version="2026.01.1",
                ),
                status=status,
            )
        out = StringIO()
        call_command("list_reevaluation_candidates", stdout=out)
        assert out.getvalue().strip() == ""

    @pytest.mark.parametrize(
        ("status_arg", "matching_status", "slug"),
        [
            ("pending", ReviewStatus.PENDING, "p"),
            ("rejected", ReviewStatus.REJECTED, "r"),
        ],
    )
    def test_status_argument_selects_that_review_state(
        self,
        status_arg: str,
        matching_status: str,
        slug: str,
    ) -> None:
        """``--status pending`` / ``--status rejected`` let curators
        target unreviewed or previously-rejected evals when
        rebuilding after a prompt bump."""
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_eval_data(
                url=f"https://{slug}-match.example",
                prompt_version="2026.01.1",
            ),
            status=matching_status,
        )
        # Different status that should be excluded by the filter.
        OrganizationEvaluation.objects.create(
            evaluation_data=_make_eval_data(
                url="https://approved-excluded.example",
                prompt_version="2026.01.1",
            ),
            status=ReviewStatus.APPROVED,
        )
        out = StringIO()
        call_command(
            "list_reevaluation_candidates",
            "--status", status_arg,
            stdout=out,
        )
        assert (
            out.getvalue().strip() == f"https://{slug}-match.example"
        )

    def test_status_all_includes_every_review_state(self) -> None:
        """``--status all`` is useful when a curator wants to see
        everything that predates the current prompt, regardless of
        where it is in the review pipeline."""
        for status, slug in (
            (ReviewStatus.PENDING, "p"),
            (ReviewStatus.APPROVED, "a"),
            (ReviewStatus.REJECTED, "r"),
        ):
            OrganizationEvaluation.objects.create(
                evaluation_data=_make_eval_data(
                    url=f"https://{slug}.example",
                    prompt_version="2026.01.1",
                ),
                status=status,
            )
        out = StringIO()
        call_command(
            "list_reevaluation_candidates",
            "--status", "all",
            stdout=out,
        )
        assert sorted(out.getvalue().splitlines()) == [
            "https://a.example",
            "https://p.example",
            "https://r.example",
        ]

    def test_invalid_status_argument_errors(self) -> None:
        """argparse rejects an unknown ``--status`` value — caller
        can't silently miss rows because they typo'd the flag."""
        from django.core.management.base import CommandError

        with pytest.raises((CommandError, SystemExit)):
            call_command(
                "list_reevaluation_candidates",
                "--status", "nonsense",
            )

    def test_skips_approved_evals_missing_website_url(self) -> None:
        """Silently skip rather than emit a blank line that would
        confuse downstream piping to ``evaluate_urls_to_fixtures``."""
        OrganizationEvaluation.objects.create(
            evaluation_data={
                "org_metadata": {"name": "No URL"},
                "prompt_version": "2026.01.1",
            },
            status=ReviewStatus.APPROVED,
        )
        out = StringIO()
        call_command(
            "list_reevaluation_candidates",
            "--status", "approved",
            stdout=out,
        )
        assert out.getvalue().strip() == ""

    def test_emits_one_url_per_line_in_pk_order(self) -> None:
        """Order is stable and deterministic (pk asc) so re-running
        the command produces the same URL list — useful when
        `diff`-ing between runs or splitting batches."""
        for url in (
            "https://b.example",
            "https://a.example",
            "https://c.example",
        ):
            OrganizationEvaluation.objects.create(
                evaluation_data=_make_eval_data(url=url),
                status=ReviewStatus.REJECTED,
            )
        out = StringIO()
        call_command("list_reevaluation_candidates", stdout=out)
        assert out.getvalue().splitlines() == [
            "https://b.example",
            "https://a.example",
            "https://c.example",
        ]
