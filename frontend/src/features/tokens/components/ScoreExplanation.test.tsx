/**
 * TDD tests for the ScoreExplanation component.
 *
 * Naming: renders_<element>_when_<condition>
 *
 * This component fetches GET /tokens/:symbol/explanation and displays
 * a human-readable "Why this score?" section with per-pillar explanations.
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  tokenExplanationHandler,
  tokenExplanationErrorHandler,
  MOCK_EXPLANATION,
} from "@/test/msw/handlers";
import { ScoreExplanation } from "./ScoreExplanation";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
}

function renderComponent(symbol = "BTC") {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <ScoreExplanation symbol={symbol} />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("ScoreExplanation", () => {
  it("renders_loading_skeleton_while_fetching", () => {
    renderComponent();
    const skeleton = screen.getByLabelText(/loading score explanation/i);
    expect(skeleton).toBeInTheDocument();
  });

  it("renders_section_heading_why_this_score", async () => {
    renderComponent("BTC");
    await waitFor(() => {
      expect(screen.getByText(/why this score/i)).toBeInTheDocument();
    });
  });

  it("renders_all_pillar_explanations", async () => {
    renderComponent("BTC");
    await waitFor(() => {
      // Each pillar has a score badge — check for percentage badges
      expect(screen.getByText("76%")).toBeInTheDocument(); // fundamental
      expect(screen.getByText("33%")).toBeInTheDocument(); // growth
      expect(screen.getByText("38%")).toBeInTheDocument(); // narrative
      expect(screen.getByText("100%")).toBeInTheDocument(); // listing
      expect(screen.getByText("91%")).toBeInTheDocument(); // risk
    });
  });

  it("renders_explanation_text_for_each_pillar", async () => {
    renderComponent("BTC");
    await waitFor(() => {
      expect(
        screen.getByText(/strongest sub-pillar: technology/i),
      ).toBeInTheDocument();
    });
  });

  it("renders_overall_explanation_separately", async () => {
    renderComponent("BTC");
    await waitFor(() => {
      expect(
        screen.getByText(/strong overall opportunity score/i),
      ).toBeInTheDocument();
    });
  });

  it("renders_pillar_labels_capitalized", async () => {
    renderComponent("BTC");
    await waitFor(() => {
      // Pillar names rendered as capitalized labels
      const section = screen.getByRole("region", { name: /score explanation/i });
      expect(section).toBeInTheDocument();
      // 5 pillar labels (not "overall" — that's rendered separately)
      expect(screen.getByText("fundamental")).toBeInTheDocument();
      expect(screen.getByText("listing")).toBeInTheDocument();
    });
  });

  it("renders_nothing_when_api_returns_error", async () => {
    server.use(tokenExplanationErrorHandler());
    const { container } = renderComponent("UNKNOWN");
    await waitFor(() => {
      // After loading finishes, the component should be empty (graceful fallback)
      const skeleton = container.querySelector(".animate-pulse");
      expect(skeleton).not.toBeInTheDocument();
    });
    // No error alert — just hides gracefully
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
