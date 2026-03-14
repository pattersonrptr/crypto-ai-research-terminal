/**
 * Unit tests for graph.service.ts
 * MSW intercepts Axios calls — no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  graphCommunitiesHandler,
  graphCommunitiesErrorHandler,
  graphCentralityHandler,
  graphEcosystemHandler,
  MOCK_COMMUNITIES,
  MOCK_CENTRALITY,
  MOCK_ECOSYSTEM,
} from "@/test/msw/handlers";
import {
  fetchCommunities,
  fetchCentrality,
  fetchEcosystem,
} from "./graph.service";

describe("graph.service", () => {
  // ── fetchCommunities ──────────────────────────────────────────────────

  it("fetchCommunities_returns_array_of_Community", async () => {
    server.use(graphCommunitiesHandler(MOCK_COMMUNITIES));
    const result = await fetchCommunities();
    expect(Array.isArray(result)).toBe(true);
    expect(result).toHaveLength(MOCK_COMMUNITIES.length);
  });

  it("fetchCommunities_returns_correct_fields", async () => {
    server.use(graphCommunitiesHandler(MOCK_COMMUNITIES));
    const [first] = await fetchCommunities();
    expect(first.id).toBe(0);
    expect(Array.isArray(first.members)).toBe(true);
    expect(typeof first.size).toBe("number");
  });

  it("fetchCommunities_throws_on_server_error", async () => {
    server.use(graphCommunitiesErrorHandler());
    await expect(fetchCommunities()).rejects.toThrow();
  });

  it("fetchCommunities_returns_empty_array_when_none", async () => {
    server.use(graphCommunitiesHandler([]));
    const result = await fetchCommunities();
    expect(result).toHaveLength(0);
  });

  // ── fetchCentrality ───────────────────────────────────────────────────

  it("fetchCentrality_returns_array_of_CentralityResult", async () => {
    server.use(graphCentralityHandler(MOCK_CENTRALITY));
    const result = await fetchCentrality();
    expect(Array.isArray(result)).toBe(true);
    expect(result).toHaveLength(MOCK_CENTRALITY.length);
  });

  it("fetchCentrality_returns_correct_fields", async () => {
    server.use(graphCentralityHandler(MOCK_CENTRALITY));
    const [first] = await fetchCentrality();
    expect(first.symbol).toBe("ETH");
    expect(typeof first.pagerank).toBe("number");
    expect(typeof first.betweenness).toBe("number");
    expect(typeof first.degree_centrality).toBe("number");
  });

  it("fetchCentrality_accepts_top_n_param", async () => {
    server.use(graphCentralityHandler(MOCK_CENTRALITY.slice(0, 1)));
    const result = await fetchCentrality(1);
    expect(result).toHaveLength(1);
  });

  // ── fetchEcosystem ────────────────────────────────────────────────────

  it("fetchEcosystem_returns_EcosystemSnapshot", async () => {
    server.use(graphEcosystemHandler(MOCK_ECOSYSTEM));
    const result = await fetchEcosystem();
    expect(typeof result.timestamp).toBe("string");
    expect(typeof result.n_communities).toBe("number");
    expect(typeof result.total_tokens).toBe("number");
    expect(Array.isArray(result.top_tokens)).toBe(true);
  });

  it("fetchEcosystem_returns_correct_top_tokens", async () => {
    server.use(graphEcosystemHandler(MOCK_ECOSYSTEM));
    const result = await fetchEcosystem();
    expect(result.top_tokens).toContain("ETH");
  });
});
