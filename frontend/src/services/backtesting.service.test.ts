/**
 * Unit tests for backtesting.service.ts
 * MSW intercepts Axios calls — no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  backtestRunHandler,
  backtestRunErrorHandler,
  MOCK_BACKTEST_RESULT,
} from "@/test/msw/handlers";
import { runBacktest } from "./backtesting.service";

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
