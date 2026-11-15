import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [react(), VitePWA({ manifest: false, injectRegister: false })],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.tsx'],
    restoreMocks: true,
  },
});
