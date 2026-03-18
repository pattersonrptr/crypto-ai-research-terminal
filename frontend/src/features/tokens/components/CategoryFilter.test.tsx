/**
 * TDD tests for CategoryFilter component.
 *
 * CategoryFilter shows available categories as toggle chips and lets users
 * exclude categories from rankings. It fetches categories from the API
 * and renders them as buttons.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import { useTableStore } from "@/store/tableStore";
import { CategoryFilter } from "./CategoryFilter";

// ── Helpers ──────────────────────────────────────────────────────────────

const MOCK_CATEGORIES = [
  { category: "l1", count: 10 },
  { category: "defi", count: 8 },
  { category: "memecoin", count: 5 },
  { category: "l2", count: 4 },
  { category: "ai", count: 3 },
  { category: "infrastructure", count: 2 },
];

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
}

function renderCategoryFilter() {
  server.use(
    http.get("/api/rankings/categories", () =>
      HttpResponse.json(MOCK_CATEGORIES),
    ),
  );

  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <CategoryFilter />
    </QueryClientProvider>,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("CategoryFilter", () => {
  beforeEach(() => {
    useTableStore.setState(useTableStore.getInitialState());
  });

  it("renders_category_chips_when_api_returns_data", async () => {
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /l1/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /defi/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /memecoin/i })).toBeInTheDocument();
  });

  it("renders_category_count_in_chip", async () => {
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /l1/i })).toBeInTheDocument();
    });
    // Should show count next to category name
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("renders_excluded_categories_with_different_style", async () => {
    // Default exclusions: stablecoin, wrapped-tokens
    // None of our mock data has those, so all should be active
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /l1/i })).toBeInTheDocument();
    });

    // All chips should be "active" (not excluded)
    const l1Btn = screen.getByRole("button", { name: /l1/i });
    expect(l1Btn).not.toHaveAttribute("data-excluded", "true");
  });

  it("toggles_exclude_when_chip_clicked", async () => {
    const user = userEvent.setup();
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /memecoin/i })).toBeInTheDocument();
    });

    const memeBtn = screen.getByRole("button", { name: /memecoin/i });

    // Click to exclude
    await user.click(memeBtn);

    // Store should now have memecoin in excludeCategories
    const state = useTableStore.getState();
    expect(state.excludeCategories).toContain("memecoin");
  });

  it("removes_from_excluded_when_excluded_chip_clicked_again", async () => {
    // Pre-set memecoin as excluded
    useTableStore.setState({
      excludeCategories: ["stablecoin", "wrapped-tokens", "memecoin"],
    });

    const user = userEvent.setup();
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /memecoin/i })).toBeInTheDocument();
    });

    const memeBtn = screen.getByRole("button", { name: /memecoin/i });

    // Click to re-include
    await user.click(memeBtn);

    const state = useTableStore.getState();
    expect(state.excludeCategories).not.toContain("memecoin");
  });

  it("renders_nothing_when_api_returns_empty", async () => {
    server.use(
      http.get("/api/rankings/categories", () => HttpResponse.json([])),
    );

    const { container } = render(
      <QueryClientProvider client={makeQueryClient()}>
        <CategoryFilter />
      </QueryClientProvider>,
    );

    // Wait a tick for the query to resolve
    await waitFor(() => {
      // Should render no chips
      expect(container.querySelectorAll("[data-testid='category-chip']").length).toBe(0);
    });
  });

  it("shows_excluded_chip_with_data_excluded_attribute", async () => {
    // Pre-exclude l1
    useTableStore.setState({
      excludeCategories: ["stablecoin", "wrapped-tokens", "l1"],
    });

    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /l1/i })).toBeInTheDocument();
    });

    const l1Btn = screen.getByRole("button", { name: /l1/i });
    expect(l1Btn).toHaveAttribute("data-excluded", "true");
  });

  it("renders_reset_button_that_clears_category_exclusions", async () => {
    useTableStore.setState({
      excludeCategories: ["stablecoin", "wrapped-tokens", "memecoin"],
    });

    const user = userEvent.setup();
    renderCategoryFilter();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /reset filters/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /reset filters/i }));

    const state = useTableStore.getState();
    // Should reset to defaults
    expect(state.excludeCategories).toEqual(["stablecoin", "wrapped-tokens"]);
  });
});
