<script>
  import { Card, Button } from 'flowbite-svelte';
  import { DEFAULT_ORG_ACTION_TEXT } from '$lib/components/organizationGrid.styles';
  import { trackEvent } from '$lib/utils/analytics';

  export let name = '';
  export let description = '';
  export let websiteUrl = '';
  export let actionUrl = '';
  export let imageUrl = '';
  export let actionText = DEFAULT_ORG_ACTION_TEXT;
  export let tags = [];
  export let tagColor = 'blue'; // 'blue', 'green', 'gold', 'purple', 'orange', 'red', 'gray'
  export let buttonColor = 'blue'; // 'blue', 'green', 'gold', 'purple'

  // Map tag colors to dark theme values
  const tagColorMap = {
    blue: { bg: 'bg-blue-900/60', text: 'text-blue-400', hover: 'hover:bg-blue-900/70' },
    green: { bg: 'bg-green-900/60', text: 'text-green-400', hover: 'hover:bg-green-900/70' },
    gold: { bg: 'bg-amber-900/60', text: 'text-amber-400', hover: 'hover:bg-amber-900/70' },
    purple: { bg: 'bg-purple-900/60', text: 'text-purple-400', hover: 'hover:bg-purple-900/70' },
    orange: { bg: 'bg-orange-900/60', text: 'text-orange-400', hover: 'hover:bg-orange-900/70' },
    red: { bg: 'bg-red-900/60', text: 'text-red-400', hover: 'hover:bg-red-900/70' },
    gray: { bg: 'bg-gray-800/60', text: 'text-gray-400', hover: 'hover:bg-gray-800/70' }
  };

  // Default to blue if no valid color is provided
  $: tagStyle = tagColorMap[tagColor] || tagColorMap.blue;

  // Map button colors to brand styles
  const buttonStyleMap = {
    blue: {
      bg: 'background-color: var(--btn-blue)',
      hover: 'org-btn-blue',
      text: 'text-white'
    },
    green: {
      bg: 'background-color: var(--btn-green)',
      hover: 'org-btn-green',
      text: 'text-white'
    },
    gold: {
      bg: 'background-color: var(--btn-gold)',
      hover: 'org-btn-gold',
      text: 'text-white'
    },
    purple: {
      bg: 'background-color: var(--btn-purple)',
      hover: 'org-btn-purple',
      text: 'text-white'
    }
  };

  $: btnStyle = buttonStyleMap[buttonColor] || buttonStyleMap.blue;

  // The CTA deep-links to the per-pathway action_url (volunteer
  // signup, jobs board); unfiltered/nearby contexts return "" so the
  // card falls back to the org's website. Svelte prop defaults only
  // fire on undefined, not "", so the fallback has to be explicit.
  $: linkUrl = actionUrl || websiteUrl;

  // Handle button click for analytics tracking
  function handleButtonClick() {
    trackEvent('organization_click', {
      organization_name: name,
      organization_url: websiteUrl,
      action_url: linkUrl,
      button_text: actionText,
      categories: tags.join(',')
    });
  }
</script>

<Card
  img=""
  class="!bg-navy h-full !max-w-none border border-white/10 p-5 transition-all duration-300 hover:shadow-lg"
>
  <h3 class="mb-2 text-xl font-bold tracking-tight text-white">{name}</h3>

  {#if tags.length > 0}
    <div class="mb-3 flex flex-wrap gap-1.5">
      {#each tags as tag (tag)}
        <span
          class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {tagStyle.bg} {tagStyle.text} {tagStyle.hover} transition-colors duration-200"
        >
          {tag}
        </span>
      {/each}
    </div>
  {/if}

  <p class="mb-5 text-gray-400">{description}</p>

  <div class="mt-auto">
    <Button
      color="none"
      href={linkUrl}
      target="_blank"
      rel="noopener noreferrer"
      style={btnStyle.bg}
      class="w-full {btnStyle.text} {btnStyle.hover} shadow-sm transition-all duration-200 hover:shadow"
      onclick={handleButtonClick}
    >
      {actionText}
    </Button>
  </div>
</Card>

<style>
  :global(.org-btn-blue:hover) {
    background-color: var(--btn-blue-hover) !important;
  }

  :global(.org-btn-green:hover) {
    background-color: var(--btn-green-hover) !important;
  }

  :global(.org-btn-gold:hover) {
    background-color: var(--btn-gold-hover) !important;
  }

  :global(.org-btn-purple:hover) {
    background-color: var(--btn-purple-hover) !important;
  }
</style>
