/**
 * TDD tests for the CollectNowButton component.
 *
 * MSW intercepts `/api/pipeline/collect-now` and `/api/pipeline/status/:id`.
 */

import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse, delay } from "msw";
import { server } from "@/test/msw/server";
import {
  collectNowHandler,
  collectNowErrorHandler,
} from "@/test/msw/handlers";
import { CollectNowButton } from "./CollectNowButton";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

function renderButton() {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <CollectNowButton />
    </QueryClientProvider>,
  );
}

describe("CollectNowButton", () => {
  it("renders Collect Now button", () => {
    renderButton();
    expect(
      screen.getByRole("button", { name: /collect now/i }),
    ).toBeInTheDocument();
  });

  it("shows collecting state while request is in flight", async () => {
    // Use a slow handler so we can observe the in-flight state
    server.use(
      http.post("/api/pipeline/collect-now", async () => {
        await delay("infinite");
        return HttpResponse.json({ job_id: "x", status: "pending" });
      }),
    );
    renderButton();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /collect now/i }));

    await waitFor(() => {
      expect(screen.getByText(/collecting/i)).toBeInTheDocument();
      expect(screen.getByRole("button")).toBeDisabled();
    });
  });

  it("shows done state after successful collection", async () => {
    server.use(collectNowHandler());
    renderButton();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /collect now/i }));

    await waitFor(() => {
      expect(screen.getByText(/collected/i)).toBeInTheDocument();
    });
  });

  it("shows error state on failure", async () => {
    server.use(collectNowErrorHandler());
    renderButton();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /collect now/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });
});
