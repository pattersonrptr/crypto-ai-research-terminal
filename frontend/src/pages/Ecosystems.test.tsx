/**
 * TDD tests for the Ecosystems page.
 *
 * MSW intercepts GET /api/graph/communities and GET /api/graph/ecosystem.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  graphCommunitiesHandler,
  graphCommunitiesErrorHandler,
  graphEcosystemHandler,
  graphCentralityHandler,
  MOCK_COMMUNITIES,
  MOCK_ECOSYSTEM,
  MOCK_CENTRALITY,
} from "@/test/msw/handlers";
import { Ecosystems } from "./Ecosystems";

// ── helpers ────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderEcosystems() {
  const qc = makeQueryClient();
  server.use(
    graphCommunitiesHandler(MOCK_COMMUNITIES),
    graphEcosystemHandler(MOCK_ECOSYSTEM),
    graphCentralityHandler(MOCK_CENTRALITY),
  );
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Ecosystems />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── tests ──────────────────────────────────────────────────────────────────

describe("Ecosystems", () => {
  it("renders_page_header_with_ecosystems_title", async () => {
    renderEcosystems();
    await waitFor(() => {
      expect(screen.getByText("Ecosystems")).toBeInTheDocument();
    });
  });

  it("renders_community_count_from_ecosystem_snapshot", async () => {
    renderEcosystems();
    await waitFor(() => {
      // MOCK_ECOSYSTEM.n_communities = 3
      expect(screen.getAllByText(/^3$/).length).toBeGreaterThan(0);
    });
  });

  it("renders_community_member_tokens", async () => {
    renderEcosystems();
    await waitFor(() => {
      expect(screen.getAllByText("ETH").length).toBeGreaterThan(0);
    });
  });

  it("renders_top_tokens_section", async () => {
    renderEcosystems();
    await waitFor(() => {
      expect(screen.getByText(/Top Tokens/i)).toBeInTheDocument();
    });
  });

  it("renders_top_tokens_from_ecosystem_snapshot", async () => {
    renderEcosystems();
    await waitFor(() => {
      expect(screen.getAllByText("BTC").length).toBeGreaterThan(0);
    });
  });

  it("renders_loading_state_before_data_arrives", () => {
    const qc = makeQueryClient();
    server.use(
      graphCommunitiesHandler(MOCK_COMMUNITIES),
      graphEcosystemHandler(MOCK_ECOSYSTEM),
      graphCentralityHandler(MOCK_CENTRALITY),
    );
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Ecosystems />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    // Loading indicator must appear immediately
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders_error_state_on_api_failure", async () => {
    const qc = makeQueryClient();
    server.use(graphCommunitiesErrorHandler());
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Ecosystems />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await waitFor(() => {
      expect(
        screen.getByText(/failed to load ecosystem data/i),
      ).toBeInTheDocument();
    });
  });
});
