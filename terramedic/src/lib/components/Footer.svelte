<script>
  import SignupForm from './SignupForm.svelte';
  import Logo from './Logo.svelte';
  export let form;
</script>

<footer class="bg-abyss mt-16 pt-12 pb-8 text-gray-300">
  <!-- Top warming stripes accent bar -->
  <div class="mb-8 h-1.5 w-full bg-gradient-to-r from-blue-500 via-yellow-400 to-red-600"></div>

  <div class="container-narrow">
    <div class="grid grid-cols-1 gap-8 md:grid-cols-3 lg:gap-12">
      <div class="md:col-span-1">
        <div class="mb-2">
          <Logo size="medium" />
        </div>
        <p class="mb-4 max-w-md text-gray-400">
          Healing the Earth starts with you. Join our community of change-makers dedicated to
          building a cleaner, healthier world.
        </p>

        <!-- Social Media Icons -->
        <div class="mt-4 flex space-x-4">
          <!-- GitHub Icon -->
          <a
            href="https://github.com/lhadjchikh/terramedic"
            class="text-gray-400 transition-colors hover:text-white"
          >
            <img src="/images/github-logo.svg" alt="GitHub" class="h-6 w-6 invert" />
          </a>
        </div>
      </div>

      <div class="md:col-span-2">
        <div class="grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3">
          <div>
            <h3 class="mb-3 text-sm font-semibold tracking-wider text-gray-400 uppercase">
              Navigation
            </h3>
            <ul class="space-y-2">
              <li>
                <a href="/" class="text-gray-400 transition-colors hover:text-white">Home</a>
              </li>
              <li>
                <a href="/about" class="text-gray-400 transition-colors hover:text-white"
                  >About Warming Stripes</a
                >
              </li>
              <li>
                <a href="/volunteer" class="text-gray-400 transition-colors hover:text-white"
                  >Volunteer</a
                >
              </li>
              <li>
                <a href="/donate" class="text-gray-400 transition-colors hover:text-white">Donate</a
                >
              </li>
              <li>
                <a href="/other-actions" class="text-gray-400 transition-colors hover:text-white"
                  >Other Ways to Help</a
                >
              </li>
              <li>
                <a href="/resources" class="text-gray-400 transition-colors hover:text-white"
                  >Resources for Advocates</a
                >
              </li>
            </ul>
          </div>

          <div>
            <h3 class="mb-3 text-sm font-semibold tracking-wider text-gray-400 uppercase">
              Resources
            </h3>
            <ul class="space-y-2">
              <li>
                <a
                  href="https://showyourstripes.info/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center text-gray-400 transition-colors hover:text-white"
                >
                  Show Your Stripes
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="ml-1 h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </li>
              <li>
                <a
                  href="https://climate.nasa.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center text-gray-400 transition-colors hover:text-white"
                >
                  NASA Climate
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="ml-1 h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </li>
              <li>
                <a
                  href="https://www.ipcc.ch/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center text-gray-400 transition-colors hover:text-white"
                >
                  IPCC
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="ml-1 h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </li>
            </ul>
          </div>

          <div>
            <div class="mb-6">
              <h3 class="mb-3 text-sm font-semibold tracking-wider text-gray-400 uppercase">
                Contact Us
              </h3>
              <ul class="space-y-2">
                <li>
                  <a href="mailto:info@terramedic.org" class="text-gray-400 hover:text-white"
                    >info@terramedic.org</a
                  >
                </li>
                <li>
                  <a href="/contact-us" class="text-gray-400 hover:text-white">Contact Form</a>
                </li>
              </ul>
            </div>

            <!-- Newsletter Sign-up Form -->
            <SignupForm {form} />
          </div>
        </div>
      </div>
    </div>

    <div class="mt-12 border-t border-white/10 pt-6">
      <p class="text-center text-sm text-balance text-gray-400">
        © {new Date().getFullYear()} Terramedic Corps. Created for a healthier planet.
        <a href="/privacy" class="text-gray-400 transition-colors hover:text-white">
          Privacy Policy
        </a>
      </p>
    </div>
  </div>
</footer>
