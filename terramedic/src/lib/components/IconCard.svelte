<script>
  export let title = '';
  export let description = '';
  /** @type {import('svelte').ComponentType | undefined} */
  export let icon = undefined;
  /** @type {'blue' | 'gold' | 'green' | 'purple'} */
  export let color = 'purple';

  const colorClasses = {
    blue: { bg: 'bg-blue-500/15', text: 'text-blue-400' },
    gold: { bg: 'bg-amber-500/15', text: 'text-amber-400' },
    green: { bg: 'bg-green-500/15', text: 'text-green-400' },
    purple: { bg: 'bg-purple-500/15', text: 'text-purple-400' }
  };

  $: colors = colorClasses[color] ?? colorClasses.purple;
</script>

<div class="bg-navy grid grid-cols-[auto_1fr] gap-4 rounded-lg p-5">
  {#if icon}
    <div class="flex aspect-square w-12 items-center justify-center rounded-xl {colors.bg}">
      <svelte:component this={icon} class="h-9 w-9 {colors.text}" />
    </div>
  {/if}
  <div>
    <h3 class="mb-1 text-base font-semibold text-white md:text-lg">{title}</h3>
    <p class="text-sm text-gray-300">{description}</p>
  </div>
</div>
