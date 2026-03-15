<script>
  import { GREEN_CROSS } from '$lib/icons';

  export let size = 'medium'; // small, medium, large, or inherit
  export let showWordmark = true;

  $: fontSize =
    size === 'small'
      ? '1.125rem'
      : size === 'medium'
        ? '1.5rem'
        : size === 'large'
          ? '2rem'
          : 'inherit';
</script>

<span class="logo-text" style="font-size: {fontSize};">
  <span class="sr-only">Terramedic</span><svg
    class="logo-t"
    viewBox={GREEN_CROSS.viewBox}
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    {#each GREEN_CROSS.arms as arm (arm.x)}
      <rect
        x={arm.x}
        y={arm.y}
        width={arm.width}
        height={arm.height}
        rx={arm.rx}
        fill={GREEN_CROSS.fill}
      />
    {/each}
  </svg>{#if showWordmark}<span aria-hidden="true">erramedic</span>{/if}
</span>

<style>
  .logo-text {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: white;
    line-height: 1;
    white-space: nowrap;
  }

  .logo-t {
    display: inline-block;
    height: 0.85em;
    width: 0.85em;
    vertical-align: -0.05em;
    margin-right: 0.03em;
  }
</style>
