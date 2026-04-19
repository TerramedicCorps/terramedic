"""Tests for the nomination claiming helper."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from terramedic.nominations.claim import (
    claim_nominations,
    sweep_stuck_claims,
)
from terramedic.nominations.models import Nomination, NominationStatus
from terramedic.nominations.tests.conftest import (
    make_pending_nomination,
    make_queued_nomination,
)


@pytest.mark.django_db
class TestClaimNominations:
    def test_yields_claimed_nominations(self) -> None:
        make_queued_nomination("https://one.org")
        make_queued_nomination("https://two.org")

        result = list(claim_nominations(limit=10))

        assert len(result) == 2
        urls = {n.url for n in result}
        assert urls == {"https://one.org", "https://two.org"}

    def test_nominations_are_in_evaluating_status(self) -> None:
        nom = make_queued_nomination()

        claimed = list(claim_nominations(limit=10))

        assert len(claimed) == 1
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING

    def test_respects_limit(self) -> None:
        make_queued_nomination("https://one.org")
        make_queued_nomination("https://two.org")

        result = list(claim_nominations(limit=1))
        assert len(result) == 1

    def test_increments_evaluation_attempts(self) -> None:
        nom = make_queued_nomination()
        assert nom.evaluation_attempts == 0

        list(claim_nominations(limit=10))

        nom.refresh_from_db()
        assert nom.evaluation_attempts == 1

    def test_skips_already_claimed_nomination(self) -> None:
        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.save(update_fields=["status"])

        result = list(claim_nominations(limit=10))
        assert len(result) == 0

    @patch(
        "terramedic.nominations.claim.should_skip_url",
        return_value=True,
    )
    def test_skips_skipworthy_url_and_reverts(self, mock_skip: object) -> None:  # noqa: ARG002
        nom = make_queued_nomination("https://example.org")

        result = list(claim_nominations(limit=10))

        assert len(result) == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING
        assert nom.evaluation_attempts == 0

    def test_empty_queue(self) -> None:
        result = list(claim_nominations(limit=10))
        assert len(result) == 0

    def test_sets_claimed_at(self) -> None:
        nom = make_queued_nomination()
        assert nom.claimed_at is None
        before = timezone.now()

        list(claim_nominations(limit=10))

        nom.refresh_from_db()
        assert nom.claimed_at is not None
        assert nom.claimed_at >= before

    def test_default_from_status_is_queued_ignores_pending(self) -> None:
        """Backward-compat: default claim still ignores PENDING rows."""
        make_pending_nomination("https://pending.org")
        make_queued_nomination("https://queued.org")

        result = list(claim_nominations(limit=10))

        urls = {n.url for n in result}
        assert urls == {"https://queued.org"}

    def test_from_status_pending_claims_pending(self) -> None:
        """Local command path: claim PENDING, leave QUEUED alone."""
        make_pending_nomination("https://pending.org")
        make_queued_nomination("https://queued.org")

        result = list(
            claim_nominations(
                limit=10,
                from_status=NominationStatus.PENDING,
            ),
        )

        urls = {n.url for n in result}
        assert urls == {"https://pending.org"}

    def test_from_status_pending_transitions_to_evaluating(self) -> None:
        nom = make_pending_nomination()

        list(
            claim_nominations(
                limit=10,
                from_status=NominationStatus.PENDING,
            ),
        )

        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING

    @patch(
        "terramedic.nominations.claim.should_skip_url",
        return_value=True,
    )
    def test_from_status_pending_reverts_skipworthy_to_pending(
        self, mock_skip: object,  # noqa: ARG002
    ) -> None:
        """On skip, always revert to PENDING regardless of from_status."""
        nom = make_pending_nomination()

        result = list(
            claim_nominations(
                limit=10,
                from_status=NominationStatus.PENDING,
            ),
        )

        assert len(result) == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.PENDING
        assert nom.evaluation_attempts == 0


@pytest.mark.django_db
class TestSweepStuckClaims:
    def test_sweeps_old_evaluating_to_failed(self) -> None:
        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.claimed_at = timezone.now() - timedelta(hours=1)
        nom.save(update_fields=["status", "claimed_at"])

        swept = sweep_stuck_claims()

        assert swept == 1
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_leaves_recent_evaluating_alone(self) -> None:
        nom = make_queued_nomination()
        nom.status = NominationStatus.EVALUATING
        nom.claimed_at = timezone.now()
        nom.save(update_fields=["status", "claimed_at"])

        swept = sweep_stuck_claims()

        assert swept == 0
        nom.refresh_from_db()
        assert nom.status == NominationStatus.EVALUATING

    def test_sweeps_null_claimed_at_evaluating(self) -> None:
        # Pre-migration rows, or any row that somehow entered
        # EVALUATING without a claim timestamp, must not leak.
        nom = make_queued_nomination()
        Nomination.objects.filter(pk=nom.pk).update(
            status=NominationStatus.EVALUATING,
            claimed_at=None,
        )

        swept = sweep_stuck_claims()

        assert swept == 1
        nom.refresh_from_db()
        assert nom.status == NominationStatus.FAILED

    def test_does_not_touch_other_statuses(self) -> None:
        # Intentionally set claimed_at to old so the date cutoff
        # would otherwise match — the status filter should protect
        # these rows.
        old_claim = timezone.now() - timedelta(hours=1)
        for status in (
            NominationStatus.QUEUED,
            NominationStatus.EVALUATED,
            NominationStatus.FAILED,
            NominationStatus.PENDING,
        ):
            nom = make_queued_nomination(f"https://{status}.org")
            Nomination.objects.filter(pk=nom.pk).update(
                status=status,
                claimed_at=old_claim,
            )

        swept = sweep_stuck_claims()

        assert swept == 0
