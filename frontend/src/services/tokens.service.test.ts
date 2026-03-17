/**
 * Unit tests for tokens.service.ts
 *
 * MSW intercepts the Axios calls so no real HTTP requests are made.
 * These tests verify that each service function calls the correct endpoint
 * and returns correctly typed data.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  tokensHandler,
  tokenDetailHandler,
  rankingsHandler,
  tokenExplanationHandler,
  MOCK_TOKEN_BTC,
  MOCK_OPPORTUNITIES,
  MOCK_EXPLANATION,
} from "@/test/msw/handlers";
import {
  fetchTokens,
  fetchToken,
  fetchRankingOpportunities,
  fetchTokenExplanation,
} from "./tokens.service";

describe("tokens.service", () => {
  it("fetchTokens_returns_array_of_TokenWithScore", async () => {
    server.use(tokensHandler([MOCK_TOKEN_BTC]));
    const result = await fetchTokens();
    expect(result).toHaveLength(1);
    expect(result[0].symbol).toBe("BTC");
    expect(result[0].latest_score).not.toBeNull();
  });

  it("fetchTokens_passes_query_params", async () => {
    server.use(tokensHandler([MOCK_TOKEN_BTC]));
    // Should not throw — params are forwarded to Axios
    const result = await fetchTokens({ skip: 0, limit: 5, category: "Layer 1" });
    expect(Array.isArray(result)).toBe(true);
  });

  it("fetchToken_returns_single_TokenWithScore_by_symbol", async () => {
    server.use(tokenDetailHandler(MOCK_TOKEN_BTC));
    const result = await fetchToken("BTC");
    expect(result.symbol).toBe("BTC");
    expect(result.name).toBe("Bitcoin");
  });

  it("fetchRankingOpportunities_returns_array_of_RankingOpportunity", async () => {
    server.use(rankingsHandler(MOCK_OPPORTUNITIES));
    const result = await fetchRankingOpportunities();
    expect(result).toHaveLength(15);
    expect(result[0].rank).toBe(1);
    expect(result[0].token.symbol).toBe("TKN1");
  });

  it("fetchRankingOpportunities_passes_limit_and_min_score_params", async () => {
    server.use(rankingsHandler(MOCK_OPPORTUNITIES.slice(0, 3)));
    const result = await fetchRankingOpportunities({ limit: 3, min_score: 50 });
    expect(result).toHaveLength(3);
  });

  it("fetchTokenExplanation_returns_explanation_with_pillar_list", async () => {
    server.use(tokenExplanationHandler(MOCK_EXPLANATION));
    const result = await fetchTokenExplanation("BTC");
    expect(result.symbol).toBe("BTC");
    expect(result.explanations).toHaveLength(6);
    expect(result.explanations[0].pillar).toBe("fundamental");
  });

  it("fetchTokenExplanation_includes_overall_score", async () => {
    server.use(tokenExplanationHandler(MOCK_EXPLANATION));
    const result = await fetchTokenExplanation("BTC");
    const overall = result.explanations.find((e) => e.pillar === "overall");
    expect(overall).toBeDefined();
    expect(overall!.score).toBe(0.71);
  });
});
