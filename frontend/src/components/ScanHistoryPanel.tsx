import type { ScanHistorySummary } from "../api/scanner";

type ScanHistoryPanelProps = {
  runs: ScanHistorySummary[];
  loading: boolean;
  openingId: number | null;
  error: string | null;
  onOpen: (runId: number) => void;
};

function strategyLabel(strategies: ScanHistorySummary["strategies"]) {
  return strategies.map((strategy) => strategy === "cash_secured_put" ? "CSP" : "IC").join(" + ");
}

export function ScanHistoryPanel({ runs, loading, openingId, error, onOpen }: ScanHistoryPanelProps) {
  return (
    <section className="history-panel" aria-labelledby="scan-history-heading">
      <div className="history-heading">
        <div><p className="kicker">Saved locally</p><h2 id="scan-history-heading">Recent scans</h2></div>
        <span>Exact stored results / newest first</span>
      </div>
      {error ? <p className="history-error" role="status">{error}</p> : null}
      {loading ? <p className="history-empty">Loading scan history...</p> : null}
      {!loading && runs.length === 0 ? <p className="history-empty">Run the scanner to create the first history entry.</p> : null}
      {runs.length > 0 ? (
        <div className="history-strip">
          {runs.map((run) => (
            <button type="button" className="history-card" key={run.id} onClick={() => onOpen(run.id)} disabled={openingId === run.id}>
              <span className="history-run">Run #{String(run.id).padStart(3, "0")}</span>
              <time dateTime={run.generated_at}>{new Date(run.generated_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</time>
              <strong>{run.symbols.join(" / ")}</strong>
              <span>{strategyLabel(run.strategies)} · {run.result_count} shown / {run.total_candidates} raw</span>
              <em>{openingId === run.id ? "Opening..." : "Review stored result"}</em>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
