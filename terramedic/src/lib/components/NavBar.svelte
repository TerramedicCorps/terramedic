<script>
  import Logo from './Logo.svelte';
  import {
    Navbar,
    NavBrand,
    NavLi,
    NavUl,
    NavHamburger,
    Dropdown,
    DropdownItem
  } from 'flowbite-svelte';
  import { ChevronDownOutline } from 'flowbite-svelte-icons';

  let activeUrl = '';

  // Get current path
  if (typeof window !== 'undefined') {
    activeUrl = window.location.pathname;
  }
</script>

<div class="sticky top-0 z-50">
  <div class="navbar-background relative overflow-hidden shadow-md">
    <div class="container-narrow relative z-10">
      <Navbar
        class="my-0 border-0 bg-transparent px-0 py-2"
        breakpoint="lg"
        navContainerClass="lg:flex-nowrap"
      >
        <NavBrand href="/">
          <div data-testid="nav-logo">
            <Logo size="small" />
          </div>
        </NavBrand>

        <NavHamburger class="text-white focus:ring-0" />

        <NavUl
          ulClass="flex flex-col p-4 mt-4 bg-[#0f1829]/95 border border-white/10 rounded-lg lg:flex-row lg:space-x-4 lg:mt-0 lg:text-sm lg:font-medium lg:border-0 lg:bg-transparent"
          class="nav-menu-wrapper mt-0"
        >
          <NavLi
            class="nav-item about-dropdown-trigger"
            active={activeUrl === '/about' || activeUrl === '/warming-stripes'}
          >
            <button class="nav-link about-link" aria-haspopup="true">
              About
              <ChevronDownOutline class="ms-1 h-3 w-3" />
            </button>
          </NavLi>
          <Dropdown class="z-50 rounded-lg border border-white/10 bg-[#0f1829] shadow-lg">
            <DropdownItem href="/about" class="dropdown-link">Terramedic Corps</DropdownItem>
            <DropdownItem href="/warming-stripes" class="dropdown-link"
              >Warming Stripes</DropdownItem
            >
          </Dropdown>
          <NavLi href="/volunteer" active={activeUrl === '/volunteer'} class="nav-item">
            <span class="nav-link">Volunteer</span>
          </NavLi>
          <NavLi href="/donate" active={activeUrl === '/donate'} class="nav-item">
            <span class="nav-link">Donate</span>
          </NavLi>
          <NavLi href="/other-actions" active={activeUrl === '/other-actions'} class="nav-item">
            <span class="nav-link">Other Actions</span>
          </NavLi>
          <NavLi href="/careers" active={activeUrl === '/careers'} class="nav-item">
            <span class="nav-link">Careers</span>
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
  <!-- Warming stripes accent strip -->
  <div class="warming-stripes-strip h-[5px] w-full"></div>
</div>

<style>
  /* Override Flowbite styles */
  :global(.navbar-background .nav-item) {
    width: 100%;
  }

  :global(.navbar-background .nav-link) {
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 0.5rem;
    border-radius: 0.25rem;
    transition: all 0.2s ease;
    white-space: nowrap;
    display: block;
    width: 100%;
  }

  :global(.navbar-background .about-link) {
    display: inline-flex;
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
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

  /* Below the lg breakpoint, enforce mobile layout. Flowbite v1.31.0 sets
     breakpoint context inside $effect (not during SSR), so prerendered HTML
     gets md: classes regardless of the breakpoint="lg" prop. These overrides
     correct the breakpoint behavior. Unlayered styles beat Tailwind's layered
     utilities without needing !important (CSS cascade layer rules). */
  @media (max-width: 1023px) {
    :global(.nav-menu-wrapper.hidden) {
      display: none;
    }

    :global(.navbar-background button[aria-label='Open main menu']) {
      display: inline-flex;
    }

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

  /* Solid dark navbar background */
  .navbar-background {
    background-color: var(--color-deep-navy);
  }

  /* Warming stripes accent strip */
  .warming-stripes-strip {
    background: linear-gradient(
      90deg,
      #08306b 0%,
      #2171b5 15%,
      #6baed6 25%,
      #fed976 40%,
      #fd8d3c 55%,
      #e31a1c 70%,
      #bd0026 85%,
      #800026 100%
    );
  }

  /* Dropdown link styles */
  :global(.dropdown-link) {
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
  }

  :global(.dropdown-link:hover) {
    background-color: rgba(255, 255, 255, 0.1);
    color: white;
  }

  /* Override Flowbite navbar background */
  :global(.navbar-background nav) {
    background: transparent;
    border: none;
    box-shadow: none;
  }

  /* Force correct desktop layout above the lg breakpoint. */
  @media (min-width: 1024px) {
    :global(.navbar-background nav > div) {
      flex-wrap: nowrap;
    }

    :global(.nav-menu-wrapper) {
      display: block;
      width: auto;
    }

    :global(.nav-menu-wrapper ul) {
      flex-direction: row;
    }

    :global(.navbar-background .nav-item) {
      width: auto;
    }

    :global(.navbar-background button[aria-label='Open main menu']) {
      display: none;
    }
  }
</style>
