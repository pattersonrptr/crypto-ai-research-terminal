import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types (mirror backend CollectNowResponse / JobStatusResponse) ──────────

export interface CollectNowResponse {
  job_id: string;
  status: string;
}

export interface PipelineStatusResponse {
  job_id: string;
  status: string;
  detail: string;
}

// ── Service functions ──────────────────────────────────────────────────────

export async function triggerCollectNow(): Promise<CollectNowResponse> {
  const res: AxiosResponse<CollectNowResponse> = await apiClient.post(
    "/pipeline/collect-now",
  );
  return res.data;
}

export async function fetchPipelineStatus(
  jobId: string,
): Promise<PipelineStatusResponse> {
  const res: AxiosResponse<PipelineStatusResponse> = await apiClient.get(
    `/pipeline/status/${jobId}`,
  );
  return res.data;
}
