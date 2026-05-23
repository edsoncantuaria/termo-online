import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";

const BuildId = process.env.VITE_BUILD_ID || String(Date.now());

export default defineConfig({
  define: {
    __TERM0_BUILD_ID__: JSON.stringify(BuildId),
  },
  plugins: [
    vue(),
    {
      name: "termo-build-id",
      transformIndexHtml(html) {
        return html.replace(
          'name="termo-build" content="dev"',
          `name="termo-build" content="${BuildId}"`
        );
      },
    },
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: false,
      includeAssets: [
        "favicon.svg",
        "termo-icon.svg",
        "cloudive-icon.svg",
        "pwa-192.png",
        "pwa-512.png",
        "offline.html",
        "sounds/*.ogg",
      ],
      manifest: {
        id: "/",
        name: "Termo Online · Cloudive",
        short_name: "Termo",
        description: "Termo em português — um jogo Cloudive",
        theme_color: "#14111c",
        background_color: "#14111c",
        display: "standalone",
        orientation: "portrait",
        lang: "pt-BR",
        start_url: "/",
        scope: "/",
        categories: ["games", "entertainment"],
        icons: [
          {
            src: "/pwa-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/pwa-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/pwa-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,svg,ogg,woff2,png}"],
        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api/, /^\/ws/, /^\/offline\.html$/],
        additionalManifestEntries: [
          { url: "/offline.html", revision: BuildId },
        ],
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.mode === "navigate",
            handler: "NetworkFirst",
            options: {
              cacheName: "termo-paginas",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 4, maxAgeSeconds: 86400 },
            },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@cloudive-brand": fileURLToPath(
        new URL("../cloudive/termo-online", import.meta.url)
      ),
    },
  },
  build: {
    outDir: "../src/static/dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
