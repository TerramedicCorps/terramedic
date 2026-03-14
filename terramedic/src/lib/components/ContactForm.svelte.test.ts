import { describe, test, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import ContactForm from './ContactForm.svelte';

// Mock analytics
const mockTrackEvent = vi.fn();
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: (...args: unknown[]) => mockTrackEvent(...args)
}));

// Mock fetch for Netlify form submission
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('ContactForm', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
    mockFetch.mockClear();
  });

  test('tracks contact_form_submit event on successful submission', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    const user = userEvent.setup();

    render(ContactForm);

    await user.type(screen.getByPlaceholderText('First name'), 'Jane');
    await user.type(screen.getByPlaceholderText('Last name'), 'Doe');
    await user.type(screen.getByPlaceholderText('you@example.com'), 'jane@example.com');
    await user.type(screen.getByPlaceholderText('Message subject'), 'Hello');
    await user.type(screen.getByPlaceholderText('Your message'), 'Test message');

    const submitButton = screen.getByRole('button', { name: /send message/i });
    await user.click(submitButton);

    expect(mockTrackEvent).toHaveBeenCalledWith('contact_form_submit', {
      subject: 'Hello'
    });
  });

  test('does not track event on failed submission', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });
    const user = userEvent.setup();

    render(ContactForm);

    await user.type(screen.getByPlaceholderText('First name'), 'Jane');
    await user.type(screen.getByPlaceholderText('Last name'), 'Doe');
    await user.type(screen.getByPlaceholderText('you@example.com'), 'jane@example.com');
    await user.type(screen.getByPlaceholderText('Message subject'), 'Hello');
    await user.type(screen.getByPlaceholderText('Your message'), 'Test message');

    const submitButton = screen.getByRole('button', { name: /send message/i });
    await user.click(submitButton);

    expect(mockTrackEvent).not.toHaveBeenCalled();
  });
});
