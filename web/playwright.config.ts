import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  forbidOnly: true,
  retries: 0,
  workers: 2,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:4187${process.env.LAYOUT_BASE_PATH ?? '/'}`,
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'pnpm exec vite preview --host 127.0.0.1 --port 4187 --strictPort',
    url: `http://127.0.0.1:4187${process.env.LAYOUT_BASE_PATH ?? '/'}`,
    reuseExistingServer: false,
    env: { VITE_BASE_PATH: process.env.LAYOUT_BASE_PATH ?? '/' },
  },
});
