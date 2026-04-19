import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import OrganizationGridSkeleton from './OrganizationGridSkeleton.svelte';

describe('OrganizationGridSkeleton', () => {
  test('defaults to 3 skeleton cards', () => {
    const { container } = render(OrganizationGridSkeleton);
    const cards = container.querySelectorAll('.animate-pulse');
    expect(cards).toHaveLength(3);
  });

  test('respects custom count prop', () => {
    const { container } = render(OrganizationGridSkeleton, { props: { count: 6 } });
    const cards = container.querySelectorAll('.animate-pulse');
    expect(cards).toHaveLength(6);
  });

  test('applies default gridClass (3-column layout)', () => {
    const { container } = render(OrganizationGridSkeleton);
    const root = container.firstElementChild;
    expect(root).toHaveClass('grid', 'gap-6', 'md:grid-cols-2', 'lg:grid-cols-3');
  });

  test('applies custom gridClass prop', () => {
    const { container } = render(OrganizationGridSkeleton, {
      props: { gridClass: 'grid gap-8 md:grid-cols-2' }
    });
    const root = container.firstElementChild;
    expect(root).toHaveClass('grid', 'gap-8', 'md:grid-cols-2');
    expect(root).not.toHaveClass('lg:grid-cols-3');
  });

  test('exposes a polite live region that announces loading', () => {
    const { container } = render(OrganizationGridSkeleton);
    const root = container.firstElementChild;
    expect(root).toHaveAttribute('role', 'status');
    expect(root).toHaveAttribute('aria-live', 'polite');
    expect(root).toHaveAttribute('aria-busy', 'true');
  });

  test('renders visually-hidden loading text for screen readers', () => {
    render(OrganizationGridSkeleton);
    expect(screen.getByText('Loading organizations')).toBeInTheDocument();
  });

  test('getByRole("status") finds the loading region', () => {
    render(OrganizationGridSkeleton);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
