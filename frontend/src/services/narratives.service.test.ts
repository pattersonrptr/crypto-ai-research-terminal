/**
 * Unit tests for narratives.service.ts
 *
 * MSW intercepts the Axios calls so no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  narrativesHandler,
  narrativesErrorHandler,
  MOCK_NARRATIVES,
} from "@/test/msw/handlers";
import { fetchNarratives } from "./narratives.service";

describe("narratives.service", () => {
  it("fetchNarratives_returns_array_of_NarrativeCluster", async () => {
    server.use(narrativesHandler(MOCK_NARRATIVES));
    const result = await fetchNarratives();
    expect(Array.isArray(result)).toBe(true);
    expect(result).toHaveLength(2);
  });

  it("fetchNarratives_returns_correct_fields", async () => {
    server.use(narrativesHandler(MOCK_NARRATIVES));
    const [first] = await fetchNarratives();
    expect(first.id).toBe(1);
    expect(first.name).toBe("AI & Machine Learning");
    expect(first.momentum_score).toBe(9.2);
    expect(first.trend).toBe("accelerating");
    expect(first.tokens).toContain("FET");
    expect(first.token_count).toBe(3);
  });

  it("fetchNarratives_returns_empty_array_when_none", async () => {
    server.use(narrativesHandler([]));
    const result = await fetchNarratives();
    expect(result).toHaveLength(0);
  });

  it("fetchNarratives_throws_on_server_error", async () => {
    server.use(narrativesErrorHandler());
    await expect(fetchNarratives()).rejects.toThrow();
  });

  it("fetchNarratives_calls_correct_endpoint", async () => {
    server.use(narrativesHandler(MOCK_NARRATIVES));
    // If the endpoint is wrong, MSW would throw an unhandled request error
    const result = await fetchNarratives();
    expect(result).toBeDefined();
  });
});
