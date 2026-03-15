import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";
import { ArrowLeft, FileText, Download } from "lucide-react";
import { fetchToken } from "@/services/tokens.service";
import {
  fetchTokenReport,
  downloadPdf,
  type ReportFormat,
} from "@/services/reports.service";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn, formatUsd, formatScore, scoreColour, formatPct } from "@/lib/utils";

/**
 * TokenDetail page — full analysis of a single token.
 */
export function TokenDetail() {
  const { symbol } = useParams<{ symbol: string }>();

  const { data: token, isLoading, isError } = useQuery({
    queryKey: ["token", symbol],
    queryFn: () => fetchToken(symbol!),
    enabled: !!symbol,
  });

  async function handleDownloadReport(format: ReportFormat) {
    if (!symbol) return;
    const result = await fetchTokenReport(symbol, format);
    if (format === "pdf") {
      downloadPdf(result as Blob, `${symbol}-report.pdf`);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-xl bg-card" />
      </div>
    );
  }

  if (isError || !token) {
    return (
      <p className="text-destructive" role="alert">
        Token not found or backend unavailable.
      </p>
    );
  }

  const score = token.latest_score;

  // Radar chart data — 5 fundamental pillars
  const radarData = score
    ? [
        { pillar: "Technology",   value: score.technology_score },
        { pillar: "Tokenomics",   value: score.tokenomics_score },
        { pillar: "Adoption",     value: score.adoption_score },
        { pillar: "Dev Activity", value: score.dev_activity_score },
        { pillar: "Narrative",    value: score.narrative_score },
      ]
    : [];

  return (
    <div>
      {/* Back link */}
      <Link
        to="/"
        aria-label="Back to rankings"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Rankings
      </Link>

      <PageHeader
        title={`${token.symbol} — ${token.name}`}
        description={token.category ?? undefined}
        actions={
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleDownloadReport("markdown")}
              aria-label={`Download ${token.symbol} markdown report`}
              className={cn(
                "flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5",
                "text-sm transition-colors hover:bg-accent",
              )}
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              Report MD
            </button>
            <button
              type="button"
              onClick={() => handleDownloadReport("pdf")}
              aria-label={`Download ${token.symbol} PDF report`}
              className={cn(
                "flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5",
                "text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
              )}
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              PDF Report
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* ── Radar chart ─────────────────────────────────────────── */}
        <section
          className="rounded-xl border border-border bg-card p-5"
          aria-label="Score radar chart"
        >
          <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Score Breakdown
          </h2>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="pillar"
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                />
                <Radar
                  name={token.symbol}
                  dataKey="value"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground">No score data available.</p>
          )}
        </section>

        {/* ── Score pillars ────────────────────────────────────────── */}
        <section
          className="rounded-xl border border-border bg-card p-5"
          aria-label="Detailed scores"
        >
          <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Detailed Scores
          </h2>
          {score ? (
            <div className="space-y-3">
              {(
                [
                  ["Opportunity",  score.opportunity_score],
                  ["Fundamental",  score.fundamental_score],
                  ["Technology",   score.technology_score],
                  ["Tokenomics",   score.tokenomics_score],
                  ["Adoption",     score.adoption_score],
                  ["Dev Activity", score.dev_activity_score],
                  ["Narrative",    score.narrative_score],
                  ["Growth",       score.growth_score],
                  ["Risk",         score.risk_score],
                ] as [string, number][]
              ).map(([label, raw]) => {
                // API returns 0-1; scale to 0-10 for display
                const value = raw * 10;
                return (
                <div key={label} className="flex items-center justify-between gap-4">
                  <span className="text-sm text-muted-foreground">{label}</span>
                  <div className="flex flex-1 items-center gap-2">
                    {/* Progress bar */}
                    <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className={cn("h-full rounded-full transition-all", {
                          "bg-score-high": value >= 7,
                          "bg-score-mid": value >= 4 && value < 7,
                          "bg-score-low": value < 4,
                        })}
                        style={{ width: `${(value / 10) * 100}%` }}
                        role="progressbar"
                        aria-valuenow={Math.round(value * 10) / 10}
                        aria-valuemin={0}
                        aria-valuemax={10}
                        aria-label={`${label} score`}
                      />
                    </div>
                    <span className={cn("font-numeric w-8 text-right text-sm font-semibold", scoreColour(value))}>
                      {formatScore(value)}
                    </span>
                  </div>
                </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No score data available.</p>
          )}
        </section>

        {/* ── Market metrics ───────────────────────────────────────── */}
        <section
          className="rounded-xl border border-border bg-card p-5 lg:col-span-2"
          aria-label="Market metrics"
        >
          <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Market Metrics
          </h2>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              ["Price",      token.price_usd    !== null ? formatUsd(token.price_usd)    : "—"],
              ["Market Cap", token.market_cap    !== null ? formatUsd(token.market_cap)   : "—"],
              ["Volume 24h", token.volume_24h    !== null ? formatUsd(token.volume_24h)   : "—"],
              ["7d Change",  token.price_change_7d !== null ? formatPct(token.price_change_7d) : "—"],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs text-muted-foreground">{label}</dt>
                <dd className="font-numeric mt-1 text-lg font-semibold text-foreground">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}
