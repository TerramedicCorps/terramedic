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
    'mailto:volunteer@example.com',
    'https://evil.example/phish',
    'http://127.0.0.1:3000/admin',
    'http://intranet/admin',
    'https://example.com@evil.example/phish'
  ])('button rejects unsafe actionUrl scheme %s', (actionUrl) => {
    render(OrganizationCard, { props: { ...baseProps, actionUrl } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  test.each([
    'http://100.64.0.1/', // CGNAT 100.64.0.0/10
    'http://192.0.0.5/', // IETF protocol assignments 192.0.0.0/24
    'http://192.0.2.5/', // TEST-NET-1 192.0.2.0/24
    'http://198.18.0.5/', // benchmark 198.18.0.0/15
    'http://198.51.100.5/', // TEST-NET-2 198.51.100.0/24
    'http://203.0.113.5/' // TEST-NET-3 203.0.113.0/24
  ])('button rejects reserved-range websiteUrl %s (matches backend is_global)', (websiteUrl) => {
    // These ranges are non-global per Python ipaddress.is_global, so the
    // serializer's is_safe_web_url rejects them. The card's mirror must
    // reject them too, or it becomes strictly more permissive than the
    // server on the one field (website_url) the API returns unsanitized.
    render(OrganizationCard, { props: { ...baseProps, websiteUrl } });
    const link = screen.queryByRole('link');
    expect(link?.getAttribute('href') ?? '').toBe('');
  });

  test.each([
    'https://exam_ple.org/', // underscore is not a valid DNS label
    'https://-example.org/', // leading hyphen
    'https://example-.org/', // trailing hyphen
    'https://exa mple.org/' // space in host
  ])('button rejects malformed-host websiteUrl %s (matches backend web_hostname)', (websiteUrl) => {
    // `new URL` tolerates underscores and edge hyphens that the backend
    // web_hostname now rejects; the mirror must reject them too so a
    // malformed website_url the API returns raw never becomes an href.
    render(OrganizationCard, { props: { ...baseProps, websiteUrl } });
    const link = screen.queryByRole('link');
    expect(link?.getAttribute('href') ?? '').toBe('');
  });

  test('button allows a numeric subdomain label', () => {
    // A digit-only label is valid as long as the TLD is not all-numeric;
    // this must not be swept up by the disguised-IP rejection.
    render(OrganizationCard, {
      props: { ...baseProps, websiteUrl: 'https://1.example.com/' }
    });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://1.example.com/');
  });

  test('button allows an organization-owned subdomain', () => {
    render(OrganizationCard, {
      props: {
        ...baseProps,
        websiteUrl: 'https://www.example.com',
        actionUrl: 'https://jobs.example.com/openings'
      }
    });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link).toHaveAttribute('href', 'https://jobs.example.com/openings');
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
