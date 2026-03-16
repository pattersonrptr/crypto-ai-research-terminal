/**
 * Unit tests for backtesting.service.ts
 * MSW intercepts Axios calls — no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  backtestRunHandler,
  backtestRunErrorHandler,
  backtestValidateHandler,
  backtestValidateErrorHandler,
  backtestCalibrateHandler,
  backtestCyclesHandler,
  backtestCyclesErrorHandler,
  backtestWeightsHandler,
  backtestWeightsErrorHandler,
  MOCK_BACKTEST_RESULT,
  MOCK_VALIDATE_RESULT,
  MOCK_CALIBRATE_RESULT,
  MOCK_CYCLES,
  MOCK_ACTIVE_WEIGHTS,
} from "@/test/msw/handlers";
import { runBacktest, runValidation, runCalibration, fetchCycles, fetchActiveWeights } from "./backtesting.service";

describe("backtesting.service", () => {
  it("runBacktest_returns_BacktestResult", async () => {
    server.use(backtestRunHandler(MOCK_BACKTEST_RESULT));
    const result = await runBacktest({ symbol: "BTC", cycle: "bull" });
    expect(result.symbol).toBe("BTC");
    expect(result.cycle).toBe("bull");
  });

  it("runBacktest_returns_correct_fields", async () => {
    server.use(backtestRunHandler(MOCK_BACKTEST_RESULT));
    const result = await runBacktest({ symbol: "BTC", cycle: "bull" });
    expect(typeof result.total_return_pct).toBe("number");
    expect(typeof result.n_trades).toBe("number");
    expect(typeof result.win_rate).toBe("number");
    expect(typeof result.sharpe_ratio).toBe("number");
    expect(typeof result.max_drawdown_pct).toBe("number");
    expect(typeof result.avg_trade_return_pct).toBe("number");
    expect(typeof result.is_profitable).toBe("boolean");
  });

  it("runBacktest_sends_symbol_and_cycle_in_body", async () => {
    server.use(backtestRunHandler({ ...MOCK_BACKTEST_RESULT, symbol: "ETH", cycle: "bear" }));
    const result = await runBacktest({ symbol: "ETH", cycle: "bear" });
    expect(result.symbol).toBe("ETH");
    expect(result.cycle).toBe("bear");
  });

  it("runBacktest_throws_on_server_error", async () => {
    server.use(backtestRunErrorHandler());
    await expect(runBacktest({ symbol: "BTC", cycle: "bull" })).rejects.toThrow();
  });

  it("runBacktest_works_with_accumulation_cycle", async () => {
    const accResult = { ...MOCK_BACKTEST_RESULT, cycle: "accumulation" };
    server.use(backtestRunHandler(accResult));
    const result = await runBacktest({ symbol: "SOL", cycle: "accumulation" });
    expect(result.cycle).toBe("accumulation");
  });
});

describe("backtesting.service validation", () => {
  it("runValidation_returns_ValidateResult", async () => {
    server.use(backtestValidateHandler(MOCK_VALIDATE_RESULT));
    const result = await runValidation({ k: 10 });
    expect(result.precision_at_k).toBe(0.8);
    expect(result.recall_at_k).toBe(0.6);
    expect(result.hit_rate).toBe(0.7);
  });

  it("runValidation_returns_token_breakdown", async () => {
    server.use(backtestValidateHandler(MOCK_VALIDATE_RESULT));
    const result = await runValidation({ k: 5 });
    expect(Array.isArray(result.token_breakdown)).toBe(true);
    expect(result.token_breakdown.length).toBeGreaterThan(0);
  });

  it("runValidation_includes_model_is_useful", async () => {
    server.use(backtestValidateHandler(MOCK_VALIDATE_RESULT));
    const result = await runValidation();
    expect(typeof result.model_is_useful).toBe("boolean");
  });

  it("runValidation_throws_on_server_error", async () => {
    server.use(backtestValidateErrorHandler());
    await expect(runValidation()).rejects.toThrow();
  });
});

describe("backtesting.service calibration", () => {
  it("runCalibration_returns_CalibrateResult", async () => {
    server.use(backtestCalibrateHandler(MOCK_CALIBRATE_RESULT));
    const result = await runCalibration({ step: 0.25 });
    expect(result.best_precision_at_k).toBe(0.85);
    expect(result.n_combinations_tested).toBe(56);
  });

  it("runCalibration_returns_best_weights", async () => {
    server.use(backtestCalibrateHandler(MOCK_CALIBRATE_RESULT));
    const result = await runCalibration();
    expect(result.best_weights.fundamental).toBe(0.4);
    expect(result.best_weights.growth).toBe(0.2);
  });

  it("runCalibration_includes_improved_flag", async () => {
    server.use(backtestCalibrateHandler(MOCK_CALIBRATE_RESULT));
    const result = await runCalibration();
    expect(typeof result.improved).toBe("boolean");
  });
});

describe("backtesting.service cycles", () => {
  it("fetchCycles_returns_list_of_cycles", async () => {
    server.use(backtestCyclesHandler(MOCK_CYCLES));
    const result = await fetchCycles();
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBe(3);
  });

  it("fetchCycles_returns_cycle_fields", async () => {
    server.use(backtestCyclesHandler(MOCK_CYCLES));
    const result = await fetchCycles();
    expect(result[0].name).toBe("cycle_1_2015_2018");
    expect(result[0].n_tokens).toBe(15);
  });

  it("fetchCycles_throws_on_server_error", async () => {
    server.use(backtestCyclesErrorHandler());
    await expect(fetchCycles()).rejects.toThrow();
  });
});

describe("backtesting.service weights", () => {
  it("fetchActiveWeights_returns_weight_data", async () => {
    server.use(backtestWeightsHandler(MOCK_ACTIVE_WEIGHTS));
    const result = await fetchActiveWeights();
    expect(result.fundamental).toBe(0.30);
    expect(result.source).toBe("default_phase9");
  });

  it("fetchActiveWeights_returns_all_pillar_weights", async () => {
    server.use(backtestWeightsHandler(MOCK_ACTIVE_WEIGHTS));
    const result = await fetchActiveWeights();
    const total = result.fundamental + result.growth + result.narrative + result.listing + result.risk;
    expect(total).toBeCloseTo(1.0);
  });

  it("fetchActiveWeights_throws_on_server_error", async () => {
    server.use(backtestWeightsErrorHandler());
    await expect(fetchActiveWeights()).rejects.toThrow();
  });
});
