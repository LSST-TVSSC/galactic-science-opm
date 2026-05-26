import { defineConfig } from "vite";

export default defineConfig({
  base: '/static/custom_code/dist/',
  build: {
    outDir: "../custom_code/static/custom_code/dist",
    emptyOutDir: true,
    manifest: true
  },
  server: {
    port: 5173,
  },
});