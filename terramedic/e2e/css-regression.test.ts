import { expect, test } from '@playwright/test';

test.describe('Navbar responsive layout', () => {
  test('nav links should be visible and inline on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    // Check that all nav links are visible
    const navLinks = ['Volunteer', 'Donate', 'Other Actions', 'Careers', 'Resources', 'Contact'];
    const nav = page.locator('nav');
    for (const linkText of navLinks) {
      await expect(nav.getByRole('link', { name: linkText, exact: true })).toBeVisible();
    }

    // About dropdown trigger should be visible (it's a button, not a link)
    await expect(nav.getByRole('button', { name: /About/ })).toBeVisible();

    // Check that a nav link is on the same row as the logo (not stacked below)
    const logoBox = await page.locator('[data-testid="nav-logo"]').boundingBox();
    const aboutLink = nav.getByRole('button', { name: /About/ });
    const linkBox = await aboutLink.boundingBox();

    expect(logoBox).not.toBeNull();
    expect(linkBox).not.toBeNull();

    // Links should be vertically overlapping with the logo (same row)
    const logoVerticalCenter = logoBox!.y + logoBox!.height / 2;
    const tolerance = logoBox!.height / 2;
    expect(linkBox!.y).toBeLessThan(logoVerticalCenter + tolerance);
    expect(linkBox!.y + linkBox!.height).toBeGreaterThan(logoVerticalCenter - tolerance);
  });

  test('nav links should be hidden behind hamburger below lg breakpoint', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 900 });
    await page.goto('/');

    // Nav links should not be visible below the lg breakpoint (1024px)
    const aboutButton = page.locator('nav').getByRole('button', { name: /About/ });
    await expect(aboutButton).not.toBeVisible();

    // Hamburger button should be visible
    const hamburger = page.locator('nav button').first();
    await expect(hamburger).toBeVisible();
  });
});
