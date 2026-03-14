<script>
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
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
  <title>Donate to Make a Difference | Terramedic</title>
  <meta
    name="description"
    content="Put your money to work for a healthier planet. Support vetted organizations driving real change through advocacy, voter mobilization, and grassroots action."
  />
  <meta property="og:title" content="Donate to Make a Difference | Terramedic" />
  <meta
    property="og:description"
    content="Put your money to work for a healthier planet. Support vetted organizations driving real change."
  />
  <meta property="og:url" content="https://terramedic.org/donate" />
  <meta name="twitter:title" content="Donate to Make a Difference | Terramedic" />
  <meta
    name="twitter:description"
    content="Put your money to work for a healthier planet. Support vetted organizations driving real change."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Power Civic Action
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-balance text-gray-400">
        From voter mobilization to grassroots advocacy, these organizations make it easy for
        everyday people to push for a healthier planet. Your donation keeps that work going.
      </p>

      <div
        class="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
        use:trackSectionView={{ section: 'organizations', page: 'donate' }}
      >
        {#each data.organizations as org (org.id)}
          <OrganizationCard
            name={org.name}
            description={org.description}
            websiteUrl={org.website_url}
            imageUrl={org.image_url}
            tags={org.tags}
            tagColor="green"
            buttonColor="green"
            actionText={org.action_text}
          />
        {/each}
      </div>

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
