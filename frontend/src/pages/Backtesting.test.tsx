/**
 * TDD tests for the Backtesting page.
 *
 * MSW intercepts POST /api/backtesting/run, /validate, /calibrate.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/test/msw/server";
import {
  backtestRunHandler,
  backtestRunErrorHandler,
  backtestValidateHandler,
  MOCK_BACKTEST_RESULT,
  MOCK_VALIDATE_RESULT,
} from "@/test/msw/handlers";
import { Backtesting } from "./Backtesting";

// ── helpers ────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderBacktesting() {
  const qc = makeQueryClient();
  server.use(backtestRunHandler(MOCK_BACKTEST_RESULT));
  server.use(backtestValidateHandler(MOCK_VALIDATE_RESULT));
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Backtesting />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── tests ──────────────────────────────────────────────────────────────────

describe("Backtesting", () => {
  it("renders_page_header_with_backtesting_title", () => {
    renderBacktesting();
    expect(screen.getByText("Backtesting")).toBeInTheDocument();
  });

  it("renders_symbol_input_field", () => {
    renderBacktesting();
    expect(
      screen.getByRole("textbox", { name: /symbol/i }),
    ).toBeInTheDocument();
  });

  it("renders_cycle_select_field", () => {
    renderBacktesting();
    expect(screen.getByRole("combobox", { name: /cycle/i })).toBeInTheDocument();
  });

  it("renders_run_button", () => {
    renderBacktesting();
    expect(
      screen.getByRole("button", { name: /run backtest/i }),
    ).toBeInTheDocument();
  });

  it("shows_results_after_successful_run", async () => {
    renderBacktesting();
    const symbolInput = screen.getByRole("textbox", { name: /symbol/i });
    fireEvent.change(symbolInput, { target: { value: "BTC" } });

    fireEvent.click(screen.getByRole("button", { name: /run backtest/i }));

    await waitFor(() => {
      expect(screen.getByText(/total return/i)).toBeInTheDocument();
    });
  });

  it("shows_total_return_value_in_results", async () => {
    renderBacktesting();
    fireEvent.change(screen.getByRole("textbox", { name: /symbol/i }), {
      target: { value: "BTC" },
    });
    fireEvent.click(screen.getByRole("button", { name: /run backtest/i }));
    await waitFor(() => {
      // MOCK_BACKTEST_RESULT.total_return_pct = 42.5
      expect(screen.getByText(/42\.5/)).toBeInTheDocument();
    });
  });

  it("shows_n_trades_in_results", async () => {
    renderBacktesting();
    fireEvent.change(screen.getByRole("textbox", { name: /symbol/i }), {
      target: { value: "BTC" },
    });
    fireEvent.click(screen.getByRole("button", { name: /run backtest/i }));
    await waitFor(() => {
      expect(screen.getByText(/trades/i)).toBeInTheDocument();
    });
  });

  it("shows_error_message_on_api_failure", async () => {
    const qc = makeQueryClient();
    server.use(backtestRunErrorHandler());
    server.use(backtestValidateHandler(MOCK_VALIDATE_RESULT));
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Backtesting />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    fireEvent.change(screen.getByRole("textbox", { name: /symbol/i }), {
      target: { value: "BTC" },
    });
    fireEvent.click(screen.getByRole("button", { name: /run backtest/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/simulation failed/i),
      ).toBeInTheDocument();
    });
  });

  it("renders_model_validation_section_heading", () => {
    renderBacktesting();
    expect(screen.getByText(/model validation/i)).toBeInTheDocument();
  });

  it("renders_validate_button", () => {
    renderBacktesting();
    expect(
      screen.getByRole("button", { name: /run validation/i }),
    ).toBeInTheDocument();
  });

  it("shows_validation_metrics_after_clicking_validate", async () => {
    renderBacktesting();
    fireEvent.click(screen.getByRole("button", { name: /run validation/i }));

    await waitFor(() => {
      expect(screen.getByText(/precision/i)).toBeInTheDocument();
    });
  });

  it("shows_token_breakdown_table_after_validation", async () => {
    renderBacktesting();
    fireEvent.click(screen.getByRole("button", { name: /run validation/i }));

    await waitFor(() => {
      // MOCK_VALIDATE_RESULT has SOL as first token
      expect(screen.getByText("SOL")).toBeInTheDocument();
    });
  });
});
