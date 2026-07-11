import { describe, test, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import OrganizationCard from './OrganizationCard.svelte';
import { trackEvent } from '$lib/utils/analytics';

// Mock analytics
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: vi.fn()
}));

describe('OrganizationCard', () => {
  const baseProps = {
    name: 'Test Org',
    description: 'A test organization',
    websiteUrl: 'https://example.com',
    actionText: 'Visit Website'
  };

  test('blue button uses btn-blue background color', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'blue' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.getAttribute('style')).toContain('--btn-blue');
  });

  test('green button uses btn-green background color', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'green' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.getAttribute('style')).toContain('--btn-green');
  });

  test('purple button uses btn-purple background color', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'purple' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.getAttribute('style')).toContain('--btn-purple');
  });

  test('gold button uses btn-gold background color', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'gold' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.getAttribute('style')).toContain('--btn-gold');
  });

  test('button text is white, not dark', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'blue' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.className).toContain('text-white');
    expect(link.className).not.toContain('text-[#0a0e17]');
  });

  test('button links to actionUrl when provided', () => {
    // Per-pathway deep link: the card must send the reader to the
    // pathway-specific page (volunteer signup, jobs board), not the
    // org homepage.
    render(OrganizationCard, {
      props: { ...baseProps, actionUrl: 'https://example.com/volunteer/signup' }
    });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://example.com/volunteer/signup');
  });

  test('button falls back to websiteUrl when actionUrl is empty', () => {
    // Unfiltered/nearby responses return action_url="" — the card
    // must still have somewhere to send the reader.
    render(OrganizationCard, { props: baseProps });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  test.each([
    'javascript:alert(document.domain)',
    'data:text/html,owned',
    'mailto:volunteer@example.com'
  ])('button rejects unsafe actionUrl scheme %s', (actionUrl) => {
    render(OrganizationCard, { props: { ...baseProps, actionUrl } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  test('click tracking reports the effective link target', async () => {
    // organization_url stays the org's identity (homepage); action_url
    // records where the click actually sent the reader, so deep-link
    // quality can be audited from analytics.
    render(OrganizationCard, {
      props: { ...baseProps, actionUrl: 'https://example.com/volunteer/signup' }
    });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    await fireEvent.click(link);
    expect(trackEvent).toHaveBeenCalledWith(
      'organization_click',
      expect.objectContaining({
        organization_url: 'https://example.com',
        action_url: 'https://example.com/volunteer/signup'
      })
    );
  });
});
