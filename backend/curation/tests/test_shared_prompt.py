"""Tests guarding drift between the curation prompt and the admin
AI-descriptions service.

Both write per-category org copy. They share voice-and-style rules
that live as module-level constants in ``curation/prompt.py``; the
admin service imports them so the two prompts can't silently diverge
on length, pathway-reader framing, or CTA style.
"""

from __future__ import annotations


class TestSharedPromptConstants:
    def test_per_category_guidance_names_each_canonical_pathway(self) -> None:
        """Reader-per-pathway framing is the whole point of per-category
        copy. If a slug goes missing from the shared constant,
        downstream copy drops the pathway-specific voice that
        differentiates 'why donate' from 'why volunteer'."""
        from curation.prompt import PER_CATEGORY_COPY_GUIDANCE

        for slug in ("donate", "volunteer", "resource", "everyday", "career"):
            assert slug in PER_CATEGORY_COPY_GUIDANCE, (
                f"shared guidance missing {slug!r}"
            )

    def test_description_style_rules_cover_length_and_filler(
        self,
    ) -> None:
        from curation.prompt import DESCRIPTION_STYLE_RULES

        assert "120" in DESCRIPTION_STYLE_RULES
        assert "180" in DESCRIPTION_STYLE_RULES
        assert "filler" in DESCRIPTION_STYLE_RULES.lower()

    def test_guidance_carries_501c3_compliance_context(self) -> None:
        """Both donate and volunteer rules depend on this context —
        if it goes missing, neither pathway-specific guard below can
        do its job. Isolated from the per-pathway tests so the
        compliance note itself can be asserted once, then referenced.
        """
        from curation.prompt import PER_CATEGORY_COPY_GUIDANCE

        assert "501(c)(3)" in PER_CATEGORY_COPY_GUIDANCE
        assert (
            "501(c)(4)" in PER_CATEGORY_COPY_GUIDANCE
            or "non-(c)(3)" in PER_CATEGORY_COPY_GUIDANCE
        )

    def test_donate_guidance_keeps_tone_neutral_for_non_c3_orgs(
        self,
    ) -> None:
        """Terramedic, a 501(c)(3), must not appear to solicit
        donations on behalf of 501(c)(4)s, PACs, or bundlers it
        lists. The donate bullet must tell the model to stay
        informational rather than imperative — writing "Donate to
        fund X" for a (c)(4) creates legal risk."""
        from curation.prompt import PER_CATEGORY_COPY_GUIDANCE

        lower = PER_CATEGORY_COPY_GUIDANCE.lower()
        assert "donate" in lower
        # Either "informational" / "neutral" appears (the positive
        # framing) or "solicit" / "imperative" appears (the
        # negative framing the guidance rules out). Accept either —
        # both express the same constraint.
        assert any(
            term in lower
            for term in ("informational", "solicit", "imperative", "neutral")
        ), "donate guidance must name the neutral/non-solicitation rule"

    def test_volunteer_guidance_avoids_recruiting_for_c4_activities(
        self,
    ) -> None:
        """Many listed orgs recruit volunteers for lobbying,
        canvassing, or electoral campaigning — classic (c)(4)
        activity. A (c)(3) can't appear to recruit volunteers for
        those activities on behalf of a (c)(4). The volunteer rule
        must flag this so the model doesn't write "Join us to lobby
        Congress" copy."""
        from curation.prompt import PER_CATEGORY_COPY_GUIDANCE

        lower = PER_CATEGORY_COPY_GUIDANCE.lower()
        assert "volunteer" in lower
        # The rule has to surface at least one of the specific (c)(4)
        # activity types — lobby/canvass/campaign/recruit — so the
        # model knows what to avoid framing as a direct call.
        assert any(
            term in lower
            for term in ("recruit", "lobby", "canvass", "campaign")
        ), (
            "volunteer guidance must name the specific activity types"
            " ((c)(4)-style recruiting) it constrains"
        )


class TestBothPromptsEmbedSharedConstants:
    def test_curation_system_prompt_embeds_per_category_guidance(
        self,
    ) -> None:
        from curation.prompt import (
            PER_CATEGORY_COPY_GUIDANCE,
            SYSTEM_PROMPT,
        )

        assert PER_CATEGORY_COPY_GUIDANCE in SYSTEM_PROMPT

    def test_curation_system_prompt_embeds_description_style_rules(
        self,
    ) -> None:
        from curation.prompt import (
            DESCRIPTION_STYLE_RULES,
            SYSTEM_PROMPT,
        )

        assert DESCRIPTION_STYLE_RULES in SYSTEM_PROMPT

    def test_ai_descriptions_service_embeds_per_category_guidance(
        self,
    ) -> None:
        from curation.prompt import PER_CATEGORY_COPY_GUIDANCE
        from terramedic.organizations.services.ai_descriptions import (
            _SYSTEM_PROMPT,
        )

        assert PER_CATEGORY_COPY_GUIDANCE in _SYSTEM_PROMPT

    def test_ai_descriptions_service_embeds_description_style_rules(
        self,
    ) -> None:
        from curation.prompt import DESCRIPTION_STYLE_RULES
        from terramedic.organizations.services.ai_descriptions import (
            _SYSTEM_PROMPT,
        )

        assert DESCRIPTION_STYLE_RULES in _SYSTEM_PROMPT
