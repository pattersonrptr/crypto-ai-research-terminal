/**
 * Graph service — fetches Graph Intelligence data from the backend.
 *
 * Endpoints:
 * - GET /graph/communities  — detected token communities (Louvain)
 * - GET /graph/centrality   — PageRank / betweenness / degree centrality
 * - GET /graph/ecosystem    — full ecosystem snapshot
 */

import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Community {
  id: number;
  members: string[];
  size: number;
}

export interface CentralityResult {
  symbol: string;
  pagerank: number;
  betweenness: number;
  degree_centrality: number;
}

export interface EcosystemSnapshot {
  timestamp: string;
  n_communities: number;
  total_tokens: number;
  top_tokens: string[];
}

// ── Service functions ──────────────────────────────────────────────────────

/**
 * Fetch all detected token communities.
 */
export async function fetchCommunities(): Promise<Community[]> {
  const res: AxiosResponse<Community[]> = await apiClient.get(
    "/graph/communities",
  );
  return res.data;
}

/**
 * Fetch centrality scores, ranked by PageRank descending.
 *
 * @param topN - Limit results to the top-N tokens (default: 10).
 */
export async function fetchCentrality(topN?: number): Promise<CentralityResult[]> {
  const params = topN !== undefined ? { top_n: topN } : {};
  const res: AxiosResponse<CentralityResult[]> = await apiClient.get(
    "/graph/centrality",
    { params },
  );
  return res.data;
}

/**
 * Fetch the full ecosystem snapshot (communities + top tokens).
 */
export async function fetchEcosystem(): Promise<EcosystemSnapshot> {
  const res: AxiosResponse<EcosystemSnapshot> = await apiClient.get(
    "/graph/ecosystem",
  );
  return res.data;
}
