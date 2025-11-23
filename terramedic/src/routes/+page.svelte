<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import ActionCards from '$lib/components/ActionCards.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import HeroImage from '$lib/components/HeroImage.svelte';
  import ImageModal from '$lib/components/ImageModal.svelte';
  import { A, Button } from 'flowbite-svelte';
  import { ArrowRightOutline } from 'flowbite-svelte-icons';

  export let form;

  // Modal state
  let showModal = false;
  let modalImage = '/images/2025GenerationsStripes.jpg';
  let modalAlt = '2025 Generations Stripes';

  import { trackEvent } from '$lib/utils/analytics';

  // Function to open modal
  function openModal(src, alt) {
    modalImage = src;
    modalAlt = alt;
    showModal = true;

    // Track modal open event
    trackEvent('image_view', {
      image_src: src,
      image_alt: alt
    });
  }

  // Function to close modal
  function closeModal() {
    showModal = false;
  }
</script>

<svelte:head>
  <title>Terramedic | Climate Action Hub</title>
  <meta
    name="description"
    content="Learn about warming stripes and how you can help address climate change through volunteering or donations."
  />
</svelte:head>

<div class="flex min-h-screen flex-col bg-gray-50">
  <NavBar />

  <main class="flex-grow">
    <!-- Hero Section -->
    <section class="relative">
      <HeroImage
        src="/images/hero.svg"
        alt="Anyone can become a terramedic"
        size="large"
        title="Ready&nbsp;to&nbsp;take&nbsp;action?"
        description="Move beyond awareness and join our community of climate advocates helping to heal our planet and preserve our world for future generations."
      />

      <!-- Subtle divider -->
      <div
        class="absolute right-0 bottom-0 left-0 z-20 h-6 bg-gradient-to-b from-transparent to-gray-50"
      ></div>
    </section>

    <!-- Main Content Section -->
    <section class="section container-narrow">
      <h2 class="section-title text-terra-dark-blue">Climate Crisis: Our Shared Challenge</h2>

      <!-- Take Action Section -->
      <div id="take-action" class="mt-16 mb-16 scroll-mt-20 pt-4">
        <div class="mb-10 px-4 text-center md:mb-12">
          <h2 class="text-terra-dark-blue mb-4 text-2xl font-bold md:text-3xl">
            Choose Your Path to Climate Action
          </h2>
          <p class="mx-auto max-w-2xl text-base text-gray-700 md:text-lg">
            Become a terramedic and start healing our planet today. Even if your time or money is
            limited, you can make a difference.
          </p>
        </div>

        <!-- Action Cards -->
        <div class="mx-auto max-w-4xl">
          <ActionCards />
        </div>

        <!-- Resources Link -->
        <div class="mt-10 px-4 text-center md:mt-12">
          <A
            href="/resources"
            class="text-terra-dark-blue hover:text-terra-blue inline-flex flex-wrap items-center justify-center text-lg font-medium transition-colors md:text-xl"
          >
            <span class="mr-1">Already a climate advocate? Find resources here</span>
            <ArrowRightOutline class="h-5 w-5" />
          </A>
        </div>
      </div>
    </section>

    <div class="mt-16 overflow-hidden rounded-xl bg-white shadow-sm">
      <div class="flex flex-col md:flex-row">
        <div
          class="flex w-full items-center justify-center p-6 text-center md:w-1/2 md:justify-start md:p-10 md:text-left"
        >
          <div>
            <h3 class="text-terra-dark-blue mx-auto mb-4 text-2xl font-bold md:mx-0 md:text-3xl">
              Understanding Warming Stripes
            </h3>
            <p class="mx-auto text-base text-gray-700 md:text-lg">
              The warming stripes (a.k.a. climate stripes) show our planet's rising temperatures
              over time. Each stripe is one year, red for warmer-than-average, blue for cooler. The
              shift to red tells the story of climate change.
            </p>
            <div class="mt-6 flex justify-center md:justify-start">
              <Button href="/about" color="blue" class="font-medium">
                <span>Learn more about warming stripes</span>
                <ArrowRightOutline class="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <div
          class="from-terra-blue to-terra-dark-blue w-full bg-gradient-to-br p-6 md:w-1/2 md:p-8"
        >
          <div class="relative flex h-[250px] items-center justify-center md:h-full">
            <div
              class="absolute inset-0 bg-[url('/images/WarmingStripes-1850-2024.png')] bg-cover bg-center opacity-10"
            ></div>
            <!-- Clickable image that opens modal -->
            <button
              class="relative z-10 mx-auto w-full max-w-md cursor-pointer overflow-hidden rounded-lg shadow-lg transition-transform hover:scale-[1.02]"
              on:click={() =>
                openModal('/images/2025GenerationsStripes.jpg', '2025 Generations Stripes')}
              title="Click to enlarge"
            >
              <img
                src="/images/2025GenerationsStripes.jpg"
                alt="2025 Generations Stripes"
                class="w-full object-contain"
              />
              <!-- Zoom indicator overlay -->
              <div
                class="absolute right-2 bottom-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5 8a1 1 0 011-1h1V6a1 1 0 012 0v1h1a1 1 0 110 2H9v1a1 1 0 11-2 0V9H6a1 1 0 01-1-1z"
                  />
                  <path
                    fill-rule="evenodd"
                    d="M2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8zm6-4a4 4 0 100 8 4 4 0 000-8z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>

  <Footer {form} />

  <!-- Image modal component -->
  <ImageModal show={showModal} imageSrc={modalImage} imageAlt={modalAlt} on:close={closeModal} />
</div>
