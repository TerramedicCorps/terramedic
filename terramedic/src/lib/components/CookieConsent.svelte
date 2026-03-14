<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { initAnalytics, initPageTracking } from '$lib/utils/analytics';

  let showBanner = false;

  onMount(() => {
    const consent = localStorage.getItem('cookie-consent');
    if (consent === 'accepted') {
      initAnalytics();
      initPageTracking(page);
    } else if (!consent) {
      showBanner = true;
    }
  });

  function accept() {
    localStorage.setItem('cookie-consent', 'accepted');
    showBanner = false;
    initAnalytics();
    initPageTracking(page);
  }

  function decline() {
    localStorage.setItem('cookie-consent', 'declined');
    showBanner = false;
  }
</script>

{#if showBanner}
  <div
    class="fixed right-0 bottom-0 left-0 z-50 border-t border-white/10 bg-[#0f1829]/95 p-4 backdrop-blur-sm"
    role="region"
    aria-label="Cookie consent"
  >
    <div class="container-narrow flex flex-col items-center gap-4 sm:flex-row">
      <p class="flex-1 text-sm text-gray-300">
        We use cookies to understand how visitors interact with our site so we can improve the
        experience. No personal information is shared with third parties.
      </p>
      <div class="flex gap-3">
        <button
          on:click={decline}
          class="rounded-lg border border-white/20 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-white/10"
        >
          Decline
        </button>
        <button
          on:click={accept}
          class="bg-terra-green rounded-lg px-4 py-2 text-sm font-medium text-[#0a0e17] transition-colors hover:bg-green-400"
        >
          Accept
        </button>
      </div>
    </div>
  </div>
{/if}
