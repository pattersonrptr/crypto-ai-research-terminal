import { useQuery } from "@tanstack/react-query";
import { fetchMarketCycle } from "@/services/market.service";
import { cn } from "@/lib/utils";

/** Colours and emojis keyed by cycle phase. */
const PHASE_STYLE: Record<string, { emoji: string; colorClass: string }> = {
  bull: { emoji: "🟢", colorClass: "text-green-500" },
  accumulation: { emoji: "🔵", colorClass: "text-blue-500" },
  distribution: { emoji: "🟠", colorClass: "text-orange-500" },
  bear: { emoji: "🔴", colorClass: "text-red-500" },
};

/**
 * CycleIndicator — compact badge that shows the current market cycle phase.
 *
 * Designed to sit in the dashboard header. Fetches data from `/market/cycle`
 * and auto-refreshes every 60 s.
 */
export function CycleIndicator() {
  const {
    data: cycle,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["market-cycle"],
    queryFn: fetchMarketCycle,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  if (isLoading) {
    return (
      <span
        className="inline-block h-6 w-32 animate-pulse rounded-md bg-muted"
        aria-label="Loading cycle indicator"
      />
    );
  }

  if (isError || !cycle) {
    return null; // gracefully hidden
  }

  const style = PHASE_STYLE[cycle.phase] ?? {
    emoji: "⚪",
    colorClass: "text-muted-foreground",
  };

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-sm shadow-sm"
      aria-label="Market cycle indicator"
      title={cycle.phase_description}
    >
      <span aria-hidden="true">{style.emoji}</span>
      <span className={cn("font-medium capitalize", style.colorClass)}>
        {cycle.phase}
      </span>
      <span className="text-muted-foreground">
        ({Math.round(cycle.confidence * 100)}%)
      </span>
    </div>
  );
}
