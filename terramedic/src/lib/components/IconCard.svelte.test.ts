import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import IconCard from './IconCard.svelte';

describe('IconCard', () => {
  const baseProps = {
    title: 'Effectiveness',
    description: 'Organizations that use evidence-based approaches.'
  };

  test('renders title text', () => {
    render(IconCard, { props: baseProps });
    expect(screen.getByText('Effectiveness')).toBeInTheDocument();
  });

  test('renders description text', () => {
    render(IconCard, { props: baseProps });
    expect(
      screen.getByText('Organizations that use evidence-based approaches.')
    ).toBeInTheDocument();
  });

  test('title is rendered as an h3', () => {
    render(IconCard, { props: baseProps });
    const heading = screen.getByRole('heading', { level: 3, name: /Effectiveness/i });
    expect(heading).toBeInTheDocument();
  });

  test('defaults to purple color scheme', () => {
    const { container } = render(IconCard, { props: baseProps });
    const iconWrapper = container.querySelector('.bg-purple-500\\/15');
    expect(iconWrapper).toBeInTheDocument();
  });

  test('green color scheme applies green classes', () => {
    const { container } = render(IconCard, { props: { ...baseProps, color: 'green' } });
    const iconWrapper = container.querySelector('.bg-green-500\\/15');
    expect(iconWrapper).toBeInTheDocument();
  });

  test('purple color scheme does not have green classes', () => {
    const { container } = render(IconCard, { props: { ...baseProps, color: 'purple' } });
    const iconWrapper = container.querySelector('.bg-green-500\\/15');
    expect(iconWrapper).not.toBeInTheDocument();
  });

  test('green color scheme does not have purple classes', () => {
    const { container } = render(IconCard, { props: { ...baseProps, color: 'green' } });
    const iconWrapper = container.querySelector('.bg-purple-500\\/15');
    expect(iconWrapper).not.toBeInTheDocument();
  });

  test('blue color scheme applies blue classes', () => {
    const { container } = render(IconCard, { props: { ...baseProps, color: 'blue' } });
    const iconWrapper = container.querySelector('.bg-blue-500\\/15');
    expect(iconWrapper).toBeInTheDocument();
  });
});
