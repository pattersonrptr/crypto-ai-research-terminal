/**
 * Unit tests for pipeline.service.ts
 *
 * MSW intercepts the Axios calls so no real HTTP requests are made.
 */

import { describe, it, expect } from "vitest";
import { server } from "@/test/msw/server";
import {
  collectNowHandler,
  collectNowErrorHandler,
  pipelineStatusHandler,
  pipelineStatusNotFoundHandler,
} from "@/test/msw/handlers";
import { triggerCollectNow, fetchPipelineStatus } from "./pipeline.service";

describe("pipeline.service", () => {
  describe("triggerCollectNow", () => {
    it("returns job_id and status on success", async () => {
      server.use(collectNowHandler());
      const result = await triggerCollectNow();
      expect(result.job_id).toBeDefined();
      expect(result.status).toBe("pending");
    });

    it("propagates error on 500", async () => {
      server.use(collectNowErrorHandler());
      await expect(triggerCollectNow()).rejects.toThrow();
    });
  });

  describe("fetchPipelineStatus", () => {
    it("returns job status on success", async () => {
      server.use(pipelineStatusHandler());
      const result = await fetchPipelineStatus("test-job-123");
      expect(result.job_id).toBe("test-job-123");
      expect(result.status).toBe("completed");
      expect(result.detail).toBe("42 tokens collected");
    });

    it("propagates error on 404", async () => {
      server.use(pipelineStatusNotFoundHandler());
      await expect(fetchPipelineStatus("unknown")).rejects.toThrow();
    });
  });
});
