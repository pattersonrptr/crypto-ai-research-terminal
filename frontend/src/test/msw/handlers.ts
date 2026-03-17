/**
 * MSW v2 request handlers — used by every component/page test that calls the API.
 *
 * All paths are prefixed with `/api` to match the Axios baseURL default ("/api")
 * that is used in tests (VITE_API_BASE_URL is not set in the Vitest environment).
 *
 * Export `handlers` (default happy-path) and individual factory functions so
 * individual tests can override specific endpoints via `server.use(...)`.
 */

import { http, HttpResponse } from "msw";
import type {
  TokenWithScore,
  TokenScore,
  RankingOpportunity,
  ExplanationResponse,
} from "@/services/tokens.service";
import type { Alert, AlertStats } from "@/services/alerts.service";
import type { NarrativeCluster } from "@/services/narratives.service";
import type {
  Community,
  CentralityResult,
  EcosystemSnapshot,
} from "@/services/graph.service";
import type { MarketCycleResponse } from "@/services/market.service";
import type {
  CollectNowResponse,
  PipelineStatusResponse,
} from "@/services/pipeline.service";

// ── Shared mock data factories ─────────────────────────────────────────────

export function makeMockScore(overrides: Partial<TokenScore> = {}): TokenScore {
  return {
    fundamental_score: 0.72,
    technology_score: 0.80,
    tokenomics_score: 0.65,
    adoption_score: 0.70,
    dev_activity_score: 0.75,
    narrative_score: 0.68,
    growth_score: 0.60,
    risk_score: 0.30,
    listing_probability: 0.55,
    cycle_leader_prob: 0.40,
    opportunity_score: 0.71,
    snapshot_date: "2025-01-15T00:00:00Z",
    ...overrides,
  };
}

export function makeMockToken(
  overrides: Partial<TokenWithScore> = {},
): TokenWithScore {
  return {
    id: 1,
    symbol: "BTC",
    name: "Bitcoin",
    coingecko_id: "bitcoin",
    category: "Layer 1",
    github_repo: "https://github.com/bitcoin/bitcoin",
    whitepaper_url: "https://bitcoin.org/bitcoin.pdf",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2025-01-15T00:00:00Z",
    latest_score: makeMockScore(),
    price_usd: 45_000,
    market_cap: 880_000_000_000,
    volume_24h: 25_000_000_000,
    price_change_7d: 3.5,
    rank: 1,
    ...overrides,
  };
}

export function makeMockOpportunity(
  rank: number,
  tokenOverrides: Partial<TokenWithScore> = {},
): RankingOpportunity {
  return {
    rank,
    token: makeMockToken({ id: rank, rank, ...tokenOverrides }),
    signals: ["Strong developer activity", "Narrative alignment"],
  };
}

/** 15 mock opportunities — enough to test pagination (10 on page 1, 5 on page 2). */
export const MOCK_OPPORTUNITIES: RankingOpportunity[] = Array.from(
  { length: 15 },
  (_, i) => {
    const rank = i + 1;
    return makeMockOpportunity(rank, {
      symbol: `TKN${rank}`,
      name: `Token ${rank}`,
      id: rank,
    });
  },
);

export const MOCK_TOKEN_BTC = makeMockToken();

export const MOCK_ALERTS: Alert[] = [
  {
    id: 1,
    token_id: 1,
    alert_type: "LISTING_CANDIDATE",
    message: "BTC is a strong listing candidate.",
    metadata: {},
    sent_telegram: false,
    acknowledged: false,
    created_at: "2025-01-15T10:00:00Z",
  },
  {
    id: 2,
    token_id: null,
    alert_type: "DAILY_REPORT",
    message: "Daily market report generated.",
    metadata: {},
    sent_telegram: true,
    acknowledged: true,
    created_at: "2025-01-15T08:00:00Z",
  },
];

export const MOCK_ALERT_STATS: AlertStats = {
  total: 42,
  by_type: {
    LISTING_CANDIDATE: 10,
    MEMECOIN_HYPE_DETECTED: 5,
    WHALE_ACCUMULATION: 8,
    NARRATIVE_EMERGING: 4,
    RUGPULL_RISK: 3,
    TOKEN_UNLOCK_SOON: 2,
    DAILY_REPORT: 7,
    MANIPULATION_DETECTED: 3,
  },
  unacknowledged: 15,
};

export const MOCK_NARRATIVES: NarrativeCluster[] = [
  {
    id: 1,
    name: "AI & Machine Learning",
    momentum_score: 9.2,
    trend: "accelerating",
    tokens: ["FET", "RNDR", "TAO"],
    keywords: ["AI agents", "GPU compute"],
    token_count: 3,
  },
  {
    id: 2,
    name: "Layer 2 Scaling",
    momentum_score: 7.8,
    trend: "stable",
    tokens: ["ARB", "OP", "MATIC"],
    keywords: ["rollups", "gas fees"],
    token_count: 3,
  },
];

// ── Handler factories (for per-test overrides) ────────────────────────────

export function rankingsHandler(
  data: RankingOpportunity[] = MOCK_OPPORTUNITIES,
) {
  return http.get("/api/rankings/opportunities", () =>
    HttpResponse.json(data),
  );
}

export function rankingsErrorHandler() {
  return http.get("/api/rankings/opportunities", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

export function tokensHandler(data: TokenWithScore[] = [MOCK_TOKEN_BTC]) {
  return http.get("/api/tokens", () => HttpResponse.json(data));
}

export function tokenDetailHandler(data: TokenWithScore = MOCK_TOKEN_BTC) {
  return http.get("/api/tokens/:symbol", () => HttpResponse.json(data));
}

export function tokenDetailErrorHandler() {
  return http.get("/api/tokens/:symbol", () =>
    HttpResponse.json({ detail: "Token not found" }, { status: 404 }),
  );
}

export function alertsHandler(data: Alert[] = MOCK_ALERTS) {
  return http.get("/api/alerts", () => HttpResponse.json(data));
}

export function alertStatsHandler(data: AlertStats = MOCK_ALERT_STATS) {
  return http.get("/api/alerts/stats", () => HttpResponse.json(data));
}

export function acknowledgeAlertHandler() {
  return http.put("/api/alerts/:id/acknowledge", ({ params }) => {
    const id = Number(params.id);
    const alert = MOCK_ALERTS.find((a) => a.id === id) ?? MOCK_ALERTS[0];
    return HttpResponse.json({ ...alert, acknowledged: true });
  });
}

export function testAlertHandler() {
  return http.post("/api/alerts/test", () =>
    HttpResponse.json({ status: "ok" }),
  );
}

export function narrativesHandler(data: NarrativeCluster[] = MOCK_NARRATIVES) {
  return http.get("/api/narratives", () => HttpResponse.json(data));
}

export function narrativesErrorHandler() {
  return http.get("/api/narratives", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

export function tokenReportHandler(symbol = "BTC") {
  return http.get(`/api/reports/token/${symbol}`, () =>
    new HttpResponse(
      `# ${symbol} Research Report\n\nThis is a mock report for testing purposes.`,
      { headers: { "Content-Type": "text/plain" } },
    ),
  );
}

export function marketReportHandler() {
  return http.get("/api/reports/market", () =>
    new HttpResponse("# Market Report\n\nMock market report.", {
      headers: { "Content-Type": "text/plain" },
    }),
  );
}

// ── Graph mock data ───────────────────────────────────────────────────────

export const MOCK_COMMUNITIES: Community[] = [
  { id: 0, members: ["ETH", "ARB", "OP", "MATIC", "UNI", "AAVE"], size: 6 },
  { id: 1, members: ["FET", "RNDR", "TAO"], size: 3 },
  { id: 2, members: ["BTC", "BNB", "SOL", "AVAX", "TIA"], size: 5 },
];

export const MOCK_CENTRALITY: CentralityResult[] = [
  { symbol: "ETH", pagerank: 0.22, betweenness: 0.45, degree_centrality: 0.57 },
  { symbol: "BTC", pagerank: 0.14, betweenness: 0.10, degree_centrality: 0.14 },
  { symbol: "FET", pagerank: 0.09, betweenness: 0.20, degree_centrality: 0.29 },
];

export const MOCK_ECOSYSTEM: EcosystemSnapshot = {
  timestamp: "2025-01-15T00:00:00+00:00",
  n_communities: 3,
  total_tokens: 14,
  top_tokens: ["ETH", "BTC", "FET", "UNI", "RNDR"],
};

// ── Graph handler factories ───────────────────────────────────────────────

export function graphCommunitiesHandler(data: Community[] = MOCK_COMMUNITIES) {
  return http.get("/api/graph/communities", () => HttpResponse.json(data));
}

export function graphCommunitiesErrorHandler() {
  return http.get("/api/graph/communities", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

export function graphCentralityHandler(
  data: CentralityResult[] = MOCK_CENTRALITY,
) {
  return http.get("/api/graph/centrality", () => HttpResponse.json(data));
}

export function graphEcosystemHandler(data: EcosystemSnapshot = MOCK_ECOSYSTEM) {
  return http.get("/api/graph/ecosystem", () => HttpResponse.json(data));
}

// ── Backtesting mock data ─────────────────────────────────────────────────

export interface BacktestResult {
  symbol: string;
  cycle: string;
  total_return_pct: number;
  n_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  avg_trade_return_pct: number;
  is_profitable: boolean;
}

export const MOCK_BACKTEST_RESULT: BacktestResult = {
  symbol: "BTC",
  cycle: "bull",
  total_return_pct: 42.5,
  n_trades: 8,
  win_rate: 0.75,
  sharpe_ratio: 1.2,
  max_drawdown_pct: 15.3,
  avg_trade_return_pct: 5.3,
  is_profitable: true,
};

// ── Backtesting handler factories ─────────────────────────────────────────

export function backtestRunHandler(data: BacktestResult = MOCK_BACKTEST_RESULT) {
  return http.post("/api/backtesting/run", () => HttpResponse.json(data));
}

export function backtestRunErrorHandler() {
  return http.post("/api/backtesting/run", () =>
    HttpResponse.json({ detail: "Simulation failed" }, { status: 500 }),
  );
}

// ── Validation mock data ──────────────────────────────────────────────────

export interface TokenBreakdownItem {
  symbol: string;
  model_rank: number;
  model_score: number;
  actual_multiplier: number;
  is_winner: boolean;
}

export interface ValidateResult {
  precision_at_k: number;
  recall_at_k: number;
  hit_rate: number;
  k: number;
  winner_threshold: number;
  n_total_tokens: number;
  n_winners: number;
  model_is_useful: boolean;
  token_breakdown: TokenBreakdownItem[];
}

export const MOCK_VALIDATE_RESULT: ValidateResult = {
  precision_at_k: 0.8,
  recall_at_k: 0.6,
  hit_rate: 0.7,
  k: 10,
  winner_threshold: 5.0,
  n_total_tokens: 15,
  n_winners: 12,
  model_is_useful: true,
  token_breakdown: [
    { symbol: "SOL", model_rank: 1, model_score: 0.88, actual_multiplier: 320.0, is_winner: true },
    { symbol: "AVAX", model_rank: 2, model_score: 0.85, actual_multiplier: 55.0, is_winner: true },
    { symbol: "MATIC", model_rank: 3, model_score: 0.82, actual_multiplier: 95.0, is_winner: true },
    { symbol: "LINK", model_rank: 4, model_score: 0.78, actual_multiplier: 12.0, is_winner: true },
    { symbol: "UNI", model_rank: 5, model_score: 0.75, actual_multiplier: 18.0, is_winner: true },
  ],
};

export interface CalibrateResult {
  best_weights: {
    fundamental: number;
    growth: number;
    narrative: number;
    listing: number;
    risk: number;
  };
  best_precision_at_k: number;
  n_combinations_tested: number;
  improved: boolean;
}

export const MOCK_CALIBRATE_RESULT: CalibrateResult = {
  best_weights: {
    fundamental: 0.40,
    growth: 0.20,
    narrative: 0.20,
    listing: 0.10,
    risk: 0.10,
  },
  best_precision_at_k: 0.85,
  n_combinations_tested: 56,
  improved: true,
};

// ── Validation handler factories ──────────────────────────────────────────

export function backtestValidateHandler(data: ValidateResult = MOCK_VALIDATE_RESULT) {
  return http.post("/api/backtesting/validate", () => HttpResponse.json(data));
}

export function backtestValidateErrorHandler() {
  return http.post("/api/backtesting/validate", () =>
    HttpResponse.json({ detail: "Validation failed" }, { status: 500 }),
  );
}

export function backtestCalibrateHandler(data: CalibrateResult = MOCK_CALIBRATE_RESULT) {
  return http.post("/api/backtesting/calibrate", () => HttpResponse.json(data));
}

// ── Phase 14 — Cycle & weights mock data ──────────────────────────────────

export interface CycleInfo {
  name: string;
  bottom_date: string;
  top_date: string;
  n_tokens: number;
}

export const MOCK_CYCLES: CycleInfo[] = [
  { name: "cycle_1_2015_2018", bottom_date: "2015-01-14", top_date: "2017-12-17", n_tokens: 15 },
  { name: "cycle_2_2019_2021", bottom_date: "2018-12-15", top_date: "2021-11-10", n_tokens: 31 },
  { name: "cycle_3_2022_2025", bottom_date: "2022-11-21", top_date: "2025-01-20", n_tokens: 50 },
];

export interface ActiveWeights {
  fundamental: number;
  growth: number;
  narrative: number;
  listing: number;
  risk: number;
  source: string;
}

export const MOCK_ACTIVE_WEIGHTS: ActiveWeights = {
  fundamental: 0.30,
  growth: 0.25,
  narrative: 0.20,
  listing: 0.15,
  risk: 0.10,
  source: "default_phase9",
};

export function backtestCyclesHandler(data: CycleInfo[] = MOCK_CYCLES) {
  return http.get("/api/backtesting/cycles", () => HttpResponse.json(data));
}

export function backtestCyclesErrorHandler() {
  return http.get("/api/backtesting/cycles", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

export function backtestWeightsHandler(data: ActiveWeights = MOCK_ACTIVE_WEIGHTS) {
  return http.get("/api/backtesting/weights", () => HttpResponse.json(data));
}

export function backtestWeightsErrorHandler() {
  return http.get("/api/backtesting/weights", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

// ── Market cycle mock data ────────────────────────────────────────────────

export const MOCK_MARKET_CYCLE: MarketCycleResponse = {
  phase: "accumulation",
  confidence: 0.72,
  phase_description:
    "Accumulation phase — smart money is quietly building positions while prices consolidate.",
  indicators: {
    btc_dominance: 54.2,
    fear_greed_index: 35,
    fear_greed_label: "Fear",
  },
};

// ── Market cycle handler factories ────────────────────────────────────────

export function marketCycleHandler(
  data: MarketCycleResponse = MOCK_MARKET_CYCLE,
) {
  return http.get("/api/market/cycle", () => HttpResponse.json(data));
}

export function marketCycleErrorHandler() {
  return http.get("/api/market/cycle", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

// ── Pipeline handler factories ────────────────────────────────────────────

const MOCK_COLLECT_NOW: CollectNowResponse = {
  job_id: "test-job-123",
  status: "pending",
};

const MOCK_PIPELINE_STATUS: PipelineStatusResponse = {
  job_id: "test-job-123",
  status: "completed",
  detail: "42 tokens collected",
};

export function collectNowHandler(
  data: CollectNowResponse = MOCK_COLLECT_NOW,
) {
  return http.post("/api/pipeline/collect-now", () => HttpResponse.json(data, { status: 202 }));
}

export function collectNowErrorHandler() {
  return http.post("/api/pipeline/collect-now", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
  );
}

export function pipelineStatusHandler(
  data: PipelineStatusResponse = MOCK_PIPELINE_STATUS,
) {
  return http.get("/api/pipeline/status/:jobId", () => HttpResponse.json(data));
}

export function pipelineStatusNotFoundHandler() {
  return http.get("/api/pipeline/status/:jobId", () =>
    HttpResponse.json({ detail: "job not found" }, { status: 404 }),
  );
}

// ── Token explanation mock data ────────────────────────────────────────────

export const MOCK_EXPLANATION: ExplanationResponse = {
  symbol: "BTC",
  name: "Bitcoin",
  opportunity_score: 0.71,
  explanations: [
    {
      pillar: "fundamental",
      score: 0.76,
      explanation: "Fundamental score is strong (76%). Strongest sub-pillar: technology (100%).",
    },
    {
      pillar: "growth",
      score: 0.33,
      explanation: "Growth/momentum score is weak (33%). 24h volume: $62B.",
    },
    {
      pillar: "narrative",
      score: 0.38,
      explanation: "Narrative/social score is weak (38%). Reddit: 8M subscribers.",
    },
    {
      pillar: "listing",
      score: 1.0,
      explanation: "Listing probability is very strong (100%).",
    },
    {
      pillar: "risk",
      score: 0.91,
      explanation: "Risk-adjusted score is very strong (91%). Low risk profile.",
    },
    {
      pillar: "overall",
      score: 0.71,
      explanation: "BTC has a strong overall opportunity score (71%).",
    },
  ],
};

// ── Token explanation handler factories ───────────────────────────────────

export function tokenExplanationHandler(
  data: ExplanationResponse = MOCK_EXPLANATION,
) {
  return http.get("/api/tokens/:symbol/explanation", () =>
    HttpResponse.json(data),
  );
}

export function tokenExplanationErrorHandler() {
  return http.get("/api/tokens/:symbol/explanation", () =>
    HttpResponse.json({ detail: "Token not found" }, { status: 404 }),
  );
}

// ── Default handlers (happy-path baseline) ────────────────────────────────

export const handlers = [
  rankingsHandler(),
  tokensHandler(),
  tokenDetailHandler(),
  alertsHandler(),
  alertStatsHandler(),
  acknowledgeAlertHandler(),
  testAlertHandler(),
  narrativesHandler(),
  tokenReportHandler(),
  marketReportHandler(),
  graphCommunitiesHandler(),
  graphCentralityHandler(),
  graphEcosystemHandler(),
  backtestRunHandler(),
  backtestValidateHandler(),
  backtestCalibrateHandler(),
  backtestCyclesHandler(),
  backtestWeightsHandler(),
  marketCycleHandler(),
  tokenExplanationHandler(),
];
