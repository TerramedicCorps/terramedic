import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import Logo from './Logo.svelte';

describe('Logo', () => {
  test('renders wordmark text by default', () => {
    render(Logo);
    expect(screen.getByText(/erramedic/)).toBeInTheDocument();
  });

  test('full brand name is accessible for SEO and screen readers', () => {
    const { container } = render(Logo);
    expect(container.textContent).toMatch(/Terramedic/);
  });

  test('does not render wordmark when showWordmark is false', () => {
    render(Logo, { props: { showWordmark: false } });
    expect(screen.queryByText(/erramedic/)).not.toBeInTheDocument();
  });

  test('renders logo cross SVG', () => {
    const { container } = render(Logo);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  test('applies small font size', () => {
    const { container } = render(Logo, { props: { size: 'small' } });
    const logoText = container.querySelector('span');
    expect(logoText).toHaveStyle('font-size: 1.125rem');
  });

  test('applies large font size', () => {
    const { container } = render(Logo, { props: { size: 'large' } });
    const logoText = container.querySelector('span');
    expect(logoText).toHaveStyle('font-size: 2rem');
  });
});
