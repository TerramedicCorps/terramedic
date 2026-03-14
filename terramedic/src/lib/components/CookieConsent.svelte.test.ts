import { describe, test, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import CookieConsent from './CookieConsent.svelte';

// Mock analytics
const mockInitAnalytics = vi.fn();
const mockInitPageTracking = vi.fn();
vi.mock('$lib/utils/analytics', () => ({
  initAnalytics: () => mockInitAnalytics(),
  initPageTracking: () => mockInitPageTracking(),
  trackEvent: vi.fn()
}));

describe('CookieConsent', () => {
  beforeEach(() => {
    mockInitAnalytics.mockClear();
    mockInitPageTracking.mockClear();
    localStorage.clear();
  });

  test('shows banner when no consent choice has been made', () => {
    render(CookieConsent);
    expect(screen.getByText(/we use cookies/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /decline/i })).toBeInTheDocument();
  });

  test('hides banner when user has previously accepted', () => {
    localStorage.setItem('cookie-consent', 'accepted');
    render(CookieConsent);
    expect(screen.queryByText(/we use cookies/i)).not.toBeInTheDocument();
  });

  test('hides banner when user has previously declined', () => {
    localStorage.setItem('cookie-consent', 'declined');
    render(CookieConsent);
    expect(screen.queryByText(/we use cookies/i)).not.toBeInTheDocument();
  });

  test('hides banner and stores preference when accepted', async () => {
    const user = userEvent.setup();
    render(CookieConsent);

    await user.click(screen.getByRole('button', { name: /accept/i }));

    expect(screen.queryByText(/we use cookies/i)).not.toBeInTheDocument();
    expect(localStorage.getItem('cookie-consent')).toBe('accepted');
  });

  test('hides banner and stores preference when declined', async () => {
    const user = userEvent.setup();
    render(CookieConsent);

    await user.click(screen.getByRole('button', { name: /decline/i }));

    expect(screen.queryByText(/we use cookies/i)).not.toBeInTheDocument();
    expect(localStorage.getItem('cookie-consent')).toBe('declined');
  });

  test('initializes analytics when user accepts', async () => {
    const user = userEvent.setup();
    render(CookieConsent);

    await user.click(screen.getByRole('button', { name: /accept/i }));

    expect(mockInitAnalytics).toHaveBeenCalled();
  });

  test('does not initialize analytics when user declines', async () => {
    const user = userEvent.setup();
    render(CookieConsent);

    await user.click(screen.getByRole('button', { name: /decline/i }));

    expect(mockInitAnalytics).not.toHaveBeenCalled();
  });

  test('initializes analytics on mount if previously accepted', () => {
    localStorage.setItem('cookie-consent', 'accepted');
    render(CookieConsent);

    expect(mockInitAnalytics).toHaveBeenCalled();
  });

  test('does not initialize analytics on mount if previously declined', () => {
    localStorage.setItem('cookie-consent', 'declined');
    render(CookieConsent);

    expect(mockInitAnalytics).not.toHaveBeenCalled();
  });
});
