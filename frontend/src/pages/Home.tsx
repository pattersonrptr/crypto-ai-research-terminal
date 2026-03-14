import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchRankingOpportunities } from "@/services/tokens.service";
import { TokenCard } from "@/features/tokens/components/TokenCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;

/**
 * Home page — paginated rankings grid.
 * Each page shows 10 TokenCards (airy layout).
 */
export function Home() {
  const [page, setPage] = useState(1);

  const { data: opportunities = [], isLoading, isError } = useQuery({
    queryKey: ["rankings"],
    queryFn: () => fetchRankingOpportunities({ limit: 100 }),
    refetchInterval: 30_000,
  });

  const totalPages = Math.max(1, Math.ceil(opportunities.length / PAGE_SIZE));
  const pageItems = opportunities.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div>
      <PageHeader
        title="Top Opportunities"
        description={`${opportunities.length} tokens analysed — updated daily`}
      />

      {/* ── Loading state ─────────────────────────────────────────── */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: PAGE_SIZE }).map((_, i) => (
            <div
              key={i}
              className="h-52 animate-pulse rounded-xl border border-border bg-card"
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

      {/* ── Cards grid ────────────────────────────────────────────── */}
      {!isLoading && !isError && (
        <>
          <div
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
            aria-label="Token rankings"
          >
            {pageItems.map((opp) => (
              <TokenCard key={opp.token.symbol} opportunity={opp} />
            ))}
          </div>

          {/* ── Pagination ──────────────────────────────────────────── */}
          {totalPages > 1 && (
            <nav
              className="mt-8 flex items-center justify-center gap-2"
              aria-label="Rankings pagination"
            >
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                aria-label="Previous page"
                className={cn(
                  "rounded-md border border-border px-3 py-1.5 text-sm",
                  "transition-colors hover:bg-accent disabled:opacity-40",
                )}
              >
                ← Prev
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPage(p)}
                  aria-label={`Go to page ${p}`}
                  aria-current={page === p ? "page" : undefined}
                  className={cn(
                    "rounded-md border px-3 py-1.5 text-sm transition-colors",
                    page === p
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border hover:bg-accent",
                  )}
                >
                  {p}
                </button>
              ))}

              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
