<script>
  import OrganizationGrid from '$lib/components/OrganizationGrid.svelte';
  import IconCard from '$lib/components/IconCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import {
    ChartLineUpOutline,
    ScaleBalancedOutline,
    SearchOutline,
    RefreshOutline
  } from 'flowbite-svelte-icons';
  import { trackSectionView } from '$lib/utils/analytics';

  export let data;
  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/donate" />
  <title>Explore Donation Opportunities | Terramedic</title>
  <meta
    name="description"
    content="Explore a sampling of environmental organizations working toward a healthier planet. Learn about their missions and how your donation can help."
  />
  <meta property="og:title" content="Explore Donation Opportunities | Terramedic" />
  <meta
    property="og:description"
    content="Explore a sampling of environmental organizations working toward a healthier planet."
  />
  <meta property="og:url" content="https://terramedic.org/donate" />
  <meta name="twitter:title" content="Explore Donation Opportunities | Terramedic" />
  <meta
    name="twitter:description"
    content="Explore a sampling of environmental organizations working toward a healthier planet."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Explore Donation Opportunities
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-balance text-gray-400">
        From grassroots education to community engagement, these organizations make it easy for
        everyday people to support a healthier planet. Learn about their work and how your donation
        can help.
      </p>

      <OrganizationGrid
        promise={data.organizations}
        tagColor="green"
        buttonColor="green"
        emptyText="No donation opportunities yet — check back soon."
        analyticsSection="organizations"
        analyticsPage="donate"
      />

      <div class="mt-16 mb-6 text-center">
        <h2 class="mb-2 text-xl font-bold text-white md:text-2xl">Maximizing Your Impact</h2>
        <p class="mx-auto max-w-xl text-balance text-gray-300">
          When donating to these organizations, consider these factors to maximize your impact:
        </p>
      </div>

      <div
        class="mb-8 grid gap-4 md:grid-cols-2"
        use:trackSectionView={{ section: 'maximizing_impact', page: 'donate' }}
      >
        <IconCard
          title="Effectiveness"
          description="Organizations that use evidence-based approaches and measure their results."
          icon={ChartLineUpOutline}
          color="green"
        />
        <IconCard
          title="Leverage"
          description="Groups that can influence policy changes or systemic solutions."
          icon={ScaleBalancedOutline}
          color="green"
        />
        <IconCard
          title="Neglected Areas"
          description="Issues or approaches that receive less funding but have high potential impact."
          icon={SearchOutline}
          color="green"
        />
        <IconCard
          title="Recurring Donations"
          description="Regular monthly contributions help organizations plan and sustain their work."
          icon={RefreshOutline}
          color="green"
        />
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
