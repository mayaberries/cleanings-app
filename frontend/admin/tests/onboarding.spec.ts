import { test, expect } from '@playwright/test';
import { account, clinic, mismatchedConfirmPassword, service } from './fixtures/onboarding';
import { enableDemoMode, fillAccountStep, fillClinicStep, fillFirstService } from './helpers/onboarding';

/**
 * Covers the onboarding wizard (src/pages/onboarding.astro and src/lib/onboarding/*):
 * clicking through from the login view, filling out the account/clinic/services
 * steps, reviewing, and launching the clinic.
 *
 * Runs in the wizard's built-in demo mode, which swaps every backend call for a
 * mocked response (see src/lib/onboarding/demoBackend.js) — no API or database
 * needs to be up for these tests.
 *
 * Input data lives in tests/fixtures/onboarding.ts; the fill/toggle steps below
 * live in tests/helpers/onboarding.ts, so other onboarding specs can reuse both.
 */

test.describe('Onboarding wizard', () => {
  test('the login view links through to the onboarding wizard', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: 'Register and get bookable' }).click();

    await expect(page).toHaveURL(/\/onboarding/);
    await expect(page.locator('.step-panel[data-step="0"]')).toBeVisible();
  });

  test('blocks progress out of the account step until the fields are valid', async ({ page }) => {
    await page.goto('/onboarding');

    // Submitting blank fails validation and the panel doesn't advance.
    await page.locator('#nextBtn').click();
    await expect(page.locator('.field-error[data-for="acc_email"]')).toHaveText(/valid email/i);
    await expect(page.locator('.field-error[data-for="acc_username"]')).toHaveText(/3\+ characters/i);
    await expect(page.locator('.field-error[data-for="acc_password"]')).toHaveText(/at least 7 characters/i);
    await expect(page.locator('.step-panel[data-step="0"]')).toBeVisible();

    // Valid fields but a mismatched confirmation still blocks progress.
    await fillAccountStep(page);
    await page.locator('#acc_password2').fill(mismatchedConfirmPassword);
    await page.locator('#nextBtn').click();
    await expect(page.locator('.field-error[data-for="acc_password2"]')).toHaveText(/don't match/i);
    await expect(page.locator('.step-panel[data-step="0"]')).toBeVisible();

    // Fixing it lets the wizard move on.
    await page.locator('#acc_password2').fill(account.password);
    await page.locator('#nextBtn').click();
    await expect(page.locator('.step-panel[data-step="1"]')).toBeVisible();
  });

  test('supports adding and removing services on the services step', async ({ page }) => {
    await page.goto('/onboarding');
    await fillAccountStep(page);
    await page.locator('#nextBtn').click();
    await fillClinicStep(page);
    await page.locator('#nextBtn').click();

    // Scoped to direct children: every field within a service card also carries
    // a `data-svc` attribute, so an unscoped `[data-svc]` locator overcounts.
    const serviceCards = page.locator('#servicesList > [data-svc]');
    await expect(serviceCards).toHaveCount(1);

    await page.locator('#addServiceBtn').click();
    await expect(serviceCards).toHaveCount(2);

    await page.locator('.remove-svc').first().click();
    await expect(serviceCards).toHaveCount(1);
  });

  test('completes account, clinic, services, and review through to launch', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: 'Register and get bookable' }).click();
    await enableDemoMode(page);

    // Step 0: account
    await expect(page.locator('.step-panel[data-step="0"]')).toBeVisible();
    await fillAccountStep(page);
    await page.locator('#nextBtn').click();

    // Step 1: clinic — slug should auto-derive from the name
    await expect(page.locator('.step-panel[data-step="1"]')).toBeVisible();
    await fillClinicStep(page);
    await expect(page.locator('#cl_slug')).toHaveValue(clinic.slug);
    await page.locator('#nextBtn').click();

    // Step 2: services
    await expect(page.locator('.step-panel[data-step="2"]')).toBeVisible();
    await fillFirstService(page);
    await page.locator('#nextBtn').click();

    // Step 3: review — summarizes everything entered so far, nothing sent yet
    await expect(page.locator('.step-panel[data-step="3"]')).toBeVisible();
    const review = page.locator('#reviewBlock');
    await expect(review).toContainText(account.username);
    await expect(review).toContainText(account.email);
    await expect(review).toContainText(clinic.name);
    await expect(review).toContainText(service.name);
    await expect(page.locator('#nextBtn')).toHaveText('Launch clinic 🚀');

    // Accept the review and launch
    await page.locator('#nextBtn').click();

    // Step 4: success
    await expect(page.locator('.step-panel[data-step="4"]')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('heading', { name: "You're bookable" })).toBeVisible();
    await expect(page.locator('#keyText')).toHaveText(/^pk_live_demo_/);
  });
});
