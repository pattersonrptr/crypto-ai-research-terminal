import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types (mirror backend CycleResponse schema) ────────────────────────────

export interface CycleIndicators {
  btc_dominance: number;
  fear_greed_index: number;
  fear_greed_label: string;
}

export interface MarketCycleResponse {
  phase: string;
  confidence: number;
  phase_description: string;
  indicators: CycleIndicators;
}

// ── Service functions ──────────────────────────────────────────────────────

export async function fetchMarketCycle(): Promise<MarketCycleResponse> {
  const res: AxiosResponse<MarketCycleResponse> = await apiClient.get(
    "/market/cycle",
  );
  return res.data;
}
