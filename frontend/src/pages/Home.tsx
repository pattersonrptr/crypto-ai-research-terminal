import { useQuery } from "@tanstack/react-query";
import { fetchRankingOpportunities } from "@/services/tokens.service";
import { RankingsTable } from "@/features/tokens/components/RankingsTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { CycleIndicator } from "@/components/Dashboard/CycleIndicator";
import { CollectNowButton } from "@/components/Dashboard/CollectNowButton";
import { useTableStore } from "@/store/tableStore";
import type { SortOrder } from "@/store/tableStore";
import { cn } from "@/lib/utils";

/**
 * Home page — server-side paginated rankings table.
 * Query state (search, categories, sort, page) lives in the tableStore and is
 * forwarded as API query params so filtering + sorting happen on the backend.
 */
export function Home() {
  const {
    search,
    setSearch,
    categories,
    excludeCategories,
    sort,
    order,
    setSort,
    page,
    setPage,
    pageSize,
  } = useTableStore();

  const { data: response, isLoading, isError } = useQuery({
    queryKey: [
      "rankings",
      { search, categories, excludeCategories, sort, order, page, pageSize },
    ],
    queryFn: () =>
      fetchRankingOpportunities({
        search: search || undefined,
        categories: categories.length ? categories.join(",") : undefined,
        exclude_categories: excludeCategories.length
          ? excludeCategories.join(",")
          : undefined,
        sort,
        order,
        page,
        page_size: pageSize,
      }),
    refetchInterval: 30_000,
  });

  const opportunities = response?.data ?? [];
  const totalCount = response?.total_count ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  function handleSortChange(column: string) {
    // Toggle direction if same column, default to desc for new column
    const newOrder: SortOrder =
      sort === column && order === "desc" ? "asc" : "desc";
    setSort(column, newOrder);
  }

  return (
    <div>
      <PageHeader
        title="Top Opportunities"
        description={`${totalCount} tokens analysed — updated daily`}
        actions={
          <div className="flex items-center gap-2">
            <CollectNowButton />
            <CycleIndicator />
          </div>
        }
      />

      {/* ── Search bar ────────────────────────────────────────────── */}
      <div className="mb-4">
        <input
          type="search"
          placeholder="Search tokens…"
          aria-label="Search tokens"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm rounded-md border border-border bg-background px-3 py-2
                     text-sm placeholder:text-muted-foreground
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      {/* ── Loading state ─────────────────────────────────────────── */}
      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-10 animate-pulse rounded border border-border bg-card"
              aria-hidden="true"
            />
          ))}
        </div>
      )}

      {/* ── Error state ───────────────────────────────────────────── */}
      {isError && (
        <p className="text-destructive" role="alert">
          Failed to load rankings. Make sure the backend is running.
        </p>
      )}

      {/* ── Table ─────────────────────────────────────────────────── */}
      {!isLoading && !isError && (
        <>
          <RankingsTable
            data={opportunities}
            sort={sort}
            order={order}
            onSortChange={handleSortChange}
          />

          {/* ── Pagination ──────────────────────────────────────────── */}
          {totalPages > 1 && (
            <nav
              className="mt-4 flex items-center justify-center gap-2"
              aria-label="Rankings pagination"
            >
              <button
                type="button"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                aria-label="Previous page"
                className={cn(
                  "rounded-md border border-border px-3 py-1.5 text-sm",
                  "transition-colors hover:bg-accent disabled:opacity-40",
                )}
              >
                ← Prev
              </button>

              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>

              <button
                type="button"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                aria-label="Next page"
                className={cn(
                  "rounded-md border border-border px-3 py-1.5 text-sm",
                  "transition-colors hover:bg-accent disabled:opacity-40",
                )}
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
