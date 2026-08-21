import { test, expect } from '@playwright/test';

/**
 * ROADMAP — superadmin "Clinics" list. No page exists yet; src/pages/index.astro
 * currently says "Superadmin session — clinics list + site launch panel come next."
 *
 * Backend already supports the list (docs/openapi.json, tag "clinics"):
 *   GET /api/clinics/
 *
 * There's no dedicated "get one clinic's site-launch panel" endpoint yet —
 * that second test below is more speculative than the others in wip/ and may
 * need a new backend route, not just a new page.
 *
 * See tests/wip/README.md for how to graduate this spec once the page exists.
 */
test.describe.skip('Superadmin · Clinics', () => {
  test('lists every clinic on the platform', async ({ page }) => {
    await page.goto('/clinics');
    await expect(page.getByRole('heading', { name: 'Clinics' })).toBeVisible();
    await expect(page.getByRole('row')).not.toHaveCount(0);
  });

  test('links from a clinic row to its site-launch panel', async ({ page }) => {
    await page.goto('/clinics');
    await page.getByRole('row').first().getByRole('link', { name: /view/i }).click();

    await expect(page.getByRole('heading', { name: /site launch/i })).toBeVisible();
  });
});
