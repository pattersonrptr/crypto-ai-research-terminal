import { type ReactNode, useEffect } from "react";
import { useThemeStore } from "@/store/themeStore";

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * ThemeProvider applies the stored theme class to <html> on first render
 * and keeps it in sync whenever the Zustand store changes.
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const { mode, setMode } = useThemeStore();

  // Apply on mount (covers SSR hydration and hard refresh)
  useEffect(() => {
    setMode(mode);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>;
}
