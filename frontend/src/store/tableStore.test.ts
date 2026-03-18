/**
 * TDD tests for tableStore.
 *
 * Tests cover column visibility, server-side query state (search, categories,
 * sort, order, pagination) and default excluded categories.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useTableStore } from "./tableStore";

// Reset Zustand store between tests so state doesn't leak.
function resetStore() {
  useTableStore.setState(useTableStore.getInitialState());
}

describe("tableStore", () => {
  beforeEach(() => {
    resetStore();
  });

  // ── Column visibility (existing) ──────────────────────────────────────

  it("has_default_visible_columns_on_init", () => {
    const { visibleColumns } = useTableStore.getState();
    expect(visibleColumns.has("rank")).toBe(true);
    expect(visibleColumns.has("symbol")).toBe(true);
    expect(visibleColumns.has("opportunity_score")).toBe(true);
  });

  it("toggleColumn_hides_a_visible_hideable_column", () => {
    useTableStore.getState().toggleColumn("name");
    expect(useTableStore.getState().visibleColumns.has("name")).toBe(false);
  });

  it("toggleColumn_does_not_hide_non_hideable_column", () => {
    useTableStore.getState().toggleColumn("rank");
    expect(useTableStore.getState().visibleColumns.has("rank")).toBe(true);
  });

  it("resetColumns_restores_default_visibility", () => {
    useTableStore.getState().toggleColumn("name");
    useTableStore.getState().resetColumns();
    expect(useTableStore.getState().visibleColumns.has("name")).toBe(true);
  });

  // ── Search state ──────────────────────────────────────────────────────

  it("search_defaults_to_empty_string", () => {
    expect(useTableStore.getState().search).toBe("");
  });

  it("setSearch_updates_search_value", () => {
    useTableStore.getState().setSearch("bitcoin");
    expect(useTableStore.getState().search).toBe("bitcoin");
  });

  it("setSearch_resets_page_to_1", () => {
    useTableStore.getState().setPage(3);
    useTableStore.getState().setSearch("eth");
    expect(useTableStore.getState().page).toBe(1);
  });

  // ── Category filters ──────────────────────────────────────────────────

  it("categories_defaults_to_empty_array", () => {
    expect(useTableStore.getState().categories).toEqual([]);
  });

  it("setCategories_updates_categories_filter", () => {
    useTableStore.getState().setCategories(["defi", "l1"]);
    expect(useTableStore.getState().categories).toEqual(["defi", "l1"]);
  });

  it("setCategories_resets_page_to_1", () => {
    useTableStore.getState().setPage(2);
    useTableStore.getState().setCategories(["defi"]);
    expect(useTableStore.getState().page).toBe(1);
  });

  it("excludeCategories_defaults_to_stablecoin_and_wrapped", () => {
    const { excludeCategories } = useTableStore.getState();
    expect(excludeCategories).toContain("stablecoin");
    expect(excludeCategories).toContain("wrapped-tokens");
  });

  it("setExcludeCategories_updates_exclude_list", () => {
    useTableStore.getState().setExcludeCategories(["memecoin"]);
    expect(useTableStore.getState().excludeCategories).toEqual(["memecoin"]);
  });

  // ── Sort state ────────────────────────────────────────────────────────

  it("sort_defaults_to_opportunity_score_desc", () => {
    const state = useTableStore.getState();
    expect(state.sort).toBe("opportunity_score");
    expect(state.order).toBe("desc");
  });

  it("setSort_updates_sort_column_and_order", () => {
    useTableStore.getState().setSort("market_cap", "asc");
    const state = useTableStore.getState();
    expect(state.sort).toBe("market_cap");
    expect(state.order).toBe("asc");
  });

  it("setSort_resets_page_to_1", () => {
    useTableStore.getState().setPage(5);
    useTableStore.getState().setSort("risk_score", "asc");
    expect(useTableStore.getState().page).toBe(1);
  });

  // ── Pagination state ──────────────────────────────────────────────────

  it("page_defaults_to_1", () => {
    expect(useTableStore.getState().page).toBe(1);
  });

  it("pageSize_defaults_to_50", () => {
    expect(useTableStore.getState().pageSize).toBe(50);
  });

  it("setPage_updates_page_number", () => {
    useTableStore.getState().setPage(3);
    expect(useTableStore.getState().page).toBe(3);
  });

  it("setPageSize_updates_page_size_and_resets_page", () => {
    useTableStore.getState().setPage(5);
    useTableStore.getState().setPageSize(25);
    expect(useTableStore.getState().pageSize).toBe(25);
    expect(useTableStore.getState().page).toBe(1);
  });

  // ── Reset ─────────────────────────────────────────────────────────────

  it("resetFilters_clears_search_categories_and_resets_page", () => {
    useTableStore.getState().setSearch("bitcoin");
    useTableStore.getState().setCategories(["defi"]);
    useTableStore.getState().setPage(3);
    useTableStore.getState().resetFilters();

    const state = useTableStore.getState();
    expect(state.search).toBe("");
    expect(state.categories).toEqual([]);
    expect(state.page).toBe(1);
    // excludeCategories should be back to defaults
    expect(state.excludeCategories).toContain("stablecoin");
    expect(state.excludeCategories).toContain("wrapped-tokens");
  });
});
