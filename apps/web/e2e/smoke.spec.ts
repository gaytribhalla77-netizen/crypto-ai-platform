import { test, expect } from '@playwright/test';

test('landing page loads and exposes dashboard entry point', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/IQ200/);
  await expect(page.getByRole('heading', { name: /Trade smarter/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /Launch Trading Cockpit/i })).toHaveAttribute('href', '/dashboard');
});

test('dashboard route renders without a server error', async ({ page }) => {
  const response = await page.goto('/dashboard');
  expect(response?.status()).toBe(200);
  await expect(page.getByText('IQ200', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('FAIL-CLOSED', { exact: true }).first()).toBeVisible();
});
