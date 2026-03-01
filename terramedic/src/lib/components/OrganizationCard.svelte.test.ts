import { describe, test, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import OrganizationCard from './OrganizationCard.svelte';

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

  test('button text is white, not dark', () => {
    render(OrganizationCard, { props: { ...baseProps, buttonColor: 'blue' } });
    const link = screen.getByRole('link', { name: /Visit Website/i });
    expect(link.className).toContain('text-white');
    expect(link.className).not.toContain('text-[#0a0e17]');
  });
});
