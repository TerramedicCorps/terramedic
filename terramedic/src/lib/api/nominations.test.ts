import { describe, test, expect } from 'vitest';
import { submitNomination, lookupNominationStatus } from './nominations';

describe('submitNomination', () => {
  test('returns a confirmation ID for valid payload', async () => {
    const result = await submitNomination({
      url: 'https://example.org',
      categories: ['volunteer'],
      notes: ''
    });
    expect(result.confirmation_id).toBeTruthy();
    expect(result.confirmation_id).toMatch(/^NOM-/);
  });

  test('throws when URL is empty', async () => {
    await expect(
      submitNomination({ url: '', categories: ['volunteer'], notes: '' })
    ).rejects.toThrow('URL is required');
  });

  test('throws when categories are empty', async () => {
    await expect(
      submitNomination({ url: 'https://example.org', categories: [], notes: '' })
    ).rejects.toThrow('At least one category is required');
  });
});

describe('lookupNominationStatus', () => {
  test('returns status for a valid confirmation ID', async () => {
    const result = await lookupNominationStatus('NOM-ABC123');
    expect(result.confirmation_id).toBe('NOM-ABC123');
    expect(result.status).toBe('pending');
    expect(result.url).toBeTruthy();
    expect(result.created_at).toBeTruthy();
  });

  test('throws for empty confirmation ID', async () => {
    await expect(lookupNominationStatus('')).rejects.toThrow('Confirmation ID is required');
  });

  test('throws for invalid confirmation ID format', async () => {
    await expect(lookupNominationStatus('INVALID-123')).rejects.toThrow('Nomination not found');
  });
});
