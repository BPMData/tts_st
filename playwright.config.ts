import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/pwa',
  fullyParallel: true,
  use: { baseURL: 'http://127.0.0.1:4173' },
  webServer: {
    command: 'node server.ts',
    url: 'http://127.0.0.1:4173/api/health',
    env: { NODE_ENV: 'production', HOST: '127.0.0.1', PORT: '4173' },
    reuseExistingServer: false,
  },
  projects: [
    { name: 'desktop-chrome', use: { ...devices['Desktop Chrome'] } },
    { name: 'android-chrome', use: { ...devices['Pixel 7'] } },
  ],
});
