import type { AxiosResponse } from "axios";
import { apiClient } from "./api";

// ── Types (mirror backend Pydantic schemas) ────────────────────────────────

export interface TokenScore {
  fundamental_score: number;
  technology_score: number;
  tokenomics_score: number;
  adoption_score: number;
  dev_activity_score: number;
  narrative_score: number;
  growth_score: number;
  risk_score: number;
  listing_probability: number;
  cycle_leader_prob: number;
  opportunity_score: number;
  snapshot_date: string;
}

export interface Token {
  id: number;
  symbol: string;
  name: string;
  coingecko_id: string | null;
  category: string | null;
  github_repo: string | null;
  whitepaper_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenWithScore extends Token {
  latest_score: TokenScore | null;
  price_usd: number | null;
  market_cap: number | null;
  volume_24h: number | null;
  price_change_7d: number | null;
  rank: number | null;
}

export interface RankingOpportunity {
  rank: number;
  token: TokenWithScore;
  signals: string[];
}

export interface TokensListParams {
  skip?: number;
  limit?: number;
  category?: string;
}

export interface RankingsParams {
  categories?: string;
  exclude_categories?: string;
  sort?: string;
  order?: "asc" | "desc";
  search?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedRankingsResponse {
  data: RankingOpportunity[];
  total_count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface PillarExplanation {
  pillar: string;
  score: number;
  explanation: string;
}

export interface ExplanationResponse {
  symbol: string;
  name: string;
  opportunity_score: number;
  explanations: PillarExplanation[];
}

// ── Service functions ──────────────────────────────────────────────────────

export async function fetchTokens(
  params: TokensListParams = {},
): Promise<TokenWithScore[]> {
  const res: AxiosResponse<TokenWithScore[]> = await apiClient.get("/tokens", {
    params,
  });
  return res.data;
}

export async function fetchToken(symbol: string): Promise<TokenWithScore> {
  const res: AxiosResponse<TokenWithScore> = await apiClient.get(
    `/tokens/${symbol}`,
  );
  return res.data;
}

export async function fetchRankingOpportunities(
  params: RankingsParams = {},
): Promise<PaginatedRankingsResponse> {
  const res: AxiosResponse<PaginatedRankingsResponse> = await apiClient.get(
    "/rankings/opportunities",
    { params },
  );
  return res.data;
}

export async function fetchCategories(): Promise<CategoryCount[]> {
  const res: AxiosResponse<CategoryCount[]> = await apiClient.get(
    "/rankings/categories",
  );
  return res.data;
}

export async function fetchTokenExplanation(
  symbol: string,
): Promise<ExplanationResponse> {
  const res: AxiosResponse<ExplanationResponse> = await apiClient.get(
    `/tokens/${symbol}/explanation`,
  );
  return res.data;
}
