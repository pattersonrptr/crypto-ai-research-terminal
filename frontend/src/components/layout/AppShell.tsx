import { type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useSidebarStore } from "@/store/sidebarStore";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: ReactNode;
}

/**
 * AppShell — root layout wrapper.
 * Renders the retractable sidebar + topbar + main content area.
 */
export function AppShell({ children }: AppShellProps) {
  const isOpen = useSidebarStore((s) => s.isOpen);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <Sidebar />

      {/* Content area — shifts right when sidebar is open */}
      <div
        className={cn(
          "flex flex-1 flex-col overflow-hidden transition-all duration-200",
          isOpen ? "ml-0" : "ml-0", // sidebar handles its own width
        )}
      >
        <TopBar />
        <main
          className="flex-1 overflow-y-auto p-6"
          aria-label="Main content"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
