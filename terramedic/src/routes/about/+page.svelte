<script>
  import ActionButton from '$lib/components/ActionButton.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/about" />
  <title>About Terramedic Corps | Terramedic</title>
  <meta
    name="description"
    content="Terramedic turns awareness into action by connecting people who want to heal our planet with meaningful ways to make a difference."
  />
  <meta property="og:title" content="About Terramedic Corps | Terramedic" />
  <meta
    property="og:description"
    content="Terramedic turns awareness into action by connecting people who want to heal our planet with meaningful ways to make a difference."
  />
  <meta property="og:url" content="https://terramedic.org/about" />
  <meta name="twitter:title" content="About Terramedic Corps | Terramedic" />
  <meta
    name="twitter:description"
    content="Terramedic turns awareness into action by connecting people who want to heal our planet with meaningful ways to make a difference."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-12 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        About Terramedic Corps
      </h1>

      <div
        class="bg-navy mb-16 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'what_we_do', page: 'about' }}
      >
        <div class="flex flex-col items-center md:flex-row">
          <!-- Image on the left -->
          <div class="relative mb-6 flex w-full justify-center md:mr-8 md:mb-0 md:w-1/3">
            <img src="/images/logo.svg" alt="Terramedic Logo" class="h-auto w-48 md:w-64" />
          </div>

          <!-- Text block -->
          <div class="w-full md:w-2/3">
            <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">What We Do</h2>
            <p class="mb-4 text-gray-300">
              Terramedic turns awareness into action by connecting people who want to heal our
              planet with meaningful ways to make a difference.
            </p>
          </div>
        </div>
      </div>

      <div
        class="bg-navy mb-16 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'word_terramedic', page: 'about' }}
      >
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">The Word "Terramedic"</h2>
        <p class="mb-4 text-gray-300">
          The word "terramedic" was coined by Leila Hadj-Chikh as the name for her team at
          <a
            href="https://www.conservationxlabs.com/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-terra-green hover:underline">Conservation X Labs'</a
          >
          <a
            href="https://www.makefortheplanet.com/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-terra-green hover:underline">Make for the Planet</a
          >
          competition at the inaugural Earth Optimism Summit in Washington, DC in 2017.
        </p>
        <p class="mb-4 text-gray-300">
          The term is intentionally placed in the public domain under
          <a
            href="https://creativecommons.org/publicdomain/zero/1.0/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-terra-green hover:underline">CC0 1.0 Universal</a
          >. It is free for anyone to use, share, adapt, and apply in any context — without
          restriction or attribution.
        </p>
        <p class="text-gray-300">
          We encourage everyone to use "terramedics" to describe individuals and communities caring
          for the Earth.
        </p>
      </div>

      <div
        class="bg-navy mb-16 rounded-lg p-6 shadow-sm"
        use:trackSectionView={{ section: 'take_action', page: 'about' }}
      >
        <div class="flex flex-col md:flex-row">
          <div class="w-full pr-0 md:w-3/5 md:pr-8">
            <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">Take Action Now</h2>
            <p class="mb-4 text-gray-300">
              You can help heal our planet right now by volunteering your time or supporting
              organizations making a difference. Every contribution matters. Choose a path here to
              get started.
            </p>
          </div>

          <div class="mt-2 w-full md:mt-0 md:w-2/5">
            <div class="flex flex-col gap-4">
              <ActionButton
                text="Volunteer Your Time"
                href="/volunteer"
                type="primary"
                icon="heart"
              />
              <ActionButton
                text="Donate to Make a Difference"
                href="/donate"
                type="secondary"
                icon="banknotes"
              />
              <ActionButton
                text="Explore Other Ways to Help"
                href="/other-actions"
                type="purple"
                icon="bolt"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
