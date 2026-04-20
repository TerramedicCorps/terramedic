<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import OrganizationGrid from '$lib/components/OrganizationGrid.svelte';

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

      <OrganizationGrid
        promise={data.organizations}
        tagColor="blue"
        buttonColor="blue"
        emptyText="No advocate resources yet — check back soon."
        analyticsSection="organizations"
        analyticsPage="resources"
        actionText="Explore resources"
      />
    </div>
  </main>

  <Footer {form} />
</div>
