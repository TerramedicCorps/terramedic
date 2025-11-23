<script>
  import { Button, Input, Label } from 'flowbite-svelte';
  import { onMount } from 'svelte';

  // Receive form data from SvelteKit form actions
  export let form = undefined;

  // Form state
  let email = '';
  let isSubmitting = false;
  let isSuccess = false;
  let errorMessage = '';

  // Handle server-side form responses
  $: if (form?.success) {
    isSuccess = true;
    email = '';
  } else if (form?.error) {
    errorMessage =
      form.message || 'There was a problem submitting your information. Please try again.';
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
        formData.append('form-name', 'newsletter-signup');

        const formEntries = Object.fromEntries(formData.entries());
        const response = await fetch('/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams(formEntries).toString()
        });

        if (response.ok) {
          isSuccess = true;
          email = '';
        } else {
          throw new Error('Network response was not ok');
        }
      } catch (error) {
        console.error('Error submitting form:', error);
        errorMessage = 'There was a problem submitting your information. Please try again.';
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
    }, 5000); // Reset after 5 seconds
  }
  /* eslint-enable svelte/infinite-reactive-loop */
</script>

<div class="signup-form-container">
  <h3 class="mb-3 text-sm font-semibold tracking-wider text-gray-400 uppercase">
    Sign Up for Updates
  </h3>

  {#if isSuccess}
    <div class="success-message mb-4 rounded-md bg-green-100 p-3 text-green-800">
      Thank you for signing up! We'll keep you updated on climate action opportunities.
    </div>
  {:else}
    <form
      on:submit={handleSubmit}
      name="newsletter-signup"
      method="POST"
      data-netlify="true"
      netlify-honeypot="bot-field"
      class="space-y-3"
    >
      <!-- Hidden inputs required by Netlify Forms -->
      <input type="hidden" name="form-name" value="newsletter-signup" />
      <div class="hidden">
        <label>
          Don't fill this out if you're human: <input name="bot-field" />
        </label>
      </div>

      <!-- Email field -->
      <div>
        <Label for="email" class="mb-1 block text-xs text-gray-600">Email Address</Label>
        <Input
          id="email"
          name="email"
          type="email"
          bind:value={email}
          required
          placeholder="you@example.com"
          class="w-full text-gray-800"
        />
      </div>

      <!-- Submit button -->
      <div>
        <Button
          type="submit"
          disabled={isSubmitting}
          class="bg-terra-blue hover:bg-terra-dark-blue w-full text-white transition-colors"
        >
          {isSubmitting ? 'Sending...' : 'Subscribe'}
        </Button>
      </div>

      {#if errorMessage}
        <div class="error-message text-sm text-red-500">
          {errorMessage}
        </div>
      {/if}

      <p class="mt-2 text-xs text-gray-500">We respect your privacy. Unsubscribe at any time.</p>
    </form>
  {/if}
</div>

<style>
  .signup-form-container {
    width: 100%;
  }
</style>
