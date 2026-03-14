import { Link } from "react-router-dom";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { RankingOpportunity } from "@/services/tokens.service";
import { cn, formatUsd, formatScore, formatPct, scoreColour } from "@/lib/utils";

interface TokenCardProps {
  opportunity: RankingOpportunity;
}

/**
 * TokenCard — airy card displaying one ranked token.
 * 10 per page on the Home view.
 */
export function TokenCard({ opportunity }: TokenCardProps) {
  const { rank, token, signals } = opportunity;
  const score = token.latest_score;

  const changeIcon =
    token.price_change_7d === null || token.price_change_7d === 0 ? (
      <Minus className="h-3 w-3" aria-hidden="true" />
    ) : token.price_change_7d > 0 ? (
      <TrendingUp className="h-3 w-3" aria-hidden="true" />
    ) : (
      <TrendingDown className="h-3 w-3" aria-hidden="true" />
    );

  const changeColour =
    token.price_change_7d === null || token.price_change_7d === 0
      ? "text-muted-foreground"
      : token.price_change_7d > 0
        ? "text-score-high"
        : "text-score-low";

  return (
    <Link
      to={`/tokens/${token.symbol}`}
      aria-label={`View ${token.symbol} details`}
      className="group block rounded-xl border border-border bg-card p-5 shadow-sm
                 transition-all duration-150 hover:border-primary/40 hover:shadow-md
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {/* ── Row 1: rank + symbol + name + category ─────────────────── */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <span className="font-numeric w-8 text-center text-xs font-semibold text-muted-foreground">
            #{rank}
          </span>
          <div>
            <span className="font-mono text-lg font-bold text-foreground">
              {token.symbol}
            </span>
            <p className="text-xs text-muted-foreground">{token.name}</p>
          </div>
        </div>

        {/* Category badge */}
        {token.category && (
          <span className="shrink-0 rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
            {token.category}
          </span>
        )}
      </div>

      {/* ── Row 2: scores ───────────────────────────────────────────── */}
      <div className="mt-4 grid grid-cols-5 gap-2">
        {(
          [
            ["Score",  score?.opportunity_score  ?? null],
            ["Fund.",  score?.fundamental_score  ?? null],
            ["Growth", score?.growth_score        ?? null],
            ["Narr.",  score?.narrative_score     ?? null],
            ["Risk",   score?.risk_score          ?? null],
          ] as [string, number | null][]
        ).map(([label, value]) => (
          <div key={label} className="flex flex-col items-center">
            <span className="text-[10px] text-muted-foreground">{label}</span>
            <span
              className={cn(
                "font-numeric text-sm font-semibold",
                value !== null ? scoreColour(value) : "text-muted-foreground",
              )}
            >
              {value !== null ? formatScore(value) : "N/A"}
            </span>
          </div>
        ))}
      </div>

      {/* ── Row 3: market stats ─────────────────────────────────────── */}
      <div className="mt-4 flex items-center justify-between gap-2 text-xs text-muted-foreground">
        {token.price_usd !== null && (
          <span className="font-numeric font-medium text-foreground">
            {formatUsd(token.price_usd)}
          </span>
        )}

        {token.market_cap !== null && (
          <span>Mkt: {formatUsd(token.market_cap)}</span>
        )}

        {token.price_change_7d !== null && (
          <span className={cn("flex items-center gap-0.5 font-medium", changeColour)}>
            {changeIcon}
            {formatPct(token.price_change_7d)}
          </span>
        )}
      </div>

      {/* ── Row 4: signal chips ─────────────────────────────────────── */}
      {signals.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {signals.map((sig) => (
            <span
              key={sig}
              className="rounded-md bg-primary/10 px-2 py-0.5 text-[10px]
                         font-medium text-primary"
            >
              {sig}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
