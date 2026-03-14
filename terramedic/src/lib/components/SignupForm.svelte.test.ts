import { describe, test, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import SignupForm from './SignupForm.svelte';

// Mock analytics
const mockTrackEvent = vi.fn();
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: (...args: unknown[]) => mockTrackEvent(...args)
}));

// Mock fetch for Netlify form submission
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('SignupForm', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
    mockFetch.mockClear();
  });

  test('tracks newsletter_signup event on successful submission', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    const user = userEvent.setup();

    render(SignupForm);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    await user.type(emailInput, 'test@example.com');

    const submitButton = screen.getByRole('button', { name: /subscribe/i });
    await user.click(submitButton);

    expect(mockTrackEvent).toHaveBeenCalledWith('newsletter_signup', {
      method: 'footer_form'
    });
  });

  test('does not track event on failed submission', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });
    const user = userEvent.setup();

    render(SignupForm);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    await user.type(emailInput, 'test@example.com');

    const submitButton = screen.getByRole('button', { name: /subscribe/i });
    await user.click(submitButton);

    expect(mockTrackEvent).not.toHaveBeenCalled();
  });
});
