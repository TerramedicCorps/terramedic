<script>
  import { onDestroy } from 'svelte'; // Import onDestroy

  export let images = []; // Array of image paths
  export let interval = 5000; // Time in milliseconds for auto-rotation

  let currentIndex = 0;
  let timer;

  // Start the auto-rotation
  function startRotation() {
    stopRotation(); // Clear any existing timer
    timer = setInterval(() => {
      nextImage();
    }, interval);
  }

  // Stop the auto-rotation
  function stopRotation() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  // Go to the next image
  function nextImage() {
    currentIndex = (currentIndex + 1) % images.length;
  }

  // Go to the previous image
  function prevImage() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
  }

  // Start rotation when the component is mounted
  startRotation();

  // Stop rotation when the component is destroyed
  onDestroy(() => {
    stopRotation();
  });
</script>

<div class="carousel relative h-96 w-full overflow-hidden rounded-lg bg-gray-100 md:h-[32rem]">
  <!-- Images -->
  {#if images.length > 0}
    {#each images as image, index (image)}
      <img
        src={image}
        alt="Carousel Image {index + 1}"
        class="absolute inset-0 h-full w-full object-contain transition-opacity duration-700"
        style="opacity: {index === currentIndex ? 1 : 0};"
      />
    {/each}
  {/if}

  <!-- Navigation Buttons -->
  <button
    class="absolute top-1/2 left-8 -translate-y-1/2 transform rounded-full bg-white p-2 text-black shadow-md"
    on:click={prevImage}
  >
    &#8592;
  </button>
  <button
    class="absolute top-1/2 right-0 -translate-y-1/2 transform rounded-full bg-white p-2 text-black shadow-md"
    on:click={nextImage}
  >
    &#8594;
  </button>
</div>

<style>
  .carousel img {
    opacity: 0;
    transition: opacity 0.7s ease-in-out;
  }
</style>
