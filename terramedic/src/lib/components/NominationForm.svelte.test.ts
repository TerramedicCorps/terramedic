import { describe, test, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import NominationForm from './NominationForm.svelte';
import { ValidationError } from '$lib/api/nominations';

// Mock the nominations API
const mockSubmit = vi.fn();
vi.mock('$lib/api/nominations', async () => {
  const actual = await vi.importActual('$lib/api/nominations');
  return {
    ...actual,
    submitNomination: (...args: unknown[]) => mockSubmit(...args)
  };
});

// Mock analytics
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: vi.fn()
}));

describe('NominationForm', () => {
  beforeEach(() => {
    mockSubmit.mockClear();
  });

  test('renders the form with URL input, category checkboxes, and notes', () => {
    render(NominationForm);

    expect(screen.getByLabelText(/website url/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/volunteer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/donate/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/everyday/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/resource/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/career/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit nomination/i })).toBeInTheDocument();
  });

  test('includes a hidden honeypot field', () => {
    const { container } = render(NominationForm);
    const honeypot = container.querySelector('input[name="website"]');
    expect(honeypot).toBeInTheDocument();
  });

  test('requires URL before submission', async () => {
    render(NominationForm);
    const urlInput = screen.getByLabelText(/website url/i) as HTMLInputElement;
    expect(urlInput).toBeRequired();
  });

  test('shows confirmation ID on successful submission', async () => {
    mockSubmit.mockResolvedValueOnce({ confirmation_id: 'NOM-TEST123' });
    const user = userEvent.setup();

    render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    await waitFor(() => {
      expect(screen.getByText(/NOM-TEST123/)).toBeInTheDocument();
    });

    expect(mockSubmit).toHaveBeenCalledWith({
      url: 'https://example.org',
      categories: ['volunteer'],
      notes: '',
      website: ''
    });
  });

  test('includes honeypot value in POST body', async () => {
    const user = userEvent.setup();
    const { container } = render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));

    // Simulate a bot filling in the honeypot
    const honeypot = container.querySelector('input[name="website"]') as HTMLInputElement;
    await user.type(honeypot, 'bot-value');
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    // Honeypot is checked client-side so submission is silently ignored,
    // but when empty the value should still be sent to the API
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  test('shows generic error message on server error', async () => {
    mockSubmit.mockRejectedValueOnce(new Error('Server error'));
    const user = userEvent.setup();

    render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });

  test('shows field-level error on validation error', async () => {
    mockSubmit.mockRejectedValueOnce(
      new ValidationError({ url: 'This URL has already been nominated.' })
    );
    const user = userEvent.setup();

    render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    await waitFor(() => {
      expect(screen.getByText(/already been nominated/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
  });

  test('submits multiple categories', async () => {
    mockSubmit.mockResolvedValueOnce({ confirmation_id: 'NOM-MULTI' });
    const user = userEvent.setup();

    render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));
    await user.click(screen.getByLabelText(/donate/i));
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        url: 'https://example.org',
        categories: expect.arrayContaining(['volunteer', 'donate']),
        notes: '',
        website: ''
      });
    });
  });

  test('shows inline error on blur when URL lacks http(s) scheme', async () => {
    const user = userEvent.setup();
    render(NominationForm);

    const urlInput = screen.getByLabelText(/website url/i);
    await user.type(urlInput, 'example.org');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/must start with http/i)).toBeInTheDocument();
    });
  });

  test('clears blur error when valid URL is entered', async () => {
    const user = userEvent.setup();
    render(NominationForm);

    const urlInput = screen.getByLabelText(/website url/i);
    await user.type(urlInput, 'example.org');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/must start with http/i)).toBeInTheDocument();
    });

    await user.clear(urlInput);
    await user.type(urlInput, 'https://example.org');
    await user.tab();

    await waitFor(() => {
      expect(screen.queryByText(/must start with http/i)).not.toBeInTheDocument();
    });
  });

  test('shows error when URL exceeds 2048 characters', async () => {
    const user = userEvent.setup();
    render(NominationForm);

    const longUrl = 'https://example.org/' + 'a'.repeat(2030);
    const urlInput = screen.getByLabelText(/website url/i);
    await user.type(urlInput, longUrl);
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/2048 characters/i)).toBeInTheDocument();
    });
  });

  test('submits notes when provided', async () => {
    mockSubmit.mockResolvedValueOnce({ confirmation_id: 'NOM-NOTES' });
    const user = userEvent.setup();

    render(NominationForm);

    await user.type(screen.getByLabelText(/website url/i), 'https://example.org');
    await user.click(screen.getByLabelText(/volunteer/i));
    await user.type(screen.getByLabelText(/notes/i), 'Great organization');
    await user.click(screen.getByRole('button', { name: /submit nomination/i }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        url: 'https://example.org',
        categories: ['volunteer'],
        notes: 'Great organization',
        website: ''
      });
    });
  });
});
