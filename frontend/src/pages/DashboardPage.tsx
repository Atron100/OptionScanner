import { useEffect, useState, type FormEvent } from "react";

import { getTrackedUnderlyings, ingestSymbol, type TrackedUnderlying } from "../api/marketData";
import { getScanHistory, getScanHistoryRun, runScan, type RankedScanResult, type ScanHistorySummary, type ScanRequest, type ScanResponse } from "../api/scanner";
import { BackendStatusCard } from "../components/BackendStatusCard";
import { ScanConsole, type ScanFormValues } from "../components/ScanConsole";
import { ScanHistoryPanel } from "../components/ScanHistoryPanel";
import { ScanResults } from "../components/ScanResults";
import { StrategyDetail } from "../components/StrategyDetail";
import { TrackedStocksPanel } from "../components/TrackedStocksPanel";

const initialValues: ScanFormValues = {
  symbols: "OPEN",
  strategies: ["cash_secured_put", "iron_condor"],
  minimumPop: "",
  minimumDte: "1",
  maximumDte: "45",
  minimumCredit: "0.05",
  minimumOpenInterest: "0",
  minimumVolume: "0",
  limit: "20",
};

export function DashboardPage() {
  const [values, setValues] = useState(initialValues);
  const [response, setResponse] = useState<ScanResponse | null>(null);
  const [selectedResult, setSelectedResult] = useState<RankedScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stocks, setStocks] = useState<TrackedUnderlying[]>([]);
  const [stocksLoading, setStocksLoading] = useState(true);
  const [refreshingStock, setRefreshingStock] = useState(false);
  const [stockMessage, setStockMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<ScanHistorySummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [openingHistoryId, setOpeningHistoryId] = useState<number | null>(null);
  const activeSymbol = values.symbols.split(/[\s,]+/)[0]?.trim().toUpperCase() ?? "";

  async function loadStocks() {
    const payload = await getTrackedUnderlyings();
    setStocks(payload.underlyings);
  }

  async function loadHistory() {
    const payload = await getScanHistory();
    setHistory(payload.runs);
  }

  useEffect(() => {
    let active = true;
    getTrackedUnderlyings()
      .then((payload) => {
        if (active) setStocks(payload.underlyings);
      })
      .catch(() => {
        if (active) setStockMessage("Stored stocks could not be loaded. Confirm the backend is running.");
      })
      .finally(() => {
        if (active) setStocksLoading(false);
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    getScanHistory()
      .then((payload) => {
        if (active) setHistory(payload.runs);
      })
      .catch(() => {
        if (active) setHistoryError("Scan history could not be loaded.");
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => { active = false; };
  }, []);

  function handleSelectStock(symbol: string) {
    setValues((current) => ({ ...current, symbols: symbol }));
    setResponse(null);
    setSelectedResult(null);
    setError(null);
  }

  async function handleRefreshStock() {
    if (!activeSymbol) return;
    setRefreshingStock(true);
    setStockMessage(null);
    try {
      const result = await ingestSymbol(activeSymbol);
      await loadStocks();
      setStockMessage(`${result.symbol} updated with ${result.quote_count} option quotes.`);
    } catch (refreshError) {
      setStockMessage(refreshError instanceof Error ? refreshError.message : "Market data refresh failed.");
    } finally {
      setRefreshingStock(false);
      setStocksLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const symbols = values.symbols.split(/[\s,]+/).map((symbol) => symbol.trim()).filter(Boolean);
    if (symbols.length === 0 || values.strategies.length === 0) {
      setError("Enter at least one symbol and select one strategy.");
      return;
    }
    const request: ScanRequest = {
      symbols,
      strategies: values.strategies,
      minimum_days_to_expiration: Number(values.minimumDte || 0),
      minimum_credit: Number(values.minimumCredit || 0),
      minimum_open_interest: Number(values.minimumOpenInterest || 0),
      minimum_volume: Number(values.minimumVolume || 0),
      limit: Number(values.limit || 20),
    };
    if (values.minimumPop) request.minimum_probability_of_profit = Number(values.minimumPop) / 100;
    if (values.maximumDte) request.maximum_days_to_expiration = Number(values.maximumDte);

    setLoading(true);
    setError(null);
    try {
      const scanResponse = await runScan(request);
      setResponse(scanResponse);
      setSelectedResult(scanResponse.results[0] ?? null);
      await loadHistory();
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Scanner request failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleOpenHistory(runId: number) {
    setOpeningHistoryId(runId);
    setHistoryError(null);
    try {
      const detail = await getScanHistoryRun(runId);
      const request = detail.request;
      setValues({
        symbols: request.symbols.join(", "),
        strategies: request.strategies,
        minimumPop: request.minimum_probability_of_profit === undefined ? "" : String(request.minimum_probability_of_profit * 100),
        minimumDte: String(request.minimum_days_to_expiration),
        maximumDte: request.maximum_days_to_expiration === undefined ? "" : String(request.maximum_days_to_expiration),
        minimumCredit: String(request.minimum_credit),
        minimumOpenInterest: String(request.minimum_open_interest),
        minimumVolume: String(request.minimum_volume),
        limit: String(request.limit),
      });
      setResponse(detail.response);
      setSelectedResult(detail.response.results[0] ?? null);
      setError(null);
    } catch (historyRequestError) {
      setHistoryError(historyRequestError instanceof Error ? historyRequestError.message : "Stored scan could not be opened.");
    } finally {
      setOpeningHistoryId(null);
    }
  }

  return (
    <main className="page-shell">
      <header className="masthead">
        <a className="brand" href="/" aria-label="OptionScanner home"><span>Option</span><strong>Scanner</strong></a>
        <p>Read-only options research terminal</p>
        <BackendStatusCard />
      </header>
      <section className="hero-panel">
        <div><p className="eyebrow">Phase 04 / Scanner</p><h1>Find structure<br /><em>inside the chain.</em></h1></div>
        <p className="hero-copy">Rank stored option chains by probability, capital efficiency, risk, and liquidity. No orders. No hidden automation.</p>
      </section>
      <TrackedStocksPanel
        stocks={stocks}
        activeSymbol={activeSymbol}
        loading={stocksLoading}
        refreshing={refreshingStock}
        message={stockMessage}
        onSelect={handleSelectStock}
        onRefresh={handleRefreshStock}
      />
      {error ? <div className="page-error" role="alert">{error}</div> : null}
      <div className="dashboard-grid">
        <ScanConsole values={values} loading={loading} onChange={setValues} onSubmit={handleSubmit} />
        <ScanResults response={response} loading={loading} selectedResult={selectedResult} onSelect={setSelectedResult} />
      </div>
      <ScanHistoryPanel runs={history} loading={historyLoading} openingId={openingHistoryId} error={historyError} onOpen={handleOpenHistory} />
      {selectedResult ? <StrategyDetail result={selectedResult} onClose={() => setSelectedResult(null)} /> : null}
      <footer><span>OptionScanner / Local research only</span><span>Data source: latest stored snapshot</span></footer>
    </main>
  );
}
