/**
 * Unit tests for market.service.ts
 *
 * MSW intercepts the Axios calls so no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  marketCycleHandler,
  marketCycleErrorHandler,
} from "@/test/msw/handlers";
import { fetchMarketCycle } from "./market.service";

describe("market.service", () => {
  it("fetchMarketCycle returns MarketCycleResponse", async () => {
    server.use(marketCycleHandler());
    const result = await fetchMarketCycle();
    expect(result.phase).toBe("accumulation");
    expect(result.confidence).toBe(0.72);
    expect(result.indicators.btc_dominance).toBe(54.2);
    expect(result.indicators.fear_greed_index).toBe(35);
  });

  it("fetchMarketCycle propagates error on 500", async () => {
    server.use(marketCycleErrorHandler());
    await expect(fetchMarketCycle()).rejects.toThrow();
  });
});
