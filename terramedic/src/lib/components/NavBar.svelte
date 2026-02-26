<script>
  import Logo from './Logo.svelte';
  import { Navbar, NavBrand, NavLi, NavUl, NavHamburger } from 'flowbite-svelte';

  let activeUrl = '';

  // Get current path
  if (typeof window !== 'undefined') {
    activeUrl = window.location.pathname;
  }
</script>

<div class="sticky top-0 z-50">
  <div class="navbar-background relative overflow-hidden shadow-md">
    <!-- Center blur overlay - edges stay clear -->
    <div
      class="blur-container pointer-events-none absolute top-0 bottom-0 left-1/2 -translate-x-1/2"
    ></div>

    <div class="container-narrow relative z-10">
      <Navbar navClass="px-0 py-2 my-0 bg-transparent !border-0" breakpoint="lg">
        <NavBrand href="/">
          <div class="rounded-md bg-white p-1" data-testid="nav-logo">
            <Logo size="small" />
          </div>
        </NavBrand>

        <NavHamburger class="text-white focus:ring-0" />

        <NavUl
          ulClass="flex flex-col p-4 mt-4 bg-[#1a2a38]/95 border border-slate-700/30 rounded-lg lg:flex-row lg:space-x-4 lg:mt-0 lg:text-sm lg:font-medium lg:border-0 lg:bg-transparent"
          class="nav-menu-wrapper mt-0"
        >
          <NavLi href="/" active={activeUrl === '/'} class="nav-item">
            <span class="nav-link">Home</span>
          </NavLi>
          <NavLi href="/about" active={activeUrl === '/about'} class="nav-item">
            <span class="nav-link">About</span>
          </NavLi>
          <NavLi href="/volunteer" active={activeUrl === '/volunteer'} class="nav-item">
            <span class="nav-link">Volunteer</span>
          </NavLi>
          <NavLi href="/donate" active={activeUrl === '/donate'} class="nav-item">
            <span class="nav-link">Donate</span>
          </NavLi>
          <NavLi href="/other-actions" active={activeUrl === '/other-actions'} class="nav-item">
            <span class="nav-link">Other Actions</span>
          </NavLi>
          <NavLi href="/resources" active={activeUrl === '/resources'} class="nav-item">
            <span class="nav-link">Resources</span>
          </NavLi>
          <NavLi href="/contact-us" active={activeUrl === '/contact-us'} class="nav-item">
            <span class="nav-link">Contact</span>
          </NavLi>
        </NavUl>
      </Navbar>
    </div>
  </div>
</div>

<style>
  /* Center blur container with clear edges */
  .blur-container {
    width: 70%;
    backdrop-filter: blur(5px);
    z-index: 5;
  }

  /* Override Flowbite styles */
  :global(.navbar-background .nav-item) {
    width: 100%;
  }

  :global(.navbar-background .nav-link) {
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    border-radius: 0.25rem;
    transition: all 0.2s ease;
    white-space: nowrap;
    display: block;
    width: 100%;
  }

  :global(.navbar-background .nav-item:hover .nav-link) {
    background-color: rgba(255, 255, 255, 0.1);
  }

  :global(.navbar-background .nav-item.active .nav-link) {
    text-decoration: underline;
    text-underline-offset: 4px;
    font-weight: 700;
    background-color: rgba(255, 255, 255, 0.1);
  }

  /* Media query for mobile menu items */
  @media (max-width: 1023px) {
    :global(.navbar-background .nav-item) {
      padding: 0.25rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    :global(.navbar-background .nav-item:last-child) {
      border-bottom: none;
    }

    :global(.navbar-background .nav-link) {
      padding: 0.75rem 1rem;
    }
  }

  /* Background image for the navbar */
  .navbar-background {
    background-image: url('/images/WarmingStripes-1850-2024.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
  }

  /* Override Flowbite navbar background */
  :global(.navbar-background nav) {
    background: transparent;
    border: none;
    box-shadow: none;
  }

  /* Flowbite's theme applies hidden, w-full, and flex-col as base classes.
     Tailwind v4's responsive variants (lg:block, lg:w-auto, lg:flex-row)
     don't reliably override these base utilities in production builds.
     Force correct desktop layout. */
  @media (min-width: 1024px) {
    :global(.nav-menu-wrapper) {
      display: block !important;
      width: auto !important;
    }

    :global(.nav-menu-wrapper ul) {
      flex-direction: row !important;
    }

    :global(.navbar-background .nav-item) {
      width: auto;
    }
  }
</style>
