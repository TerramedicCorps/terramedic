<script>
  import { Button, Input, Label, Textarea } from 'flowbite-svelte';
  import { submitNomination } from '$lib/api/nominations';
  import { trackEvent } from '$lib/utils/analytics';

  // Form state
  let url = '';
  let categories = [];
  let notes = '';
  let honeypot = '';
  let isSubmitting = false;
  let confirmationId = '';
  let errorMessage = '';
  let urlError = '';

  const URL_MAX_LENGTH = 2048;

  const categoryOptions = [
    { value: 'volunteer', label: 'Volunteer' },
    { value: 'donate', label: 'Donate' },
    { value: 'everyday', label: 'Everyday Actions' },
    { value: 'resource', label: 'Resource' },
    { value: 'career', label: 'Career' }
  ];

  function validateUrl() {
    if (!url) {
      urlError = '';
      return;
    }
    if (url.length > URL_MAX_LENGTH) {
      urlError = `URL must be under ${URL_MAX_LENGTH} characters.`;
    } else if (!/^https?:\/\//i.test(url)) {
      urlError = 'URL must start with http:// or https://.';
    } else {
      urlError = '';
    }
  }

  function handleCheckbox(value) {
    if (categories.includes(value)) {
      categories = categories.filter((c) => c !== value);
    } else {
      categories = [...categories, value];
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    // Honeypot check — if filled, silently ignore
    if (honeypot) return;

    if (categories.length === 0) {
      errorMessage = 'Please select at least one category.';
      return;
    }

    isSubmitting = true;
    errorMessage = '';

    try {
      const result = await submitNomination({ url, categories, notes });
      confirmationId = result.confirmation_id;
      trackEvent('nomination_submit', { categories: categories.join(',') });
    } catch {
      errorMessage = 'Something went wrong. Please try again.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="nomination-form-container mx-auto max-w-2xl">
  {#if confirmationId}
    <div class="success-message mb-4 rounded-md bg-green-900/30 p-6 text-center text-green-400">
      <h3 class="mb-2 text-xl font-bold">Nomination Received</h3>
      <p class="mb-3">Thank you for nominating an organization. Your confirmation ID is:</p>
      <p class="font-mono text-lg font-semibold text-white">{confirmationId}</p>
      <p class="mt-3 text-sm text-gray-400">
        Save this ID to check on your nomination's status at
        <a href="/nominate/status" class="text-terra-green hover:underline">/nominate/status</a>.
      </p>
    </div>
  {:else}
    <form on:submit={handleSubmit} class="bg-navy space-y-4 rounded-lg p-6 shadow-sm">
      <!-- Honeypot field — hidden from real users -->
      <div class="absolute -left-[9999px]" aria-hidden="true">
        <label>
          Do not fill this in: <input
            name="website"
            bind:value={honeypot}
            tabindex="-1"
            autocomplete="off"
          />
        </label>
      </div>

      <!-- URL input -->
      <div>
        <Label for="nomination-url" class="mb-1 block text-sm text-gray-400">Website URL</Label>
        <Input
          id="nomination-url"
          name="url"
          type="url"
          bind:value={url}
          onBlur={validateUrl}
          required
          placeholder="https://example.org"
          class="bg-deep-navy w-full text-white"
        />
        {#if urlError}
          <p class="mt-1 text-sm text-red-400">{urlError}</p>
        {/if}
      </div>

      <!-- Category checkboxes -->
      <fieldset>
        <legend class="mb-2 block text-sm text-gray-400">Categories</legend>
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {#each categoryOptions as option (option.value)}
            <label
              class="bg-deep-navy flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-white transition-colors hover:bg-white/5"
            >
              <input
                type="checkbox"
                value={option.value}
                checked={categories.includes(option.value)}
                on:change={() => handleCheckbox(option.value)}
                class="accent-terra-green bg-deep-navy h-4 w-4 rounded border-gray-600"
              />
              {option.label}
            </label>
          {/each}
        </div>
      </fieldset>

      <!-- Notes (optional) -->
      <div>
        <Label for="nomination-notes" class="mb-1 flex items-center text-sm text-gray-400">
          Notes
          <span class="ml-1 text-xs text-gray-400 italic">(optional)</span>
        </Label>
        <Textarea
          id="nomination-notes"
          name="notes"
          bind:value={notes}
          placeholder="Anything we should know about this organization?"
          rows="3"
          class="bg-deep-navy w-full text-white"
        />
      </div>

      <!-- Submit button -->
      <div>
        <Button
          type="submit"
          disabled={isSubmitting}
          color="none"
          class="bg-btn-green hover:bg-btn-green-hover w-full text-white transition-colors"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Nomination'}
        </Button>
      </div>

      {#if errorMessage}
        <div class="error-message text-sm text-red-400">
          {errorMessage}
        </div>
      {/if}
    </form>
  {/if}
</div>

<style>
  .nomination-form-container {
    width: 100%;
  }
</style>
