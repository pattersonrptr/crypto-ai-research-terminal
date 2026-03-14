/**
 * Narratives service — fetches market narrative clusters from the backend.
 */

import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types ──────────────────────────────────────────────────────────────────

export type NarrativeTrend = "accelerating" | "stable" | "declining";

export interface NarrativeCluster {
  id: number;
  name: string;
  momentum_score: number;
  trend: NarrativeTrend;
  tokens: string[];
  keywords: string[];
  token_count: number;
}

// ── Service functions ──────────────────────────────────────────────────────

/**
 * Fetch all active narrative clusters from the backend, sorted by
 * momentum_score descending.
 */
export async function fetchNarratives(): Promise<NarrativeCluster[]> {
  const res: AxiosResponse<NarrativeCluster[]> = await apiClient.get(
    "/narratives/",
  );
  return res.data;
}
