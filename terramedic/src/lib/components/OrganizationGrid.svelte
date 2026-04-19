<script>
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import OrganizationGridSkeleton from '$lib/components/OrganizationGridSkeleton.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  // Shared wrapper for listing pages (/volunteer, /donate, etc.) that
  // stream an organization list via {#await}. Handles skeleton / empty
  // / error states and attaches analytics to a wrapper that's present
  // in every branch so section_view fires regardless of outcome.
  export let promise;
  export let gridClass;
  export let tagColor;
  export let buttonColor;
  export let emptyText;
  export let analyticsSection;
  export let analyticsPage;
  // Button label for every card on this page. Page-level override of
  // `org.action_text` so /donate shows "Learn more", /volunteer shows
  // "Volunteer", etc. — the stored `action_text` is auto-generated
  // per-org ("Support {name}") and less contextual than the page verb.
  export let actionText;
</script>

<div use:trackSectionView={{ section: analyticsSection, page: analyticsPage }}>
  {#await promise}
    <OrganizationGridSkeleton {gridClass} />
  {:then organizations}
    {#if organizations.length === 0}
      <p class="text-center text-gray-400">{emptyText}</p>
    {:else}
      <div class={gridClass}>
        {#each organizations as org (org.id)}
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
        {/each}
      </div>
    {/if}
  {:catch}
    <p class="text-center text-red-400">
      Couldn't load organizations. Please refresh to try again.
    </p>
  {/await}
</div>
