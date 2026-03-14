/**
 * Ecosystems page — visualises the token Knowledge Graph.
 *
 * Features:
 * - Community cards showing member tokens per detected cluster
 * - Top Tokens section ranked by PageRank
 * - Ecosystem snapshot summary (community count, total tokens)
 * - Loading state
 * - Error state
 */

import { useQuery } from "@tanstack/react-query";
import { Network, Star } from "lucide-react";
import { fetchCommunities, fetchEcosystem } from "@/services/graph.service";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn } from "@/lib/utils";

// ── CommunityCard ─────────────────────────────────────────────────────────

interface CommunityCardProps {
  id: number;
  members: string[];
}

function CommunityCard({ id, members }: CommunityCardProps) {
  return (
    <article
      className="rounded-lg border border-border bg-card p-4"
      aria-label={`Community ${id}`}
    >
      <header className="mb-3 flex items-center gap-2">
        <Network className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-foreground">
          Cluster {id}
        </h3>
        <span className="ml-auto text-xs text-muted-foreground">
          {members.length} tokens
        </span>
      </header>
      <div className="flex flex-wrap gap-1.5">
        {members.map((symbol) => (
          <span
            key={symbol}
            className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
          >
            {symbol}
          </span>
        ))}
      </div>
    </article>
  );
}

// ── TopTokenBadge ─────────────────────────────────────────────────────────

function TopTokenBadge({ symbol, rank }: { symbol: string; rank: number }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
      <Star
        className={cn(
          "h-3.5 w-3.5 shrink-0",
          rank === 1
            ? "fill-yellow-400 text-yellow-400"
            : rank <= 3
              ? "fill-muted-foreground text-muted-foreground"
              : "text-muted-foreground",
        )}
        aria-hidden="true"
      />
      <span className="text-xs font-medium text-foreground">{symbol}</span>
      <span className="ml-auto text-xs text-muted-foreground">#{rank}</span>
    </div>
  );
}

// ── Ecosystems ────────────────────────────────────────────────────────────

export function Ecosystems() {
  const communitiesQuery = useQuery({
    queryKey: ["graph", "communities"],
    queryFn: fetchCommunities,
  });

  const ecosystemQuery = useQuery({
    queryKey: ["graph", "ecosystem"],
    queryFn: fetchEcosystem,
  });

  const isLoading = communitiesQuery.isLoading || ecosystemQuery.isLoading;
  const isError = communitiesQuery.isError || ecosystemQuery.isError;

  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Loading ecosystem data"
        className="flex items-center justify-center py-16"
      >
        <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (isError) {
    return (
      <p className="py-8 text-center text-sm text-destructive">
        Failed to load ecosystem data. Please try again.
      </p>
    );
  }

  const communities = communitiesQuery.data ?? [];
  const snapshot = ecosystemQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ecosystems"
        description="Token knowledge graph — community clusters and influence scores"
      />

      {/* Summary stats */}
      {snapshot && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-4 text-center">
            <p className="text-2xl font-bold text-primary">
              {snapshot.n_communities}
            </p>
            <p className="text-xs text-muted-foreground">Communities</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4 text-center">
            <p className="text-2xl font-bold text-primary">
              {snapshot.total_tokens}
            </p>
            <p className="text-xs text-muted-foreground">Total Tokens</p>
          </div>
        </div>
      )}

      {/* Community clusters */}
      <section aria-labelledby="communities-heading">
        <h2
          id="communities-heading"
          className="mb-4 text-base font-semibold text-foreground"
        >
          Token Communities
        </h2>
        {communities.length === 0 ? (
          <p className="text-sm text-muted-foreground">No communities found.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {communities.map((c) => (
              <CommunityCard key={c.id} id={c.id} members={c.members} />
            ))}
          </div>
        )}
      </section>

      {/* Top tokens */}
      {snapshot && snapshot.top_tokens.length > 0 && (
        <section aria-labelledby="top-tokens-heading">
          <h2
            id="top-tokens-heading"
            className="mb-4 text-base font-semibold text-foreground"
          >
            Top Tokens by PageRank
          </h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {snapshot.top_tokens.map((symbol, idx) => (
              <TopTokenBadge key={symbol} symbol={symbol} rank={idx + 1} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
