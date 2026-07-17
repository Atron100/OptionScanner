import { getJson, postJson } from "./client";

export type TrackedUnderlying = {
  symbol: string;
  name: string | null;
  provider: string;
  underlying_price: number | null;
  as_of: string;
  quote_count: number;
};

export type TrackedUnderlyingsResponse = {
  count: number;
  underlyings: TrackedUnderlying[];
};

type IngestRequest = {
  symbol: string;
  expiration_count: number;
};

export type IngestResponse = {
  symbol: string;
  provider: string;
  snapshot_id: number;
  quote_count: number;
  underlying_price: number | null;
  warnings: string[];
};

export function getTrackedUnderlyings() {
  return getJson<TrackedUnderlyingsResponse>("/api/v1/market-data/underlyings");
}

export function ingestSymbol(symbol: string) {
  return postJson<IngestResponse, IngestRequest>("/api/v1/market-data/ingest", {
    symbol,
    expiration_count: 5,
  });
}
