<script>
  import ActionButton from '$lib/components/ActionButton.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  export let form;
</script>

<svelte:head>
  <title>Other Ways to Help | Terramedic</title>
  <meta
    name="description"
    content="Learn about other ways to make a difference even without spare time or money."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-4 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Other Ways to Make a Difference
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-center text-lg text-gray-400">
        Even if you don't have spare time or money right now, there are still meaningful ways you
        can contribute to healing the planet.
      </p>

      <div class="bg-navy mb-8 rounded-lg p-6 shadow-sm">
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">
          Yale Climate Connections Solutions Hub
        </h2>
        <p class="mb-4 text-gray-300">
          The <a
            href="https://yaleclimateconnections.org/solutions/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sunrise-gold hover:underline">Yale Climate Connections Solutions Hub</a
          > is an excellent resource for anyone looking to take meaningful action, regardless of their
          circumstances. It provides:
        </p>

        <ul class="mb-4 list-disc space-y-2 pl-6 text-gray-300">
          <li>Accessible information about solutions at different scales</li>
          <li>Evidence-based approaches that make a meaningful difference</li>
          <li>Options that fit diverse lifestyles, resources, and circumstances</li>
          <li>Regular updates on news and developments</li>
        </ul>

        <div class="mt-6">
          <ActionButton
            text="Visit the Yale Climate Solutions Hub"
            href="https://yaleclimateconnections.org/solutions/"
            type="purple"
            icon="bolt"
          />
        </div>
      </div>

      <div class="bg-navy mb-8 rounded-lg p-6 shadow-sm">
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">Small Steps with Big Impact</h2>
        <p class="mb-4 text-gray-300">
          These actions require minimal time or financial investment but can still make a
          difference:
        </p>

        <div class="mb-4 grid gap-4 md:grid-cols-2">
          <div class="bg-deep-navy rounded-lg p-4">
            <h3 class="mb-2 text-base font-semibold text-white md:text-lg">Start Conversations</h3>
            <p class="text-gray-300">
              Simply talking about these issues with friends, family, and colleagues helps normalize
              the topic and spread awareness. Sharing what you've learned about warming stripes is a
              great starting point.
            </p>
          </div>

          <div class="bg-deep-navy rounded-lg p-4">
            <h3 class="mb-2 text-base font-semibold text-white md:text-lg">
              Make Conscious Choices
            </h3>
            <p class="text-gray-300">
              When making everyday decisions about food, transportation, or purchases, consider the
              environmental impact. Even small changes in routine can add up over time.
            </p>
          </div>

          <div class="bg-deep-navy rounded-lg p-4">
            <h3 class="mb-2 text-base font-semibold text-white md:text-lg">Stay Informed</h3>
            <p class="text-gray-300">
              Follow reliable news sources and subscribe to newsletters. Being informed helps you
              make better decisions and identify opportunities to take action when your
              circumstances change.
            </p>
          </div>

          <div class="bg-deep-navy rounded-lg p-4">
            <h3 class="mb-2 text-base font-semibold text-white md:text-lg">Use Your Voice</h3>
            <p class="text-gray-300">
              Contact elected officials when key votes arise. A quick phone call or email can be
              completed in minutes but helps demonstrate public support for a cleaner, healthier
              world.
            </p>
          </div>
        </div>
      </div>

      <div class="bg-navy mb-8 rounded-lg p-6 shadow-sm">
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">The Power of Community</h2>
        <p class="mb-4 text-gray-300">
          Remember that healing the planet is a collective effort. While individual actions matter,
          systemic changes driven by communities, businesses, and governments are essential for
          meaningful progress.
        </p>
        <p class="mb-4 text-gray-300">
          By learning about solutions and sharing that knowledge, you're already contributing to the
          broader movement. As your circumstances change, you may find new opportunities to engage
          more deeply through volunteering or donations.
        </p>
      </div>

      <div class="text-center">
        <p class="mb-4 text-gray-400">When you're ready to take the next step:</p>
        <div class="mx-auto flex max-w-2xl flex-col justify-center gap-4 sm:flex-row">
          <ActionButton
            text="Explore Volunteer Options"
            href="/volunteer"
            type="primary"
            icon="clock"
          />
          <ActionButton
            text="Consider Donation Options"
            href="/donate"
            type="secondary"
            icon="banknotes"
          />
        </div>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
