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
      includeAssets: ["favicon.svg", "sounds/*.ogg"],
      manifest: {
        name: "Termo Online · Cloudive",
        short_name: "Termo",
        description: "Termo em português — um jogo Cloudive",
        theme_color: "#14111c",
        background_color: "#14111c",
        display: "standalone",
        lang: "pt-BR",
        icons: [
          {
            src: "/favicon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,ico,svg,ogg,woff2}"],
        globIgnores: ["**/index.html"],
        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api/, /^\/ws/],
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.mode === "navigate",
            handler: "NetworkFirst",
            options: {
              cacheName: "termo-paginas",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 2, maxAgeSeconds: 60 },
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
