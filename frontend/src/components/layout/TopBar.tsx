import { Moon, Sun, Monitor } from "lucide-react";
import { useThemeStore, type ThemeMode } from "@/store/themeStore";
import { cn } from "@/lib/utils";

const THEME_OPTIONS: { mode: ThemeMode; icon: React.ComponentType<{ className?: string }>; label: string }[] = [
  { mode: "light",  icon: Sun,     label: "Light theme"  },
  { mode: "dark",   icon: Moon,    label: "Dark theme"   },
  { mode: "system", icon: Monitor, label: "System theme" },
];

/**
 * TopBar — horizontal bar at the top of the content area.
 * Contains the page breadcrumb slot (left) and global controls (right).
 */
export function TopBar() {
  const { mode, setMode } = useThemeStore();

  return (
    <header
      className="flex h-12 shrink-0 items-center justify-between border-b border-border bg-card px-4"
      aria-label="Top navigation bar"
    >
      {/* Left slot — page title injected via PageHeader in each page */}
      <div className="flex items-center gap-2" id="topbar-title-slot" />

      {/* Right slot — global controls */}
      <div className="flex items-center gap-1" role="group" aria-label="Theme selector">
        {THEME_OPTIONS.map(({ mode: m, icon: Icon, label }) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            aria-label={label}
            aria-pressed={mode === m}
            className={cn(
              "rounded-md p-1.5 transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              mode === m
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground",
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </button>
        ))}
      </div>
    </header>
  );
}
