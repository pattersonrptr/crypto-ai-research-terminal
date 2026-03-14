import axios from "axios";

/**
 * Central Axios instance.
 * Base URL is read from the Vite env variable VITE_API_BASE_URL (default: /api).
 * The Vite dev-server proxy rewrites /api → http://localhost:8000.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

// ── Request interceptor — attach any future auth token here ───────────────
apiClient.interceptors.request.use((config) => config);

// ── Response interceptor — normalise errors ───────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    // Re-throw so React Query can surface it to the UI
    return Promise.reject(error);
  },
);
