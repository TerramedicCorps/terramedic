import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import OrganizationGrid from './OrganizationGrid.svelte';
import type { Organization } from '$lib/server/api';

const baseProps = {
  gridClass: 'grid gap-6 md:grid-cols-2',
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
    action_text: 'Visit',
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
    expect(screen.getByLabelText('Loading organizations')).toBeInTheDocument();
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  test('shows empty-text when the promise resolves to an empty array', async () => {
    const promise = Promise.resolve<Organization[]>([]);
    render(OrganizationGrid, { props: { ...baseProps, promise } });

    await waitFor(() => {
      expect(screen.getByText('No organizations yet.')).toBeInTheDocument();
    });
    expect(screen.queryByLabelText('Loading organizations')).not.toBeInTheDocument();
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
