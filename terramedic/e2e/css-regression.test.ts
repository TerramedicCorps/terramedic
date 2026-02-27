import { expect, test } from '@playwright/test';

test.describe('Navbar responsive layout', () => {
  test('nav links should be visible and inline on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    // Check that all nav links are visible
    const navLinks = [
      'Home',
      'About',
      'Volunteer',
      'Donate',
      'Other Actions',
      'Resources',
      'Contact'
    ];
    for (const linkText of navLinks) {
      await expect(page.locator(`nav a:has-text("${linkText}")`)).toBeVisible();
    }

    // Check that a nav link is on the same row as the logo (not stacked below)
    const logoBox = await page.locator('[data-testid="nav-logo"]').boundingBox();
    const aboutLink = page.locator('nav a:has-text("About")');
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
    const aboutLink = page.locator('nav').getByRole('link', { name: 'About', exact: true });
    await expect(aboutLink).not.toBeVisible();

    // Hamburger button should be visible
    const hamburger = page.locator('nav button').first();
    await expect(hamburger).toBeVisible();
  });
});
