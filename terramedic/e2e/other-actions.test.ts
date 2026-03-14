import { expect, test } from '@playwright/test';

test.describe('Other Actions page', () => {
  test('renders organization card grid', async ({ page }) => {
    await page.goto('/other-actions');
    const cards = page.locator('[data-testid="org-card-grid"] > *');
    await expect(cards).toHaveCount(2);
  });

  test('Yale Climate Connections card is visible with correct link', async ({ page }) => {
    await page.goto('/other-actions');
    await expect(page.getByText('Yale Climate Connections')).toBeVisible();
    const link = page.locator('a[href="https://yaleclimateconnections.org/solutions/"]');
    await expect(link).toBeVisible();
  });

  test('SHIFT card is visible with correct link', async ({ page }) => {
    await page.goto('/other-actions');
    await expect(page.getByRole('heading', { name: 'SHIFT' })).toBeVisible();
    const link = page.locator('a[href="https://jointheshift.earth/"]');
    await expect(link).toBeVisible();
  });

  test('Small Steps and Power of Community sections still exist', async ({ page }) => {
    await page.goto('/other-actions');
    await expect(page.getByText('Small Steps with Big Impact')).toBeVisible();
    await expect(page.getByText('The Power of Community')).toBeVisible();
  });
});
