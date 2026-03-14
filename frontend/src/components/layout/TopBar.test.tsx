/**
 * TDD tests for the TopBar layout component.
 *
 * Naming: test_<unit>_<scenario>_<expected_outcome>
 *
 * TopBar uses useThemeStore (Zustand + localStorage persist).
 * We reset the store to a known state before each test.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useThemeStore } from "@/store/themeStore";
import { TopBar } from "./TopBar";

// ── helpers ───────────────────────────────────────────────────────────────

function renderTopBar() {
  return render(<TopBar />);
}

// Reset store to dark mode before every test
beforeEach(() => {
  useThemeStore.setState({ mode: "dark", resolved: "dark" });
  // Clear any class applied to <html> from previous tests
  document.documentElement.className = "";
});

// ── rendering ─────────────────────────────────────────────────────────────

describe("TopBar", () => {
  it("renders_header_landmark_with_correct_aria_label", () => {
    renderTopBar();
    expect(
      screen.getByRole("banner", { name: /top navigation bar/i }),
    ).toBeInTheDocument();
  });

  it("renders_theme_selector_group", () => {
    renderTopBar();
    expect(
      screen.getByRole("group", { name: /theme selector/i }),
    ).toBeInTheDocument();
  });

  it("renders_all_three_theme_buttons", () => {
    renderTopBar();
    expect(screen.getByRole("button", { name: /light theme/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dark theme/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /system theme/i })).toBeInTheDocument();
  });

  // ── aria-pressed state ──────────────────────────────────────────────────

  it("dark_button_is_aria_pressed_true_when_mode_is_dark", () => {
    renderTopBar();
    expect(
      screen.getByRole("button", { name: /dark theme/i }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("light_and_system_buttons_are_aria_pressed_false_when_mode_is_dark", () => {
    renderTopBar();
    expect(
      screen.getByRole("button", { name: /light theme/i }),
    ).toHaveAttribute("aria-pressed", "false");
    expect(
      screen.getByRole("button", { name: /system theme/i }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  // ── clicking updates active state ───────────────────────────────────────

  it("clicking_light_button_sets_light_as_aria_pressed_true", async () => {
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { name: /light theme/i }));

    expect(
      screen.getByRole("button", { name: /light theme/i }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: /dark theme/i }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("clicking_system_button_sets_system_as_aria_pressed_true", async () => {
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { name: /system theme/i }));

    expect(
      screen.getByRole("button", { name: /system theme/i }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  // ── store + DOM side-effects ─────────────────────────────────────────────

  it("clicking_light_updates_zustand_store_mode_to_light", async () => {
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { name: /light theme/i }));

    expect(useThemeStore.getState().mode).toBe("light");
  });

  it("clicking_dark_adds_dark_class_to_html_element", async () => {
    // Start in light so clicking dark is a real change
    useThemeStore.setState({ mode: "light", resolved: "light" });
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { name: /dark theme/i }));

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("clicking_light_adds_light_class_to_html_element", async () => {
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { name: /light theme/i }));

    expect(document.documentElement.classList.contains("light")).toBe(true);
  });
});
