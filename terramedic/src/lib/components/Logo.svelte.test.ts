import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render } from '@testing-library/svelte';
import Logo from './Logo.svelte';

describe('Logo', () => {
  test('renders visible wordmark text by default', () => {
    const { container } = render(Logo);
    const visible = container.querySelector('span[aria-hidden="true"]');
    expect(visible).toBeInTheDocument();
    expect(visible?.textContent).toBe('erramedic');
  });

  test('full brand name is accessible for SEO and screen readers', () => {
    const { container } = render(Logo);
    expect(container.textContent).toMatch(/Terramedic/);
  });

  test('full brand name is accessible even when wordmark is hidden', () => {
    const { container } = render(Logo, { props: { showWordmark: false } });
    expect(container.textContent).toMatch(/Terramedic/);
  });

  test('does not render visible wordmark when showWordmark is false', () => {
    const { container } = render(Logo, { props: { showWordmark: false } });
    const visible = container.querySelector('span[aria-hidden="true"]');
    expect(visible).not.toBeInTheDocument();
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
