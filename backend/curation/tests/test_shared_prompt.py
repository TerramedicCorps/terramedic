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
