// Vitest + React Testing Library global setup
// This file is referenced in vitest.config.ts → test.setupFiles

import "@testing-library/jest-dom";
import { server } from "./msw/server";

// ── jsdom polyfills ───────────────────────────────────────────────────────

/**
 * Recharts' ResponsiveContainer uses ResizeObserver which is not available
 * in jsdom. Polyfill it with a no-op so chart components render without crashing.
 */
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// ── MSW server lifecycle ──────────────────────────────────────────────────

// Start MSW before all tests, reset handlers between tests so
// per-test overrides (server.use) don't bleed across tests,
// and shut down cleanly after the suite.
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
