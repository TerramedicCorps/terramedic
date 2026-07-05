<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import StatusLookup from '$lib/components/StatusLookup.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/nominate/status" />
  <title>Nomination Status | Terramedic</title>
  <meta
    name="description"
    content="Check the status of your organization nomination using your confirmation ID."
  />
  <meta property="og:title" content="Nomination Status | Terramedic" />
  <meta
    property="og:description"
    content="Check the status of your organization nomination using your confirmation ID."
  />
  <meta property="og:url" content="https://terramedic.org/nominate/status" />
  <meta name="twitter:title" content="Nomination Status | Terramedic" />
  <meta
    name="twitter:description"
    content="Check the status of your organization nomination using your confirmation ID."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-8 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Nomination Status
      </h1>

      <div
        use:trackSectionView={{ section: 'status_lookup', page: 'nominate-status' }}
        class="bg-navy mx-auto mb-8 max-w-2xl rounded-lg p-6 text-center shadow-sm"
      >
        <p class="mb-4 text-gray-300">
          Enter the confirmation ID you received when you submitted your nomination to check its
          current status.
        </p>
        <p class="text-sm text-gray-400">
          Want to nominate an organization?
          <a href="/nominate" class="text-terra-green hover:underline">Submit a nomination here</a>.
        </p>
      </div>

      <StatusLookup />
    </div>
  </main>

  <Footer {form} />
</div>
