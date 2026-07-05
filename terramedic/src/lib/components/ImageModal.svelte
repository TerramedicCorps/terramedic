<script>
  export let show = false;
  export let imageSrc = '';
  export let imageAlt = '';
  // Callback prop instead of createEventDispatcher (deprecated in
  // Svelte 5): consumers pass onclose={handler}.
  export let onclose = () => {};

  function closeModal() {
    onclose();
  }

  // Close modal on Escape key
  function handleKeydown(event) {
    if (event.key === 'Escape' && show) {
      closeModal();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
  <!-- Modal backdrop with click action to close -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 transition-opacity duration-300"
    role="button"
    aria-label="Close"
    tabindex="0"
    on:click={closeModal}
    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && closeModal()}
  >
    <!-- Modal content - stop propagation to prevent closing when clicking on the image -->
    <div
      class="relative max-h-[90vh] max-w-[90vw] overflow-hidden rounded-lg bg-white shadow-xl"
      role="dialog"
      aria-modal="true"
      tabindex="0"
      on:click|stopPropagation
      on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && closeModal()}
    >
      <!-- Close button -->
      <button
        type="button"
        class="absolute top-3 right-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80 focus:outline-none"
        aria-label="Close"
        on:click={closeModal}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clip-rule="evenodd"
          />
        </svg>
      </button>

      <!-- Image with max dimensions constrained -->
      <img
        src={imageSrc}
        alt={imageAlt}
        class="h-auto max-h-[90vh] w-auto max-w-[90vw] object-contain"
      />
    </div>
  </div>
{/if}
