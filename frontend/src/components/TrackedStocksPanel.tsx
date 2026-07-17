import type { TrackedUnderlying } from "../api/marketData";

type TrackedStocksPanelProps = {
  stocks: TrackedUnderlying[];
  activeSymbol: string;
  loading: boolean;
  refreshing: boolean;
  message: string | null;
  onSelect: (symbol: string) => void;
  onRefresh: () => void;
};

function formatPrice(price: number | null) {
  return price === null ? "Price unavailable" : `$${price.toFixed(2)}`;
}

function formatSnapshotTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function TrackedStocksPanel({
  stocks,
  activeSymbol,
  loading,
  refreshing,
  message,
  onSelect,
  onRefresh,
}: TrackedStocksPanelProps) {
  return (
    <section className="stocks-panel" aria-labelledby="tracked-stocks-heading">
      <div className="stocks-heading">
        <div>
          <p className="kicker">Local market universe</p>
          <h2 id="tracked-stocks-heading">Tracked stocks</h2>
        </div>
        <button className="refresh-stock-button" type="button" onClick={onRefresh} disabled={refreshing || !activeSymbol}>
          {refreshing ? "Collecting data..." : `Add / refresh ${activeSymbol || "symbol"}`}
        </button>
      </div>
      {message ? <p className="stocks-message" role="status">{message}</p> : null}
      {loading ? <p className="stocks-empty">Loading stored stocks...</p> : null}
      {!loading && stocks.length === 0 ? (
        <p className="stocks-empty">No stored stocks yet. Enter a symbol below, then use Add / refresh.</p>
      ) : null}
      {stocks.length > 0 ? (
        <div className="stock-strip">
          {stocks.map((stock) => (
            <button
              className={`stock-card ${stock.symbol === activeSymbol ? "stock-card-active" : ""}`}
              type="button"
              key={stock.symbol}
              onClick={() => onSelect(stock.symbol)}
              aria-pressed={stock.symbol === activeSymbol}
            >
              <span className="stock-symbol">{stock.symbol}</span>
              <strong>{formatPrice(stock.underlying_price)}</strong>
              <span>{stock.provider.toUpperCase()} / {stock.quote_count} quotes</span>
              <time dateTime={stock.as_of}>{formatSnapshotTime(stock.as_of)}</time>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
