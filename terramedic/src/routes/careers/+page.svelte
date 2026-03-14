<script>
  import OrganizationCard from '$lib/components/OrganizationCard.svelte';
  import IconCard from '$lib/components/IconCard.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import {
    GlobeOutline,
    RocketOutline,
    LightbulbOutline,
    GraduationCapOutline
  } from 'flowbite-svelte-icons';
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
  <meta property="og:title" content="Careers in Healing the Planet | Terramedic" />
  <meta
    property="og:description"
    content="Find your career in healing the planet. Browse job boards for roles in clean energy, conservation, sustainability, and more."
  />
  <meta property="og:url" content="https://terramedic.org/careers" />
  <meta name="twitter:title" content="Careers in Healing the Planet | Terramedic" />
  <meta
    name="twitter:description"
    content="Find your career in healing the planet. Browse job boards for roles in clean energy, conservation, sustainability, and more."
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

      <div class="mt-16 mb-6 text-center">
        <h2 class="mb-2 text-xl font-bold text-white md:text-2xl">
          Why Work on Healing the Planet?
        </h2>
        <p class="mx-auto max-w-xl text-balance text-gray-300">
          Environmental careers are growing fast and span every skill set. Here's why people are
          making the switch.
        </p>
      </div>

      <div
        class="mb-8 grid gap-4 md:grid-cols-2"
        use:trackSectionView={{ section: 'why_careers', page: 'careers' }}
      >
        <IconCard
          title="A Growing Field"
          description="More organizations than ever are hiring people to work on environmental solutions, from startups to governments to established companies."
          icon={RocketOutline}
          color="blue"
        />
        <IconCard
          title="Every Skill Set Counts"
          description="These organizations need engineers, marketers, designers, writers, analysts, and more — not just scientists."
          icon={LightbulbOutline}
          color="blue"
        />
        <IconCard
          title="Work That Matters"
          description="Whether you're restoring wetlands down the road or designing clean energy systems across continents, this is work you can be proud of."
          icon={GlobeOutline}
          color="blue"
        />
        <IconCard
          title="Career Changers Welcome"
          description="Transferable skills go a long way. Bootcamps, fellowships, and volunteer experience can help bridge the gap into environmental work."
          icon={GraduationCapOutline}
          color="blue"
        />
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
