<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';

  export let data;
  export let form;
</script>

<svelte:head>
  <title>Resources for Advocates | Terramedic</title>
  <meta
    name="description"
    content="Resources for advocates including research tools, communication strategies, and advocacy support."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Resources for Advocates
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-balance text-gray-400">
        Tools, research, and support for those already engaged in advocacy work.
      </p>

      <div class="mx-auto mb-12 grid max-w-4xl gap-8 px-4 sm:px-6 md:grid-cols-2">
        {#each data.organizations as org (org.id)}
          <OrganizationCard
            name={org.name}
            description={org.description}
            websiteUrl={org.website_url}
            imageUrl={org.image_url}
            actionText={org.action_text}
            tags={org.tags}
            tagColor="gold"
            buttonColor="gold"
          />
        {/each}
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
