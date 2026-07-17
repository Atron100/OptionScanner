import type { FormEvent } from "react";

import type { ScannableStrategy } from "../api/scanner";

export type ScanFormValues = {
  symbols: string;
  strategies: ScannableStrategy[];
  minimumPop: string;
  minimumDte: string;
  maximumDte: string;
  minimumCredit: string;
  minimumOpenInterest: string;
  minimumVolume: string;
  limit: string;
};

type ScanConsoleProps = {
  values: ScanFormValues;
  loading: boolean;
  onChange: (values: ScanFormValues) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

const strategyOptions: Array<{ value: ScannableStrategy; label: string; code: string }> = [
  { value: "cash_secured_put", label: "Cash secured put", code: "CSP" },
  { value: "iron_condor", label: "Iron condor", code: "IC" },
];

export function ScanConsole({ values, loading, onChange, onSubmit }: ScanConsoleProps) {
  function update<K extends keyof ScanFormValues>(key: K, value: ScanFormValues[K]) {
    onChange({ ...values, [key]: value });
  }

  function toggleStrategy(strategy: ScannableStrategy) {
    const selected = values.strategies.includes(strategy)
      ? values.strategies.filter((item) => item !== strategy)
      : [...values.strategies, strategy];
    update("strategies", selected);
  }

  return (
    <form className="scan-console" onSubmit={onSubmit}>
      <div className="console-heading">
        <span className="section-index">01</span>
        <div>
          <p className="kicker">Scan parameters</p>
          <h2>Build the field</h2>
        </div>
      </div>

      <label className="field field-wide">
        <span>Symbols</span>
        <input
          aria-label="Symbols"
          value={values.symbols}
          onChange={(event) => update("symbols", event.target.value)}
          placeholder="OPEN, AAPL, SPY"
        />
        <small>Comma or space separated. Uses latest stored chains.</small>
      </label>

      <fieldset className="strategy-picker">
        <legend>Strategies</legend>
        {strategyOptions.map((option) => (
          <label className="strategy-option" key={option.value}>
            <input
              type="checkbox"
              checked={values.strategies.includes(option.value)}
              onChange={() => toggleStrategy(option.value)}
            />
            <span className="strategy-code">{option.code}</span>
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>

      <div className="filter-grid">
        <label className="field">
          <span>Min POP %</span>
          <input aria-label="Minimum POP" type="number" min="0" max="100" step="1" value={values.minimumPop} onChange={(event) => update("minimumPop", event.target.value)} />
        </label>
        <label className="field">
          <span>Min DTE</span>
          <input aria-label="Minimum DTE" type="number" min="0" value={values.minimumDte} onChange={(event) => update("minimumDte", event.target.value)} />
        </label>
        <label className="field">
          <span>Max DTE</span>
          <input aria-label="Maximum DTE" type="number" min="0" value={values.maximumDte} onChange={(event) => update("maximumDte", event.target.value)} />
        </label>
        <label className="field">
          <span>Min credit</span>
          <input aria-label="Minimum credit" type="number" min="0" step="0.01" value={values.minimumCredit} onChange={(event) => update("minimumCredit", event.target.value)} />
        </label>
        <label className="field">
          <span>Min OI</span>
          <input aria-label="Minimum open interest" type="number" min="0" value={values.minimumOpenInterest} onChange={(event) => update("minimumOpenInterest", event.target.value)} />
        </label>
        <label className="field">
          <span>Min volume</span>
          <input aria-label="Minimum volume" type="number" min="0" value={values.minimumVolume} onChange={(event) => update("minimumVolume", event.target.value)} />
        </label>
      </div>

      <div className="console-footer">
        <label className="field limit-field">
          <span>Result limit</span>
          <input aria-label="Result limit" type="number" min="1" max="500" value={values.limit} onChange={(event) => update("limit", event.target.value)} />
        </label>
        <button className="scan-button" type="submit" disabled={loading}>
          <span>{loading ? "Scanning" : "Run scan"}</span>
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}
