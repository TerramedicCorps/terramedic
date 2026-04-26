<script>
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>{$page.status === 404 ? 'Page Not Found' : 'Something Went Wrong'} | Terramedic</title>
</svelte:head>

<div
  class="flex min-h-screen flex-col items-center justify-center bg-[#060806] px-4 py-12 text-center"
>
  {#if $page.status === 404}
    <h1 class="mb-8 max-w-3xl text-3xl leading-tight font-bold text-balance text-white md:text-5xl">
      Like Planet B, the page you're looking for doesn't exist.
    </h1>
  {:else}
    <h1 class="mb-6 max-w-3xl text-3xl leading-tight font-bold text-balance text-white md:text-5xl">
      Something went wrong.
    </h1>
    <p class="mb-8 max-w-xl text-lg leading-relaxed text-gray-300">
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
    src="/images/art002e000192.webp"
    alt="Earth photographed from NASA's Artemis II Orion spacecraft after the translunar injection burn, with auroras, zodiacal light, and Venus visible"
    class="w-full max-w-2xl md:max-w-3xl lg:max-w-4xl"
  />
  <p class="mt-6 max-w-2xl text-center text-xs leading-relaxed text-gray-400">
    &ldquo;<a
      href="https://www.flickr.com/photos/nasa2explore/55185633398/"
      class="text-terra-green focus-visible:outline-terra-green underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2"
      rel="noopener noreferrer"
      target="_blank">Hello, World</a
    >&rdquo; — Earth photographed by Artemis II Commander Reid Wiseman from an Orion spacecraft
    window after translunar injection. Credit: NASA, licensed under
    <a
      href="https://creativecommons.org/licenses/by-nc-nd/4.0/"
      class="text-terra-green focus-visible:outline-terra-green whitespace-nowrap underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2"
      rel="noopener noreferrer"
      target="_blank">CC BY-NC-ND 4.0</a
    >.
  </p>
</div>
