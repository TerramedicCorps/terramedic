<script>
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let data;
  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/careers" />
  <title>Careers in Healing the Planet | Terramedic</title>
  <meta
    name="description"
    content="Find your career in healing the planet. Browse job boards for roles in clean energy, conservation, sustainability, environmental policy, and more."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Careers in Healing the Planet
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-balance text-gray-400">
        Turn your passion into your profession. These job boards connect you with organizations
        hiring people who want to make a difference.
      </p>

      <div
        class="grid gap-6 md:grid-cols-2"
        use:trackSectionView={{ section: 'organizations', page: 'careers' }}
      >
        {#each data.organizations as org (org.id)}
          <OrganizationCard
            name={org.name}
            description={org.description}
            websiteUrl={org.website_url}
            imageUrl={org.image_url}
            tags={org.tags}
            tagColor="gold"
            buttonColor="gold"
            actionText={org.action_text}
          />
        {/each}
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
