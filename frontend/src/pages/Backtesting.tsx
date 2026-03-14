/**
 * Backtesting page — configure and run historical backtests.
 *
 * Features:
 * - Form: symbol input + cycle selector + run button
 * - Results panel with key metrics (total return, trades, win rate, Sharpe, drawdown)
 * - Error state
 * - Loading state on the button while running
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { PlayCircle } from "lucide-react";
import {
  runBacktest,
  type BacktestResult,
  type CycleLabel,
} from "@/services/backtesting.service";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn } from "@/lib/utils";

// ── MetricCard ────────────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "positive" | "negative" | "neutral";
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 text-center">
      <p
        className={cn(
          "text-xl font-bold",
          highlight === "positive"
            ? "text-green-400"
            : highlight === "negative"
              ? "text-red-400"
              : "text-foreground",
        )}
      >
        {value}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

// ── ResultsPanel ──────────────────────────────────────────────────────────

function ResultsPanel({ result }: { result: BacktestResult }) {
  const returnHighlight = result.is_profitable ? "positive" : "negative";
  return (
    <section aria-labelledby="results-heading" className="space-y-4">
      <h2
        id="results-heading"
        className="text-base font-semibold text-foreground"
      >
        Results —{" "}
        <span className="text-primary">
          {result.symbol} / {result.cycle}
        </span>
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          label="Total Return"
          value={`${result.total_return_pct.toFixed(1)}%`}
          highlight={returnHighlight}
        />
        <MetricCard
          label="Trades"
          value={String(result.n_trades)}
          highlight="neutral"
        />
        <MetricCard
          label="Win Rate"
          value={`${(result.win_rate * 100).toFixed(0)}%`}
          highlight={result.win_rate >= 0.5 ? "positive" : "negative"}
        />
        <MetricCard
          label="Sharpe Ratio"
          value={result.sharpe_ratio.toFixed(2)}
          highlight={result.sharpe_ratio > 1 ? "positive" : "neutral"}
        />
        <MetricCard
          label="Max Drawdown"
          value={`${result.max_drawdown_pct.toFixed(1)}%`}
          highlight="negative"
        />
        <MetricCard
          label="Avg Trade"
          value={`${result.avg_trade_return_pct.toFixed(1)}%`}
          highlight={result.avg_trade_return_pct >= 0 ? "positive" : "negative"}
        />
      </div>
    </section>
  );
}

// ── Backtesting ───────────────────────────────────────────────────────────

const CYCLE_OPTIONS: { value: CycleLabel; label: string }[] = [
  { value: "bull", label: "Bull (2017–2018)" },
  { value: "bear", label: "Bear (2018–2020)" },
  { value: "accumulation", label: "Accumulation (2020–2021)" },
];

export function Backtesting() {
  const [symbol, setSymbol] = useState("BTC");
  const [cycle, setCycle] = useState<CycleLabel>("bull");

  const mutation = useMutation({
    mutationFn: () => runBacktest({ symbol: symbol.trim().toUpperCase(), cycle }),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Backtesting"
        description="Replay the momentum strategy on historical market cycles to validate signal quality."
      />

      {/* Configuration form */}
      <section aria-labelledby="config-heading">
        <h2
          id="config-heading"
          className="mb-4 text-base font-semibold text-foreground"
        >
          Simulation Parameters
        </h2>
        <form
          onSubmit={handleSubmit}
          className="flex flex-wrap items-end gap-4"
          aria-label="Backtest configuration"
        >
          {/* Symbol */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="backtest-symbol"
              className="text-xs font-medium text-muted-foreground"
            >
              Symbol
            </label>
            <input
              id="backtest-symbol"
              type="text"
              aria-label="Symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="e.g. BTC"
              className="w-32 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Cycle */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="backtest-cycle"
              className="text-xs font-medium text-muted-foreground"
            >
              Cycle
            </label>
            <select
              id="backtest-cycle"
              aria-label="Cycle"
              value={cycle}
              onChange={(e) => setCycle(e.target.value as CycleLabel)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {CYCLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            aria-label="Run backtest"
            disabled={mutation.isPending || !symbol.trim()}
            className={cn(
              "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
              "bg-primary text-primary-foreground transition-opacity",
              "hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring",
              (mutation.isPending || !symbol.trim()) && "cursor-not-allowed opacity-50",
            )}
          >
            <PlayCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            {mutation.isPending ? "Running…" : "Run Backtest"}
          </button>
        </form>
      </section>

      {/* Error state */}
      {mutation.isError && (
        <p className="text-sm text-destructive">
          Simulation failed. Please check the symbol and try again.
        </p>
      )}

      {/* Results */}
      {mutation.data && <ResultsPanel result={mutation.data} />}
    </div>
  );
}
