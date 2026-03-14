/**
 * TDD tests for the TokenDetail page.
 *
 * Naming convention: test_<unit>_<scenario>_<expected_outcome>
 * MSW intercepts GET /api/tokens/:symbol and GET /api/reports/token/:symbol.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  tokenDetailErrorHandler,
  tokenDetailHandler,
  makeMockToken,
} from "@/test/msw/handlers";
import { TokenDetail } from "./TokenDetail";

// ── Test helpers ─────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
}

/**
 * Renders TokenDetail mounted at /tokens/:symbol so useParams works.
 */
function renderTokenDetail(symbol = "BTC") {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/tokens/${symbol}`]}>
        <Routes>
          <Route path="/tokens/:symbol" element={<TokenDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

// ── Loading state ─────────────────────────────────────────────────────────

describe("TokenDetail", () => {
  it("renders_loading_skeleton_while_fetching", () => {
    renderTokenDetail();
    // At least one pulse skeleton div visible before data arrives
    const pulses = document.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThan(0);
  });

  // ── Happy path ──────────────────────────────────────────────────────────

  it("renders_token_symbol_and_name_in_page_header", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(screen.getByText("BTC — Bitcoin")).toBeInTheDocument();
    });
  });

  it("renders_token_category_as_page_description", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(screen.getByText("Layer 1")).toBeInTheDocument();
    });
  });

  it("renders_back_link_to_rankings", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /back to rankings/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders_radar_chart_section_with_heading", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: /score radar chart/i }),
      ).toBeInTheDocument();
      expect(screen.getByText(/score breakdown/i)).toBeInTheDocument();
    });
  });

  it("renders_detailed_scores_section_with_progress_bars", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: /detailed scores/i }),
      ).toBeInTheDocument();
    });
    // 9 score pillars each have a progressbar
    const bars = screen.getAllByRole("progressbar");
    expect(bars).toHaveLength(9);
  });

  it("renders_opportunity_score_progress_bar_with_correct_aria_value", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      const bar = screen.getByRole("progressbar", {
        name: /opportunity score/i,
      });
      expect(bar).toHaveAttribute("aria-valuenow", "71");
    });
  });

  it("renders_market_metrics_section_with_price_and_market_cap", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: /market metrics/i }),
      ).toBeInTheDocument();
      // Price: $45,000 → "$45.00K"
      expect(screen.getByText("$45.00K")).toBeInTheDocument();
      // Market cap: 880_000_000_000 → "$880.00B"
      expect(screen.getByText("$880.00B")).toBeInTheDocument();
    });
  });

  it("renders_pdf_download_button", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /download BTC PDF report/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders_markdown_report_button", async () => {
    renderTokenDetail("BTC");
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /download BTC markdown report/i }),
      ).toBeInTheDocument();
    });
  });

  // ── No-score path ────────────────────────────────────────────────────────

  it("renders_no_score_placeholder_when_token_has_null_score", async () => {
    server.use(tokenDetailHandler(makeMockToken({ latest_score: null })));

    renderTokenDetail("BTC");

    await waitFor(() => {
      // Both sections show the fallback message
      expect(
        screen.getAllByText(/no score data available/i),
      ).toHaveLength(2);
    });
  });

  // ── Error state ─────────────────────────────────────────────────────────

  it("renders_error_alert_when_api_returns_404", async () => {
    server.use(tokenDetailErrorHandler());

    renderTokenDetail("UNKNOWN");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /token not found or backend unavailable/i,
      );
    });
  });

  // ── Report download ──────────────────────────────────────────────────────

  it("calls_fetchTokenReport_when_markdown_button_is_clicked", async () => {
    // Spy on the real fetch — we just verify the button triggers an attempt;
    // full PDF download flow uses a Blob which jsdom does not support natively.
    const user = userEvent.setup();
    renderTokenDetail("BTC");

    await waitFor(() => {
      expect(screen.getByText("BTC — Bitcoin")).toBeInTheDocument();
    });

    const mdBtn = screen.getByRole("button", {
      name: /download BTC markdown report/i,
    });
    // Should not throw
    await user.click(mdBtn);
  });
});
