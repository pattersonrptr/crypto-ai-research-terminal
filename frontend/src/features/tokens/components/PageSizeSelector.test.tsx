/**
 * TDD tests for PageSizeSelector component.
 *
 * PageSizeSelector renders a dropdown to choose page size (25, 50, 100)
 * and wires into the tableStore.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useTableStore } from "@/store/tableStore";
import { PageSizeSelector } from "./PageSizeSelector";

describe("PageSizeSelector", () => {
  beforeEach(() => {
    useTableStore.setState(useTableStore.getInitialState());
  });

  it("renders_select_with_default_value_50", () => {
    render(<PageSizeSelector />);
    const select = screen.getByRole("combobox", { name: /rows per page/i });
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue("50");
  });

  it("renders_options_25_50_100", () => {
    render(<PageSizeSelector />);
    const options = screen.getAllByRole("option");
    const values = options.map((o) => o.getAttribute("value"));
    expect(values).toEqual(["25", "50", "100"]);
  });

  it("updates_store_when_option_selected", async () => {
    const user = userEvent.setup();
    render(<PageSizeSelector />);

    const select = screen.getByRole("combobox", { name: /rows per page/i });
    await user.selectOptions(select, "25");

    const state = useTableStore.getState();
    expect(state.pageSize).toBe(25);
    // Page should reset to 1
    expect(state.page).toBe(1);
  });

  it("reflects_current_store_page_size", () => {
    useTableStore.setState({ pageSize: 100 });
    render(<PageSizeSelector />);

    const select = screen.getByRole("combobox", { name: /rows per page/i });
    expect(select).toHaveValue("100");
  });
});
