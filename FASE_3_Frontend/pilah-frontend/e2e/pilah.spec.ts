// E2E browser verification for Pilah.in frontend
// Uses Playwright to actually render pages and check for runtime errors.
import { test, expect, type Page } from '@playwright/test';

const FRONTEND = 'http://localhost:3000';

// Collect console errors and page errors from every page visited.
let consoleErrors: string[] = [];
let pageErrors: string[] = [];

function attachErrorListeners(page: Page) {
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(`[console] ${msg.text()}`);
  });
  page.on('pageerror', err => {
    pageErrors.push(`[pageerror] ${err.message}`);
  });
}

test.beforeEach(async ({ page }) => {
  consoleErrors = [];
  pageErrors = [];
  attachErrorListeners(page);
});

async function expectNoErrors(page: Page, ctx: string) {
  // Allow harmless favicon 404 / HMR noise / resource load failures
  const significant = (e: string) =>
    !e.includes('favicon') &&
    !e.includes('manifest') &&
    !e.includes('net::ERR') &&
    !e.includes('Failed to load resource') &&
    !e.includes('Download the React DevTools');
  const sigConsole = consoleErrors.filter(significant);
  const sigPage = pageErrors.filter(significant);
  if (sigConsole.length || sigPage.length) {
    throw new Error(
      `[${ctx}] Runtime errors detected:\n` +
      sigConsole.join('\n') + '\n' +
      sigPage.join('\n')
    );
  }
}

async function login(page: Page, identifier: string, password: string, expectedPath: string) {
  await page.goto(`${FRONTEND}/login`);
  await page.fill('input[type="text"]', identifier);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  // Wait for navigation to expectedPath - this is the critical assertion
  await page.waitForURL(`**${expectedPath}`, { waitUntil: 'networkidle', timeout: 15000 });
  await expectNoErrors(page, `login(${identifier})`);
}

// ---------------------------------------------------------------------------
// CIVITAS FLOW
// ---------------------------------------------------------------------------
test.describe('Civitas flow', () => {
  test('login civitas redirects to dashboard (THE reported bug)', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    // Greeting must be visible on dashboard
    await expect(page.getByText(/Halo,/)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Total Poin')).toBeVisible();
  });

  test('login civitas via npm_nip also works', async ({ page }) => {
    await login(page, '140810240099', 'StrongPass123!', '/dashboard');
    await expect(page.getByText(/Halo,/)).toBeVisible();
  });

  test('dashboard renders without crash', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await expect(page.getByRole('button', { name: 'Unggah Foto Sampah' })).toBeVisible();
    await expect(page.getByText('Aktivitas Terkini')).toBeVisible();
    await expectNoErrors(page, 'dashboard');
  });

  test('history page renders', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/history`);
    await expect(page.getByRole('heading', { name: 'Riwayat Aktivitas' })).toBeVisible();
    await expect(page.getByText('Total Unggahan')).toBeVisible();
    await expectNoErrors(page, 'history');
  });

  test('rewards page renders', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/rewards`);
    // NOTE: two headings contain the word "Reward" ("Reward" h1 + "Reward Tersedia" h2),
    // so use exact match to disambiguate.
    await expect(page.getByRole('heading', { name: 'Reward', exact: true })).toBeVisible();
    await expect(page.getByText('Poin Anda')).toBeVisible();
    // At least one redeemable reward with "Tukar" button
    await expect(page.getByText('Reward Tersedia')).toBeVisible();
    await expectNoErrors(page, 'rewards');
  });

  test('education list renders', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/education`);
    await expect(page.getByRole('heading', { name: 'Edukasi' })).toBeVisible();
    await expect(page.getByText('Memilah Sampah Organik dengan Benar')).toBeVisible({ timeout: 5000 });
    await expectNoErrors(page, 'education');
  });

  test('education detail opens', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/education`);
    await page.getByText('Memilah Sampah Organik dengan Benar').click();
    await expect(page.getByText('Ringkasan')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Kembali')).toBeVisible();
    await expectNoErrors(page, 'education-detail');
  });

  test('leaderboard renders (user + building tabs)', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/leaderboard`);
    await expect(page.getByRole('heading', { name: 'Peringkat' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Pengguna' })).toBeVisible();
    await page.getByRole('button', { name: 'Unit/Gedung' }).click();
    await expect(page.getByText('Teknik Informatika').first()).toBeVisible({ timeout: 5000 });
    await expectNoErrors(page, 'leaderboard');
  });

  test('profile renders with correct fields', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/profile`);
    await expect(page.getByRole('heading', { name: 'Profil' })).toBeVisible();
    await expect(page.getByText('NPM/NIP')).toBeVisible();
    // Input values are NOT exposed as text nodes by innerText; verify via inputValue.
    const npmInput = page.locator('input').first();
    await expect(npmInput).toHaveValue('140810240099');
    await expect(page.getByText('Civitas Akademika')).toBeVisible();
    await expectNoErrors(page, 'profile');
  });

  test('logout returns to /login', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/profile`);
    await page.getByRole('button', { name: 'Keluar' }).click();
    await page.waitForURL('**/login', { timeout: 10000 });
    await expectNoErrors(page, 'logout');
  });

  test('protected route redirects to login when not authed', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForURL('**/login', { timeout: 5000 });
  });

  test('upload + classify flow (FR-003, SCR-04/05/06)', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/upload`);

    // Upload view (SCR-04)
    await expect(page.getByRole('heading', { name: 'Unggah Foto Sampah' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Kirim Foto' })).toBeDisabled();

    // Generate a small green PNG (organik-like) in the browser context,
    // then set it as the file input value. Playwright needs a real File on disk,
    // so we use setInputFiles with a buffer path instead.
    // Create the file via page.evaluate + download, but simpler: use a data URL
    // routed through a temp file via setInputFiles buffer.
    const pngBuffer = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'base64'
    );
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test-sampah.png',
      mimeType: 'image/png',
      buffer: pngBuffer,
    });

    // Kirim Foto button should now be enabled
    await expect(page.getByRole('button', { name: 'Kirim Foto' })).toBeEnabled();
    await page.getByRole('button', { name: 'Kirim Foto' }).click();

    // Processing view (SCR-05)
    await expect(page.getByText('Memproses Foto')).toBeVisible({ timeout: 5000 });

    // Result view (SCR-06/07) - polling should complete
    await expect(page.getByRole('heading', { name: 'Hasil Klasifikasi' })).toBeVisible({ timeout: 30000 });

    // Category badge + disposal guidance + points visible (since ML returns organik)
    await expect(page.getByText('Kategori sampah')).toBeVisible();
    // Either points awarded (organik) or "Foto belum dapat dikenali" (invalid)
    const hasPoints = await page.getByText(/poin/).count();
    expect(hasPoints).toBeGreaterThan(0);

    await expectNoErrors(page, 'upload+classify');
  });

  test('redeem reward flow (FR-005, SCR-09)', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/rewards`);

    // At least one reward should be redeemable (user has >=30 points, reward costs 5)
    const tukarBtn = page.getByRole('button', { name: 'Tukar' }).first();
    await expect(tukarBtn).toBeVisible();
    await tukarBtn.click();

    // Confirm modal appears
    await expect(page.getByText('Konfirmasi Penukaran')).toBeVisible({ timeout: 5000 });
    // Click the confirm button inside the modal (last Tukar in modal)
    await page.getByRole('button', { name: 'Tukar' }).last().click();

    // Voucher code should appear (format RWD-...)
    await expect(page.getByText(/RWD-/)).toBeVisible({ timeout: 10000 });

    await expectNoErrors(page, 'redeem');
  });
});

// ---------------------------------------------------------------------------
// ADMIN FLOW
// ---------------------------------------------------------------------------
test.describe('Admin flow', () => {
  test('login admin redirects to /admin', async ({ page }) => {
    await login(page, 'admin.gogreen@unpad.ac.id', 'AdminPass123!', '/admin');
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
  });

  test('admin overview tab shows stats', async ({ page }) => {
    await login(page, 'admin.gogreen@unpad.ac.id', 'AdminPass123!', '/admin');
    await expect(page.getByText('Total Pengguna')).toBeVisible();
    await expect(page.getByText('Total Upload')).toBeVisible();
    await expect(page.getByText('Distribusi Kategori Sampah')).toBeVisible();
    await expectNoErrors(page, 'admin-overview');
  });

  test('admin activities tab shows table', async ({ page }) => {
    await login(page, 'admin.gogreen@unpad.ac.id', 'AdminPass123!', '/admin');
    await page.getByRole('tab', { name: 'Admin tab: Aktivitas' }).click();
    await expect(page.getByText('NPM/NIP').first()).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('Smoke Tester').first()).toBeVisible();
    await expectNoErrors(page, 'admin-activities');
  });

  test('admin rewards tab shows CRUD', async ({ page }) => {
    await login(page, 'admin.gogreen@unpad.ac.id', 'AdminPass123!', '/admin');
    await page.getByRole('tab', { name: 'Admin tab: Reward' }).click();
    await expect(page.getByRole('button', { name: '+ Tambah Reward' })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('Diskon Kantin 10%').first()).toBeVisible();
    await expectNoErrors(page, 'admin-rewards');
  });

  test('admin education tab shows list', async ({ page }) => {
    await login(page, 'admin.gogreen@unpad.ac.id', 'AdminPass123!', '/admin');
    await page.getByRole('tab', { name: 'Admin tab: Edukasi' }).click();
    await expect(page.getByText('Memilah Sampah Organik dengan Benar')).toBeVisible({ timeout: 8000 });
    await expectNoErrors(page, 'admin-education');
  });

  test('civitas cannot access /admin', async ({ page }) => {
    await login(page, 'smoke099@mail.unpad.ac.id', 'StrongPass123!', '/dashboard');
    await page.goto(`${FRONTEND}/admin`);
    await page.waitForURL('**/dashboard', { timeout: 5000 });
    await expectNoErrors(page, 'civitas-blocked-admin');
  });
});

// ---------------------------------------------------------------------------
// REGISTER FLOW
// ---------------------------------------------------------------------------
test.describe('Register flow', () => {
  test('register page renders (SCR-01)', async ({ page }) => {
    await page.goto(`${FRONTEND}/register`);
    await expect(page.getByRole('heading', { name: 'Buat Akun' })).toBeVisible();
    await expect(page.getByText('NPM/NIP').first()).toBeVisible();
    await expectNoErrors(page, 'register-page');
  });

  test('register validation - password mismatch shows inline error', async ({ page }) => {
    await page.goto(`${FRONTEND}/register`);
    await page.fill('input[name="npm_nip"]', '140810240999');
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', 'testuser@mail.unpad.ac.id');
    await page.locator('select[name="unit_gedung"]').selectOption({ index: 1 });
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="password2"]', 'Different123!');
    // The inline error under the confirm-password field should appear.
    await expect(page.getByText('Kata sandi tidak cocok')).toBeVisible({ timeout: 5000 });
    // Submit button should be disabled (cannot submit mismatched passwords)
    await expect(page.getByRole('button', { name: 'Daftar' })).toBeDisabled();
    await expectNoErrors(page, 'register-validation');
  });
});
