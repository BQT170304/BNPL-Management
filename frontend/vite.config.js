import { defineConfig } from "vite";

// The new frontend is a React + in-browser-Babel prototype served as static
// assets from `public/`. Vite here is just a dev server + a proxy that forwards
// `/api/*` to the FastAPI backend, plus a static build.
const API_TARGET = process.env.VITE_API_TARGET || "http://127.0.0.1:8001";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "^/api/": {
        target: API_TARGET,
        changeOrigin: true,
        // backend routes are not prefixed with /api, so strip it
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      "^/api/": {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
