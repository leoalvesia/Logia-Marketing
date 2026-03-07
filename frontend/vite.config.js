import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { visualizer } from "rollup-plugin-visualizer";

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: false, filename: "dist/stats.html", gzipSize: true }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Core vendor: react, router, state, HTTP
          if (
            id.includes("node_modules/react/") ||
            id.includes("node_modules/react-dom/") ||
            id.includes("node_modules/react-router-dom/") ||
            id.includes("node_modules/axios/") ||
            id.includes("node_modules/zustand/") ||
            id.includes("node_modules/immer/")
          )
            return "vendor";

          // Radix UI primitives
          if (id.includes("node_modules/@radix-ui/")) return "radix-ui";

          // Heavy utility libs
          if (
            id.includes("node_modules/@dnd-kit/") ||
            id.includes("node_modules/@tanstack/")
          )
            return "ui-libs";

          // Route-level chunks
          if (
            id.includes("/pages/PipelinePage") ||
            id.includes("/components/Pipeline")
          )
            return "pipeline";

          if (
            id.includes("/pages/LibraryPage") ||
            id.includes("/components/Library")
          )
            return "library";

          if (
            id.includes("/pages/SettingsPage") ||
            id.includes("/components/Settings")
          )
            return "settings";
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
