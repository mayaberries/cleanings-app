import { test, expect } from '@playwright/test';
import { newService } from './fixtures';

/**
 * ROADMAP — clinic admin "Services" tab. No page exists yet; src/pages/index.astro
 * currently says "real appointments/services/keys tabs come next."
 *
 * Backend already supports this in full (docs/openapi.json, tag "services"):
 *   GET/POST   /api/services/
 *   PUT/DELETE /api/services/{service_id}/
 *
 * See tests/wip/README.md for how to graduate this spec once the page exists.
 */
test.describe.skip('Clinic admin · Services', () => {
  test('lists the clinic’s existing services', async ({ page }) => {
    await page.goto('/services');
    await expect(page.getByRole('heading', { name: 'Services' })).toBeVisible();
    await expect(page.getByRole('row')).not.toHaveCount(0);
  });

  test('creates a new service', async ({ page }) => {
    await page.goto('/services');
    await page.getByRole('button', { name: /add service/i }).click();

    await page.getByLabel(/service name/i).fill(newService.name);
    await page.getByLabel(/category/i).selectOption(newService.category);
    await page.getByLabel(/price/i).fill(newService.price);
    await page.getByLabel(/duration/i).fill(newService.duration_minutes);
    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText(newService.name)).toBeVisible();
  });

  test('edits an existing service', async ({ page }) => {
    await page.goto('/services');
    const row = page.getByRole('row').filter({ hasText: newService.name });
    await row.getByRole('button', { name: /edit/i }).click();

    await page.getByLabel(/price/i).fill('150');
    await page.getByRole('button', { name: /save/i }).click();

    await expect(row.getByText('150')).toBeVisible();
  });

  test('deletes a service', async ({ page }) => {
    await page.goto('/services');
    const row = page.getByRole('row').filter({ hasText: newService.name });
    await row.getByRole('button', { name: /delete/i }).click();
    await page.getByRole('button', { name: /confirm/i }).click();

    await expect(row).toHaveCount(0);
  });
});
