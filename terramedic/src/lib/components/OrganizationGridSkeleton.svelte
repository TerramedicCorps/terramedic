<script>
  // Skeleton shown while the org list streams in. Mirrors the
  // 1/2/3-column OrganizationCard grid so the layout doesn't jump.
  export let count = 3;

  $: indices = [...Array(count).keys()];
</script>

<div
  class="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
  aria-busy="true"
  aria-label="Loading organizations"
>
  {#each indices as i (i)}
    <div class="!bg-navy h-full animate-pulse rounded-lg border border-white/10 p-5">
      <div class="mb-3 h-6 w-3/4 rounded bg-white/10"></div>
      <div class="mb-3 flex flex-wrap gap-1.5">
        <span class="inline-block h-5 w-16 rounded-full bg-white/10"></span>
        <span class="inline-block h-5 w-20 rounded-full bg-white/10"></span>
      </div>
      <div class="mb-2 h-4 w-full rounded bg-white/5"></div>
      <div class="mb-2 h-4 w-5/6 rounded bg-white/5"></div>
      <div class="mb-5 h-4 w-2/3 rounded bg-white/5"></div>
      <div class="mt-auto h-10 w-full rounded bg-white/10"></div>
    </div>
  {/each}
</div>
