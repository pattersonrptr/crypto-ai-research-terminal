import { useTableStore } from "@/store/tableStore";

const PAGE_SIZES = [25, 50, 100] as const;

/**
 * PageSizeSelector — dropdown to choose how many rows per page.
 *
 * Updates `tableStore.pageSize` and resets to page 1 on change.
 */
export function PageSizeSelector() {
  const { pageSize, setPageSize } = useTableStore();

  return (
    <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
      <span>Rows per page</span>
      <select
        aria-label="Rows per page"
        value={pageSize}
        onChange={(e) => setPageSize(Number(e.target.value))}
        className="rounded-md border border-border bg-background px-2 py-1 text-sm
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {PAGE_SIZES.map((size) => (
          <option key={size} value={size}>
            {size}
          </option>
        ))}
      </select>
    </label>
  );
}
