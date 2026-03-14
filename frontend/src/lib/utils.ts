import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes without conflicts.
 * Usage: cn("px-4 py-2", isActive && "bg-primary", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as a compact USD price.
 * e.g. 1234567 → "$1.23M"
 */
export function formatUsd(value: number): string {
  if (value >= 1_000_000_000)
    return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

/**
 * Format a score (0–10) to one decimal place.
 */
export function formatScore(value: number): string {
  return value.toFixed(1);
}

/**
 * Return a Tailwind colour class based on a 0–10 score.
 */
export function scoreColour(score: number): string {
  if (score >= 7) return "text-score-high";
  if (score >= 4) return "text-score-mid";
  return "text-score-low";
}

/**
 * Return a Tailwind colour class for risk level strings.
 */
export function riskColour(risk: "low" | "medium" | "high"): string {
  const map: Record<string, string> = {
    low: "text-risk-low",
    medium: "text-risk-medium",
    high: "text-risk-high",
  };
  return map[risk] ?? "text-muted-foreground";
}

/**
 * Format a percentage change with sign.
 * e.g. 0.123 → "+12.3%"
 */
export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(1)}%`;
}
