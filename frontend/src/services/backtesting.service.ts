/**
 * Backtesting service — runs backtesting simulations via the backend.
 *
 * Endpoints:
 * - POST /backtesting/run  — Run a simulation for a symbol over a market cycle
 */

import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types ──────────────────────────────────────────────────────────────────

export type CycleLabel = "bull" | "bear" | "accumulation";

export interface BacktestRequest {
  symbol: string;
  cycle: CycleLabel;
}

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

// ── Service functions ──────────────────────────────────────────────────────

/**
 * Run a backtesting simulation for the given symbol and market cycle.
 */
export async function runBacktest(request: BacktestRequest): Promise<BacktestResult> {
  const res: AxiosResponse<BacktestResult> = await apiClient.post(
    "/backtesting/run",
    request,
  );
  return res.data;
}
