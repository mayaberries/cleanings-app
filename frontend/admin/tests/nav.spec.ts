import { test, expect, type Page } from '@playwright/test';

/**
 * Covers the dashboard tab bar (src/components/AdminNav.vue) and the role gate
 * that backs it (src/middleware.ts + src/lib/nav.ts) — ported from the
 * prototype's renderShell()/boot() in docs/proto/shared.js.
 *
 * Runs against the demo session seeded by the sign-in page's "Demo · Clinic
 * admin" button (src/lib/demoData.ts), so no API or database needs to be up.
 * That demo user is always a clinic_admin, which is why the superadmin side of
 * the gate — the Clinics tab, and a superadmin being kept off /overview — isn't
 * exercised here; it needs either a real backend login or a demo superadmin.
 */

const CLINIC_ADMIN_TABS = ['Overview', 'Appointments', 'Services', 'API Keys', 'Website', 'Account'];

async function signInAsDemoClinicAdmin(page: Page) {
  await page.goto('/login');
  await page.getByRole('button', { name: 'Demo · Clinic admin' }).click();
  await expect(page).toHaveURL(/\/overview$/);
}

test.describe('Dashboard nav', () => {
  test('signing in lands on the clinic admin overview tab', async ({ page }) => {
    await signInAsDemoClinicAdmin(page);
    await expect(page.getByRole('heading', { name: 'Overview', level: 1 })).toBeVisible();
  });

  test('shows every clinic admin tab and hides the superadmin one', async ({ page }) => {
    await signInAsDemoClinicAdmin(page);

    const nav = page.getByRole('navigation');
    await expect(nav.getByRole('link')).toHaveText(CLINIC_ADMIN_TABS);
    await expect(nav.getByRole('link', { name: 'Clinics' })).toHaveCount(0);
  });

  test('navigates between tabs and marks the current one', async ({ page }) => {
    await signInAsDemoClinicAdmin(page);
    const nav = page.getByRole('navigation');

    for (const label of CLINIC_ADMIN_TABS) {
      await nav.getByRole('link', { name: label, exact: true }).click();
      await expect(page.getByRole('heading', { name: label, level: 1 })).toBeVisible();

      // aria-current is the nav's only source of "which tab am I on" — it's
      // driven by the URL, so it has to survive the real navigation each click
      // triggers, not just the first server render.
      await expect(nav.getByRole('link', { name: label, exact: true })).toHaveAttribute('aria-current', 'page');
      await expect(nav.locator('a[aria-current="page"]')).toHaveCount(1);
    }
  });

  test('bounces a clinic admin off a superadmin-only URL', async ({ page }) => {
    await signInAsDemoClinicAdmin(page);

    await page.goto('/clinics');

    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByRole('heading', { name: 'Overview', level: 1 })).toBeVisible();
  });

  test('sends a signed-out visitor to the login page', async ({ page }) => {
    await page.goto('/services');
    await expect(page).toHaveURL(/\/login$/);
  });
});
