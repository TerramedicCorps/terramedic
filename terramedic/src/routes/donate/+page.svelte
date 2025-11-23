<script>
  import { donationOrganizations } from '$lib/data/donation-orgs.js';
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  export let form;
</script>

<svelte:head>
  <title>Donate to Climate Organizations | Terramedic</title>
  <meta
    name="description"
    content="Support organizations fighting climate change through donations and make a financial impact."
  />
</svelte:head>

<div class="flex min-h-screen flex-col bg-gray-50">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="text-terra-dark-blue mb-4 text-center text-3xl font-bold md:text-4xl lg:text-5xl">
        Support Climate Action
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-gray-600">
        Your financial support enables these organizations to scale their impact and implement
        powerful climate solutions. Every contribution makes a difference.
      </p>

      <div class="mx-auto grid max-w-4xl gap-6 px-4 sm:px-6 md:grid-cols-2">
        {#each donationOrganizations as org (org.websiteUrl)}
          <OrganizationCard
            name={org.name}
            description={org.description}
            websiteUrl={org.websiteUrl}
            imageUrl={org.imageUrl}
            tags={org.tags}
            actionText={org.actionText}
          />
        {/each}
      </div>

      <div class="mt-12 rounded-lg bg-white p-6 shadow-sm">
        <h2 class="text-terra-dark-blue mb-4 text-center text-xl font-bold md:text-2xl">
          Maximizing Your Climate Giving Impact
        </h2>
        <p class="mb-3">
          When donating to climate organizations, consider these factors to maximize your impact:
        </p>
        <ul class="mb-4 list-disc space-y-2 pl-6">
          <li>
            <strong>Effectiveness:</strong> Organizations that use evidence-based approaches and measure
            their results
          </li>
          <li>
            <strong>Leverage:</strong> Groups that can influence policy changes or systemic solutions
          </li>
          <li>
            <strong>Neglected areas:</strong> Issues or approaches that receive less funding but have
            high potential impact
          </li>
          <li>
            <strong>Recurring donations:</strong> Regular monthly contributions help organizations plan
            and sustain their work
          </li>
        </ul>
        <p>
          The organizations listed here have been selected based on their potential for high impact
          in addressing climate change through various approaches.
        </p>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
