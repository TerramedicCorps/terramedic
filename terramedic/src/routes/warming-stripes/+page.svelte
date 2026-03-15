<script>
  import Footer from '$lib/components/Footer.svelte';
  import ImageModal from '$lib/components/ImageModal.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import { trackEvent, trackSectionView } from '$lib/utils/analytics';

  export let form;

  // Modal state
  let showModal = false;
  let modalImage = '/images/2025GenerationsStripes.jpg';
  let modalAlt = '2025 Generations Stripes';

  function openModal(src: string, alt: string) {
    modalImage = src;
    modalAlt = alt;
    showModal = true;

    trackEvent('image_view', {
      image_src: src,
      image_alt: alt
    });
  }

  function closeModal() {
    showModal = false;
  }
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/warming-stripes" />
  <title>Understanding Warming Stripes | Terramedic</title>
  <meta
    name="description"
    content="Learn about warming stripes, the powerful visualization of rising global temperatures created by climate scientist Ed Hawkins, and the science behind them."
  />
  <meta property="og:title" content="Understanding Warming Stripes | Terramedic" />
  <meta
    property="og:description"
    content="Learn about warming stripes, the powerful visualization of rising global temperatures created by climate scientist Ed Hawkins."
  />
  <meta property="og:url" content="https://terramedic.org/warming-stripes" />
  <meta name="twitter:title" content="Understanding Warming Stripes | Terramedic" />
  <meta
    name="twitter:description"
    content="Learn about warming stripes, the powerful visualization of rising global temperatures created by climate scientist Ed Hawkins."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-12 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Understanding Warming Stripes
      </h1>

      <div
        class="bg-navy mb-16 rounded-lg shadow-sm"
        use:trackSectionView={{ section: 'what_are_stripes', page: 'warming-stripes' }}
      >
        <div class="flex flex-col md:flex-row">
          <!-- Button image on the top for mobile, right for larger screens -->
          <div class="order-1 flex w-full items-center justify-center p-8 md:order-2 md:w-1/3">
            <div
              class="relative max-w-[220px] overflow-hidden rounded-lg shadow-md transition-transform hover:scale-105"
            >
              <img
                src="/images/warming-stripes-button.png"
                alt="Warming stripes button"
                class="h-auto w-full"
              />
              <div class="absolute inset-0 rounded-lg ring-1 ring-white/10"></div>
            </div>
          </div>

          <!-- Text content on the bottom for mobile, left for larger screens -->
          <div class="order-2 w-full p-8 md:order-1 md:w-2/3">
            <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">What are Warming Stripes?</h2>
            <p class="mb-4 text-gray-300">
              Terramedic promotes warming stripes everywhere we go because they communicate the
              story of a warming world so powerfully and simply.
            </p>
            <p class="mb-4 text-gray-300">
              Created by climate scientist Ed Hawkins in 2018, warming stripes represent the average
              temperature for individual years, relative to the average temperature over a baseline
              period, typically 1961-2010. Red stripes represent years that were warmer than the
              baseline average, from lighter to deeper tones for the bigger differences. Blue
              stripes show the same for cooler years. Together, they paint the picture of a warming
              planet.
            </p>
            <p class="mb-4 text-gray-300">
              The stripes buttons at Terramedic events help people get involved. The first step is
              wearing one and telling people what it means. The second step is up to you.
            </p>
          </div>
        </div>
      </div>

      <div
        class="bg-navy mb-16 overflow-hidden rounded-xl shadow-sm"
        use:trackSectionView={{ section: 'science', page: 'warming-stripes' }}
      >
        <div class="flex flex-col md:flex-row">
          <div class="from-terra-blue to-terra-dark-blue w-full bg-gradient-to-br p-8 md:w-1/2">
            <div class="relative flex h-[250px] flex-col items-center justify-center md:h-full">
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
              <!-- Credit text -->
              <p class="mt-4 text-center text-xs text-gray-400">
                Graphics and lead scientist: Ed Hawkins, NCAS, UoR. Data: Berkeley Earth &
                ERA5-Land, NOAA, UK Met Office, MeteoSwiss, DWD, SMHI, UoR & ZAMG.
              </p>
            </div>
          </div>
          <div class="flex w-full items-center p-8 md:w-1/2 md:justify-start md:text-left">
            <div>
              <h2 class="mx-auto mb-4 text-2xl font-bold text-white md:mx-0 md:text-3xl">
                The Science<br />Behind&nbsp;the Stripes
              </h2>
              <p class="mb-4 text-gray-300">
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

      <div class="text-center">
        <a
          href="https://showyourstripes.info/"
          target="_blank"
          rel="noopener noreferrer"
          class="text-terra-green inline-block hover:underline"
        >
          Visit ShowYourStripes.info for more information →
        </a>
      </div>
    </div>
  </main>

  <Footer {form} />

  <ImageModal show={showModal} imageSrc={modalImage} imageAlt={modalAlt} on:close={closeModal} />
</div>
