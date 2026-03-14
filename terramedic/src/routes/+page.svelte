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

  import { trackEvent, trackSectionView } from '$lib/utils/analytics';

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
  <link rel="canonical" href="https://terramedic.org/" />
  <title>Terramedic | Heal the Earth</title>
  <meta
    name="description"
    content="Learn about warming stripes and discover how you can help heal our planet through volunteering, donations, or daily actions."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <!-- Hero Section -->
    <section class="relative" use:trackSectionView={{ section: 'hero', page: 'home' }}>
      <HeroImage
        tagline=""
        title="Anyone can be a"
        titleBrand="erramedic"
        description="It doesn't take much to start healing our planet."
      />
    </section>

    <!-- Main Content Section -->
    <section class="section container-narrow">
      <h2 class="section-title text-white">Mother Earth is hurting.<br />But you can help her.</h2>

      <!-- Take Action Section -->
      <div
        id="take-action"
        class="mt-16 mb-16 scroll-mt-20 pt-4"
        use:trackSectionView={{ section: 'action_cards', page: 'home' }}
      >
        <div class="mb-10 px-4 text-center md:mb-12">
          <h2 class="mb-4 text-2xl font-bold text-white md:text-3xl">Choose Your Path to Action</h2>
        </div>

        <!-- Action Cards -->
        <div class="mx-auto max-w-4xl">
          <ActionCards />
        </div>

        <!-- Resources Link -->
        <div class="mt-10 px-4 text-center md:mt-12">
          <A
            href="/resources"
            class="text-terra-green inline-flex flex-wrap items-center justify-center text-lg font-medium transition-colors hover:text-green-400 md:text-xl"
          >
            <span class="mr-1">Already taking action?</span>
            <span class="inline-flex items-center whitespace-nowrap"
              >Find resources here
              <ArrowRightOutline class="ml-1 h-5 w-5" />
            </span>
          </A>
        </div>
      </div>
    </section>

    <section
      class="section container-narrow"
      use:trackSectionView={{ section: 'warming_stripes', page: 'home' }}
    >
      <div class="bg-navy overflow-hidden rounded-xl shadow-sm">
        <div class="flex flex-col md:flex-row">
          <div
            class="flex w-full items-center justify-center p-6 text-center md:w-1/2 md:justify-start md:p-10 md:text-left"
          >
            <div>
              <h3
                class="mx-auto mb-4 text-2xl font-bold text-balance text-white md:mx-0 md:text-3xl"
              >
                Understanding Warming Stripes
              </h3>
              <p class="mx-auto text-base text-gray-400 md:text-lg">
                The warming stripes show our planet's rising temperatures over time. Each stripe is
                one year, red for warmer-than-average, blue for cooler. The shift to red tells the
                story of a warming world.
              </p>
              <div class="mt-6 flex justify-center md:justify-start">
                <Button
                  href="/about"
                  color="none"
                  class="bg-btn-blue font-medium text-white hover:bg-[#0d47a1]"
                >
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
                  loading="lazy"
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
    </section>
  </main>

  <Footer {form} />

  <!-- Image modal component -->
  <ImageModal show={showModal} imageSrc={modalImage} imageAlt={modalAlt} on:close={closeModal} />
</div>
