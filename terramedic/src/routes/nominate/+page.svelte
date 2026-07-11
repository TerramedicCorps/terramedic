<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import NominationForm from '$lib/components/NominationForm.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/nominate" />
  <title>Nominate an Organization | Terramedic</title>
  <meta
    name="description"
    content="Know an environmental organization doing great work? Nominate it for inclusion in the Terramedic database."
  />
  <meta property="og:title" content="Nominate an Organization | Terramedic" />
  <meta
    property="og:description"
    content="Know an environmental organization doing great work? Nominate it for inclusion in the Terramedic database."
  />
  <meta property="og:url" content="https://terramedic.org/nominate" />
  <meta name="twitter:title" content="Nominate an Organization | Terramedic" />
  <meta
    name="twitter:description"
    content="Know an environmental organization doing great work? Nominate it for inclusion in the Terramedic database."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-8 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Nominate an Organization
      </h1>

      <div
        use:trackSectionView={{ section: 'nomination_form', page: 'nominate' }}
        class="bg-navy mx-auto mb-8 max-w-2xl rounded-lg p-6 text-center shadow-sm"
      >
        <p class="mb-4 text-gray-300">
          Know an environmental organization that's making a difference? Help us grow our database
          by nominating it. Every nomination is reviewed by a human before inclusion.
        </p>
        <p class="text-sm text-gray-400">
          Already submitted a nomination?
          <a href="/nominate/status" class="text-terra-green hover:underline"
            >Check its status here</a
          >.
        </p>
      </div>

      <NominationForm />
    </div>
  </main>

  <Footer {form} />
</div>
