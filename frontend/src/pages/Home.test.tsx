/**
 * TDD tests for the Home page.
 *
 * Naming convention: test_<unit>_<scenario>_<expected_outcome>
 * MSW intercepts all `/api/rankings/opportunities` requests.
 */

import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import {
  rankingsErrorHandler,
  rankingsHandler,
  MOCK_OPPORTUNITIES,
} from "@/test/msw/handlers";
import { useTableStore } from "@/store/tableStore";
import { Home } from "./Home";

// ── Test helpers ─────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // No retries in tests -- fail fast so error states render immediately
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderHome() {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("Home", () => {
  beforeEach(() => {
    // Reset tableStore between tests so state doesn't leak
    useTableStore.setState(useTableStore.getInitialState());
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ── Loading state ───────────────────────────────────────────────────

  it("renders_loading_skeletons_while_fetching", async () => {
    renderHome();
    const skeletons = document.querySelectorAll("[aria-hidden='true']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  // ── Happy path ──────────────────────────────────────────────────────

  it("renders_page_header_with_total_token_count_when_data_loads", async () => {
    renderHome();
    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });
    // MOCK_OPPORTUNITIES has 15 items -> total_count = 15
    expect(
      screen.getByText(/15 tokens analysed/i),
    ).toBeInTheDocument();
  });

  it("renders_a_table_with_token_symbols", async () => {
    renderHome();
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
    // All 15 on page 1 (pageSize=50)
    expect(screen.getByText("TKN1")).toBeInTheDocument();
    expect(screen.getByText("TKN15")).toBeInTheDocument();
  });

  it("renders_search_input", async () => {
    renderHome();
    expect(
      screen.getByRole("searchbox", { name: /search tokens/i }),
    ).toBeInTheDocument();
  });

  // ── Pagination ──────────────────────────────────────────────────────

  it("does_not_render_pagination_when_results_fit_on_one_page", async () => {
    // 15 items with pageSize=50 means 1 page — no pagination nav
    renderHome();
    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("navigation", { name: /rankings pagination/i }),
    ).not.toBeInTheDocument();
  });

  it("renders_pagination_when_total_count_exceeds_page_size", async () => {
    // Override handler to return total_count > pageSize (50)
    server.use(
      http.get("/api/rankings/opportunities", () =>
        HttpResponse.json({
          data: MOCK_OPPORTUNITIES.slice(0, 15),
          total_count: 100,
        }),
      ),
    );

    renderHome();
    await waitFor(() => {
      expect(
        screen.getByRole("navigation", { name: /rankings pagination/i }),
      ).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /previous page/i })).toBeDisabled();
    expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument();
  });

  // ── Error state ─────────────────────────────────────────────────────

  it("renders_error_message_when_api_returns_500", async () => {
    server.use(rankingsErrorHandler());

    renderHome();
    await waitFor(() => {
      expect(
        screen.getByRole("alert"),
      ).toHaveTextContent(/failed to load rankings/i);
    });
  });

  it("renders_empty_message_when_api_returns_empty_data", async () => {
    server.use(rankingsHandler([]));

    renderHome();
    await waitFor(() => {
      // Wait until loading finishes and table appears
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
    expect(screen.getByText(/0 tokens analysed/i)).toBeInTheDocument();
    // Table is shown but with "No results" message
    expect(screen.getByText(/no results/i)).toBeInTheDocument();
  });

  // ── Polling ─────────────────────────────────────────────────────────

  it("polls_rankings_api_every_30_seconds_via_refetch_interval", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    let requestCount = 0;
    server.use(
      http.get("/api/rankings/opportunities", () => {
        requestCount++;
        return HttpResponse.json({
          data: MOCK_OPPORTUNITIES,
          total_count: MOCK_OPPORTUNITIES.length,
        });
      }),
    );

    renderHome();

    // Initial fetch
    await waitFor(() => expect(requestCount).toBe(1));

    // Advance 30 s -> refetchInterval triggers second fetch
    await act(async () => {
      vi.advanceTimersByTime(30_000);
    });
    await waitFor(() => expect(requestCount).toBe(2));
  });
});
