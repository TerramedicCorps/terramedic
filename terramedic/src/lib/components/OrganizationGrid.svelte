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
  //
  // Each card's CTA comes from org.action_text — the backend
  // guarantees a non-empty value for category-filtered responses via
  // the Category.default_action_text fallback, so the frontend
  // trusts it.
  export let promise;
  export let tagColor;
  export let buttonColor;
  export let emptyText;
  export let analyticsSection;
  export let analyticsPage;
</script>

<div use:trackSectionView={{ section: analyticsSection, page: analyticsPage }}>
  {#await promise}
    <OrganizationGridSkeleton />
  {:then organizations}
    {#if organizations.length === 0}
      <p class="text-center text-gray-400">{emptyText}</p>
    {:else}
      <div class={ORG_GRID_CONTAINER_CLASS}>
        {#each organizations as org (org.id)}
          <div class={ORG_CARD_WRAPPER_CLASS}>
            <OrganizationCard
              name={org.name}
              description={org.description}
              websiteUrl={org.website_url}
              imageUrl={org.image_url}
              tags={org.tags}
              actionText={org.action_text}
              {tagColor}
              {buttonColor}
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
