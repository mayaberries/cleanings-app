import { test, expect } from '@playwright/test';
import { existingAppointment } from './fixtures';

/**
 * ROADMAP — clinic admin "Appointments" tab. No page exists yet; src/pages/index.astro
 * currently says "real appointments/services/keys tabs come next."
 *
 * Backend already supports this in full (docs/openapi.json, tag "appointments"):
 *   GET    /api/services/{service_id}/appointments/                (list)
 *   GET    /api/services/{service_id}/appointments/{appointment_id}
 *   PUT    /api/services/{service_id}/appointments/{appointment_id}/confirm
 *   PUT    /api/services/{service_id}/appointments/{appointment_id}/cancel
 *   DELETE /api/services/{service_id}/appointments/{appointment_id}   (withdraw)
 *
 * The admin's own view is necessarily cross-service (an appointment list, not
 * a per-service one) — expect it to aggregate across every service's endpoint,
 * or for the backend to grow a clinic-wide listing route to back it.
 *
 * See tests/wip/README.md for how to graduate this spec once the page exists.
 */
test.describe.skip('Clinic admin · Appointments', () => {
  test('lists appointments across all services', async ({ page }) => {
    await page.goto('/appointments');
    await expect(page.getByRole('heading', { name: 'Appointments' })).toBeVisible();
    await expect(page.getByRole('row').filter({ hasText: existingAppointment.petName })).toBeVisible();
  });

  test('filters appointments by status', async ({ page }) => {
    await page.goto('/appointments');
    await page.getByLabel(/status/i).selectOption('requested');

    await expect(page.getByRole('row').filter({ hasText: /requested/i })).not.toHaveCount(0);
    await expect(page.getByRole('row').filter({ hasText: /cancelled/i })).toHaveCount(0);
  });

  test('confirms a requested appointment', async ({ page }) => {
    await page.goto('/appointments');
    const row = page.getByRole('row').filter({ hasText: existingAppointment.petName });

    await row.getByRole('button', { name: /confirm/i }).click();

    await expect(row.getByText(/confirmed/i)).toBeVisible();
  });

  test('cancels an appointment with a reason', async ({ page }) => {
    await page.goto('/appointments');
    const row = page.getByRole('row').filter({ hasText: existingAppointment.petName });

    await row.getByRole('button', { name: /cancel/i }).click();
    await page.getByLabel(/reason/i).fill('Clinic closed that day');
    await page.getByRole('button', { name: /confirm cancellation/i }).click();

    await expect(row.getByText(/cancelled/i)).toBeVisible();
  });
});
