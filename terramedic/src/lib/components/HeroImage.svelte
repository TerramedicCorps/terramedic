<script>
  import { onMount } from 'svelte';
  import { GREEN_CROSS } from '$lib/icons';

  export let tagline = 'Your planet needs you';
  export let title = '';
  export let titleBrand = '';
  export let description = '';
  export let description2 = '';

  // Add smooth scrolling for anchor links
  onMount(() => {
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');

    smoothScrollLinks.forEach((link) => {
      link.addEventListener('click', function (e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);

        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop - 80, // Offset for navbar height
            behavior: 'smooth'
          });
        }
      });
    });
  });
</script>

<div class="hero-section relative w-full overflow-hidden">
  <!-- Space background -->
  <div class="hero-space-bg">
    <!-- Decorative stars -->
    <div class="star star-1"></div>
    <div class="star star-2"></div>
    <div class="star star-3"></div>
    <div class="star star-4"></div>
    <div class="star star-5"></div>
    <div class="star star-6"></div>
    <div class="star star-7"></div>
    <div class="star star-8"></div>

    <!-- Atmospheric glow -->
    <div class="atmosphere-glow"></div>

    <!-- Earth video -->
    <div class="earth">
      <video
        class="earth-video"
        autoplay
        loop
        muted
        playsinline
        poster="/images/earth-hero-poster.jpg"
      >
        <source src="/videos/earth-hero.webm" type="video/webm" />
        <source src="/videos/earth-hero.mp4" type="video/mp4" />
      </video>
    </div>

    <!-- Dark scrim for text legibility -->
    <div class="hero-scrim"></div>

    <!-- Content overlay -->
    <div class="hero-content relative z-10 flex flex-col items-center justify-center text-center">
      {#if tagline}
        <p
          class="text-terra-green mb-4 text-sm font-semibold tracking-widest uppercase md:text-base"
        >
          {tagline}
        </p>
      {/if}

      {#if title || titleBrand}
        <h1 class="mx-auto mb-6 max-w-3xl font-bold text-white">
          <span class="block text-2xl md:text-4xl lg:text-5xl">{title}</span>
          {#if titleBrand}
            <span class="block text-5xl md:text-7xl lg:text-8xl"
              ><svg
                class="hero-logo-t"
                viewBox={GREEN_CROSS.viewBox}
                xmlns="http://www.w3.org/2000/svg"
                role="img"
                aria-label="Terramedic logo"
                >{#each GREEN_CROSS.arms as arm (arm.x)}<rect
                    x={arm.x}
                    y={arm.y}
                    width={arm.width}
                    height={arm.height}
                    rx={arm.rx}
                    fill={GREEN_CROSS.fill}
                  />{/each}</svg
              >{titleBrand}</span
            >
          {/if}
        </h1>
      {/if}

      {#if description}
        <p
          class="mx-auto max-w-2xl text-base text-gray-200 md:text-lg lg:text-xl"
          class:mb-8={!description2}
          class:mb-2={description2}
        >
          {description}
        </p>
      {/if}

      {#if description2}
        <p class="mx-auto mb-8 max-w-2xl text-base text-gray-200 md:text-lg lg:text-xl">
          {description2}
        </p>
      {/if}

      <div class="flex flex-col gap-4 sm:flex-row">
        <a
          href="#take-action"
          class="bg-terra-green inline-flex items-center rounded-md px-6 py-3 text-base font-semibold text-[#0a0e17] shadow-lg transition-colors hover:bg-green-400"
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
    min-height: 36rem;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    background: radial-gradient(ellipse at 50% 120%, #0a1628 0%, #060a12 50%, #000000 100%);
    overflow: hidden;
  }

  @media (min-width: 768px) {
    .hero-space-bg {
      min-height: 40rem;
    }
  }

  @media (min-width: 1024px) {
    .hero-space-bg {
      min-height: 48rem;
    }
  }

  .hero-content {
    padding: 5rem 1rem 2rem;
  }

  @media (min-width: 768px) {
    .hero-content {
      padding-top: 6rem;
    }
  }

  @media (min-width: 1024px) {
    .hero-content {
      padding-top: 7rem;
    }
  }

  /* Green cross as the "t" in terramedic */
  .hero-logo-t {
    display: inline-block;
    height: 0.85em;
    width: 0.85em;
    vertical-align: -0.05em;
    margin-right: 0.03em;
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
    object-position: center center;
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

  /* Decorative stars */
  .star {
    position: absolute;
    border-radius: 50%;
    background: white;
    animation: twinkle 3s ease-in-out infinite alternate;
  }

  .star-1 {
    width: 2px;
    height: 2px;
    top: 10%;
    left: 15%;
    animation-delay: 0s;
  }
  .star-2 {
    width: 3px;
    height: 3px;
    top: 8%;
    left: 75%;
    animation-delay: 0.5s;
  }
  .star-3 {
    width: 2px;
    height: 2px;
    top: 25%;
    left: 90%;
    animation-delay: 1s;
  }
  .star-4 {
    width: 2px;
    height: 2px;
    top: 15%;
    left: 45%;
    animation-delay: 1.5s;
  }
  .star-5 {
    width: 3px;
    height: 3px;
    top: 30%;
    left: 20%;
    animation-delay: 2s;
  }
  .star-6 {
    width: 2px;
    height: 2px;
    top: 5%;
    left: 60%;
    animation-delay: 0.3s;
  }
  .star-7 {
    width: 2px;
    height: 2px;
    top: 20%;
    left: 35%;
    animation-delay: 1.2s;
  }
  .star-8 {
    width: 3px;
    height: 3px;
    top: 12%;
    left: 85%;
    animation-delay: 0.8s;
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
