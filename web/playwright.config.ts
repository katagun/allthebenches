import { defineConfig } from '@playwright/test';

const port = Number(process.env.LAYOUT_PORT ?? 4187);
const liveBaseURL = process.env.LAYOUT_BASE_URL;

export default defineConfig({
  testDir: './e2e',
  forbidOnly: true,
  retries: 0,
  workers: 2,
  reporter: 'list',
  use: {
    baseURL: liveBaseURL ?? `http://127.0.0.1:${port}${process.env.LAYOUT_BASE_PATH ?? '/'}`,
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: liveBaseURL ? undefined : {
    command: `pnpm exec vite preview --host 127.0.0.1 --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}${process.env.LAYOUT_BASE_PATH ?? '/'}`,
    reuseExistingServer: false,
    env: { VITE_BASE_PATH: process.env.LAYOUT_BASE_PATH ?? '/' },
  },
});
