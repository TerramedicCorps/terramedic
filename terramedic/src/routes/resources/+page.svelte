<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import OrganizationGridSkeleton from '$lib/components/OrganizationGridSkeleton.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let data;
  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/resources" />
  <title>Resources for Advocates | Terramedic</title>
  <meta
    name="description"
    content="Tools, research, and support for those already engaged in advocacy. Find communication strategies, data resources, and organizations that amplify your impact."
  />
  <meta property="og:title" content="Resources for Advocates | Terramedic" />
  <meta
    property="og:description"
    content="Tools, research, and support for those already engaged in advocacy. Find strategies and resources that amplify your impact."
  />
  <meta property="og:url" content="https://terramedic.org/resources" />
  <meta name="twitter:title" content="Resources for Advocates | Terramedic" />
  <meta
    name="twitter:description"
    content="Tools, research, and support for those already engaged in advocacy. Find strategies and resources that amplify your impact."
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

      <div class="mx-auto mb-12 max-w-4xl px-4 sm:px-6">
        {#await data.organizations}
          <OrganizationGridSkeleton />
        {:then organizations}
          {#if organizations.length === 0}
            <p class="text-center text-gray-400">No advocate resources yet — check back soon.</p>
          {:else}
            <div
              class="grid gap-8 md:grid-cols-2"
              use:trackSectionView={{ section: 'organizations', page: 'resources' }}
            >
              {#each organizations as org (org.id)}
                <OrganizationCard
                  name={org.name}
                  description={org.description}
                  websiteUrl={org.website_url}
                  imageUrl={org.image_url}
                  actionText={org.action_text}
                  tags={org.tags}
                  tagColor="blue"
                  buttonColor="blue"
                />
              {/each}
            </div>
          {/if}
        {:catch}
          <p class="text-center text-red-400">
            Couldn't load organizations. Please refresh to try again.
          </p>
        {/await}
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
