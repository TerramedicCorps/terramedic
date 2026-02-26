import { expect, test } from '@playwright/test';

test.describe('Navbar visibility on desktop', () => {
  test('nav links should be visible and inline on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    // Check that nav links are visible
    const homeLink = page.locator('nav a:has-text("Home")');
    await expect(homeLink).toBeVisible();

    const aboutLink = page.locator('nav a:has-text("About")');
    await expect(aboutLink).toBeVisible();

    // Check that nav links are on the same row as the logo (not stacked below)
    const logoBox = await page.locator('[data-testid="nav-logo"]').boundingBox();
    const linkBox = await aboutLink.boundingBox();

    expect(logoBox).not.toBeNull();
    expect(linkBox).not.toBeNull();

    // Links should be vertically overlapping with the logo (same row)
    const logoVerticalCenter = logoBox!.y + logoBox!.height / 2;
    expect(linkBox!.y).toBeLessThan(logoVerticalCenter + logoBox!.height);
    expect(linkBox!.y + linkBox!.height).toBeGreaterThan(logoVerticalCenter - logoBox!.height);
  });
});
