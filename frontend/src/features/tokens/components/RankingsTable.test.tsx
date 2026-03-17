/**
 * TDD tests for the RankingsTable component.
 *
 * RankingsTable renders a @tanstack/react-table powered data table of
 * RankingOpportunity items with sortable columns and links to token detail.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import type { RankingOpportunity } from "@/services/tokens.service";
import { RankingsTable } from "./RankingsTable";

// ── Helpers ──────────────────────────────────────────────────────────────

function makeOpportunity(
  overrides: Partial<RankingOpportunity> = {},
): RankingOpportunity {
  return {
    rank: 1,
    token: {
      id: 1,
      symbol: "BTC",
      name: "Bitcoin",
      coingecko_id: "bitcoin",
      category: "l1",
      github_repo: null,
      whitepaper_url: null,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
      latest_score: {
        fundamental_score: 0.8,
        technology_score: 0.7,
        tokenomics_score: 0.6,
        adoption_score: 0.75,
        dev_activity_score: 0.65,
        narrative_score: 0.7,
        growth_score: 0.6,
        risk_score: 0.3,
        listing_probability: 0.5,
        cycle_leader_prob: 0.4,
        opportunity_score: 0.71,
        snapshot_date: "2025-01-15T00:00:00Z",
      },
      price_usd: 50000,
      market_cap: 1000000000,
      volume_24h: 50000000,
      price_change_7d: 5.2,
      rank: 1,
    },
    signals: ["high_growth", "bullish"],
    ...overrides,
  };
}

const SAMPLE_DATA: RankingOpportunity[] = [
  makeOpportunity({ rank: 1 }),
  makeOpportunity({
    rank: 2,
    token: {
      ...makeOpportunity().token,
      id: 2,
      symbol: "ETH",
      name: "Ethereum",
      category: "defi",
      latest_score: {
        ...makeOpportunity().token.latest_score!,
        opportunity_score: 0.65,
      },
    },
  }),
  makeOpportunity({
    rank: 3,
    token: {
      ...makeOpportunity().token,
      id: 3,
      symbol: "SOL",
      name: "Solana",
      category: null,
    },
    signals: [],
  }),
];

function renderTable(
  props: Partial<Parameters<typeof RankingsTable>[0]> = {},
) {
  const defaultProps = {
    data: SAMPLE_DATA,
    sort: "opportunity_score",
    order: "desc" as const,
    onSortChange: vi.fn(),
  };

  return render(
    <MemoryRouter>
      <RankingsTable {...defaultProps} {...props} />
    </MemoryRouter>,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("RankingsTable", () => {
  it("renders_a_table_element", () => {
    renderTable();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("renders_column_headers", () => {
    renderTable();
    expect(screen.getByRole("columnheader", { name: /#/i })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /symbol/i })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /score/i })).toBeInTheDocument();
  });

  it("renders_one_row_per_data_item", () => {
    renderTable();
    // thead has 1 row, tbody has 3 data rows
    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(4); // 1 header + 3 data
  });

  it("renders_token_symbol_in_each_row", () => {
    renderTable();
    expect(screen.getByText("BTC")).toBeInTheDocument();
    expect(screen.getByText("ETH")).toBeInTheDocument();
    expect(screen.getByText("SOL")).toBeInTheDocument();
  });

  it("renders_rank_numbers", () => {
    renderTable();
    const tbody = screen.getByRole("table").querySelector("tbody")!;
    const firstRow = within(tbody).getAllByRole("row")[0];
    expect(within(firstRow).getByText("1")).toBeInTheDocument();
  });

  it("renders_opportunity_score_formatted_on_0_to_10_scale", () => {
    renderTable();
    // 0.71 -> 7.1 on the 0-10 scale; appears in both BTC (0.71) and ETH rows too
    const allScores = screen.getAllByText("7.1");
    expect(allScores.length).toBeGreaterThanOrEqual(1);
  });

  it("renders_category_badge_when_category_exists", () => {
    renderTable();
    expect(screen.getByText("l1")).toBeInTheDocument();
    expect(screen.getByText("defi")).toBeInTheDocument();
  });

  it("renders_dash_when_category_is_null", () => {
    renderTable();
    // SOL has null category — should show "—" or empty
    const tbody = screen.getByRole("table").querySelector("tbody")!;
    const solRow = within(tbody).getAllByRole("row")[2];
    // The category cell should contain "—"
    expect(within(solRow).getByText("—")).toBeInTheDocument();
  });

  it("renders_signal_chips", () => {
    renderTable();
    // BTC and ETH both have "high_growth" + "bullish" signals
    const growthChips = screen.getAllByText("high_growth");
    expect(growthChips.length).toBeGreaterThanOrEqual(1);
    const bullishChips = screen.getAllByText("bullish");
    expect(bullishChips.length).toBeGreaterThanOrEqual(1);
  });

  it("renders_links_to_token_detail_page", () => {
    renderTable();
    const btcLink = screen.getByRole("link", { name: /BTC/i });
    expect(btcLink).toHaveAttribute("href", "/tokens/BTC");
  });

  it("calls_onSortChange_when_sortable_header_is_clicked", async () => {
    const onSortChange = vi.fn();
    const user = userEvent.setup();
    renderTable({ onSortChange });

    const scoreHeader = screen.getByRole("columnheader", { name: /score/i });
    await user.click(scoreHeader);

    expect(onSortChange).toHaveBeenCalledWith("opportunity_score");
  });

  it("renders_empty_tbody_when_data_is_empty", () => {
    renderTable({ data: [] });
    const tbody = screen.getByRole("table").querySelector("tbody")!;
    const rows = within(tbody).queryAllByRole("row");
    // Might have an empty state row or zero rows
    expect(rows.length).toBeLessThanOrEqual(1);
  });

  it("shows_empty_message_when_data_is_empty", () => {
    renderTable({ data: [] });
    expect(screen.getByText(/no results/i)).toBeInTheDocument();
  });
});
