import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
import { strings } from './shared/strings.ts';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'allhail-html-strings',
      transformIndexHtml: {
        order: 'pre',
        handler: (html) => html
          .replaceAll('%APP_LANGUAGE%', strings.language)
          .replaceAll('%APP_NAME%', strings.appName)
          .replaceAll('%APP_DESCRIPTION%', strings.description)
          .replaceAll('%APP_NO_SCRIPT%', strings.noScript),
      },
    },
    VitePWA({
      // Ask before updating, so future speech jobs and edits aren't interrupted.
      registerType: 'prompt',
      includeAssets: ['icons/*'],
      manifest: {
        id: '/',
        name: strings.appName,
        short_name: strings.appName,
        description: strings.description,
        lang: strings.language,
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#f7f8f2',
        theme_color: '#153f35',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,svg,webmanifest}'],
        cleanupOutdatedCaches: true,
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api(?:\/|$)/],
        // Only build assets are cached. API replies and user content stay out.
        runtimeCaching: [],
      },
    }),
  ],
});
