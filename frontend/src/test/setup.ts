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

/**
 * Zustand `persist` middleware uses localStorage.setItem / getItem.
 * jsdom provides localStorage, but the Vitest worker doesn't expose it unless
 * --localstorage-file is set. Polyfill with a simple in-memory implementation
 * so Zustand stores initialise without error in tests.
 */
if (typeof localStorage === "undefined" || !localStorage.setItem) {
  const store: Record<string, string> = {};
  Object.defineProperty(global, "localStorage", {
    value: {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => { store[key] = value; },
      removeItem: (key: string) => { delete store[key]; },
      clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
      get length() { return Object.keys(store).length; },
      key: (i: number) => Object.keys(store)[i] ?? null,
    },
    writable: true,
  });
}

/**
 * themeStore uses window.matchMedia to detect OS colour-scheme preference.
 * jsdom does not implement matchMedia — provide a no-op stub.
 */
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// ── MSW server lifecycle ──────────────────────────────────────────────────

// Start MSW before all tests, reset handlers between tests so
// per-test overrides (server.use) don't bleed across tests,
// and shut down cleanly after the suite.
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
