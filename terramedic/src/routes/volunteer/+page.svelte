<script>
  import OrganizationGrid from '$lib/components/OrganizationGrid.svelte';
  import IconCard from '$lib/components/IconCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import {
    ArrowsRepeatOutline,
    UsersGroupOutline,
    GraduationCapOutline,
    GlobeOutline
  } from 'flowbite-svelte-icons';
  import { trackSectionView } from '$lib/utils/analytics';

  export let data;
  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/volunteer" />
  <title>Volunteer Opportunities | Terramedic</title>
  <meta
    name="description"
    content="Find opportunities to volunteer your time and skills to organizations making the world cleaner, safer, and healthier. Even a few hours a month makes a difference."
  />
  <meta property="og:title" content="Volunteer Opportunities | Terramedic" />
  <meta
    property="og:description"
    content="Find opportunities to volunteer your time and skills to organizations making the world cleaner, safer, and healthier."
  />
  <meta property="og:url" content="https://terramedic.org/volunteer" />
  <meta name="twitter:title" content="Volunteer Opportunities | Terramedic" />
  <meta
    name="twitter:description"
    content="Find opportunities to volunteer your time and skills to organizations making the world cleaner, safer, and healthier."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Volunteer Your Time
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-balance text-gray-400">
        These organizations are making a real impact and need people like you. Your time and skills
        can help build a healthier planet.
      </p>

      <OrganizationGrid
        promise={data.organizations}
        tagColor="blue"
        buttonColor="blue"
        emptyText="No volunteer organizations yet — check back soon."
        analyticsSection="organizations"
        analyticsPage="volunteer"
      />

      <div class="mt-16 mb-6 text-center">
        <h2 class="mb-2 text-xl font-bold text-white md:text-2xl">Why Volunteer?</h2>
        <p class="mx-auto max-w-xl text-balance text-gray-300">
          Volunteering is one of the most effective ways to create change. Even a few hours a month
          makes a difference.
        </p>
      </div>

      <div
        class="mb-8 grid gap-4 md:grid-cols-2"
        use:trackSectionView={{ section: 'why_volunteer', page: 'volunteer' }}
      >
        <IconCard
          title="Amplify Your Impact"
          description="Go beyond individual actions by joining organized efforts that multiply your contribution."
          icon={ArrowsRepeatOutline}
          color="blue"
        />
        <IconCard
          title="Build Community"
          description="Connect with like-minded people who share your commitment to a healthier planet."
          icon={UsersGroupOutline}
          color="blue"
        />
        <IconCard
          title="Develop New Skills"
          description="Gain valuable experience and knowledge while making a meaningful difference."
          icon={GraduationCapOutline}
          color="blue"
        />
        <IconCard
          title="Drive Systemic Change"
          description="Help create the large-scale shifts needed to build a cleaner, healthier world."
          icon={GlobeOutline}
          color="blue"
        />
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
