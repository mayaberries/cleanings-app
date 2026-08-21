import type { Page } from '@playwright/test';
import { account, clinic, service } from '../fixtures/onboarding';

/**
 * Page-interaction helpers for the onboarding wizard tests. Each helper fills
 * one step using tests/fixtures/onboarding.ts by default, with per-call
 * overrides for tests that need to deviate from those defaults.
 */

export async function enableDemoMode(page: Page) {
  await page.locator('#settingsToggle').click();
  await page.locator('#demoModeToggle').check();
}

export async function fillAccountStep(page: Page, overrides: Partial<typeof account> = {}) {
  const { email, username, password } = { ...account, ...overrides };
  await page.locator('#acc_email').fill(email);
  await page.locator('#acc_username').fill(username);
  await page.locator('#acc_password').fill(password);
  await page.locator('#acc_password2').fill(password);
}

export async function fillClinicStep(page: Page, overrides: Partial<typeof clinic> = {}) {
  const { name, email, phone, address } = { ...clinic, ...overrides };
  await page.locator('#cl_name').fill(name);
  await page.locator('#cl_email').fill(email);
  await page.locator('#cl_phone').fill(phone);
  await page.locator('#cl_address').fill(address);
}

export async function fillFirstService(page: Page, overrides: Partial<typeof service> = {}) {
  const { name, price, duration } = { ...service, ...overrides };
  await page.locator('.svc-name').first().fill(name);
  await page.locator('.svc-price').first().fill(price);
  await page.locator('.svc-duration').first().fill(duration);
}
