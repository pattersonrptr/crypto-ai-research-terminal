import { apiClient } from "./api";

export type ReportFormat = "markdown" | "pdf";

// ── Service functions ──────────────────────────────────────────────────────

/**
 * Fetch a token report.
 * For markdown: returns text.  For pdf: returns a Blob for download.
 */
export async function fetchTokenReport(
  symbol: string,
  format: ReportFormat = "markdown",
): Promise<string | Blob> {
  const res = await apiClient.get(`/reports/token/${symbol}`, {
    params: { format },
    responseType: format === "pdf" ? "blob" : "text",
  });
  return res.data as string | Blob;
}

/**
 * Fetch the latest market report.
 */
export async function fetchMarketReport(
  format: ReportFormat = "markdown",
): Promise<string | Blob> {
  const res = await apiClient.get("/reports/market", {
    params: { format },
    responseType: format === "pdf" ? "blob" : "text",
  });
  return res.data as string | Blob;
}

/**
 * Trigger a browser download for a PDF blob.
 */
export function downloadPdf(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
