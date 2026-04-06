<script>
  import { Button, Input, Label } from 'flowbite-svelte';
  import { lookupNominationStatus } from '$lib/api/nominations';

  let confirmationId = '';
  let isLoading = false;
  let errorMessage = '';
  let result = null;

  const statusLabels = {
    pending: 'Pending Review',
    evaluating: 'Under Evaluation',
    approved: 'Approved',
    rejected: 'Not Approved'
  };

  const statusColors = {
    pending: 'text-sunrise-gold',
    evaluating: 'text-terra-blue',
    approved: 'text-green-400',
    rejected: 'text-red-400'
  };

  async function handleSubmit(event) {
    event.preventDefault();
    isLoading = true;
    errorMessage = '';
    result = null;

    try {
      result = await lookupNominationStatus(confirmationId);
    } catch {
      errorMessage = 'Nomination not found. Please check your confirmation ID and try again.';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="status-lookup-container mx-auto max-w-2xl">
  <form on:submit={handleSubmit} class="bg-navy space-y-4 rounded-lg p-6 shadow-sm">
    <div>
      <Label for="confirmation-id" class="mb-1 block text-sm text-gray-400">Confirmation ID</Label>
      <Input
        id="confirmation-id"
        name="confirmationId"
        type="text"
        bind:value={confirmationId}
        required
        placeholder="NOM-XXXXXXXXXX"
        class="bg-deep-navy w-full text-white"
      />
    </div>

    <div>
      <Button
        type="submit"
        disabled={isLoading}
        color="none"
        class="bg-btn-blue hover:bg-btn-blue-hover w-full text-white transition-colors"
      >
        {isLoading ? 'Checking...' : 'Check Status'}
      </Button>
    </div>

    {#if errorMessage}
      <div class="error-message text-sm text-red-400">
        {errorMessage}
      </div>
    {/if}
  </form>

  {#if result}
    <div class="bg-navy mt-6 rounded-lg p-6 shadow-sm">
      <h3 class="mb-4 text-lg font-bold text-white">Nomination Status</h3>
      <dl class="space-y-3">
        <div>
          <dt class="text-sm text-gray-400">Confirmation ID</dt>
          <dd class="font-mono text-white">{result.confirmation_id}</dd>
        </div>
        <div>
          <dt class="text-sm text-gray-400">Status</dt>
          <dd class="text-lg font-semibold {statusColors[result.status] || 'text-white'}">
            {statusLabels[result.status] || result.status}
          </dd>
        </div>
        <div>
          <dt class="text-sm text-gray-400">Nominated URL</dt>
          <dd>
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              class="text-terra-blue hover:underline">{result.url}</a
            >
          </dd>
        </div>
        <div>
          <dt class="text-sm text-gray-400">Submitted</dt>
          <dd class="text-white">
            {new Date(result.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </dd>
        </div>
      </dl>
    </div>
  {/if}
</div>

<style>
  .status-lookup-container {
    width: 100%;
  }
</style>
