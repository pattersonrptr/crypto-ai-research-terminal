/**
 * Backtesting service — runs backtesting simulations via the backend.
 *
 * Endpoints:
 * - POST /backtesting/run       — Run a simulation for a symbol over a market cycle
 * - POST /backtesting/validate  — Run validation metrics on historical data
 * - POST /backtesting/calibrate — Run weight calibration sweep
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

export interface TokenBreakdownItem {
  symbol: string;
  model_rank: number;
  model_score: number;
  actual_multiplier: number;
  is_winner: boolean;
}

export interface ValidateRequest {
  k?: number;
  winner_threshold?: number;
  market_multiplier?: number;
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

export interface CalibrateRequest {
  step?: number;
  k?: number;
}

export interface WeightSet {
  fundamental: number;
  growth: number;
  narrative: number;
  listing: number;
  risk: number;
}

export interface CalibrateResult {
  best_weights: WeightSet;
  best_precision_at_k: number;
  n_combinations_tested: number;
  improved: boolean;
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

/**
 * Run validation metrics on the model's historical predictions.
 */
export async function runValidation(request: ValidateRequest = {}): Promise<ValidateResult> {
  const res: AxiosResponse<ValidateResult> = await apiClient.post(
    "/backtesting/validate",
    request,
  );
  return res.data;
}

/**
 * Run weight calibration sweep to find optimal pillar weights.
 */
export async function runCalibration(request: CalibrateRequest = {}): Promise<CalibrateResult> {
  const res: AxiosResponse<CalibrateResult> = await apiClient.post(
    "/backtesting/calibrate",
    request,
  );
  return res.data;
}
