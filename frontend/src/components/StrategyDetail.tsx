import type { RankedScanResult } from "../api/scanner";
import { PayoffChart } from "./PayoffChart";

type StrategyDetailProps = {
  result: RankedScanResult;
  onClose: () => void;
};

const percent = (value: number | null) => value === null ? "—" : `${(value * 100).toFixed(1)}%`;
const money = (value: number | null) => value === null ? "—" : `$${value.toFixed(2)}`;
const title = (strategy: string) => strategy === "iron_condor" ? "Iron condor" : "Cash secured put";

export function StrategyDetail({ result, onClose }: StrategyDetailProps) {
  const candidate = result.candidate;
  return (
    <section className="strategy-detail" aria-label="Strategy detail">
      <div className="detail-header">
        <div>
          <p className="kicker">Rank {String(result.rank).padStart(2, "0")} / Strategy detail</p>
          <h2>{candidate.symbol} <em>{title(candidate.strategy)}</em></h2>
          <p>{candidate.expiration_date} expiration · read-only research view</p>
        </div>
        <button type="button" className="detail-close" onClick={onClose} aria-label="Close strategy detail">Close ×</button>
      </div>

      <div className="detail-metrics">
        <div><span>Credit</span><strong>{money(candidate.credit)}</strong></div>
        <div><span>Max profit</span><strong>{money(candidate.max_profit)}</strong></div>
        <div><span>Max loss</span><strong>{money(candidate.max_loss)}</strong></div>
        <div><span>POP</span><strong>{percent(candidate.probability_of_profit)}</strong></div>
        <div><span>ROC</span><strong>{percent(candidate.return_on_capital)}</strong></div>
        <div><span>Estimated EV</span><strong className={result.expected_value !== null && result.expected_value < 0 ? "negative" : "positive"}>{money(result.expected_value)}</strong></div>
      </div>

      <div className="detail-grid">
        <div className="chart-card">
          <div className="card-heading"><div><p className="kicker">At expiration</p><h3>Payoff profile</h3></div><span>P/L per contract</span></div>
          <PayoffChart points={candidate.payoff_points} breakEven={candidate.break_even} upperBreakEven={candidate.upper_break_even} symbol={candidate.symbol} />
        </div>

        <aside className="contract-card">
          <p className="kicker">Structure</p>
          <h3>{candidate.legs.length ? `${candidate.legs.length} option legs` : "Single short put"}</h3>
          {candidate.legs.length ? (
            <div className="leg-list">
              {candidate.legs.map((leg, index) => (
                <div key={`${leg.action}-${leg.right}-${leg.strike}-${index}`}>
                  <span className={`leg-action action-${leg.action.toLowerCase()}`}>{leg.action}</span>
                  <strong>{leg.right} {leg.strike}</strong>
                  <span>{money(leg.price)}</span>
                </div>
              ))}
            </div>
          ) : (
            <dl className="contract-facts">
              <div><dt>Strike</dt><dd>{money(candidate.strike)}</dd></div>
              <div><dt>Break-even</dt><dd>{money(candidate.break_even)}</dd></div>
              <div><dt>Open interest</dt><dd>{candidate.open_interest ?? "—"}</dd></div>
              <div><dt>Volume</dt><dd>{candidate.volume ?? "—"}</dd></div>
            </dl>
          )}
        </aside>
      </div>

      <div className="rule-grid">
        <RuleList title="Adjustment review" rules={candidate.adjustment_rules} />
        <RuleList title="Exit review" rules={candidate.exit_rules} />
      </div>
    </section>
  );
}

function RuleList({ title: ruleTitle, rules }: { title: string; rules: RankedScanResult["candidate"]["exit_rules"] }) {
  return (
    <section className="rule-card">
      <p className="kicker">Lifecycle rules</p>
      <h3>{ruleTitle}</h3>
      {rules.map((rule) => (
        <div className="rule-row" key={`${rule.trigger}-${rule.action}`}>
          <code>{rule.trigger}</code>
          <strong>{rule.action.split("_").join(" ")}</strong>
          <p>{rule.rationale}</p>
        </div>
      ))}
    </section>
  );
}
