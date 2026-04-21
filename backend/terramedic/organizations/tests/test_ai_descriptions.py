"""Tests for the admin fallback AI-description service.

The curation pipeline populates category_copy for every category
it proposes, so this service is only hit when a curator adds a
new category to an already-approved org. Mocks the Anthropic
client to avoid real API calls.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from terramedic.organizations.models import Category, Organization
from terramedic.organizations.services.ai_descriptions import (
    AIDescriptionError,
    DraftedCopy,
    draft_for_category,
)


def _mock_client(payload: dict[str, Any]) -> MagicMock:
    client = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(payload)
    message = MagicMock()
    message.content = [block]
    client.messages.create.return_value = message
    return client


@pytest.fixture
def org(db: None) -> Organization:
    o = Organization(
        name="Citizens' Climate Lobby",
        website_url="https://citizensclimatelobby.org/",
    )
    o.set_current_language("en")
    o.description = "Grassroots climate advocacy."
    o.save()
    return o


@pytest.mark.django_db
class TestDraftForCategory:
    def test_returns_drafted_description_and_action_text(
        self, org: Organization,
    ) -> None:
        donate = Category.objects.get(slug="donate")
        client = _mock_client(
            {
                "description": "Fund bipartisan climate lobbying at scale.",
                "action_text": "Donate to CCL",
            },
        )

        result = draft_for_category(org, donate, client=client)

        assert isinstance(result, DraftedCopy)
        assert result.description == (
            "Fund bipartisan climate lobbying at scale."
        )
        assert result.action_text == "Donate to CCL"

    def test_raises_when_api_key_missing(
        self,
        org: Organization,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With no client injected and no env var, the service must
        surface a user-readable error the admin view can flash —
        not a confusing Anthropic SDK traceback."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(AIDescriptionError, match="ANTHROPIC_API_KEY"):
            draft_for_category(
                org, Category.objects.get(slug="donate"),
            )

    def test_raises_on_malformed_json(self, org: Organization) -> None:
        client = MagicMock()
        block = MagicMock()
        block.type = "text"
        block.text = "not JSON at all"
        message = MagicMock()
        message.content = [block]
        client.messages.create.return_value = message

        with pytest.raises(AIDescriptionError):
            draft_for_category(
                org, Category.objects.get(slug="donate"), client=client,
            )

    def test_raises_when_response_missing_description(
        self, org: Organization,
    ) -> None:
        client = _mock_client({"action_text": "Donate"})

        with pytest.raises(AIDescriptionError, match="description"):
            draft_for_category(
                org, Category.objects.get(slug="donate"), client=client,
            )

    def test_raises_when_response_missing_action_text(
        self, org: Organization,
    ) -> None:
        client = _mock_client({"description": "Just a description."})

        with pytest.raises(AIDescriptionError, match="action_text"):
            draft_for_category(
                org, Category.objects.get(slug="donate"), client=client,
            )

    def test_system_prompt_has_cache_control_for_prompt_cache_hits(
        self, org: Organization,
    ) -> None:
        """Multiple drafts for the same org (drafting several
        categories at once) should reuse the prompt cache. The
        service must set cache_control on the system prompt so
        Anthropic actually caches it."""
        donate = Category.objects.get(slug="donate")
        client = _mock_client(
            {"description": "d", "action_text": "a"},
        )

        draft_for_category(org, donate, client=client)

        call_kwargs = client.messages.create.call_args.kwargs
        system = call_kwargs["system"]
        assert isinstance(system, list)
        assert system[0].get("cache_control") == {"type": "ephemeral"}

    def test_user_content_includes_org_name_and_category_slug(
        self, org: Organization,
    ) -> None:
        """The call must identify which org and which pathway; the
        model can't draft without that."""
        career = Category.objects.get(slug="career")
        client = _mock_client(
            {"description": "d", "action_text": "a"},
        )

        draft_for_category(org, career, client=client)

        messages = client.messages.create.call_args.kwargs["messages"]
        user_msg = messages[0]
        # Content may be a string or a list of content blocks.
        content = user_msg["content"]
        text = (
            content if isinstance(content, str)
            else "\n".join(
                block.get("text", "") for block in content
            )
        )
        assert org.name in text
        assert "career" in text
