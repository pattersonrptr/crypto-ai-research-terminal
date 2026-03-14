/**
 * TDD tests for the Home page.
 *
 * Naming convention: test_<unit>_<scenario>_<expected_outcome>
 * MSW intercepts all `/api/rankings/opportunities` requests.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, within, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import {
  rankingsErrorHandler,
  rankingsHandler,
  MOCK_OPPORTUNITIES,
} from "@/test/msw/handlers";
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

// ── Loading state ─────────────────────────────────────────────────────────

describe("Home", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders_loading_skeletons_while_fetching", async () => {
    renderHome();
    // Skeletons are aria-hidden pulse divs rendered during loading
    const skeletons = document.querySelectorAll("[aria-hidden='true']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  // ── Happy path ──────────────────────────────────────────────────────────

  it("renders_page_header_with_total_token_count_when_data_loads", async () => {
    renderHome();
    // Wait for loading to finish and cards to appear
    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });
    // Header shows "15 tokens analysed" (MOCK_OPPORTUNITIES has 15 items)
    expect(
      screen.getByText(/15 tokens analysed/i),
    ).toBeInTheDocument();
  });

  it("renders_exactly_10_token_cards_on_page_1", async () => {
    renderHome();
    await waitFor(() => {
      // The grid has aria-label="Token rankings"; each card is an <a> with aria-label="View TKNx details"
      const grid = screen.getByLabelText("Token rankings");
      const cards = within(grid).getAllByRole("link");
      expect(cards).toHaveLength(10);
    });
  });

  it("renders_token_symbols_for_first_page_items", async () => {
    renderHome();
    await waitFor(() => {
      // First 10 of 15 mock tokens are TKN1 ... TKN10
      expect(screen.getByText("TKN1")).toBeInTheDocument();
      expect(screen.getByText("TKN10")).toBeInTheDocument();
    });
    // TKN11 ... TKN15 should NOT be visible on page 1
    expect(screen.queryByText("TKN11")).not.toBeInTheDocument();
  });

  // ── Pagination ──────────────────────────────────────────────────────────

  it("renders_pagination_controls_when_total_exceeds_page_size", async () => {
    renderHome();
    await waitFor(() => {
      expect(
        screen.getByRole("navigation", { name: /rankings pagination/i }),
      ).toBeInTheDocument();
    });
    // Should have "Prev" and "Next" buttons
    expect(screen.getByRole("button", { name: /previous page/i })).toBeInTheDocument();
  });

  it("navigates_to_page_2_and_shows_remaining_tokens_when_next_clicked", async () => {
    const user = userEvent.setup();
    renderHome();

    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });

    const page2Btn = screen.getByRole("button", { name: /go to page 2/i });
    await user.click(page2Btn);

    await waitFor(() => {
      expect(screen.getByText("TKN11")).toBeInTheDocument();
      expect(screen.getByText("TKN15")).toBeInTheDocument();
    });
    // Page 1 tokens no longer visible
    expect(screen.queryByText("TKN1")).not.toBeInTheDocument();
  });

  it("prev_button_is_disabled_on_first_page", async () => {
    renderHome();
    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });
    const prevBtn = screen.getByRole("button", { name: /previous page/i });
    expect(prevBtn).toBeDisabled();
  });

  it("does_not_render_pagination_when_results_fit_on_one_page", async () => {
    // Override: return only 5 opportunities -- fits on one page
    server.use(
      rankingsHandler(MOCK_OPPORTUNITIES.slice(0, 5)),
    );

    renderHome();

    await waitFor(() => {
      expect(screen.getByText("TKN1")).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("navigation", { name: /rankings pagination/i }),
    ).not.toBeInTheDocument();
  });

  // ── Error state ─────────────────────────────────────────────────────────

  it("renders_error_message_when_api_returns_500", async () => {
    server.use(rankingsErrorHandler());

    renderHome();

    await waitFor(() => {
      expect(
        screen.getByRole("alert"),
      ).toHaveTextContent(/failed to load rankings/i);
    });
  });

  it("renders_empty_grid_and_no_pagination_when_api_returns_empty_array", async () => {
    server.use(rankingsHandler([]));

    renderHome();

    await waitFor(() => {
      // Header shows "0 tokens analysed"
      expect(screen.getByText(/0 tokens analysed/i)).toBeInTheDocument();
    });
    // No pagination nav when list is empty
    expect(
      screen.queryByRole("navigation", { name: /rankings pagination/i }),
    ).not.toBeInTheDocument();
  });

  // ── Polling ─────────────────────────────────────────────────────────────

  it("polls_rankings_api_every_30_seconds_via_refetch_interval", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    let requestCount = 0;
    server.use(
      http.get("/api/rankings/opportunities", () => {
        requestCount++;
        return HttpResponse.json(MOCK_OPPORTUNITIES);
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
