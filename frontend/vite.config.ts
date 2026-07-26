/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import colors from 'tailwindcss/colors'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      manifest: {
        name: 'TurtleTrips',
        short_name: 'TurtleTrips',
        description: 'Self-hosted trips management',
        lang: 'es',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: colors.emerald[500],
        background_color: '#ffffff',
        icons: [
          { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/maskable-icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          // API (solo GET): red primero con fallback a caché para consultar
          // el viaje sin conexión; nunca se cachean descargas ni backups, ni
          // auth/users/families (un /auth/me cacheado serviría al usuario
          // anterior del dispositivo)
          {
            urlPattern: ({ url, request }) =>
              request.method === 'GET' &&
              url.pathname.startsWith('/api/v1/') &&
              !/\/(auth|users|families|backup|attachments\/\d+\/download|calendar\.ics|calendar\/[^/]+\.ics|expenses\/export\.csv|trips\/\d+\/cover|travelers\/\d+\/avatar)/.test(
                url.pathname,
              ),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api',
              networkTimeoutSeconds: 4,
              cacheableResponse: { statuses: [200] },
              expiration: { maxEntries: 300, maxAgeSeconds: 7 * 86400 },
            },
          },
          // tiles de CARTO: cache-first (cambian poco y pesan)
          {
            urlPattern: /^https:\/\/[abcd]\.basemaps\.cartocdn\.com\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              cacheableResponse: { statuses: [0, 200] },
              expiration: { maxEntries: 500, maxAgeSeconds: 30 * 86400 },
            },
          },
          // portadas, avatares e imágenes de país (Wikimedia)
          {
            urlPattern: ({ url }) =>
              /^\/api\/v1\/(trips\/\d+\/cover|travelers\/\d+\/avatar)/.test(url.pathname) ||
              url.hostname === 'upload.wikimedia.org',
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'images',
              cacheableResponse: { statuses: [0, 200] },
              expiration: { maxEntries: 150, maxAgeSeconds: 30 * 86400 },
            },
          },
        ],
      },
      // el SW no interfiere con el dev server (:5173 usa HMR + proxy)
      devOptions: { enabled: false },
    }),
  ],
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
