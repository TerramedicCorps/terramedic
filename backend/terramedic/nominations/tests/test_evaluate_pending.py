"""Tests for the evaluate_pending management command.

This command shells out to Claude Code (not the Anthropic API) so evals
hit the user's Max subscription instead of per-token API billing.
"""

from typing import Any
from unittest.mock import patch

import pytest
from django.core.management import call_command

from terramedic.nominations.models import NominationStatus
from terramedic.nominations.tests.conftest import (
    EVAL_RESULT,
    make_pending_nomination,
    make_queued_nomination,
)
from terramedic.organizations.models import OrganizationEvaluation

_COMMAND = "evaluate_pending"

_EVAL_VIA_CC_PATH = (
    "terramedic.nominations.management.commands"
    ".evaluate_pending.evaluate_org_via_claude_code"
)


@pytest.mark.django_db
class TestEvaluatePending:
    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_processes_pending_nomination(
        self, mock_eval: Any,  # noqa: ARG002
    ) -> None:
        nom = make_pending_nomination()
        call_command(_COMMAND)
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATED

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_leaves_queued_untouched(
        self, mock_eval: Any,  # noqa: ARG002
    ) -> None:
        """QUEUED is the AWS worker's pool. Local command must not touch it."""
        queued = make_queued_nomination("https://queued.org")
        pending = make_pending_nomination("https://pending.org")

        call_command(_COMMAND)

        queued.refresh_from_db()
        pending.refresh_from_db()
        assert queued.status == NominationStatus.QUEUED
        assert pending.status == NominationStatus.EVALUATED

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_links_evaluation_to_nomination(
        self, mock_eval: Any,  # noqa: ARG002
    ) -> None:
        nom = make_pending_nomination()
        call_command(_COMMAND)
        ev = OrganizationEvaluation.objects.get(nomination=nom)
        assert ev.nomination_id == nom.pk

    @patch(_EVAL_VIA_CC_PATH, side_effect=RuntimeError("claude failed"))
    def test_failure_marks_failed(
        self, mock_eval: Any,  # noqa: ARG002
    ) -> None:
        nom = make_pending_nomination()
        call_command(_COMMAND)
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_failure_skips_cas_when_row_changed(self) -> None:
        """Concurrent change between claim and FAILED update → no-op."""
        from terramedic.nominations.models import Nomination

        nom = make_pending_nomination()

        def mid_eval_stomp(*_a: Any, **_kw: Any) -> None:
            # Simulate sweep_stuck_claims or admin edit stomping the row
            # while Claude Code is mid-evaluation.
            Nomination.objects.filter(pk=nom.pk).update(
                status=NominationStatus.FAILED,
            )
            msg = "boom"
            raise RuntimeError(msg)

        with patch(_EVAL_VIA_CC_PATH, side_effect=mid_eval_stomp):
            call_command(_COMMAND)

        # Status already FAILED from the stomp — CAS saw no EVALUATING
        # row to transition, so no additional update happened.
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_passes_categories_to_claude_code(
        self, mock_eval: Any,
    ) -> None:
        from terramedic.nominations.models import Nomination

        Nomination.objects.create(
            url="https://with-cats.org",
            categories=["donate", "resource"],
            status=NominationStatus.PENDING,
            ip_hash=None,
        )

        call_command(_COMMAND)

        assert mock_eval.call_count == 1
        call_kwargs = mock_eval.call_args.kwargs
        assert call_kwargs.get("categories") == ["donate", "resource"]

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_respects_limit(self, mock_eval: Any) -> None:
        make_pending_nomination("https://one.org")
        make_pending_nomination("https://two.org")
        make_pending_nomination("https://three.org")

        call_command(_COMMAND, "--limit", "2")

        assert mock_eval.call_count == 2


@pytest.mark.django_db
class TestSkipBehavior:
    """Duplicate URLs must not be evaluated; the skip is driven by real
    DB state (existing org or active evaluation), exercised end-to-end."""

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_url_matching_existing_org_is_not_evaluated(
        self, mock_eval: Any,
    ) -> None:
        from terramedic.organizations.models import Organization

        Organization.objects.create(
            name="Existing",
            website_url="https://dup.org",
        )
        nom = make_pending_nomination("https://dup.org")

        call_command(_COMMAND)

        assert mock_eval.call_count == 0
        nom.refresh_from_db()
        # claim_nominations claims then reverts on skip → back to PENDING.
        assert nom.status == NominationStatus.PENDING

    @patch(_EVAL_VIA_CC_PATH, return_value=EVAL_RESULT)
    def test_mixed_batch_skips_only_duplicates(
        self, mock_eval: Any,
    ) -> None:
        from terramedic.organizations.models import Organization

        Organization.objects.create(
            name="Existing",
            website_url="https://dup.org",
        )
        dup = make_pending_nomination("https://dup.org")
        fresh = make_pending_nomination("https://fresh.org")

        call_command(_COMMAND)

        assert mock_eval.call_count == 1
        dup.refresh_from_db()
        fresh.refresh_from_db()
        assert dup.status == NominationStatus.PENDING
        assert fresh.status == NominationStatus.EVALUATED
