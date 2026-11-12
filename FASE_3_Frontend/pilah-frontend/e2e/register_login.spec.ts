// Final verification: real register -> login flow with a fresh account.
import { test, expect } from '@playwright/test';

const FRONTEND = 'http://localhost:3000';

test('register new account then login works end-to-end', async ({ page }) => {
  const unique = `user${Date.now()}`;
  const npm = `999${String(Date.now()).slice(-7)}`;
  const email = `${unique}@mail.unpad.ac.id`;
  const password = 'StrongPass123!';

  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  // --- Register ---
  await page.goto(`${FRONTEND}/register`, { waitUntil: 'networkidle' });
  await page.fill('input[name="npm_nip"]', npm);
  await page.fill('input[name="name"]', 'E2E New User');
  await page.fill('input[name="email"]', email);
  await page.locator('select[name="unit_gedung"]').selectOption({ index: 1 });
  await page.fill('input[name="password"]', password);
  await page.fill('input[name="password2"]', password);

  await expect(page.getByRole('button', { name: 'Daftar' })).toBeEnabled();
  await page.getByRole('button', { name: 'Daftar' }).click();

  // Should navigate to /login after successful registration
  await page.waitForURL('**/login', { timeout: 15000 });

  // --- Login with the new account ---
  await page.fill('input[type="text"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');

  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await expect(page.getByText(/Halo,/)).toBeVisible();

  // New user starts with 0 points
  await page.goto(`${FRONTEND}/profile`);
  await expect(page.locator('input').first()).toHaveValue(npm);
  await expect(page.getByText('Civitas Akademika')).toBeVisible();

  expect(errors.filter(e => !e.includes('favicon'))).toEqual([]);
});
