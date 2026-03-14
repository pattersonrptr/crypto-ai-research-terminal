/**
 * TDD tests for the Sidebar layout component.
 *
 * Naming: test_<unit>_<scenario>_<expected_outcome>
 *
 * The Sidebar uses useSidebarStore (Zustand + localStorage persist).
 * We reset the store to a known state before each test to avoid bleed.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { useSidebarStore } from "@/store/sidebarStore";
import { Sidebar } from "./Sidebar";

// ── helpers ───────────────────────────────────────────────────────────────

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>,
  );
}

// Reset Zustand store to a clean open state before every test
beforeEach(() => {
  useSidebarStore.setState({ isOpen: true });
});

// ── rendering ─────────────────────────────────────────────────────────────

describe("Sidebar", () => {
  it("renders_navigation_landmark_with_correct_aria_label", () => {
    renderSidebar();
    expect(
      screen.getByRole("complementary", { name: /main navigation/i }),
    ).toBeInTheDocument();
  });

  it("renders_all_three_nav_links_when_open", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: /go to rankings/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /go to narratives/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /go to alerts/i })).toBeInTheDocument();
  });

  it("renders_nav_link_labels_when_sidebar_is_open", () => {
    renderSidebar();
    expect(screen.getByText("Rankings")).toBeInTheDocument();
    expect(screen.getByText("Narratives")).toBeInTheDocument();
    expect(screen.getByText("Alerts")).toBeInTheDocument();
  });

  it("renders_collapse_button_with_correct_aria_label_when_open", () => {
    renderSidebar();
    expect(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    ).toBeInTheDocument();
  });

  // ── toggle ──────────────────────────────────────────────────────────────

  it("hides_nav_labels_and_brand_name_after_collapse", async () => {
    const user = userEvent.setup();
    renderSidebar();

    // Labels visible before collapse
    expect(screen.getByText("Rankings")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /collapse sidebar/i }));

    expect(screen.queryByText("Rankings")).not.toBeInTheDocument();
    expect(screen.queryByText("Narratives")).not.toBeInTheDocument();
    expect(screen.queryByText("Alerts")).not.toBeInTheDocument();
  });

  it("changes_toggle_button_aria_label_to_expand_after_collapse", async () => {
    const user = userEvent.setup();
    renderSidebar();

    await user.click(screen.getByRole("button", { name: /collapse sidebar/i }));

    expect(
      screen.getByRole("button", { name: /expand sidebar/i }),
    ).toBeInTheDocument();
  });

  it("restores_labels_after_expand", async () => {
    const user = userEvent.setup();
    renderSidebar();

    // Collapse then expand
    await user.click(screen.getByRole("button", { name: /collapse sidebar/i }));
    await user.click(screen.getByRole("button", { name: /expand sidebar/i }));

    expect(screen.getByText("Rankings")).toBeInTheDocument();
  });

  it("updates_zustand_store_isOpen_to_false_when_collapsed", async () => {
    const user = userEvent.setup();
    renderSidebar();

    await user.click(screen.getByRole("button", { name: /collapse sidebar/i }));

    expect(useSidebarStore.getState().isOpen).toBe(false);
  });

  it("renders_collapsed_state_when_store_starts_closed", () => {
    useSidebarStore.setState({ isOpen: false });
    renderSidebar();

    expect(screen.queryByText("Rankings")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /expand sidebar/i }),
    ).toBeInTheDocument();
  });

  // ── nav links still accessible when collapsed ───────────────────────────

  it("nav_links_still_present_when_sidebar_is_collapsed", async () => {
    useSidebarStore.setState({ isOpen: false });
    renderSidebar();

    // Links still rendered (icon only), still accessible by aria-label
    expect(screen.getByRole("link", { name: /go to rankings/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /go to alerts/i })).toBeInTheDocument();
  });
});
