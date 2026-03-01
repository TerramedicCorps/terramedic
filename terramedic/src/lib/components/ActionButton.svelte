<script>
  import { Button } from 'flowbite-svelte';
  import { ArrowRightOutline } from 'flowbite-svelte-icons';
  import { trackEvent } from '$lib/utils/analytics';
  import { ICON_PATHS } from '$lib/icons';

  export let text = 'Click me';
  export let href = '/';
  export let type = 'primary'; // primary, secondary, or purple
  export let size = 'lg';
  export let id = ''; // Optional ID for more specific tracking
  export let fullWidth = false; // Whether the button should stretch full width
  export let icon = ''; // Optional icon: 'clock', 'banknotes', or 'bolt'

  $: iconPath = icon && icon in ICON_PATHS ? ICON_PATHS[icon] : '';

  // Create style objects for different button types
  const primaryStyle = `
    background-color: var(--btn-blue);
    transition: background-color 0.2s ease-in-out;
    width: 100%;
  `;

  const secondaryStyle = `
    background-color: var(--btn-green);
    transition: background-color 0.2s ease-in-out;
    width: 100%;
  `;

  const purpleStyle = `
    background-color: var(--btn-purple);
    transition: background-color 0.2s ease-in-out;
    width: 100%;
  `;

  // Set up the dynamic style attribute based on the type
  $: style = type === 'primary' ? primaryStyle : type === 'purple' ? purpleStyle : secondaryStyle;

  $: customClass =
    type === 'primary'
      ? 'action-button-primary'
      : type === 'purple'
        ? 'action-button-purple'
        : 'action-button-secondary';

  // Handle click event for tracking
  function handleClick() {
    // Track button click event
    trackEvent('button_click', {
      button_text: text,
      button_type: type,
      button_id: id || text.toLowerCase().replace(/\s+/g, '_'),
      destination: href
    });
  }
</script>

<Button
  {size}
  {href}
  color="none"
  {style}
  class={`justify-center text-white ${customClass} ${fullWidth ? 'w-full' : 'w-full'}`}
  on:click={handleClick}
>
  {#if iconPath}
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke-width="1.5"
      stroke="currentColor"
      class="action-icon mr-2 h-5 w-5"
    >
      <path stroke-linecap="round" stroke-linejoin="round" d={iconPath} />
    </svg>
  {/if}
  <span class="mr-2">{text}</span>
  <ArrowRightOutline class="h-4 w-4" />
</Button>

<style>
  /* Global styles that won't be scoped */
  :global(.action-button-primary:hover) {
    background-color: var(--btn-blue-hover) !important;
  }

  :global(.action-button-secondary:hover) {
    background-color: var(--btn-green-hover) !important;
  }

  :global(.action-button-purple:hover) {
    background-color: var(--btn-purple-hover) !important;
  }
</style>
