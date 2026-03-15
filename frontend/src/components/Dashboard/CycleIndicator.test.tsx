/**
 * TDD tests for the CycleIndicator component.
 *
 * MSW intercepts `/api/market/cycle` requests.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  marketCycleHandler,
  marketCycleErrorHandler,
  MOCK_MARKET_CYCLE,
} from "@/test/msw/handlers";
import { CycleIndicator } from "./CycleIndicator";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
}

function renderCycleIndicator() {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <CycleIndicator />
    </QueryClientProvider>,
  );
}

describe("CycleIndicator", () => {
  it("renders loading skeleton while fetching", () => {
    renderCycleIndicator();
    expect(screen.getByLabelText("Loading cycle indicator")).toBeInTheDocument();
  });

  it("renders cycle phase after loading", async () => {
    server.use(marketCycleHandler());
    renderCycleIndicator();

    await waitFor(() => {
      expect(screen.getByLabelText("Market cycle indicator")).toBeInTheDocument();
    });

    expect(screen.getByText("accumulation")).toBeInTheDocument();
    expect(screen.getByText("(72%)")).toBeInTheDocument();
  });

  it("renders bull phase correctly", async () => {
    server.use(
      marketCycleHandler({
        ...MOCK_MARKET_CYCLE,
        phase: "bull",
        confidence: 0.88,
      }),
    );
    renderCycleIndicator();

    await waitFor(() => {
      expect(screen.getByText("bull")).toBeInTheDocument();
    });
    expect(screen.getByText("(88%)")).toBeInTheDocument();
  });

  it("renders nothing on error", async () => {
    server.use(marketCycleErrorHandler());
    renderCycleIndicator();

    await waitFor(() => {
      expect(
        screen.queryByLabelText("Loading cycle indicator"),
      ).not.toBeInTheDocument();
    });

    // After error, the component renders null (nothing)
    expect(
      screen.queryByLabelText("Market cycle indicator"),
    ).not.toBeInTheDocument();
  });

  it("shows phase_description as title tooltip", async () => {
    server.use(marketCycleHandler());
    renderCycleIndicator();

    await waitFor(() => {
      const indicator = screen.getByLabelText("Market cycle indicator");
      expect(indicator).toHaveAttribute(
        "title",
        MOCK_MARKET_CYCLE.phase_description,
      );
    });
  });
});
