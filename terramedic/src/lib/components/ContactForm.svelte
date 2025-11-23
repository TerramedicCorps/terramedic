<script>
  import { Button, Input, Label, Textarea } from 'flowbite-svelte';
  import { onMount } from 'svelte';

  // Receive form data from SvelteKit form actions
  export let form = undefined;

  // Form state
  let firstName = '';
  let lastName = '';
  let email = '';
  let message = '';
  let subject = '';
  let organization = '';
  let isSubmitting = false;
  let isSuccess = false;
  let errorMessage = '';

  // Form can be handled by SvelteKit's form actions or client-side
  // If form is defined, use SvelteKit's enhanced form actions
  $: if (form?.success) {
    isSuccess = true;
    firstName = '';
    lastName = '';
    email = '';
    message = '';
    subject = '';
    organization = '';
  } else if (form?.error) {
    errorMessage = form.message || 'There was a problem submitting your message. Please try again.';
  }

  // Function to handle form submission
  async function handleSubmit(event) {
    // Prevent default form submission if not using enhanced form handling
    if (!event.target.checkValidity()) {
      return;
    }

    if (!form) {
      // Client-side submission if no SvelteKit form handling is available
      event.preventDefault();
      isSubmitting = true;
      errorMessage = '';

      try {
        // Netlify Forms handles this automatically when form has data-netlify="true"
        const formData = new FormData(event.target);

        // For Netlify, we need to include form-name
        formData.append('form-name', 'contact-form');

        const formEntries = Object.fromEntries(formData.entries());
        const response = await fetch('/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams(formEntries).toString()
        });

        if (response.ok) {
          isSuccess = true;
          firstName = '';
          lastName = '';
          email = '';
          message = '';
          subject = '';
          organization = '';
        } else {
          throw new Error('Network response was not ok');
        }
      } catch (error) {
        console.error('Error submitting form:', error);
        errorMessage = 'There was a problem submitting your message. Please try again.';
      } finally {
        isSubmitting = false;
      }
    }
  }

  // Reset the success message after a delay
  onMount(() => {
    return () => {
      if (isSuccess) {
        // Clean up any timers if component unmounts
        clearTimeout(successTimer);
      }
    };
  });

  let successTimer;
  /* eslint-disable svelte/infinite-reactive-loop */
  $: if (isSuccess) {
    clearTimeout(successTimer);
    successTimer = setTimeout(() => {
      isSuccess = false;
    }, 8000); // Reset after 8 seconds
  }
  /* eslint-enable svelte/infinite-reactive-loop */
</script>

<div class="contact-form-container mx-auto max-w-2xl">
  <h2 class="text-terra-dark-blue mb-6 text-center text-2xl font-bold md:text-3xl">Contact Form</h2>

  {#if isSuccess}
    <div class="success-message mb-4 rounded-md bg-green-100 p-6 text-center text-green-800">
      <h3 class="mb-2 text-xl font-bold">Thank You for Your Message!</h3>
      <p>
        We've received your message and will respond as soon as possible. Thank you for reaching
        out.
      </p>
    </div>
  {:else}
    <form
      on:submit={handleSubmit}
      name="contact-form"
      method="POST"
      data-netlify="true"
      netlify-honeypot="bot-field"
      class="space-y-4 rounded-lg bg-white p-6 shadow-sm"
    >
      <!-- Hidden inputs required by Netlify Forms -->
      <input type="hidden" name="form-name" value="contact-form" />
      <div class="hidden">
        <label>
          Don't fill this out if you're human: <input name="bot-field" />
        </label>
      </div>

      <!-- Name fields -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <Label for="firstName" class="mb-1 block text-sm text-gray-700">First Name</Label>
          <Input
            id="firstName"
            name="firstName"
            type="text"
            bind:value={firstName}
            required
            placeholder="First name"
            class="w-full bg-white text-gray-800"
          />
        </div>
        <div>
          <Label for="lastName" class="mb-1 block text-sm text-gray-700">Last Name</Label>
          <Input
            id="lastName"
            name="lastName"
            type="text"
            bind:value={lastName}
            required
            placeholder="Last name"
            class="w-full bg-white text-gray-800"
          />
        </div>
      </div>

      <!-- Email field -->
      <div>
        <Label for="email" class="mb-1 block text-sm text-gray-700">Email Address</Label>
        <Input
          id="email"
          name="email"
          type="email"
          bind:value={email}
          required
          placeholder="you@example.com"
          class="w-full bg-white text-gray-800"
        />
      </div>

      <!-- Organization field (optional) -->
      <div>
        <Label for="organization" class="mb-1 flex items-center text-sm text-gray-700">
          Organization Name
          <span class="ml-1 text-xs text-gray-500 italic">(optional)</span>
        </Label>
        <Input
          id="organization"
          name="organization"
          type="text"
          bind:value={organization}
          placeholder="Your organization (if applicable)"
          class="w-full bg-white text-gray-800"
        />
      </div>

      <!-- Subject field -->
      <div>
        <Label for="subject" class="mb-1 block text-sm text-gray-700">Subject</Label>
        <Input
          id="subject"
          name="subject"
          type="text"
          bind:value={subject}
          required
          placeholder="Message subject"
          class="w-full bg-white text-gray-800"
        />
      </div>

      <!-- Message field -->
      <div>
        <Label for="message" class="mb-1 block text-sm text-gray-700">Message</Label>
        <Textarea
          id="message"
          name="message"
          bind:value={message}
          required
          placeholder="Your message"
          rows="5"
          class="w-full bg-white text-gray-800"
        />
      </div>

      <!-- Submit button -->
      <div>
        <Button type="submit" disabled={isSubmitting} color="blue" class="w-full">
          {isSubmitting ? 'Sending...' : 'Send Message'}
        </Button>
      </div>

      {#if errorMessage}
        <div class="error-message text-sm text-red-500">
          {errorMessage}
        </div>
      {/if}
    </form>
  {/if}
</div>

<style>
  .contact-form-container {
    width: 100%;
  }
</style>
