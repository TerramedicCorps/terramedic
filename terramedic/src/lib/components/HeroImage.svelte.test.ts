import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import HeroImage from './HeroImage.svelte';

describe('HeroImage', () => {
  const baseProps = {
    title: 'Welcome to',
    description: 'Test description'
  };

  test('full brand name is accessible for SEO and screen readers', () => {
    render(HeroImage, { props: baseProps });
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toMatch(/Terramedic/);
  });

  test('CTA button has dark text on white background', () => {
    render(HeroImage, { props: baseProps });
    const ctaLink = screen.getByRole('link', { name: /Pick a path/i });
    expect(ctaLink.className).toContain('text-[#0a0e17]');
    expect(ctaLink.className).toContain('bg-white');
  });
});
