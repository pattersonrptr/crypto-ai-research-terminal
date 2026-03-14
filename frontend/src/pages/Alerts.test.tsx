/**
 * TDD tests for the Alerts page.
 *
 * Naming: test_<unit>_<scenario>_<expected_outcome>
 * MSW intercepts GET /api/alerts and GET /api/alerts/stats.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  alertsHandler,
  acknowledgeAlertHandler,
  MOCK_ALERTS,
} from "@/test/msw/handlers";
import { http, HttpResponse } from "msw";
import { Alerts } from "./Alerts";

// ── helpers ───────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderAlerts() {
  const qc = makeQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Alerts />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── page structure ────────────────────────────────────────────────────────

describe("Alerts", () => {
  it("renders_page_header_with_alerts_title", async () => {
    renderAlerts();
    await waitFor(() => {
      expect(screen.getByText("Alerts")).toBeInTheDocument();
    });
  });

  it("renders_stats_bar_with_total_and_unacknowledged_counts", async () => {
    renderAlerts();
    await waitFor(() => {
      // Stats bar shows total=42 and unacknowledged=15 from MOCK_ALERT_STATS
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("15")).toBeInTheDocument();
    });
  });

  // ── alert list ────────────────────────────────────────────────────────────

  it("renders_alert_list_with_all_mock_alerts", async () => {
    renderAlerts();
    await waitFor(() => {
      expect(
        screen.getByText(MOCK_ALERTS[0].message),
      ).toBeInTheDocument();
      expect(
        screen.getByText(MOCK_ALERTS[1].message),
      ).toBeInTheDocument();
    });
  });

  it("renders_alert_type_badge_for_each_alert", async () => {
    renderAlerts();
    await waitFor(() => {
      // MOCK_ALERTS[0] has type LISTING_CANDIDATE
      expect(screen.getByText(/listing candidate/i)).toBeInTheDocument();
    });
  });

  it("renders_acknowledge_button_for_unacknowledged_alerts", async () => {
    renderAlerts();
    await waitFor(() => {
      // MOCK_ALERTS[0] is unacknowledged → should have a button
      const buttons = screen.getAllByRole("button", { name: /acknowledge/i });
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it("does_not_render_acknowledge_button_for_already_acknowledged_alerts", async () => {
    renderAlerts();
    await waitFor(() => {
      expect(screen.getByText(MOCK_ALERTS[1].message)).toBeInTheDocument();
    });
    // MOCK_ALERTS[1] is acknowledged — should show "Acknowledged" badge, not button
    // There's only 1 unacknowledged alert in the mock data
    const buttons = screen.getAllByRole("button", { name: /acknowledge/i });
    expect(buttons).toHaveLength(1);
  });

  // ── acknowledge action ────────────────────────────────────────────────────

  it("clicking_acknowledge_button_removes_acknowledge_button_after_mutation", async () => {
    const user = userEvent.setup();
    // Handler returns the alert with acknowledged:true
    server.use(acknowledgeAlertHandler());

    renderAlerts();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /acknowledge/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /acknowledge/i }));

    // After successful mutation, button disappears (optimistic or refetch)
    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /acknowledge/i }),
      ).not.toBeInTheDocument();
    });
  });

  // ── filter by type ────────────────────────────────────────────────────────

  it("renders_filter_select_or_buttons_for_alert_types", async () => {
    renderAlerts();
    await waitFor(() => {
      // Filter control — look for a combobox (select) or "All" button
      const filterEl =
        screen.queryByRole("combobox", { name: /filter/i }) ??
        screen.queryByRole("button", { name: /all/i });
      expect(filterEl).toBeInTheDocument();
    });
  });

  // ── error state ───────────────────────────────────────────────────────────

  it("renders_error_message_when_api_returns_500", async () => {
    server.use(
      http.get("/api/alerts", () =>
        HttpResponse.json({ detail: "error" }, { status: 500 }),
      ),
    );

    renderAlerts();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load/i);
    });
  });

  // ── empty state ───────────────────────────────────────────────────────────

  it("renders_empty_state_message_when_no_alerts", async () => {
    server.use(alertsHandler([]));

    renderAlerts();

    await waitFor(() => {
      expect(screen.getByText(/no alerts/i)).toBeInTheDocument();
    });
  });
});
