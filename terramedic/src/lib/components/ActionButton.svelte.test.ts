import { describe, test, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import ActionButton from './ActionButton.svelte';
import { ICON_PATHS } from '$lib/icons';

// Mock analytics
vi.mock('$lib/utils/analytics', () => ({
  trackEvent: vi.fn()
}));

describe('ActionButton', () => {
  test('primary button uses btn-blue background color', () => {
    render(ActionButton, { props: { text: 'Volunteer', href: '/volunteer', type: 'primary' } });
    const link = screen.getByRole('link', { name: /Volunteer/i });
    expect(link.getAttribute('style')).toContain('--btn-blue');
  });

  test('secondary button uses btn-green background color', () => {
    render(ActionButton, { props: { text: 'Donate', href: '/donate', type: 'secondary' } });
    const link = screen.getByRole('link', { name: /Donate/i });
    expect(link.getAttribute('style')).toContain('--btn-green');
  });

  test('purple button uses btn-purple background color', () => {
    render(ActionButton, {
      props: { text: 'Other Actions', href: '/other-actions', type: 'purple' }
    });
    const link = screen.getByRole('link', { name: /Other Actions/i });
    expect(link.getAttribute('style')).toContain('--btn-purple');
  });

  test('button text is white, not dark', () => {
    render(ActionButton, { props: { text: 'Volunteer', href: '/volunteer', type: 'primary' } });
    const link = screen.getByRole('link', { name: /Volunteer/i });
    expect(link.className).toContain('text-white');
    expect(link.className).not.toContain('text-[#0a0e17]');
  });

  test('renders clock icon when icon="clock"', () => {
    const { container } = render(ActionButton, {
      props: { text: 'Volunteer', href: '/volunteer', type: 'primary', icon: 'clock' }
    });
    const svg = container.querySelector('svg.action-icon');
    expect(svg).toBeInTheDocument();
    const path = svg?.querySelector('path');
    expect(path?.getAttribute('d')).toBe(ICON_PATHS.clock);
  });

  test('renders banknotes icon when icon="banknotes"', () => {
    const { container } = render(ActionButton, {
      props: { text: 'Donate', href: '/donate', type: 'secondary', icon: 'banknotes' }
    });
    const svg = container.querySelector('svg.action-icon');
    expect(svg).toBeInTheDocument();
    const path = svg?.querySelector('path');
    expect(path?.getAttribute('d')).toBe(ICON_PATHS.banknotes);
  });

  test('renders bolt icon when icon="bolt"', () => {
    const { container } = render(ActionButton, {
      props: { text: 'Other', href: '/other-actions', type: 'purple', icon: 'bolt' }
    });
    const svg = container.querySelector('svg.action-icon');
    expect(svg).toBeInTheDocument();
    const path = svg?.querySelector('path');
    expect(path?.getAttribute('d')).toBe(ICON_PATHS.bolt);
  });

  test('renders heart icon when icon="heart"', () => {
    const { container } = render(ActionButton, {
      props: { text: 'Volunteer', href: '/volunteer', type: 'primary', icon: 'heart' }
    });
    const svg = container.querySelector('svg.action-icon');
    expect(svg).toBeInTheDocument();
    const path = svg?.querySelector('path');
    expect(path?.getAttribute('d')).toBe(ICON_PATHS.heart);
  });

  test('does not render action-icon when no icon prop is provided', () => {
    const { container } = render(ActionButton, {
      props: { text: 'Volunteer', href: '/volunteer', type: 'primary' }
    });
    const svg = container.querySelector('svg.action-icon');
    expect(svg).not.toBeInTheDocument();
  });
});
