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
      confirmation_id: 'NOM-TEST123',
      status: 'pending',
      url: 'https://example.org',
      created_at: '2026-04-05T12:00:00Z'
    });
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'NOM-TEST123');
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
      expect(screen.getByText(/NOM-TEST123/)).toBeInTheDocument();
    });
  });

  test('shows client-side error for invalid format without calling API', async () => {
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'INVALID');
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/must start with NOM-/i)).toBeInTheDocument();
    });
    expect(mockLookup).not.toHaveBeenCalled();
  });

  test('displays error when API returns not found', async () => {
    mockLookup.mockRejectedValueOnce(new Error('Nomination not found'));
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'NOM-UNKNOWN');
    await user.click(screen.getByRole('button', { name: /check status/i }));

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument();
    });
  });

  test('error message has role="alert" for screen readers', async () => {
    const user = userEvent.setup();

    render(StatusLookup);

    await user.type(screen.getByLabelText(/confirmation id/i), 'INVALID');
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
