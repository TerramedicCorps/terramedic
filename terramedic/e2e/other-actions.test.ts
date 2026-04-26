import { expect, test } from '@playwright/test';

test.describe('Other Actions page', () => {
  test('renders the page with static sections', async ({ page }) => {
    await page.goto('/other-actions');
    await expect(page.getByText('Small Steps with Big Impact')).toBeVisible();
    await expect(page.getByText('The Power of Community')).toBeVisible();
  });

  test('renders organization card grid container', async ({ page }) => {
    await page.goto('/other-actions');
    const grid = page.locator('[data-testid="org-card-grid"]');
    await expect(grid).toBeAttached();
    // Streaming SSR should reach a terminal state — grid, empty
    // message, or error. The skeleton's aria-busy region must be
    // gone; otherwise the page is stuck loading.
    await expect(grid.locator('[aria-busy="true"]')).toHaveCount(0);
  });
});
