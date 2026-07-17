import { getJson, postJson } from "./client";

export type ScannableStrategy = "cash_secured_put" | "iron_condor";

export type ScanRequest = {
  symbols: string[];
  strategies: ScannableStrategy[];
  minimum_probability_of_profit?: number;
  minimum_days_to_expiration: number;
  maximum_days_to_expiration?: number;
  minimum_credit: number;
  minimum_open_interest: number;
  minimum_volume: number;
  limit: number;
};

type StrategyLeg = {
  action: string;
  right: string;
  strike: number;
  price: number;
  delta: number | null;
};

export type PayoffPoint = {
  underlying_price: number;
  profit_loss: number;
};

export type ManagementRule = {
  trigger: string;
  action: string;
  rationale: string;
};

export type StrategyCandidate = {
  strategy: string;
  symbol: string;
  expiration_date: string;
  strike: number;
  credit: number;
  max_profit: number;
  max_loss: number;
  break_even: number;
  upper_break_even: number | null;
  probability_of_profit: number | null;
  return_on_capital: number | null;
  score: number;
  open_interest: number | null;
  volume: number | null;
  legs: StrategyLeg[];
  payoff_points: PayoffPoint[];
  adjustment_rules: ManagementRule[];
  exit_rules: ManagementRule[];
};

export type RankedScanResult = {
  rank: number;
  expected_value: number | null;
  candidate: StrategyCandidate;
};

export type ScanResponse = {
  generated_at: string;
  symbols: string[];
  strategies: ScannableStrategy[];
  total_candidates: number;
  eligible_candidate_count: number;
  filtered_out_count: number;
  result_count: number;
  warnings: string[];
  results: RankedScanResult[];
};

export type ScanHistorySummary = {
  id: number;
  generated_at: string;
  symbols: string[];
  strategies: ScannableStrategy[];
  total_candidates: number;
  result_count: number;
};

export type ScanHistoryListResponse = {
  count: number;
  runs: ScanHistorySummary[];
};

export type ScanHistoryDetailResponse = {
  id: number;
  request: ScanRequest;
  response: ScanResponse;
};

export function runScan(request: ScanRequest) {
  return postJson<ScanResponse, ScanRequest>("/api/v1/scanner/scan", request);
}

export function getScanHistory(limit = 10) {
  return getJson<ScanHistoryListResponse>(`/api/v1/scanner/history?limit=${limit}`);
}

export function getScanHistoryRun(runId: number) {
  return getJson<ScanHistoryDetailResponse>(`/api/v1/scanner/history/${runId}`);
}
