import { test, expect } from '@playwright/test';

test('homepage has correct title and buttons', async ({ page }) => {
  await page.goto('/');

  // Check title
  await expect(page).toHaveTitle(/Terramedic/);

  // Check that main heading exists
  await expect(page.locator('h1')).toBeVisible();

  // Check that action pathways section is visible
  await expect(page.locator('#take-action')).toBeVisible();

  // Check that action cards exist with question titles
  await expect(page.locator('a:has-text("Have time to")')).toBeVisible();
  await expect(page.locator('a:has-text("Have money to")')).toBeVisible();
  await expect(page.locator('a:has-text("No time?")')).toBeVisible();

  // Test navigation to volunteer page
  await page.click('a:has-text("Have time to")');
  await expect(page).toHaveURL(/.*volunteer/);

  // Go back to home page
  await page.goto('/');

  // Test navigation to donate page
  await page.click('a:has-text("Have money to")');
  await expect(page).toHaveURL(/.*donate/);
});
