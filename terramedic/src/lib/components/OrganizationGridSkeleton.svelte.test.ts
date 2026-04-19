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

  test('sets aria-busy=true on the root for assistive tech', () => {
    const { container } = render(OrganizationGridSkeleton);
    const root = container.firstElementChild;
    expect(root).toHaveAttribute('aria-busy', 'true');
  });

  test('exposes an accessible loading label', () => {
    render(OrganizationGridSkeleton);
    expect(screen.getByLabelText('Loading organizations')).toBeInTheDocument();
  });
});
