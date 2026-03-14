/**
 * Alerts page — full implementation.
 *
 * Features:
 * - Stats bar: total, unacknowledged count
 * - Filter by alert type (select)
 * - Alert feed with type badge, message, timestamp
 * - "Acknowledge" button for unacknowledged alerts
 * - Error and empty states
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCheck, Bell } from "lucide-react";
import {
  fetchAlerts,
  fetchAlertStats,
  acknowledgeAlert,
  type Alert,
  type AlertType,
} from "@/services/alerts.service";
import { PageHeader } from "@/components/layout/PageHeader";
import { cn } from "@/lib/utils";

// ── helpers ────────────────────────────────────────────────────────────────

const TYPE_LABELS: Record<AlertType, string> = {
  LISTING_CANDIDATE:     "Listing Candidate",
  MEMECOIN_HYPE_DETECTED:"Memecoin Hype",
  WHALE_ACCUMULATION:    "Whale Accumulation",
  NARRATIVE_EMERGING:    "Narrative Emerging",
  RUGPULL_RISK:          "Rugpull Risk",
  TOKEN_UNLOCK_SOON:     "Token Unlock Soon",
  DAILY_REPORT:          "Daily Report",
  MANIPULATION_DETECTED: "Manipulation Detected",
};

const TYPE_COLOURS: Record<AlertType, string> = {
  LISTING_CANDIDATE:     "bg-green-500/10 text-green-400",
  MEMECOIN_HYPE_DETECTED:"bg-yellow-500/10 text-yellow-400",
  WHALE_ACCUMULATION:    "bg-blue-500/10 text-blue-400",
  NARRATIVE_EMERGING:    "bg-purple-500/10 text-purple-400",
  RUGPULL_RISK:          "bg-red-500/10 text-red-400",
  TOKEN_UNLOCK_SOON:     "bg-orange-500/10 text-orange-400",
  DAILY_REPORT:          "bg-muted text-muted-foreground",
  MANIPULATION_DETECTED: "bg-red-500/10 text-red-400",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── AlertRow sub-component ────────────────────────────────────────────────

function AlertRow({
  alert,
  onAcknowledge,
}: {
  alert: Alert;
  onAcknowledge: (id: number) => void;
}) {
  return (
    <li
      className={cn(
        "flex items-start justify-between gap-4 rounded-xl border border-border bg-card p-4",
        alert.acknowledged && "opacity-60",
      )}
    >
      <div className="flex flex-1 flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
              TYPE_COLOURS[alert.alert_type],
            )}
          >
            {TYPE_LABELS[alert.alert_type]}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate(alert.created_at)}
          </span>
          {alert.sent_telegram && (
            <span className="text-xs text-muted-foreground" aria-label="Sent via Telegram">
              📨
            </span>
          )}
        </div>
        <p className="text-sm text-foreground">{alert.message}</p>
      </div>

      <div className="shrink-0">
        {alert.acknowledged ? (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <CheckCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Acknowledged
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onAcknowledge(alert.id)}
            aria-label={`Acknowledge alert ${alert.id}`}
            className={cn(
              "flex items-center gap-1 rounded-md border border-border px-2.5 py-1",
              "text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
            )}
          >
            <CheckCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Acknowledge
          </button>
        )}
      </div>
    </li>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

const ALL_TYPES = "ALL" as const;
type FilterValue = typeof ALL_TYPES | AlertType;

export function Alerts() {
  const [filter, setFilter] = useState<FilterValue>(ALL_TYPES);
  const queryClient = useQueryClient();

  const {
    data: alerts = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(),
  });

  const { data: stats } = useQuery({
    queryKey: ["alert-stats"],
    queryFn: fetchAlertStats,
  });

  const { mutate: doAcknowledge } = useMutation<Alert, Error, number>({
    mutationFn: acknowledgeAlert,
    onSuccess: (updated: Alert) => {
      // Optimistically update the cached list
      queryClient.setQueryData<Alert[]>(["alerts"], (old = []) =>
        old.map((a: Alert) => (a.id === updated.id ? updated : a)),
      );
    },
  });

  const filtered: Alert[] =
    filter === ALL_TYPES
      ? alerts
      : alerts.filter((a: Alert) => a.alert_type === filter);

  return (
    <div>
      <PageHeader
        title="Alerts"
        description="Active and historical alert feed."
      />

      {/* ── Stats bar ──────────────────────────────────────────────────── */}
      {stats && (
        <div className="mb-6 flex flex-wrap gap-4" aria-label="Alert statistics">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3">
            <Bell className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <span className="text-xs text-muted-foreground">Total</span>
            <span className="font-numeric text-lg font-bold text-foreground">
              {stats.total}
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3">
            <span className="text-xs text-muted-foreground">Unacknowledged</span>
            <span className="font-numeric text-lg font-bold text-destructive">
              {stats.unacknowledged}
            </span>
          </div>
        </div>
      )}

      {/* ── Filter ─────────────────────────────────────────────────────── */}
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="alert-type-filter" className="text-sm text-muted-foreground">
          Filter by type
        </label>
        <select
          id="alert-type-filter"
          aria-label="Filter alerts by type"
          value={filter}
          onChange={(e) => setFilter(e.target.value as FilterValue)}
          className={cn(
            "rounded-md border border-border bg-card px-2 py-1 text-sm",
            "text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring",
          )}
        >
          <option value={ALL_TYPES}>All</option>
          {Object.entries(TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-xl border border-border bg-card"
              aria-hidden="true"
            />
          ))}
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {isError && (
        <p className="text-destructive" role="alert">
          Failed to load alerts. Make sure the backend is running.
        </p>
      )}

      {/* ── Empty ───────────────────────────────────────────────────────── */}
      {!isLoading && !isError && filtered.length === 0 && (
        <p className="text-sm text-muted-foreground">No alerts found.</p>
      )}

      {/* ── Alert list ──────────────────────────────────────────────────── */}
      {!isLoading && !isError && filtered.length > 0 && (
        <ul className="space-y-3" aria-label="Alert feed">
          {filtered.map((alert) => (
            <AlertRow
              key={alert.id}
              alert={alert}
              onAcknowledge={doAcknowledge}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
