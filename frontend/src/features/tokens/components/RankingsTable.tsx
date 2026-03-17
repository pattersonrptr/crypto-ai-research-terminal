import { Link } from "react-router-dom";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import type { RankingOpportunity } from "@/services/tokens.service";
import { cn, formatScore, formatUsd, formatPct, scoreColour } from "@/lib/utils";

// ── Props ────────────────────────────────────────────────────────────────

interface RankingsTableProps {
  data: RankingOpportunity[];
  sort: string;
  order: "asc" | "desc";
  onSortChange: (column: string) => void;
}

// ── Helpers ──────────────────────────────────────────────────────────────

/** Scale 0–1 score to 0–10 and format. */
function fmtScore(value: number | null | undefined): string {
  if (value == null) return "—";
  return formatScore(value * 10);
}

function ScoreCell({ value }: { value: number | null | undefined }) {
  const scaled = value != null ? value * 10 : null;
  return (
    <span
      className={cn(
        "font-numeric text-sm font-semibold",
        scaled != null ? scoreColour(scaled) : "text-muted-foreground",
      )}
    >
      {fmtScore(value)}
    </span>
  );
}

// ── Column definitions ──────────────────────────────────────────────────

const col = createColumnHelper<RankingOpportunity>();

const SORTABLE_COLUMNS: Record<string, string> = {
  rank: "token_rank",
  opportunity_score: "opportunity_score",
  fundamental_score: "fundamental_score",
  growth_score: "growth_score",
  narrative_score: "narrative_score",
  risk_score: "risk_score",
  market_cap: "market_cap",
  volume_24h: "volume_24h",
};

const columns = [
  col.accessor("rank", {
    id: "rank",
    header: "#",
    cell: (info) => (
      <span className="font-numeric text-xs font-semibold text-muted-foreground">
        {info.getValue()}
      </span>
    ),
    meta: { sortKey: "token_rank" },
  }),
  col.accessor((row) => row.token.symbol, {
    id: "symbol",
    header: "Symbol",
    cell: (info) => {
      const symbol = info.getValue();
      return (
        <Link
          to={`/tokens/${symbol}`}
          className="font-mono text-sm font-bold text-foreground hover:text-primary"
          aria-label={`${symbol} details`}
        >
          {symbol}
        </Link>
      );
    },
  }),
  col.accessor((row) => row.token.name, {
    id: "name",
    header: "Name",
    cell: (info) => (
      <span className="text-sm text-muted-foreground">{info.getValue()}</span>
    ),
  }),
  col.accessor((row) => row.token.category, {
    id: "category",
    header: "Category",
    cell: (info) => {
      const cat = info.getValue();
      if (!cat) return <span className="text-muted-foreground">—</span>;
      return (
        <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
          {cat}
        </span>
      );
    },
  }),
  col.accessor((row) => row.token.latest_score?.opportunity_score ?? null, {
    id: "opportunity_score",
    header: "Score",
    cell: (info) => <ScoreCell value={info.getValue()} />,
    meta: { sortKey: "opportunity_score" },
  }),
  col.accessor((row) => row.token.latest_score?.fundamental_score ?? null, {
    id: "fundamental_score",
    header: "Fund.",
    cell: (info) => <ScoreCell value={info.getValue()} />,
    meta: { sortKey: "fundamental_score" },
  }),
  col.accessor((row) => row.token.latest_score?.growth_score ?? null, {
    id: "growth_score",
    header: "Growth",
    cell: (info) => <ScoreCell value={info.getValue()} />,
    meta: { sortKey: "growth_score" },
  }),
  col.accessor((row) => row.token.latest_score?.narrative_score ?? null, {
    id: "narrative_score",
    header: "Narrative",
    cell: (info) => <ScoreCell value={info.getValue()} />,
    meta: { sortKey: "narrative_score" },
  }),
  col.accessor((row) => row.token.latest_score?.risk_score ?? null, {
    id: "risk_score",
    header: "Risk",
    cell: (info) => <ScoreCell value={info.getValue()} />,
    meta: { sortKey: "risk_score" },
  }),
  col.accessor((row) => row.token.market_cap, {
    id: "market_cap",
    header: "Mkt Cap",
    cell: (info) => {
      const v = info.getValue();
      return (
        <span className="font-numeric text-xs text-muted-foreground">
          {v != null ? formatUsd(v) : "—"}
        </span>
      );
    },
    meta: { sortKey: "market_cap" },
  }),
  col.accessor((row) => row.token.volume_24h, {
    id: "volume_24h",
    header: "Vol 24h",
    cell: (info) => {
      const v = info.getValue();
      return (
        <span className="font-numeric text-xs text-muted-foreground">
          {v != null ? formatUsd(v) : "—"}
        </span>
      );
    },
    meta: { sortKey: "volume_24h" },
  }),
  col.accessor((row) => row.token.price_change_7d, {
    id: "price_change_7d",
    header: "7d %",
    cell: (info) => {
      const v = info.getValue();
      if (v == null) return <span className="text-muted-foreground">—</span>;
      const colour =
        v > 0 ? "text-score-high" : v < 0 ? "text-score-low" : "text-muted-foreground";
      return (
        <span className={cn("font-numeric text-xs font-medium", colour)}>
          {formatPct(v)}
        </span>
      );
    },
  }),
  col.accessor("signals", {
    id: "signals",
    header: "Signals",
    cell: (info) => {
      const sigs = info.getValue();
      if (!sigs.length) return null;
      return (
        <div className="flex flex-wrap gap-1">
          {sigs.map((s) => (
            <span
              key={s}
              className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary"
            >
              {s}
            </span>
          ))}
        </div>
      );
    },
  }),
];

// ── Component ────────────────────────────────────────────────────────────

export function RankingsTable({
  data,
  sort,
  order,
  onSortChange,
}: RankingsTableProps) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
  });

  function SortIcon({ columnId }: { columnId: string }) {
    const meta = columns.find((c) => c.id === columnId)?.meta as
      | { sortKey?: string }
      | undefined;
    const sortKey = meta?.sortKey ?? columnId;
    if (sortKey !== sort) {
      return <ArrowUpDown className="ml-1 inline h-3 w-3 text-muted-foreground" />;
    }
    return order === "asc" ? (
      <ArrowUp className="ml-1 inline h-3 w-3" />
    ) : (
      <ArrowDown className="ml-1 inline h-3 w-3" />
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full border-collapse text-sm" role="table">
        <thead className="border-b border-border bg-muted/50">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => {
                const meta = header.column.columnDef.meta as
                  | { sortKey?: string }
                  | undefined;
                const sortKey = meta?.sortKey ?? header.column.id;
                const isSortable = sortKey in SORTABLE_COLUMNS || meta?.sortKey;

                return (
                  <th
                    key={header.id}
                    className={cn(
                      "whitespace-nowrap px-3 py-2 text-left text-xs font-medium text-muted-foreground",
                      isSortable && "cursor-pointer select-none hover:text-foreground",
                    )}
                    onClick={
                      isSortable
                        ? () =>
                            onSortChange(
                              meta?.sortKey ?? SORTABLE_COLUMNS[header.column.id] ?? header.column.id,
                            )
                        : undefined
                    }
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
                    {isSortable && <SortIcon columnId={header.column.id} />}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="py-8 text-center text-sm text-muted-foreground"
              >
                No results found.
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-border/50 transition-colors hover:bg-muted/30"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="whitespace-nowrap px-3 py-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
