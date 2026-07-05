<script>
  import { onMount } from 'svelte';
  import Logo from './Logo.svelte';

  export let tagline = 'Your planet needs you';
  export let title = '';
  export let description = '';
  export let description2 = '';

  const stars = [
    { size: 2, top: '10%', left: '15%', delay: '0s' },
    { size: 3, top: '8%', left: '75%', delay: '0.5s' },
    { size: 2, top: '25%', left: '90%', delay: '1s' },
    { size: 2, top: '15%', left: '45%', delay: '1.5s' },
    { size: 3, top: '30%', left: '20%', delay: '2s' },
    { size: 2, top: '5%', left: '60%', delay: '0.3s' },
    { size: 2, top: '20%', left: '35%', delay: '1.2s' },
    { size: 3, top: '12%', left: '85%', delay: '0.8s' }
  ];

  /** @type {HTMLVideoElement | undefined} */
  let videoEl;

  // Pause video for users who prefer reduced motion
  onMount(() => {
    if (videoEl && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      videoEl.pause();
    }
  });
</script>

<div class="hero-section relative w-full overflow-hidden">
  <!-- Space background -->
  <div class="hero-space-bg">
    <!-- Decorative stars -->
    {#each stars as star, i (i)}
      <div
        class="star"
        style="width: {star.size}px; height: {star.size}px; top: {star.top}; left: {star.left}; animation-delay: {star.delay};"
      ></div>
    {/each}

    <!-- Atmospheric glow -->
    <div class="atmosphere-glow"></div>

    <!-- Earth video -->
    <div class="earth">
      <video
        bind:this={videoEl}
        class="earth-video"
        autoplay
        loop
        muted
        playsinline
        aria-hidden="true"
        poster="/images/earth-hero-poster.jpg"
      >
        <source src="/videos/earth-hero.webm" type="video/webm" />
        <source src="/videos/earth-hero.mp4" type="video/mp4" />
      </video>
    </div>

    <!-- Dark scrim for text legibility -->
    <div class="hero-scrim"></div>

    <!-- Content overlay (absolutely positioned via .hero-content in <style>) -->
    <div
      class="hero-content z-10 flex flex-col items-center justify-start text-center"
      data-og-hero
    >
      {#if tagline}
        <p
          class="text-terra-green mb-4 text-sm font-semibold tracking-widest uppercase md:text-base"
          data-og-hide
        >
          {tagline}
        </p>
      {/if}

      {#if title}
        <h1 class="mx-auto mb-6 max-w-3xl font-bold text-white">
          <span class="block text-2xl md:text-4xl lg:text-5xl">{title}</span>
          <span class="block text-5xl whitespace-nowrap sm:text-6xl md:text-7xl lg:text-8xl">
            <Logo size="inherit" />
          </span>
        </h1>
      {/if}

      {#if description}
        <p
          class="mx-auto max-w-2xl text-base text-gray-200 md:text-lg lg:text-xl"
          class:mb-8={!description2}
          class:mb-2={description2}
          data-og-hide
        >
          {description}
        </p>
      {/if}

      {#if description2}
        <p
          class="mx-auto mb-8 max-w-2xl text-base text-gray-200 md:text-lg lg:text-xl"
          data-og-hide
        >
          {description2}
        </p>
      {/if}

      <div class="mt-16 flex flex-col gap-4 sm:flex-row" data-og-hide>
        <a
          href="#take-action"
          class="inline-flex items-center rounded-md bg-white px-6 py-3 text-base font-semibold text-[#0a0e17] transition-colors hover:bg-gray-200"
        >
          Pick a path and take a step
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="ml-2 h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </a>
      </div>
    </div>
  </div>
</div>

<style>
  .hero-space-bg {
    position: relative;
    min-height: 33rem;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    background: radial-gradient(ellipse at 50% 120%, #0a1628 0%, #060a12 50%, #000000 100%);
    overflow: hidden;
  }

  @media (min-width: 768px) {
    .hero-space-bg {
      min-height: 37rem;
    }
  }

  @media (min-width: 1024px) {
    .hero-space-bg {
      min-height: 44rem;
    }
  }

  .hero-content {
    position: absolute;
    inset: 0;
    /* Clear sticky navbar + gap */
    padding: calc(var(--navbar-height) + 2rem) 1rem 1rem;
  }

  /* Earth video — full-width background */
  .earth {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .earth-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center 100%;
  }

  /* Dark scrim between video and text */
  .hero-scrim {
    position: absolute;
    inset: 0;
    z-index: 5;
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0.8) 0%,
      rgba(0, 0, 0, 0.6) 50%,
      transparent 80%
    );
    pointer-events: none;
  }

  /* Atmospheric glow */
  .atmosphere-glow {
    position: absolute;
    bottom: -38%;
    left: 50%;
    transform: translateX(-50%);
    width: 145%;
    max-width: 940px;
    aspect-ratio: 1;
    border-radius: 50%;
    background: radial-gradient(
      circle,
      transparent 48%,
      rgba(33, 150, 243, 0.08) 50%,
      transparent 52%
    );
    pointer-events: none;
  }

  /* Decorative stars (positions set via inline styles from data array) */
  .star {
    position: absolute;
    border-radius: 50%;
    background: white;
    animation: twinkle 3s ease-in-out infinite alternate;
  }

  @keyframes twinkle {
    0% {
      opacity: 0.3;
    }
    100% {
      opacity: 1;
    }
  }
</style>
