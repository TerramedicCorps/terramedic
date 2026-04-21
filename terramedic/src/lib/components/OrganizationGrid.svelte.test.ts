import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import OrganizationGrid from './OrganizationGrid.svelte';
import type { Organization } from '$lib/server/api';

const baseProps = {
  tagColor: 'blue',
  buttonColor: 'blue',
  emptyText: 'No organizations yet.',
  analyticsSection: 'organizations',
  analyticsPage: 'test'
};

function makeOrg(overrides: Partial<Organization> = {}): Organization {
  return {
    id: 1,
    name: 'Test Org',
    description: 'A test organization',
    action_text: 'Volunteer',
    website_url: 'https://example.org',
    image_url: '',
    categories: ['volunteer'],
    tags: ['climate'],
    sort_order: 0,
    ...overrides
  };
}

describe('OrganizationGrid', () => {
  test('renders skeleton while the promise is pending', () => {
    const pending = new Promise<Organization[]>(() => {
      // never resolves
    });
    const { container } = render(OrganizationGrid, {
      props: { ...baseProps, promise: pending }
    });
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  test('shows empty-text when the promise resolves to an empty array', async () => {
    const promise = Promise.resolve<Organization[]>([]);
    render(OrganizationGrid, { props: { ...baseProps, promise } });

    await waitFor(() => {
      expect(screen.getByText('No organizations yet.')).toBeInTheDocument();
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  test('renders cards when the promise resolves with organizations', async () => {
    const orgs = [makeOrg({ id: 1, name: 'First Org' }), makeOrg({ id: 2, name: 'Second Org' })];
    const promise = Promise.resolve(orgs);
    render(OrganizationGrid, { props: { ...baseProps, promise } });

    await waitFor(() => {
      expect(screen.getByText('First Org')).toBeInTheDocument();
      expect(screen.getByText('Second Org')).toBeInTheDocument();
    });
    expect(screen.queryByText('No organizations yet.')).not.toBeInTheDocument();
  });

  test('each card uses its own action_text from the organization', async () => {
    // Two orgs with different per-category action_text values — the
    // grid should render each org's own CTA, not a single shared one.
    // This is the payoff of moving action_text onto the API response:
    // two donate orgs with different theories of change get different
    // buttons instead of sharing a page-level label.
    const orgs = [
      makeOrg({ id: 1, name: 'Donate-to-CCL Org', action_text: 'Donate to CCL' }),
      makeOrg({ id: 2, name: 'Give-Green Org', action_text: 'Give' })
    ];
    const promise = Promise.resolve(orgs);
    render(OrganizationGrid, { props: { ...baseProps, promise } });

    await waitFor(() => {
      expect(screen.getByText('Donate-to-CCL Org')).toBeInTheDocument();
    });
    expect(screen.getByRole('link', { name: 'Donate to CCL' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Give' })).toBeInTheDocument();
  });

  test('shows refresh-to-retry message when the promise rejects', async () => {
    const promise = Promise.reject(new Error('API down'));
    // Suppress the unhandled-rejection warning from the test runner.
    promise.catch(() => undefined);
    render(OrganizationGrid, { props: { ...baseProps, promise } });

    await waitFor(() => {
      expect(screen.getByText(/Couldn't load organizations/)).toBeInTheDocument();
    });
  });
});
