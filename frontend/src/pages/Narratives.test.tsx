/**
 * TDD tests for the Narratives page.
 *
 * Naming: test_<unit>_<scenario>_<expected_outcome>
 * MSW intercepts GET /api/narratives.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  narrativesHandler,
  narrativesErrorHandler,
  MOCK_NARRATIVES,
} from "@/test/msw/handlers";
import { Narratives } from "./Narratives";

// ── helpers ────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderNarratives() {
  const qc = makeQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Narratives />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── tests ──────────────────────────────────────────────────────────────────

describe("Narratives", () => {
  it("renders_page_header_with_narratives_title", async () => {
    renderNarratives();
    await waitFor(() => {
      expect(screen.getByText("Narratives")).toBeInTheDocument();
    });
  });

  it("renders_list_of_narrative_names", async () => {
    renderNarratives();
    await waitFor(() => {
      expect(
        screen.getByText(MOCK_NARRATIVES[0].name),
      ).toBeInTheDocument();
      expect(
        screen.getByText(MOCK_NARRATIVES[1].name),
      ).toBeInTheDocument();
    });
  });

  it("renders_momentum_score_for_each_narrative", async () => {
    renderNarratives();
    await waitFor(() => {
      // MOCK_NARRATIVES[0].momentum_score = 9.2
      expect(screen.getByText(/9\.2/)).toBeInTheDocument();
    });
  });

  it("renders_trend_label_for_each_narrative", async () => {
    renderNarratives();
    await waitFor(() => {
      // first narrative trend = "accelerating"
      expect(screen.getByText(/accelerating/i)).toBeInTheDocument();
    });
  });

  it("renders_token_symbols_for_each_narrative", async () => {
    renderNarratives();
    await waitFor(() => {
      // MOCK_NARRATIVES[0].tokens = ["FET", "RNDR", "TAO"]
      expect(screen.getByText(/FET/)).toBeInTheDocument();
    });
  });

  it("renders_keywords_for_each_narrative", async () => {
    renderNarratives();
    await waitFor(() => {
      // MOCK_NARRATIVES[0].keywords[0] = "AI agents"
      expect(screen.getByText(/AI agents/i)).toBeInTheDocument();
    });
  });

  it("renders_token_count_for_each_narrative", async () => {
    renderNarratives();
    await waitFor(() => {
      // MOCK_NARRATIVES[0].token_count = 3 — rendered as "3 tokens" or similar
      expect(screen.getAllByText(/3 token/i).length).toBeGreaterThan(0);
    });
  });

  it("renders_error_message_when_api_returns_500", async () => {
    server.use(narrativesErrorHandler());
    renderNarratives();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load/i);
    });
  });

  it("renders_empty_state_when_api_returns_empty_array", async () => {
    server.use(narrativesHandler([]));
    renderNarratives();
    await waitFor(() => {
      expect(screen.getByText(/no narratives/i)).toBeInTheDocument();
    });
  });

  it("renders_narrative_count_summary_in_header_area", async () => {
    renderNarratives();
    await waitFor(() => {
      // Some text that shows how many narratives are detected (e.g. "2 narratives")
      expect(screen.getByText(/narratives detected/i)).toBeInTheDocument();
    });
  });
});
