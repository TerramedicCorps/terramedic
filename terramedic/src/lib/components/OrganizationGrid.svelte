<script>
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import OrganizationGridSkeleton from '$lib/components/OrganizationGridSkeleton.svelte';
  import {
    ORG_CARD_WRAPPER_CLASS,
    ORG_GRID_CONTAINER_CLASS
  } from '$lib/components/organizationGrid.styles';
  import { trackSectionView } from '$lib/utils/analytics';

  // Shared wrapper for listing pages (/volunteer, /donate, etc.) that
  // stream an organization list via {#await}. Handles skeleton / empty
  // / error states and attaches analytics to a wrapper that's present
  // in every branch so section_view fires regardless of outcome.
  export let promise;
  export let tagColor;
  export let buttonColor;
  export let emptyText;
  export let analyticsSection;
  export let analyticsPage;
  // Button label for every card on this page. Page-level override of
  // `org.action_text` so /donate shows "Learn more", /volunteer shows
  // "Volunteer", etc. — the stored `action_text` is auto-generated
  // per-org ("Support {name}") and less contextual than the page verb.
  // Default matches OrganizationCard's default so a caller that
  // forgets to pass one still renders a labeled button (and emits a
  // sane analytics value) instead of "undefined".
  export let actionText = 'Visit Website';
</script>

<div use:trackSectionView={{ section: analyticsSection, page: analyticsPage }}>
  {#await promise}
    <OrganizationGridSkeleton />
  {:then organizations}
    {#if organizations.length === 0}
      <p class="text-center text-gray-400">{emptyText}</p>
    {:else}
      <!--
        Flex-wrap + justify-center instead of a CSS grid so rows with
        fewer than 3 cards center under the header instead of
        left-aligning. Card width 18rem gives 3 per row inside
        container-narrow (max-w-5xl) with 1.5rem gaps, 2 per row on
        tablet, and full-width on phones.
      -->
      <div class={ORG_GRID_CONTAINER_CLASS}>
        {#each organizations as org (org.id)}
          <div class={ORG_CARD_WRAPPER_CLASS}>
            <OrganizationCard
              name={org.name}
              description={org.description}
              websiteUrl={org.website_url}
              imageUrl={org.image_url}
              tags={org.tags}
              {tagColor}
              {buttonColor}
              {actionText}
            />
          </div>
        {/each}
      </div>
    {/if}
  {:catch}
    <p class="text-center text-red-400">
      Couldn't load organizations. Please refresh to try again.
    </p>
  {/await}
</div>
