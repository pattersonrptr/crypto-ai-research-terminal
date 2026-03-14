/**
 * Narratives page — displays detected market narrative clusters.
 *
 * Features:
 * - Summary count of active narratives
 * - Narrative cards with name, trend badge, momentum score, tokens, keywords
 * - Error state
 * - Empty state
 */

import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Minus, Layers } from "lucide-react";
import { fetchNarratives, type NarrativeCluster, type NarrativeTrend } from "@/services/narratives.service";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn } from "@/lib/utils";

// ── helpers ────────────────────────────────────────────────────────────────

const TREND_META: Record<
  NarrativeTrend,
  { label: string; colour: string; Icon: React.ElementType }
> = {
  accelerating: {
    label: "Accelerating",
    colour: "bg-green-500/10 text-green-400",
    Icon: TrendingUp,
  },
  stable: {
    label: "Stable",
    colour: "bg-blue-500/10 text-blue-400",
    Icon: Minus,
  },
  declining: {
    label: "Declining",
    colour: "bg-red-500/10 text-red-400",
    Icon: TrendingDown,
  },
};

function MomentumBar({ score }: { score: number }) {
  const pct = Math.round((score / 10) * 100);
  const colour =
    pct >= 80
      ? "bg-green-500"
      : pct >= 50
        ? "bg-yellow-500"
        : "bg-red-500";
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div className={cn("h-full rounded-full", colour)} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── NarrativeCard ─────────────────────────────────────────────────────────

function NarrativeCard({ narrative }: { narrative: NarrativeCluster }) {
  const { label, colour, Icon } = TREND_META[narrative.trend];

  return (
    <li className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5">
      {/* Name + trend badge */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-foreground">{narrative.name}</h3>
        <span
          className={cn(
            "flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
            colour,
          )}
          aria-label={`Trend: ${label}`}
        >
          <Icon className="h-3 w-3" aria-hidden="true" />
          {label}
        </span>
      </div>

      {/* Momentum */}
      <div className="flex items-center gap-3">
        <span className="w-20 text-xs text-muted-foreground">Momentum</span>
        <MomentumBar score={narrative.momentum_score} />
        <span className="w-8 text-right text-xs font-bold text-foreground">
          {narrative.momentum_score}
        </span>
      </div>

      {/* Token chips */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-xs text-muted-foreground">
          {narrative.token_count} token{narrative.token_count !== 1 ? "s" : ""}
        </span>
        {narrative.tokens.map((sym) => (
          <span
            key={sym}
            className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground"
          >
            {sym}
          </span>
        ))}
      </div>

      {/* Keywords */}
      <div className="flex flex-wrap gap-1.5">
        {narrative.keywords.map((kw) => (
          <span
            key={kw}
            className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground"
          >
            {kw}
          </span>
        ))}
      </div>
    </li>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

export function Narratives() {
  const {
    data: narratives = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["narratives"],
    queryFn: fetchNarratives,
    refetchInterval: 30_000,
  });

  return (
    <div>
      <PageHeader
        title="Narratives"
        description="Emerging narrative detection and momentum tracking."
      />

      {/* ── Summary ─────────────────────────────────────────────────────── */}
      {!isLoading && !isError && (
        <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
          <Layers className="h-4 w-4" aria-hidden="true" />
          <span>
            <strong className="text-foreground">{narratives.length}</strong>{" "}
            narratives detected
          </span>
        </div>
      )}

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-44 animate-pulse rounded-xl border border-border bg-card"
              aria-hidden="true"
            />
          ))}
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {isError && (
        <p className="text-destructive" role="alert">
          Failed to load narratives. Make sure the backend is running.
        </p>
      )}

      {/* ── Empty ───────────────────────────────────────────────────────── */}
      {!isLoading && !isError && narratives.length === 0 && (
        <p className="text-sm text-muted-foreground">No narratives detected yet.</p>
      )}

      {/* ── Grid ────────────────────────────────────────────────────────── */}
      {!isLoading && !isError && narratives.length > 0 && (
        <ul
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Narrative clusters"
        >
          {narratives.map((narrative: NarrativeCluster) => (
            <NarrativeCard key={narrative.id} narrative={narrative} />
          ))}
        </ul>
      )}
    </div>
  );
}
