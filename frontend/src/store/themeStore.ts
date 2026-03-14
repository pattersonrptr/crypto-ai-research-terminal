import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "dark" | "light" | "system";

interface ThemeState {
  mode: ThemeMode;
  /** Resolved theme after applying system preference — always "dark" or "light". */
  resolved: "dark" | "light";
  setMode: (mode: ThemeMode) => void;
}

/** Read the OS colour-scheme preference. */
function getSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function resolve(mode: ThemeMode): "dark" | "light" {
  return mode === "system" ? getSystemTheme() : mode;
}

/** Apply the resolved theme to <html> by toggling the "dark" / "light" class. */
function applyTheme(resolved: "dark" | "light"): void {
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  root.classList.add(resolved);
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: "dark",
      resolved: "dark",

      setMode(mode) {
        const resolved = resolve(mode);
        applyTheme(resolved);
        set({ mode, resolved });
      },
    }),
    {
      name: "theme-preference",
      // Re-apply theme on rehydration from localStorage
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = resolve(state.mode);
          applyTheme(resolved);
          state.resolved = resolved;
        }
      },
    },
  ),
);

// ── Listen for OS theme changes when mode === "system" ─────────────────────
if (typeof window !== "undefined") {
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      const { mode, setMode } = useThemeStore.getState();
      if (mode === "system") setMode("system");
    });
}
