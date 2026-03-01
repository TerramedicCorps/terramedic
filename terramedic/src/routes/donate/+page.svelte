<script>
  import { donationOrganizations } from '$lib/data/donation-orgs.js';
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  export let form;
</script>

<svelte:head>
  <title>Donate to Make a Difference | Terramedic</title>
  <meta
    name="description"
    content="Support organizations working for a cleaner, safer world through donations and make a financial impact."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Support the Mission
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-gray-400">
        Your financial support enables these organizations to scale their impact and implement
        powerful solutions. Every contribution makes a difference.
      </p>

      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {#each donationOrganizations as org (org.websiteUrl)}
          <OrganizationCard
            name={org.name}
            description={org.description}
            websiteUrl={org.websiteUrl}
            imageUrl={org.imageUrl}
            tags={org.tags}
            tagColor="green"
            buttonColor="green"
            actionText={org.actionText}
          />
        {/each}
      </div>

      <div class="bg-navy mt-12 rounded-lg p-6 shadow-sm">
        <h2 class="mb-4 text-center text-xl font-bold text-white md:text-2xl">
          Maximizing Your Impact
        </h2>
        <p class="mb-3 text-gray-300">
          When donating to these organizations, consider these factors to maximize your impact:
        </p>
        <ul class="mb-4 list-disc space-y-2 pl-6 text-gray-300">
          <li>
            <strong class="text-white">Effectiveness:</strong> Organizations that use evidence-based
            approaches and measure their results
          </li>
          <li>
            <strong class="text-white">Leverage:</strong> Groups that can influence policy changes or
            systemic solutions
          </li>
          <li>
            <strong class="text-white">Neglected areas:</strong> Issues or approaches that receive less
            funding but have high potential impact
          </li>
          <li>
            <strong class="text-white">Recurring donations:</strong> Regular monthly contributions help
            organizations plan and sustain their work
          </li>
        </ul>
        <p class="text-gray-300">
          The organizations listed here have been selected based on their potential for high impact
          in making the world cleaner and healthier through various approaches.
        </p>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
