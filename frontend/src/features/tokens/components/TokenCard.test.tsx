/**
 * TDD — RED phase
 * Tests for TokenCard written BEFORE the component exists.
 * Run: vitest run src/features/tokens/components/TokenCard.test.tsx
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import { TokenCard } from "./TokenCard";
import type { RankingOpportunity } from "@/services/tokens.service";

const mockOpportunity: RankingOpportunity = {
  rank: 1,
  signals: ["↑dev", "↑social"],
  token: {
    id: 1,
    symbol: "SOL",
    name: "Solana",
    coingecko_id: "solana",
    category: "Layer1",
    github_repo: "https://github.com/solana-labs/solana",
    whitepaper_url: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    latest_score: {
      fundamental_score: 0.85,
      technology_score: 0.90,
      tokenomics_score: 0.75,
      adoption_score: 0.88,
      dev_activity_score: 0.91,
      narrative_score: 0.88,
      growth_score: 0.91,
      risk_score: 0.82,
      listing_probability: 0.20,
      cycle_leader_prob: 0.71,
      opportunity_score: 0.87,
      snapshot_date: "2025-03-10",
    },
    price_usd: 185.42,
    market_cap: 82_000_000_000,
    volume_24h: 3_200_000_000,
    price_change_7d: 0.123,
    rank: 5,
  },
};

function renderCard(opportunity = mockOpportunity) {
  return render(
    <MemoryRouter>
      <TokenCard opportunity={opportunity} />
    </MemoryRouter>,
  );
}

describe("TokenCard", () => {
  it("renders token symbol", () => {
    renderCard();
    expect(screen.getByText("SOL")).toBeInTheDocument();
  });

  it("renders token name", () => {
    renderCard();
    expect(screen.getByText("Solana")).toBeInTheDocument();
  });

  it("renders the rank number", () => {
    renderCard();
    expect(screen.getByText("#1")).toBeInTheDocument();
  });

  it("renders the opportunity score", () => {
    renderCard();
    // API returns 0.87, display scales to 8.7
    expect(screen.getByText("8.7")).toBeInTheDocument();
  });

  it("renders the category badge", () => {
    renderCard();
    expect(screen.getByText("Layer1")).toBeInTheDocument();
  });

  it("renders each signal chip", () => {
    renderCard();
    expect(screen.getByText("↑dev")).toBeInTheDocument();
    expect(screen.getByText("↑social")).toBeInTheDocument();
  });

  it("renders a link to the token detail page", () => {
    renderCard();
    const link = screen.getByRole("link", { name: /view SOL details/i });
    expect(link).toHaveAttribute("href", "/tokens/SOL");
  });

  it("renders formatted market cap", () => {
    renderCard();
    expect(screen.getByText(/82\.00B/i)).toBeInTheDocument();
  });

  it("renders the 7-day price change with correct sign", () => {
    renderCard();
    expect(screen.getByText(/\+12\.3%/i)).toBeInTheDocument();
  });

  it("renders placeholder when score is null", () => {
    const noScore: RankingOpportunity = {
      ...mockOpportunity,
      token: { ...mockOpportunity.token, latest_score: null },
    };
    renderCard(noScore);
    // When score is null, all 5 score pillars render "N/A"
    const naElements = screen.getAllByText("N/A");
    expect(naElements.length).toBeGreaterThanOrEqual(1);
    naElements.forEach((el) => expect(el).toBeInTheDocument());
  });
});
