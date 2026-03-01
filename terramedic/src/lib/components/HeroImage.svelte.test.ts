import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import HeroImage from './HeroImage.svelte';

describe('HeroImage', () => {
  const baseProps = {
    title: 'Welcome to',
    titleBrand: 'erramedic',
    description: 'Test description'
  };

  test('CTA button has dark text on light green background', () => {
    render(HeroImage, { props: baseProps });
    const ctaLink = screen.getByRole('link', { name: /Pick a path/i });
    expect(ctaLink.className).toContain('text-[#0a0e17]');
    expect(ctaLink.className).toContain('bg-terra-green');
  });
});
