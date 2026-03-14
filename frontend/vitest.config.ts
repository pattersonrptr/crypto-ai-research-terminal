/// <reference types="vitest" />
import path from "path";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
      exclude: [
        "src/test/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
        "**/*.config.*",
        "**/node_modules/**",
        // ── Stub pages — not yet implemented, excluded until tests are added ──
        "src/pages/Alerts.tsx",
        "src/pages/Narratives.tsx",
        // ── App shell — tested end-to-end via page tests ──
        "src/App.tsx",
        // ── Layout components — dedicated tests coming next phase ──
        "src/components/layout/AppShell.tsx",
        "src/components/layout/Sidebar.tsx",
        "src/components/layout/ThemeProvider.tsx",
        "src/components/layout/TopBar.tsx",
        // ── Zustand stores — pure client state, tested via component tests ──
        "src/store/**",
        // ── Service modules not yet exercised by current tests ──
        "src/services/alerts.service.ts",
        // reports.service.ts — PDF Blob path cannot be tested in jsdom;
        // the markdown fetch is exercised via TokenDetail interaction test.
        "src/services/reports.service.ts",
      ],
    },
  },
});
