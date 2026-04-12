<script lang="ts">
  import { Button, Input, Label } from 'flowbite-svelte';
  import { lookupNominationStatus, type NominationStatus } from '$lib/api/nominations';

  let confirmationId: string = '';
  let isLoading: boolean = false;
  let errorMessage: string = '';
  let result: NominationStatus | null = null;

  const statusLabels = {
    pending: 'Pending Review',
    evaluating: 'Under Evaluation',
    evaluated: 'Evaluation Complete',
    approved: 'Approved',
    rejected: 'Not Approved'
  };

  const statusColors = {
    pending: 'text-sunrise-gold',
    evaluating: 'text-terra-blue',
    evaluated: 'text-terra-blue',
    approved: 'text-green-400',
    rejected: 'text-red-400'
  };

  async function handleSubmit() {
    errorMessage = '';
    result = null;

    const trimmed = confirmationId.trim();
    if (!trimmed) {
      errorMessage = 'Please enter a confirmation ID.';
      return;
    }

    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidPattern.test(trimmed)) {
      errorMessage = 'Invalid confirmation ID format. Please check and try again.';
      return;
    }

    isLoading = true;

    try {
      result = await lookupNominationStatus(trimmed);
    } catch {
      errorMessage = 'Nomination not found. Please check your confirmation ID and try again.';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="status-lookup-container mx-auto max-w-2xl">
  <form on:submit|preventDefault={handleSubmit} class="bg-navy space-y-4 rounded-lg p-6 shadow-sm">
    <div>
      <Label for="confirmation-id" class="mb-1 block text-sm text-gray-400">Confirmation ID</Label>
      <Input
        id="confirmation-id"
        name="confirmationId"
        type="text"
        bind:value={confirmationId}
        required
        placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
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
      <div class="error-message text-sm text-red-400" role="alert">
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
          <dt class="text-sm text-gray-400">Nominated Site</dt>
          <dd class="break-all text-white">{result.display_url}</dd>
        </div>
        <div>
          <dt class="text-sm text-gray-400">Submitted</dt>
          <dd class="text-white">
            {new Date(result.submitted_at).toLocaleDateString('en-US', {
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
