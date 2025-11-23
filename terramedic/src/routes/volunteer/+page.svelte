<script>
  import { volunteerOrganizations } from '$lib/data/volunteer-orgs.js';
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  export let form;
</script>

<svelte:head>
  <title>Volunteer Opportunities | Terramedic</title>
  <meta
    name="description"
    content="Find opportunities to volunteer your time and skills to organizations fighting climate change."
  />
</svelte:head>

<div class="flex min-h-screen flex-col bg-gray-50">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="text-terra-dark-blue mb-4 text-center text-3xl font-bold md:text-4xl lg:text-5xl">
        Volunteer Your Time
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-gray-600">
        These organizations are making a real impact on climate change and need people like you.
        Your time and skills can help build a sustainable future.
      </p>

      <div class="mx-auto grid max-w-5xl gap-6 px-4 sm:px-6 md:grid-cols-2 lg:grid-cols-3">
        {#each volunteerOrganizations as org (org.websiteUrl)}
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
          Why Volunteer for Climate Action?
        </h2>
        <p class="mb-3">
          Volunteering your time to climate organizations is one of the most effective ways to
          create change. When you volunteer, you:
        </p>
        <ul class="mb-4 list-disc space-y-2 pl-6">
          <li>Amplify your impact beyond individual actions</li>
          <li>Build community with like-minded individuals</li>
          <li>Develop new skills and knowledge</li>
          <li>Help create systemic change needed to address the climate crisis</li>
        </ul>
        <p>
          Even just a few hours a month can make a significant difference when combined with the
          efforts of others.
        </p>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
