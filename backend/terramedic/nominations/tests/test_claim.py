"""Tests for the nomination claiming helper."""

from unittest.mock import patch

import pytest

from terramedic.nominations.claim import claim_nominations
from terramedic.nominations.models import NominationStatus
from terramedic.nominations.tests.conftest import make_queued_nomination


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
