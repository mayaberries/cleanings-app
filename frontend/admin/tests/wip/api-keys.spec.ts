import { test, expect } from '@playwright/test';
import { newApiKey } from './fixtures';

/**
 * ROADMAP — clinic admin "API keys" tab. No page exists yet; src/pages/index.astro
 * currently says "real appointments/services/keys tabs come next." The
 * onboarding wizard already issues the clinic's first key (see
 * src/lib/onboarding/launch.js) — this is the page to manage it afterward.
 *
 * Backend already supports this in full (docs/openapi.json, tag "clinic-api-keys"):
 *   GET/POST /api/clinics/{clinic_id}/api-keys/
 *   DELETE   /api/clinics/{clinic_id}/api-keys/{key_id}/   (revoke)
 *
 * See tests/wip/README.md for how to graduate this spec once the page exists.
 */
test.describe.skip('Clinic admin · API keys', () => {
  test('lists existing keys with their environment and status', async ({ page }) => {
    await page.goto('/api-keys');
    await expect(page.getByRole('heading', { name: 'API keys' })).toBeVisible();
    await expect(page.getByText(/live|test/i).first()).toBeVisible();
  });

  test('issues a new key', async ({ page }) => {
    await page.goto('/api-keys');
    await page.getByRole('button', { name: /new key/i }).click();

    await page.getByLabel(/label/i).fill(newApiKey.label);
    await page.getByLabel(/environment/i).selectOption(newApiKey.environment);
    await page.getByRole('button', { name: /create/i }).click();

    await expect(page.getByText(newApiKey.label)).toBeVisible();
    await expect(page.getByText(/^pk_(live|test)_/)).toBeVisible();
  });

  test('revokes a key', async ({ page }) => {
    await page.goto('/api-keys');
    const row = page.getByRole('row').filter({ hasText: newApiKey.label });

    await row.getByRole('button', { name: /revoke/i }).click();
    await page.getByRole('button', { name: /confirm/i }).click();

    await expect(row.getByText(/revoked/i)).toBeVisible();
  });
});
