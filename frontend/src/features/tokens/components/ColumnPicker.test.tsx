/**
 * TDD tests for ColumnPicker component.
 *
 * ColumnPicker is a dropdown button that lets the user toggle which columns
 * are visible in the rankings grid and reset to defaults.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useTableStore, ALL_COLUMNS } from "@/store/tableStore";
import { ColumnPicker } from "./ColumnPicker";

// ── helpers ───────────────────────────────────────────────────────────────

function renderColumnPicker() {
  return render(<ColumnPicker />);
}

// Reset store to defaults before every test
beforeEach(() => {
  useTableStore.getState().resetColumns();
});

// ── closed state ──────────────────────────────────────────────────────────

describe("ColumnPicker", () => {
  it("renders_trigger_button_with_columns_label", () => {
    renderColumnPicker();
    expect(
      screen.getByRole("button", { name: /columns/i }),
    ).toBeInTheDocument();
  });

  it("does_not_show_column_list_when_closed", () => {
    renderColumnPicker();
    // The column checkboxes should not be visible before opening
    const hideableColumns = ALL_COLUMNS.filter((c) => c.hideable);
    expect(
      screen.queryByRole("checkbox", { name: hideableColumns[0].label }),
    ).not.toBeInTheDocument();
  });

  // ── open state ────────────────────────────────────────────────────────────

  it("opens_dropdown_showing_all_hideable_columns_when_button_clicked", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    const hideableColumns = ALL_COLUMNS.filter((c) => c.hideable);
    for (const col of hideableColumns) {
      expect(
        screen.getByRole("checkbox", { name: col.label }),
      ).toBeInTheDocument();
    }
  });

  it("non_hideable_columns_are_not_shown_in_picker", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    const nonHideable = ALL_COLUMNS.filter((c) => !c.hideable);
    for (const col of nonHideable) {
      expect(
        screen.queryByRole("checkbox", { name: col.label }),
      ).not.toBeInTheDocument();
    }
  });

  it("default_visible_columns_have_checked_checkboxes", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    const defaultOnAndHideable = ALL_COLUMNS.filter(
      (c) => c.hideable && c.defaultVisible,
    );
    for (const col of defaultOnAndHideable) {
      expect(screen.getByRole("checkbox", { name: col.label })).toBeChecked();
    }
  });

  it("default_hidden_columns_have_unchecked_checkboxes", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    const defaultOff = ALL_COLUMNS.filter(
      (c) => c.hideable && !c.defaultVisible,
    );
    for (const col of defaultOff) {
      expect(screen.getByRole("checkbox", { name: col.label })).not.toBeChecked();
    }
  });

  // ── toggling columns ──────────────────────────────────────────────────────

  it("unchecking_a_visible_column_removes_it_from_store", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    // "Name" is visible by default and hideable
    const nameCheckbox = screen.getByRole("checkbox", { name: "Name" });
    expect(nameCheckbox).toBeChecked();

    await user.click(nameCheckbox);

    expect(nameCheckbox).not.toBeChecked();
    expect(useTableStore.getState().visibleColumns.has("name")).toBe(false);
  });

  it("checking_a_hidden_column_adds_it_to_store", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    // "Mkt Cap" is hidden by default
    const mktCapCheckbox = screen.getByRole("checkbox", { name: "Mkt Cap" });
    expect(mktCapCheckbox).not.toBeChecked();

    await user.click(mktCapCheckbox);

    expect(mktCapCheckbox).toBeChecked();
    expect(useTableStore.getState().visibleColumns.has("market_cap")).toBe(true);
  });

  // ── reset ─────────────────────────────────────────────────────────────────

  it("reset_button_is_visible_when_dropdown_open", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    expect(
      screen.getByRole("button", { name: /reset/i }),
    ).toBeInTheDocument();
  });

  it("clicking_reset_restores_default_column_visibility", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));

    // Uncheck "Name" and check "Mkt Cap" to create non-default state
    await user.click(screen.getByRole("checkbox", { name: "Name" }));
    await user.click(screen.getByRole("checkbox", { name: "Mkt Cap" }));

    // Now reset
    await user.click(screen.getByRole("button", { name: /reset/i }));

    // State back to defaults
    const { visibleColumns } = useTableStore.getState();
    expect(visibleColumns.has("name")).toBe(true);
    expect(visibleColumns.has("market_cap")).toBe(false);
  });

  // ── close ─────────────────────────────────────────────────────────────────

  it("closes_dropdown_when_clicking_outside", async () => {
    const user = userEvent.setup();
    renderColumnPicker();

    await user.click(screen.getByRole("button", { name: /columns/i }));
    // Dropdown is open
    expect(
      screen.getByRole("checkbox", { name: "Name" }),
    ).toBeInTheDocument();

    // Click outside
    await user.click(document.body);

    expect(
      screen.queryByRole("checkbox", { name: "Name" }),
    ).not.toBeInTheDocument();
  });
});
