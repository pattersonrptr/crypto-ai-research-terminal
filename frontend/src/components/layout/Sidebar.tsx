import { NavLink } from "react-router-dom";
import {
  BarChart3,
  Bell,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  Network,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useSidebarStore } from "@/store/sidebarStore";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  ariaLabel: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/",            label: "Rankings",    icon: BarChart3,     ariaLabel: "Go to Rankings" },
  { to: "/narratives",  label: "Narratives",  icon: TrendingUp,    ariaLabel: "Go to Narratives" },
  { to: "/ecosystems",  label: "Ecosystems",  icon: Network,       ariaLabel: "Go to Ecosystems" },
  { to: "/backtesting", label: "Backtesting", icon: FlaskConical,  ariaLabel: "Go to Backtesting" },
  { to: "/alerts",      label: "Alerts",      icon: Bell,          ariaLabel: "Go to Alerts" },
];

/**
 * Retractable vertical sidebar with navigation links.
 * Collapse state persists via useSidebarStore (localStorage).
 */
export function Sidebar() {
  const { isOpen, toggle } = useSidebarStore();

  return (
    <aside
      className={cn(
        "relative flex flex-shrink-0 flex-col border-r border-border bg-card",
        "transition-all duration-200 ease-in-out",
        isOpen ? "w-56" : "w-14",
      )}
      aria-label="Main navigation"
    >
      {/* Logo / Brand */}
      <div
        className={cn(
          "flex items-center gap-3 border-b border-border px-3 py-4",
          !isOpen && "justify-center",
        )}
      >
        <Zap className="h-6 w-6 shrink-0 text-primary" aria-hidden="true" />
        {isOpen && (
          <span className="truncate text-sm font-semibold tracking-tight text-foreground">
            Crypto AI
          </span>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon, ariaLabel }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            aria-label={ariaLabel}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium",
                "transition-colors duration-150",
                "hover:bg-accent hover:text-accent-foreground",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground",
                !isOpen && "justify-center",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {isOpen && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle button */}
      <button
        type="button"
        onClick={toggle}
        aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
        className={cn(
          "flex items-center justify-center border-t border-border p-3",
          "text-muted-foreground transition-colors hover:text-foreground",
          "hover:bg-accent",
        )}
      >
        {isOpen ? (
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        ) : (
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        )}
      </button>
    </aside>
  );
}
