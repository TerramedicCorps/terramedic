import { describe, test, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import StatusLookup from './StatusLookup.svelte';

// Mock the nominations API
const mockLookup = vi.fn();
vi.mock('$lib/api/nominations', () => ({
  lookupNominationStatus: (...args: unknown[]) => mockLookup(...args)
}));

// Mock analytics
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: vi.fn()
}));

describe('StatusLookup', () => {
  beforeEach(() => {
    mockLookup.mockClear();
  });

  test('renders the lookup form with confirmation ID input', () => {
    render(StatusLookup);

    expect(screen.getByLabelText(/confirmation id/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /check status/i })).toBeInTheDocument();
  });

  test('displays status on successful lookup', async () => {
    mockLookup.mockResolvedValueOnce({
      confirmation_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
      status: 'pending',
      url: 'https://example.org',
      submitted_at: '2026-04-05T12:00:00Z'
    });
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(
      screen.getByLabelText(/confirmation id/i),
      'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    );
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
      expect(screen.getByText('a1b2c3d4-e5f6-7890-abcd-ef1234567890')).toBeInTheDocument();
    });
  });

  test('displays nominated site as plain text without scheme or query string', async () => {
    mockLookup.mockResolvedValueOnce({
      confirmation_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'pending',
      url: 'https://sierraclub.org/virginia?ref=123#top',
      submitted_at: '2026-04-05T12:00:00Z'
    });
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(
      screen.getByLabelText(/confirmation id/i),
      '550e8400-e29b-41d4-a716-446655440000'
    );
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      // Should show domain + path, no scheme/query/fragment
      expect(screen.getByText('sierraclub.org/virginia')).toBeInTheDocument();
      // Should NOT be a link
      expect(screen.queryByRole('link', { name: /sierraclub/i })).not.toBeInTheDocument();
    });
  });

  test('shows format error for non-UUID input without calling API', async () => {
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'not-a-uuid');
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid.*format/i)).toBeInTheDocument();
    });
    expect(mockLookup).not.toHaveBeenCalled();
  });

  test('displays error when API returns not found', async () => {
    mockLookup.mockRejectedValueOnce(new Error('Nomination not found'));
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(
      screen.getByLabelText(/confirmation id/i),
      'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    );
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument();
    });
  });

  test('error message has role="alert" for screen readers', async () => {
    mockLookup.mockRejectedValueOnce(new Error('Nomination not found'));
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'bad-id');
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  test('requires confirmation ID input', () => {
    render(StatusLookup);
    const input = screen.getByLabelText(/confirmation id/i) as HTMLInputElement;
    expect(input).toBeRequired();
  });
});
