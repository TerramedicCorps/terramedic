<script>
  import { Card, Button } from 'flowbite-svelte';
  import { trackEvent } from '$lib/utils/analytics';

  export let name = '';
  export let description = '';
  export let websiteUrl = '';
  export let imageUrl = '';
  export let actionText = 'Visit Website';
  export let tags = [];
  export let tagColor = 'blue'; // Can be 'blue', 'green', or custom
  export let buttonColor = 'blue'; // Can be 'blue', 'green', or custom

  // Map tag colors to their proper design system values
  const tagColorMap = {
    blue: { bg: 'bg-blue-100', text: 'text-blue-800', hover: 'hover:bg-blue-200' },
    green: { bg: 'bg-green-100', text: 'text-green-800', hover: 'hover:bg-green-200' },
    purple: { bg: 'bg-purple-100', text: 'text-purple-800', hover: 'hover:bg-purple-200' },
    orange: { bg: 'bg-orange-100', text: 'text-orange-800', hover: 'hover:bg-orange-200' },
    red: { bg: 'bg-red-100', text: 'text-red-800', hover: 'hover:bg-red-200' },
    gray: { bg: 'bg-gray-100', text: 'text-gray-800', hover: 'hover:bg-gray-200' }
  };

  // Default to blue if no valid color is provided
  $: tagStyle = tagColorMap[tagColor] || tagColorMap.blue;

  // Handle button click for analytics tracking
  function handleButtonClick() {
    trackEvent('organization_click', {
      organization_name: name,
      organization_url: websiteUrl,
      button_text: actionText,
      categories: tags.join(',')
    });
  }
</script>

<Card img="" class="h-full border border-gray-200 transition-all duration-300 hover:shadow-lg">
  <h3 class="text-terra-dark-blue mb-2 text-xl font-bold tracking-tight">{name}</h3>

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

  <p class="mb-5 text-gray-600">{description}</p>

  <div class="mt-auto">
    <Button
      color={buttonColor}
      href={websiteUrl}
      target="_blank"
      rel="noopener noreferrer"
      class="w-full shadow-sm transition-all duration-200 hover:shadow"
      on:click={handleButtonClick}
    >
      {actionText}
    </Button>
  </div>
</Card>
