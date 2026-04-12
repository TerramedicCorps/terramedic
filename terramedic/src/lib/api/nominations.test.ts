import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock $env/dynamic/public before importing the module
vi.mock('$env/dynamic/public', () => ({
  env: { PUBLIC_API_BASE: 'http://test-api:8000/api' }
}));

import { submitNomination, lookupNominationStatus, ValidationError } from './nominations';

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('submitNomination', () => {
  test('sends POST to /api/nominations/', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ confirmation_id: 'test-uuid' })
    });

    const result = await submitNomination({
      url: 'https://example.org',
      categories: ['volunteer'],
      notes: ''
    });

    expect(fetchMock).toHaveBeenCalledWith('http://test-api:8000/api/nominations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://example.org', categories: ['volunteer'], notes: '' })
    });
    expect(result.confirmation_id).toBe('test-uuid');
  });

  test('throws ValidationError on 422', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          detail: [{ loc: ['body', 'url'], msg: 'Invalid URL' }]
        })
    });

    await expect(
      submitNomination({ url: 'bad', categories: ['volunteer'], notes: '' })
    ).rejects.toThrow(ValidationError);
  });

  test('throws on 429 rate limit', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve({ detail: 'Rate limit exceeded.' })
    });

    await expect(
      submitNomination({ url: 'https://example.org', categories: ['volunteer'], notes: '' })
    ).rejects.toThrow('Too many nominations');
  });

  test('throws generic error on other failures', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({})
    });

    await expect(
      submitNomination({ url: 'https://example.org', categories: ['volunteer'], notes: '' })
    ).rejects.toThrow('Something went wrong');
  });
});

describe('lookupNominationStatus', () => {
  test('sends GET to /api/nominations/{id}/status/', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          confirmation_id: 'test-uuid',
          status: 'pending',
          display_url: 'example.org',
          submitted_at: '2026-04-12T12:00:00+00:00'
        })
    });

    const result = await lookupNominationStatus('test-uuid');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://test-api:8000/api/nominations/test-uuid/status/'
    );
    expect(result.confirmation_id).toBe('test-uuid');
    expect(result.status).toBe('pending');
    expect(result.display_url).toBe('example.org');
    expect(result.submitted_at).toBeTruthy();
  });

  test('throws for empty confirmation ID', async () => {
    await expect(lookupNominationStatus('')).rejects.toThrow('Confirmation ID is required');
  });

  test('throws for 422 invalid format', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ detail: 'Invalid confirmation ID' })
    });

    await expect(lookupNominationStatus('not-a-uuid')).rejects.toThrow(
      'Invalid confirmation ID format'
    );
  });

  test('throws for 404 not found', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: 'Not found' })
    });

    await expect(lookupNominationStatus('nonexistent-uuid')).rejects.toThrow(
      'Nomination not found'
    );
  });
});
