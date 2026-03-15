<script>
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>{$page.status === 404 ? 'Page Not Found' : 'Something Went Wrong'} | Terramedic</title>
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col items-center justify-center px-4 text-center">
  {#if $page.status === 404}
    <h1 class="mb-6 text-3xl font-bold text-white md:text-5xl">
      Like Planet B, the page you're looking for doesn't exist.
    </h1>
  {:else}
    <h1 class="mb-6 text-3xl font-bold text-white md:text-5xl">Something went wrong.</h1>
    <p class="mb-6 text-lg text-gray-300">
      If this keeps happening, please <a href="/contact-us" class="text-terra-green hover:underline"
        >let us know</a
      >.
    </p>
  {/if}
  <a
    href="/"
    class="bg-terra-green mb-12 inline-block rounded-lg px-8 py-3 text-lg font-semibold text-[#0a0e17] transition-colors hover:bg-green-400"
  >
    Take me Home!
  </a>
  <img
    src="/images/blue-marble.jpg"
    alt="NASA Blue Marble — Earth seen from space"
    class="max-w-sm rounded-full md:max-w-md lg:max-w-lg"
  />
</div>
