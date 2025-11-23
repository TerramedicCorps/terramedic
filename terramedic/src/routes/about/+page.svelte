<script>
  import ActionButton from '$lib/components/ActionButton.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import ImageModal from '$lib/components/ImageModal.svelte';
  import NavBar from '$lib/components/NavBar.svelte';

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
  <title>About Warming Stripes | Terramedic</title>
  <meta
    name="description"
    content="Learn about warming stripes, what they represent, and why they are an important visualization of climate change."
  />
</svelte:head>

<div class="flex min-h-screen flex-col bg-gray-50">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="text-terra-dark-blue mb-12 text-center text-3xl font-bold md:text-4xl lg:text-5xl">
        Terramedic and Warming Stripes
      </h1>

      <div class="mb-16 rounded-lg bg-white p-8 shadow-sm">
        <div class="flex flex-col items-center md:flex-row">
          <!-- Image on the left -->
          <div class="relative mb-16 flex w-full justify-center md:mr-8 md:mb-8 md:w-1/3">
            <img
              src="/images/terramedic-globe.svg"
              alt="Terramedic Globe"
              class="h-auto max-w-full"
            />
          </div>

          <!-- Text block -->
          <div class="w-full md:w-2/3">
            <h2 class="text-terra-dark-blue mb-4 text-xl font-bold md:text-2xl">What We Do</h2>
            <p class="mb-4">
              Terramedic turns awareness into action by connecting people who want to solve climate
              change with meaningful ways to heal our planet.
            </p>
          </div>
        </div>
      </div>

      <div class="mb-16 rounded-lg bg-white shadow-sm">
        <div class="flex flex-col md:flex-row">
          <!-- Button image on the top for mobile, right for larger screens -->
          <div class="order-1 flex w-full items-center justify-center p-8 md:order-2 md:w-1/3">
            <div
              class="relative max-w-[220px] overflow-hidden rounded-lg shadow-md transition-transform hover:scale-105"
            >
              <img
                src="/images/warming-stripes-button.png"
                alt="Climate warming stripes button"
                class="h-auto w-full"
              />
              <div class="absolute inset-0 rounded-lg ring-1 ring-gray-300/30"></div>
            </div>
          </div>

          <!-- Text content on the bottom for mobile, left for larger screens -->
          <div class="order-2 w-full p-8 md:order-1 md:w-2/3">
            <h2 class="text-terra-dark-blue mb-4 text-xl font-bold md:text-2xl">
              What are Warming Stripes?
            </h2>
            <p class="mb-4">
              Terramedic promotes warming stripes everywhere we go because they communicate the
              story of climate change so powerfully and simply.
            </p>
            <p class="mb-4">
              Created by climate scientist Ed Hawkins in 2018, warming stripes represent the average
              temperature for individual years, relative to the average temperature over a baseline
              period, typically 1961-2010. Red stripes represent years that were warmer than the
              baseline average, from lighter to deeper tones for the bigger differences. Blue
              stripes show the same for cooler years. Together, they paint the picture of a warming
              planet.
            </p>
            <p class="mb-4">
              The stripes buttons at Terramedic events help people get involved. The first step is
              wearing one and telling people what it means. The second step is up to you.
            </p>
          </div>
        </div>
      </div>

      <div class="mb-16 overflow-hidden rounded-xl bg-white shadow-sm">
        <div class="flex flex-col md:flex-row">
          <div class="from-terra-blue to-terra-dark-blue w-full bg-gradient-to-br p-8 md:w-1/2">
            <div class="relative flex h-[250px] flex-col items-center justify-center md:h-full">
              <div
                class="absolute inset-0 bg-[url('/images/WarmingStripes-1850-2024.png')] bg-cover bg-center opacity-10"
              ></div>
              <!-- Clickable image that opens modal -->
              <button
                class="relative z-10 mx-auto w-full max-w-md cursor-pointer overflow-hidden rounded-lg shadow-lg transition-transform hover:scale-[1.02]"
                on:click={() =>
                  openModal(
                    '/images/WarmingBarChart-1850-2024.png',
                    'Global temperature change 1850-2024'
                  )}
                title="Click to enlarge"
              >
                <img
                  src="/images/WarmingBarChart-1850-2024.png"
                  alt="Global temperature change 1850-2024"
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
              <!-- Credit text -->
              <p class="mt-4 text-center text-xs text-gray-600">
                Graphics and lead scientist: Ed Hawkins, NCAS, UoR. Data: Berkeley Earth &
                ERA5-Land, NOAA, UK Met Office, MeteoSwiss, DWD, SMHI, UoR & ZAMG.
              </p>
            </div>
          </div>
          <div class="mb-16 flex w-full items-center p-8 md:w-1/2 md:justify-start md:text-left">
            <div>
              <h2 class="text-terra-dark-blue mx-auto mb-4 text-2xl font-bold md:mx-0 md:text-3xl">
                The Science<br />Behind&nbsp;the Stripes
              </h2>
              <p class="mb-4">
                The data used to create warming stripes comes from multiple scientific sources,
                including: NASA's Goddard Institute for Space Studies, NOAA's National Centers for
                Environmental Information, UK Met Office Hadley Centre, and the Berkeley Earth
                Surface Temperature project. These organizations maintain long-term temperature
                records using thousands of weather stations around the world, as well as ocean data
                from ships and buoys. Even with slight differences between these datasets, they all
                show the same overall pattern: a rapid warming trend, especially since the 1980s.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-16 rounded-lg bg-white p-6 shadow-sm">
        <div class="flex flex-col md:flex-row">
          <div class="w-full pr-0 md:w-3/5 md:pr-8">
            <h2 class="text-terra-dark-blue mb-4 text-xl font-bold md:text-2xl">Take Action Now</h2>
            <p class="mb-4">
              You can help address climate change right now by volunteering your time or supporting
              climate organizations. Every contribution matters. Choose a path here to get started.
            </p>
          </div>

          <div class="mt-2 w-full md:mt-0 md:w-2/5">
            <div class="flex flex-col gap-4">
              <ActionButton text="Volunteer Your Time" href="/volunteer" type="primary" />
              <ActionButton
                text="Donate to Climate Organizations"
                href="/donate"
                type="secondary"
              />
              <ActionButton text="Explore Other Ways to Help" href="/other-actions" type="purple" />
            </div>
          </div>
        </div>
      </div>

      <div class="text-center">
        <a
          href="https://showyourstripes.info/"
          target="_blank"
          rel="noopener noreferrer"
          class="text-terra-blue inline-block hover:underline"
        >
          Visit ShowYourStripes.info for more information →
        </a>
      </div>
    </div>
  </main>

  <Footer {form} />

  <!-- Image modal component -->
  <ImageModal show={showModal} imageSrc={modalImage} imageAlt={modalAlt} on:close={closeModal} />
</div>
