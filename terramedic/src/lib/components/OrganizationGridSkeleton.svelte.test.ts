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

  test('uses flex-wrap + justify-center layout', () => {
    const { container } = render(OrganizationGridSkeleton);
    const root = container.firstElementChild;
    expect(root).toHaveClass('flex', 'flex-wrap', 'justify-center', 'gap-6');
  });

  test('cards have responsive width (full on mobile, 18rem on sm+)', () => {
    const { container } = render(OrganizationGridSkeleton, { props: { count: 1 } });
    const card = container.querySelector('.animate-pulse');
    expect(card).toHaveClass('w-full', 'sm:w-72');
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
