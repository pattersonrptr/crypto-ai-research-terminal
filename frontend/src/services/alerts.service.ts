import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types ──────────────────────────────────────────────────────────────────

export type AlertType =
  | "LISTING_CANDIDATE"
  | "MEMECOIN_HYPE_DETECTED"
  | "WHALE_ACCUMULATION"
  | "NARRATIVE_EMERGING"
  | "RUGPULL_RISK"
  | "TOKEN_UNLOCK_SOON"
  | "DAILY_REPORT"
  | "MANIPULATION_DETECTED";

export interface Alert {
  id: number;
  token_id: number | null;
  alert_type: AlertType;
  message: string;
  metadata: Record<string, unknown>;
  sent_telegram: boolean;
  acknowledged: boolean;
  created_at: string;
}

export interface AlertStats {
  total: number;
  by_type: Record<AlertType, number>;
  unacknowledged: number;
}

export interface AlertsListParams {
  limit?: number;
  alert_type?: AlertType;
  acknowledged?: boolean;
}

// ── Service functions ──────────────────────────────────────────────────────

export async function fetchAlerts(
  params: AlertsListParams = {},
): Promise<Alert[]> {
  const res: AxiosResponse<Alert[]> = await apiClient.get("/alerts/", {
    params,
  });
  return res.data;
}

export async function fetchAlertStats(): Promise<AlertStats> {
  const res: AxiosResponse<AlertStats> = await apiClient.get("/alerts/stats");
  return res.data;
}

export async function acknowledgeAlert(alertId: number): Promise<Alert> {
  const res: AxiosResponse<Alert> = await apiClient.put(
    `/alerts/${alertId}/acknowledge`,
  );
  return res.data;
}

export async function sendTestAlert(): Promise<{ status: string }> {
  const res: AxiosResponse<{ status: string }> = await apiClient.post(
    "/alerts/test",
  );
  return res.data;
}
