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
} from "@/services/tokens.service";
import type { Alert, AlertStats } from "@/services/alerts.service";
import type { NarrativeCluster } from "@/services/narratives.service";

// ── Shared mock data factories ─────────────────────────────────────────────

export function makeMockScore(overrides: Partial<TokenScore> = {}): TokenScore {
  return {
    fundamental_score: 72,
    technology_score: 80,
    tokenomics_score: 65,
    adoption_score: 70,
    dev_activity_score: 75,
    narrative_score: 68,
    growth_score: 60,
    risk_score: 30,
    listing_probability: 0.55,
    cycle_leader_prob: 0.4,
    opportunity_score: 71,
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
];
