<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/privacy" />
  <title>Privacy Policy | Terramedic</title>
  <meta
    name="description"
    content="Terramedic's privacy policy explains how we collect, use, and protect your information, including our cookie consent practices and use of Google Analytics."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-12 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Privacy Policy
      </h1>

      <div class="mx-auto max-w-3xl space-y-10">
        <section>
          <p class="text-gray-300">
            Terramedic Corps ("we", "us", "our") respects your privacy. This policy explains what
            information we collect when you visit
            <a href="https://terramedic.org" class="text-terra-green hover:underline"
              >terramedic.org</a
            >, how we use it, and your choices.
          </p>
          <p class="mt-3 text-sm text-gray-400">Last updated: March 14, 2026</p>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Information We Collect</h2>
          <div class="space-y-4">
            <div>
              <h3 class="mb-2 font-semibold text-gray-200">Analytics (with your consent)</h3>
              <p class="text-gray-300">
                If you accept cookies, we use Google Analytics 4 to collect anonymous usage data
                such as pages visited, time on site, and general location (country/region). This
                helps us understand how visitors interact with the site so we can improve it. Google
                Analytics uses cookies to distinguish unique users. No personally identifiable
                information is sent to Google.
              </p>
            </div>
            <div>
              <h3 class="mb-2 font-semibold text-gray-200">Newsletter signup</h3>
              <p class="text-gray-300">
                If you subscribe to our newsletter, we collect your email address. This is stored
                securely by Netlify and used solely to send you updates about Terramedic.
              </p>
            </div>
            <div>
              <h3 class="mb-2 font-semibold text-gray-200">Contact form</h3>
              <p class="text-gray-300">
                If you submit the contact form, we collect your name, email address, organization
                (optional), subject, and message. This data is stored by Netlify and emailed to us
                so we can respond to your inquiry.
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Cookies</h2>
          <p class="mb-4 text-gray-300">
            We only set cookies if you click "Accept" on the cookie consent banner. If you decline,
            no cookies are set and no analytics data is collected.
          </p>
          <p class="text-gray-300">
            Your cookie preference is stored in your browser's local storage (not a cookie itself)
            so we can remember your choice on future visits. You can change your preference at any
            time by clearing your browser's local storage for this site.
          </p>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">How We Use Your Information</h2>
          <ul class="list-inside list-disc space-y-2 text-gray-300">
            <li>Analytics data is used to improve the site and measure our effectiveness</li>
            <li>Email addresses are used only for the purpose you provided them</li>
            <li>We do not sell, rent, or share your personal information with third parties</li>
            <li>We do not use your data for advertising or profiling</li>
          </ul>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Third-Party Services</h2>
          <ul class="list-inside list-disc space-y-2 text-gray-300">
            <li>
              <strong class="text-gray-200">Google Analytics 4</strong> &mdash; analytics (only with
              consent). See
              <a
                href="https://policies.google.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                class="text-terra-green hover:underline">Google's Privacy Policy</a
              >.
            </li>
            <li>
              <strong class="text-gray-200">Netlify</strong> &mdash; hosting and form submissions.
              See
              <a
                href="https://www.netlify.com/privacy/"
                target="_blank"
                rel="noopener noreferrer"
                class="text-terra-green hover:underline">Netlify's Privacy Policy</a
              >.
            </li>
          </ul>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Your Rights</h2>
          <p class="text-gray-300">
            You have the right to decline cookies, unsubscribe from our newsletter at any time, and
            request deletion of any personal information we hold. To exercise these rights, contact
            us at
            <a href="mailto:info@terramedic.org" class="text-terra-green hover:underline"
              >info@terramedic.org</a
            >.
          </p>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Changes to This Policy</h2>
          <p class="text-gray-300">
            We may update this policy from time to time. Changes will be posted on this page with an
            updated date.
          </p>
        </section>

        <section>
          <h2 class="mb-4 text-xl font-bold text-white">Contact</h2>
          <p class="text-gray-300">
            Questions about this policy? Reach us at
            <a href="mailto:info@terramedic.org" class="text-terra-green hover:underline"
              >info@terramedic.org</a
            >
            or through our
            <a href="/contact-us" class="text-terra-green hover:underline">contact form</a>.
          </p>
        </section>
      </div>
    </div>
  </main>

  <Footer {form} />
</div>
