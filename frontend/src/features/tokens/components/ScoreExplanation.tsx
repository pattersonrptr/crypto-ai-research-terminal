import { useQuery } from "@tanstack/react-query";
import { fetchTokenExplanation } from "@/services/tokens.service";
import { cn } from "@/lib/utils";

interface ScoreExplanationProps {
  symbol: string;
}

/** Colour class for pillar score percentage. */
function pillarColour(score: number): string {
  if (score >= 0.7) return "bg-green-500/20 text-green-400";
  if (score >= 0.4) return "bg-yellow-500/20 text-yellow-400";
  return "bg-red-500/20 text-red-400";
}

/**
 * ScoreExplanation — "Why this score?" section on Token Detail.
 *
 * Fetches per-pillar explanations from GET /tokens/:symbol/explanation
 * and renders a human-readable summary for each scoring pillar.
 */
export function ScoreExplanation({ symbol }: ScoreExplanationProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["token-explanation", symbol],
    queryFn: () => fetchTokenExplanation(symbol),
    enabled: !!symbol,
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div
        className="h-48 animate-pulse rounded-xl bg-muted"
        aria-label="Loading score explanation"
      />
    );
  }

  if (isError || !data) {
    return null;
  }

  const pillarExplanations = data.explanations.filter(
    (e) => e.pillar !== "overall",
  );
  const overall = data.explanations.find((e) => e.pillar === "overall");

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      aria-label="Score explanation"
    >
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Why This Score?
      </h2>

      {/* Per-pillar explanations */}
      <div className="space-y-3">
        {pillarExplanations.map((item) => (
          <div key={item.pillar} className="flex items-start gap-3">
            <span
              className={cn(
                "mt-0.5 inline-flex h-6 min-w-[3rem] items-center justify-center rounded-full px-2 text-xs font-semibold",
                pillarColour(item.score),
              )}
            >
              {Math.round(item.score * 100)}%
            </span>
            <div>
              <span className="text-sm font-medium capitalize text-foreground">
                {item.pillar}
              </span>
              <p className="text-sm text-muted-foreground">
                {item.explanation}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Overall summary */}
      {overall && (
        <div className="mt-4 rounded-lg border border-border bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">
            {overall.explanation}
          </p>
        </div>
      )}
    </section>
  );
}
