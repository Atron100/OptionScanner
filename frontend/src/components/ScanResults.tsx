import type { RankedScanResult, ScanResponse, StrategyCandidate } from "../api/scanner";

type ScanResultsProps = {
  response: ScanResponse | null;
  loading: boolean;
  selectedResult: RankedScanResult | null;
  onSelect: (result: RankedScanResult) => void;
};

function percent(value: number | null) {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function money(value: number | null) {
  return value === null ? "—" : `$${value.toFixed(2)}`;
}

function strategyName(strategy: string) {
  return strategy === "iron_condor" ? "Iron condor" : "Cash secured put";
}

function strikeLabel(candidate: StrategyCandidate) {
  if (candidate.legs.length === 0) return `$${candidate.strike.toFixed(2)}`;
  return candidate.legs
    .map((leg) => `${leg.action === "BUY" ? "+" : "−"}${Number.isInteger(leg.strike) ? leg.strike : leg.strike.toFixed(2)}`)
    .join(" / ");
}

export function ScanResults({ response, loading, selectedResult, onSelect }: ScanResultsProps) {
  if (!response) {
    return (
      <section className="results-panel empty-results" aria-live="polite">
        <div className="empty-orbit" aria-hidden="true"><span>OS</span></div>
        <p className="kicker">Awaiting scan</p>
        <h2>Stored chains, ranked clearly.</h2>
        <p>Choose a symbol field and run the scanner. Results stay local and read-only.</p>
      </section>
    );
  }

  return (
    <section className="results-panel" aria-busy={loading} aria-live="polite">
      <div className="results-heading">
        <div>
          <p className="kicker">Ranked opportunities</p>
          <h2>{response.symbols.join(" · ")}</h2>
        </div>
        <time dateTime={response.generated_at}>{new Date(response.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
      </div>

      <div className="scan-metrics">
        <div><span>Raw</span><strong>{response.total_candidates}</strong></div>
        <div><span>Eligible</span><strong>{response.eligible_candidate_count}</strong></div>
        <div><span>Filtered</span><strong>{response.filtered_out_count}</strong></div>
        <div><span>Shown</span><strong>{response.result_count}</strong></div>
      </div>

      {response.warnings.map((warning) => <p className="warning-banner" key={warning}>{warning}</p>)}

      {response.results.length === 0 ? (
        <div className="no-results"><strong>No candidates passed.</strong><span>Relax one or more quality filters and scan again.</span></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Rank</th><th>Setup</th><th>Expiry</th><th>Strike / legs</th><th>Credit</th><th>POP</th><th>ROC</th><th>Score</th><th>EV</th><th>Liquidity</th></tr>
            </thead>
            <tbody>
              {response.results.map((result) => (
                <tr className={selectedResult?.rank === result.rank ? "selected-row" : ""} key={`${result.rank}-${result.candidate.strategy}-${result.candidate.expiration_date}-${result.candidate.strike}`}>
                  <td><span className="rank-badge">{String(result.rank).padStart(2, "0")}</span></td>
                  <td><button type="button" className="setup-button" onClick={() => onSelect(result)}><strong>{strategyName(result.candidate.strategy)}</strong><small>{result.candidate.symbol} · View detail</small></button></td>
                  <td>{new Date(`${result.candidate.expiration_date}T00:00:00`).toLocaleDateString([], { month: "short", day: "numeric" })}</td>
                  <td className="mono strike-cell">{strikeLabel(result.candidate)}</td>
                  <td className="mono">{money(result.candidate.credit)}</td>
                  <td>{percent(result.candidate.probability_of_profit)}</td>
                  <td>{percent(result.candidate.return_on_capital)}</td>
                  <td><span className="score-pill">{result.candidate.score.toFixed(1)}</span></td>
                  <td className={result.expected_value !== null && result.expected_value < 0 ? "negative" : "positive"}>{money(result.expected_value)}</td>
                  <td><span className="liquidity">OI {result.candidate.open_interest ?? "—"}<br />V {result.candidate.volume ?? "—"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
