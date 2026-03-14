/**
 * ColumnPicker — dropdown button to show/hide ranking table columns.
 *
 * Renders as a trigger button that opens a floating panel with one checkbox
 * per hideable column, plus a "Reset" button to restore defaults.
 * State is persisted in Zustand's tableStore.
 */

import { useState, useRef, useEffect } from "react";
import { Columns3 } from "lucide-react";
import { useTableStore, ALL_COLUMNS } from "@/store/tableStore";
import { cn } from "@/lib/utils";

const HIDEABLE_COLUMNS = ALL_COLUMNS.filter((c) => c.hideable);

export function ColumnPicker() {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const { visibleColumns, toggleColumn, resetColumns } = useTableStore();

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Columns"
        aria-expanded={open}
        aria-haspopup="listbox"
        className={cn(
          "flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5",
          "text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
          open && "bg-accent text-foreground",
        )}
      >
        <Columns3 className="h-4 w-4" aria-hidden="true" />
        Columns
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          role="dialog"
          aria-label="Column visibility"
          className={cn(
            "absolute right-0 top-full z-20 mt-1 w-52",
            "rounded-xl border border-border bg-card p-3 shadow-lg",
          )}
        >
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Toggle columns
          </p>

          <ul className="space-y-1">
            {HIDEABLE_COLUMNS.map((col) => {
              const checked = visibleColumns.has(col.id);
              return (
                <li key={col.id}>
                  <label className="flex cursor-pointer items-center gap-2 rounded-md px-1 py-1 text-sm hover:bg-accent">
                    <input
                      type="checkbox"
                      aria-label={col.label}
                      checked={checked}
                      onChange={() => toggleColumn(col.id)}
                      className="h-3.5 w-3.5 accent-primary"
                    />
                    <span className="text-foreground">{col.label}</span>
                  </label>
                </li>
              );
            })}
          </ul>

          <hr className="my-2 border-border" />

          <button
            type="button"
            onClick={resetColumns}
            aria-label="Reset columns to default"
            className={cn(
              "w-full rounded-md border border-border py-1 text-xs",
              "text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
            )}
          >
            Reset
          </button>
        </div>
      )}
    </div>
  );
}
