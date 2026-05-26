import { defineConfig } from "vite";

export default defineConfig({
  base: '/static/custom_code/dist/',
  build: {
    outDir: "../custom_code/static/custom_code/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        target_detail: "src/pages/target-detail.ts",
        target_list: "src/pages/target-list.ts",
        observations: "src/pages/observations.ts",
      },
    },
  },
  server: {
    port: 5173,
  },
});