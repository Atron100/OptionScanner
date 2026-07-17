import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import { DashboardPage } from "./DashboardPage";

vi.mock("../components/BackendStatusCard", () => ({
  BackendStatusCard: () => <div>Backend status card</div>,
}));

const trackedStocks = {
  count: 2,
  underlyings: [
    { symbol: "AAPL", name: "Apple", provider: "ibkr", underlying_price: 211.5, as_of: "2026-07-17T15:00:00Z", quote_count: 40 },
    { symbol: "OPEN", name: "Opendoor", provider: "ibkr", underlying_price: 4.38, as_of: "2026-07-17T15:01:00Z", quote_count: 32 },
  ],
};

const emptyHistory = { count: 0, runs: [] };

function jsonResponse(payload: unknown) {
  return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardPage", () => {
  it("renders stored stocks and selects one for scanning", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL) =>
      jsonResponse(String(input).includes("/scanner/history") ? emptyHistory : trackedStocks),
    ));
    const user = userEvent.setup();
    render(<DashboardPage />);
    expect(screen.getByText(/Find structure/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run scan/i })).toBeInTheDocument();
    expect(screen.getByText("Awaiting scan")).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: /AAPL.*211.50/i }));
    expect(screen.getByLabelText(/Symbols/i)).toHaveValue("AAPL");
  });

  it("submits a scan and renders ranked results", async () => {
    const scanResponse = {
        generated_at: "2026-07-17T15:00:00Z",
        symbols: ["OPEN"], strategies: ["cash_secured_put"],
        total_candidates: 3, eligible_candidate_count: 1, filtered_out_count: 2, result_count: 1, warnings: [],
        results: [{ rank: 1, expected_value: -90, candidate: {
          strategy: "cash_secured_put", symbol: "OPEN", expiration_date: "2026-07-31", strike: 4,
          credit: 0.1, max_profit: 10, max_loss: 390, break_even: 3.9, upper_break_even: null,
          probability_of_profit: 0.75, return_on_capital: 0.025, score: 54.2,
          open_interest: 1200, volume: 42, legs: [],
          payoff_points: [
            { underlying_price: 0, profit_loss: -390 },
            { underlying_price: 3.9, profit_loss: 0 },
            { underlying_price: 5, profit_loss: 10 },
          ],
          adjustment_rules: [{
            trigger: "underlying_price <= 4",
            action: "review_roll_or_assignment",
            rationale: "Review the challenged short put.",
          }],
          exit_rules: [{
            trigger: "remaining_option_value <= 0.0500",
            action: "review_close_for_profit",
            rationale: "Review captured premium.",
          }],
        }}],
      };
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/scanner/scan")) return jsonResponse(scanResponse);
      if (url.includes("/scanner/history")) return jsonResponse(emptyHistory);
      return jsonResponse(trackedStocks);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(screen.getByRole("button", { name: /Run scan/i }));

    await waitFor(() => expect(screen.getAllByText("Cash secured put").length).toBeGreaterThanOrEqual(2));
    expect(screen.getByText("54.2")).toBeInTheDocument();
    expect(screen.getByText("Eligible")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "OPEN payoff at expiration" })).toBeInTheDocument();
    expect(screen.getByText("Adjustment review")).toBeInTheDocument();
    expect(screen.getByText("review close for profit")).toBeInTheDocument();
    const scannerCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/api/v1/scanner/scan"));
    expect(scannerCall).toBeDefined();
    const request = JSON.parse(scannerCall?.[1]?.body as string);
    expect(request.symbols).toEqual(["OPEN"]);
    expect(request.minimum_days_to_expiration).toBe(1);

    await user.click(screen.getByRole("button", { name: "Close strategy detail" }));
    expect(screen.queryByLabelText("Strategy detail")).not.toBeInTheDocument();
  });

  it("ingests the active symbol and reloads tracked stocks", async () => {
    let stockLoads = 0;
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/market-data/ingest")) {
        return jsonResponse({ symbol: "OPEN", provider: "ibkr", snapshot_id: 9, quote_count: 36, underlying_price: 4.42, warnings: [] });
      }
      if (url.includes("/scanner/history")) return jsonResponse(emptyHistory);
      stockLoads += 1;
      return jsonResponse(trackedStocks);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(await screen.findByRole("button", { name: "Add / refresh OPEN" }));

    expect(await screen.findByText("OPEN updated with 36 option quotes.")).toBeInTheDocument();
    expect(stockLoads).toBe(2);
    const ingestCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/api/v1/market-data/ingest"));
    expect(JSON.parse(ingestCall?.[1]?.body as string)).toEqual({ symbol: "OPEN", expiration_count: 5 });
  });

  it("restores controls and exact results from scan history", async () => {
    const historyList = {
      count: 1,
      runs: [{
        id: 7,
        generated_at: "2026-07-17T14:30:00Z",
        symbols: ["AAPL"],
        strategies: ["cash_secured_put"],
        total_candidates: 4,
        result_count: 0,
      }],
    };
    const historyDetail = {
      id: 7,
      request: {
        symbols: ["AAPL"], strategies: ["cash_secured_put"],
        minimum_probability_of_profit: 0.65,
        minimum_days_to_expiration: 7, maximum_days_to_expiration: 30,
        minimum_credit: 0.2, minimum_open_interest: 100, minimum_volume: 10, limit: 12,
      },
      response: {
        generated_at: "2026-07-17T14:30:00Z",
        symbols: ["AAPL"], strategies: ["cash_secured_put"],
        total_candidates: 4, eligible_candidate_count: 0, filtered_out_count: 4, result_count: 0,
        warnings: [], results: [],
      },
    };
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/scanner/history/7")) return jsonResponse(historyDetail);
      if (url.includes("/scanner/history")) return jsonResponse(historyList);
      return jsonResponse(trackedStocks);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(await screen.findByRole("button", { name: /Run #007.*AAPL/i }));

    expect(screen.getByLabelText(/Symbols/i)).toHaveValue("AAPL");
    expect(screen.getByLabelText(/Minimum POP/i)).toHaveValue(65);
    expect(screen.getByLabelText(/Minimum DTE/i)).toHaveValue(7);
    expect(screen.getByText("No candidates passed.")).toBeInTheDocument();
  });
});
