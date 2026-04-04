import { describe, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';

describe('/methodology', () => {
  test('should render h1', () => {
    render(Page);
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  test('should explain the 5-step evaluation criteria', () => {
    render(Page);
    expect(screen.getByRole('heading', { name: /1\. Mission Fit/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /2\. Transparency/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /3\. Accessibility/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /4\. Legitimacy/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /5\. Evidence Score/i })).toBeInTheDocument();
  });

  test('should display the evidence scoring rubric (0–5)', () => {
    render(Page);
    expect(screen.getByText('No evidence')).toBeInTheDocument();
    expect(screen.getByText('Rigorous')).toBeInTheDocument();
  });

  test('should mention human review of AI-assisted research', () => {
    render(Page);
    expect(screen.getByRole('heading', { name: /Human Review/i })).toBeInTheDocument();
    const matches = screen.getAllByText(/humans review and approve every organization/i);
    expect(matches.length).toBeGreaterThan(0);
  });

  test('should include a way to suggest an organization', () => {
    render(Page);
    const link = screen.getByRole('link', { name: /suggest/i });
    expect(link).toBeInTheDocument();
  });
});
