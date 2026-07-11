<script>
  import NavBar from '$lib/components/NavBar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import ContactForm from '$lib/components/ContactForm.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  /** @type {import('$lib/types/forms').FormResult | undefined} */
  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/contact-us" />
  <title>Contact Us | Terramedic</title>
  <meta
    name="description"
    content="Have questions or want to collaborate? Reach out to the Terramedic team with feedback, partnership ideas, or general inquiries. We'd love to hear from you."
  />
  <meta property="og:title" content="Contact Us | Terramedic" />
  <meta
    property="og:description"
    content="Have questions or want to collaborate? Reach out to the Terramedic team. We'd love to hear from you."
  />
  <meta property="og:url" content="https://terramedic.org/contact-us" />
  <meta name="twitter:title" content="Contact Us | Terramedic" />
  <meta
    name="twitter:description"
    content="Have questions or want to collaborate? Reach out to the Terramedic team. We'd love to hear from you."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-8 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Contact Us
      </h1>

      <div
        use:trackSectionView={{ section: 'contact_form', page: 'contact-us' }}
        class="bg-navy mx-auto mb-8 max-w-2xl rounded-lg p-6 text-center shadow-sm"
      >
        <p class="mb-4 text-gray-300">
          Have questions, feedback, or want to collaborate? We'd love to hear from you. Fill out the
          form below and we'll get back to you as soon as possible.
        </p>
        <p class="text-sm text-gray-400">
          For general inquiries, you can also email us directly at <a
            href="mailto:info@terramedic.org"
            class="text-terra-green hover:underline">info@terramedic.org</a
          >
        </p>
      </div>

      <ContactForm {form} />
    </div>
  </main>

  <Footer {form} />
</div>
