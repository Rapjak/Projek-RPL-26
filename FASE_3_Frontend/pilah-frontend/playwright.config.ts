import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: { timeout: 10000 },
  fullyParallel: false,        // sequential - avoids auth state collision
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 20000,
    navigationTimeout: 20000,
  },
  projects: [
    // Use the system-installed Google Chrome instead of the Playwright
    // bundled Chromium (whose 205 MiB download is blocked by slow network).
    { name: 'chrome', use: { channel: 'chrome' } },
  ],
});
