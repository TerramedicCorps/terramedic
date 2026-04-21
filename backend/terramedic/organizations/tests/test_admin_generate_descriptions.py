"""Tests for the admin 'Generate descriptions' action.

Only covers behavior we own: which through rows get drafted vs.
skipped, and how AIDescriptionError is surfaced. The actual AI
call is mocked via patch(draft_for_category).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from terramedic.organizations.models import (
    Category,
    Organization,
    OrganizationCategory,
)
from terramedic.organizations.services.ai_descriptions import (
    AIDescriptionError,
    DraftedCopy,
)


@pytest.fixture
def admin_user(db: None) -> User:
    user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="pw",
    )
    return user


@pytest.fixture
def client(admin_user: User) -> Client:
    c = Client()
    c.force_login(admin_user)
    return c


@pytest.fixture
def org(db: None) -> Organization:
    o = Organization(
        name="CCL",
        website_url="https://citizensclimatelobby.org/",
    )
    o.set_current_language("en")
    o.description = "General."
    o.save()
    return o


def _url(org: Organization) -> str:
    return reverse(
        "admin:organizations_organization_generate_descriptions",
        args=[org.pk],
    )


@pytest.mark.django_db
class TestGenerateDescriptionsView:
    def test_drafts_only_blank_entries(
        self, client: Client, org: Organization,
    ) -> None:
        """Rows with non-empty description + action_text should be
        left alone; blank rows get drafted."""
        populated = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        populated.set_current_language("en")
        populated.description = "Existing donate pitch."
        populated.action_text = "Donate"
        populated.save()

        OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="volunteer"),
        )
        # Volunteer entry left blank — should be drafted.

        draft = DraftedCopy(
            description="AI-drafted volunteer pitch.",
            action_text="Volunteer",
        )
        with patch(
            "terramedic.organizations.admin.draft_for_category",
            return_value=draft,
        ) as mock_draft:
            response = client.get(_url(org), follow=False)

        assert response.status_code == 302  # redirect back to change form
        # Only the blank volunteer entry was drafted.
        assert mock_draft.call_count == 1
        (_called_org, called_category), _ = mock_draft.call_args
        assert called_category.slug == "volunteer"

        # Populated row untouched.
        populated.refresh_from_db()
        populated.set_current_language("en")
        assert populated.description == "Existing donate pitch."

        # Volunteer row now filled.
        volunteer = OrganizationCategory.objects.get(
            organization=org, category__slug="volunteer",
        )
        volunteer.set_current_language("en")
        assert volunteer.description == "AI-drafted volunteer pitch."
        assert volunteer.action_text == "Volunteer"

    def test_reports_nothing_to_draft_when_all_rows_populated(
        self, client: Client, org: Organization,
    ) -> None:
        populated = OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )
        populated.set_current_language("en")
        populated.description = "Already drafted."
        populated.action_text = "Donate"
        populated.save()

        with patch(
            "terramedic.organizations.admin.draft_for_category",
        ) as mock_draft:
            response = client.get(_url(org), follow=True)

        assert mock_draft.call_count == 0
        messages = [m.message for m in response.context["messages"]]
        assert any("Nothing to draft" in m for m in messages)

    def test_ai_description_error_surfaces_as_user_message(
        self, client: Client, org: Organization,
    ) -> None:
        OrganizationCategory.objects.create(
            organization=org,
            category=Category.objects.get(slug="donate"),
        )

        with patch(
            "terramedic.organizations.admin.draft_for_category",
            side_effect=AIDescriptionError(
                "ANTHROPIC_API_KEY is not set",
            ),
        ):
            response = client.get(_url(org), follow=True)

        assert response.status_code == 200
        messages = [m.message for m in response.context["messages"]]
        assert any("ANTHROPIC_API_KEY" in m for m in messages), messages

    def test_missing_org_redirects_with_error_message(
        self, client: Client,
    ) -> None:
        response = client.get(
            reverse(
                "admin:organizations_organization_generate_descriptions",
                args=[99999],
            ),
            follow=True,
        )
        messages = [m.message for m in response.context["messages"]]
        assert any("not found" in m.lower() for m in messages)
