import { create } from "zustand";
import { persist } from "zustand/middleware";

/** All columns available in the rankings table. */
export type ColumnId =
  | "rank"
  | "symbol"
  | "name"
  | "opportunity_score"
  | "fundamental_score"
  | "growth_score"
  | "narrative_score"
  | "risk_score"
  | "listing_probability"
  | "market_cap"
  | "volume_24h"
  | "price_change_7d"
  | "signals";

export interface ColumnDef {
  id: ColumnId;
  label: string;
  /** Whether the column is visible by default. */
  defaultVisible: boolean;
  /** Whether the column can be hidden (some are always shown). */
  hideable: boolean;
}

export const ALL_COLUMNS: ColumnDef[] = [
  { id: "rank",               label: "#",             defaultVisible: true,  hideable: false },
  { id: "symbol",             label: "Symbol",        defaultVisible: true,  hideable: false },
  { id: "name",               label: "Name",          defaultVisible: true,  hideable: true  },
  { id: "opportunity_score",  label: "Score",         defaultVisible: true,  hideable: false },
  { id: "fundamental_score",  label: "Fund.",         defaultVisible: true,  hideable: true  },
  { id: "growth_score",       label: "Growth",        defaultVisible: true,  hideable: true  },
  { id: "narrative_score",    label: "Narrative",     defaultVisible: true,  hideable: true  },
  { id: "risk_score",         label: "Risk",          defaultVisible: true,  hideable: true  },
  { id: "listing_probability",label: "Listing P.",    defaultVisible: false, hideable: true  },
  { id: "market_cap",         label: "Mkt Cap",       defaultVisible: false, hideable: true  },
  { id: "volume_24h",         label: "Vol 24h",       defaultVisible: false, hideable: true  },
  { id: "price_change_7d",    label: "7d %",          defaultVisible: false, hideable: true  },
  { id: "signals",            label: "Signals",       defaultVisible: true,  hideable: true  },
];

const DEFAULT_VISIBLE = new Set<ColumnId>(
  ALL_COLUMNS.filter((c) => c.defaultVisible).map((c) => c.id),
);

/** Categories excluded from rankings by default. */
const DEFAULT_EXCLUDE_CATEGORIES = ["stablecoin", "wrapped-tokens"];

export type SortOrder = "asc" | "desc";

interface TableState {
  // ── Column visibility ───────────────────────────────────────────────
  visibleColumns: Set<ColumnId>;
  toggleColumn: (id: ColumnId) => void;
  resetColumns: () => void;

  // ── Server-side query state ─────────────────────────────────────────
  search: string;
  setSearch: (value: string) => void;

  categories: string[];
  setCategories: (value: string[]) => void;

  excludeCategories: string[];
  setExcludeCategories: (value: string[]) => void;

  sort: string;
  order: SortOrder;
  setSort: (column: string, order: SortOrder) => void;

  page: number;
  setPage: (page: number) => void;

  pageSize: number;
  setPageSize: (size: number) => void;

  resetFilters: () => void;
}

export const useTableStore = create<TableState>()(
  persist(
    (set) => ({
      // ── Column visibility ─────────────────────────────────────────
      visibleColumns: DEFAULT_VISIBLE,

      toggleColumn(id) {
        const col = ALL_COLUMNS.find((c) => c.id === id);
        if (!col?.hideable) return;
        set((s) => {
          const next = new Set(s.visibleColumns);
          if (next.has(id)) next.delete(id);
          else next.add(id);
          return { visibleColumns: next };
        });
      },

      resetColumns() {
        set({ visibleColumns: new Set(DEFAULT_VISIBLE) });
      },

      // ── Server-side query state ───────────────────────────────────
      search: "",
      setSearch(value) {
        set({ search: value, page: 1 });
      },

      categories: [],
      setCategories(value) {
        set({ categories: value, page: 1 });
      },

      excludeCategories: [...DEFAULT_EXCLUDE_CATEGORIES],
      setExcludeCategories(value) {
        set({ excludeCategories: value });
      },

      sort: "opportunity_score",
      order: "desc" as SortOrder,
      setSort(column, order) {
        set({ sort: column, order, page: 1 });
      },

      page: 1,
      setPage(page) {
        set({ page });
      },

      pageSize: 50,
      setPageSize(size) {
        set({ pageSize: size, page: 1 });
      },

      resetFilters() {
        set({
          search: "",
          categories: [],
          excludeCategories: [...DEFAULT_EXCLUDE_CATEGORIES],
          page: 1,
        });
      },
    }),
    {
      name: "table-columns",
      // Sets are not JSON-serialisable — store as array
      storage: {
        getItem: (key) => {
          const raw = localStorage.getItem(key);
          if (!raw) return null;
          const parsed = JSON.parse(raw) as { state: { visibleColumns: ColumnId[] } };
          return {
            ...parsed,
            state: {
              ...parsed.state,
              visibleColumns: new Set(parsed.state.visibleColumns),
            },
          };
        },
        setItem: (key, value) => {
          const serialisable = {
            ...value,
            state: {
              ...value.state,
              visibleColumns: Array.from(
                (value.state as TableState).visibleColumns,
              ),
            },
          };
          localStorage.setItem(key, JSON.stringify(serialisable));
        },
        removeItem: (key) => localStorage.removeItem(key),
      },
    },
  ),
);
