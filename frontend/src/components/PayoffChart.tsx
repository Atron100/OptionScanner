import type { PayoffPoint } from "../api/scanner";

type PayoffChartProps = {
  points: PayoffPoint[];
  breakEven: number;
  upperBreakEven: number | null;
  symbol: string;
};

const width = 760;
const height = 280;
const padding = { top: 22, right: 24, bottom: 38, left: 58 };

export function PayoffChart({ points, breakEven, upperBreakEven, symbol }: PayoffChartProps) {
  if (points.length < 2) return <div className="chart-empty">Payoff data unavailable.</div>;

  const xValues = points.map((point) => point.underlying_price);
  const yValues = [...points.map((point) => point.profit_loss), 0];
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const x = (value: number) => padding.left + ((value - xMin) / xRange) * plotWidth;
  const y = (value: number) => padding.top + ((yMax - value) / yRange) * plotHeight;
  const line = points.map((point, index) => `${index === 0 ? "M" : "L"} ${x(point.underlying_price).toFixed(2)} ${y(point.profit_loss).toFixed(2)}`).join(" ");
  const lastPoint = points[points.length - 1];
  const area = `${line} L ${x(lastPoint.underlying_price).toFixed(2)} ${y(0).toFixed(2)} L ${x(points[0].underlying_price).toFixed(2)} ${y(0).toFixed(2)} Z`;
  const breakEvens = [breakEven, upperBreakEven].filter((value): value is number => value !== null && value >= xMin && value <= xMax);
  const ticks = Array.from({ length: 5 }, (_, index) => xMin + (xRange * index) / 4);
  const zeroY = y(0);

  return (
    <svg className="payoff-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${symbol} payoff at expiration`}>
      <defs>
        <linearGradient id="profit-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#c7f36b" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#c7f36b" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="loss-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f07b69" stopOpacity="0" />
          <stop offset="100%" stopColor="#f07b69" stopOpacity="0.22" />
        </linearGradient>
        <clipPath id="profit-region"><rect x={padding.left} y={padding.top} width={plotWidth} height={Math.max(0, zeroY - padding.top)} /></clipPath>
        <clipPath id="loss-region"><rect x={padding.left} y={zeroY} width={plotWidth} height={Math.max(0, height - padding.bottom - zeroY)} /></clipPath>
      </defs>
      <line className="chart-axis" x1={padding.left} x2={width - padding.right} y1={y(0)} y2={y(0)} />
      {ticks.map((tick) => (
        <g key={tick}>
          <line className="chart-grid" x1={x(tick)} x2={x(tick)} y1={padding.top} y2={height - padding.bottom} />
          <text className="chart-label" x={x(tick)} y={height - 13} textAnchor="middle">{tick.toFixed(2)}</text>
        </g>
      ))}
      {breakEvens.map((value) => (
        <g key={value}>
          <line className="break-even-line" x1={x(value)} x2={x(value)} y1={padding.top} y2={height - padding.bottom} />
          <text className="break-even-label" x={x(value)} y={padding.top + 10} textAnchor="middle">BE {value.toFixed(2)}</text>
        </g>
      ))}
      <path className="payoff-profit-area" d={area} fill="url(#profit-fill)" clipPath="url(#profit-region)" />
      <path className="payoff-loss-area" d={area} fill="url(#loss-fill)" clipPath="url(#loss-region)" />
      <path className="payoff-profit-line" d={line} clipPath="url(#profit-region)" />
      <path className="payoff-loss-line" d={line} clipPath="url(#loss-region)" />
      <text className="chart-label" x={padding.left - 10} y={y(yMax) + 4} textAnchor="end">{yMax.toFixed(2)}</text>
      <text className="chart-label" x={padding.left - 10} y={y(0) + 4} textAnchor="end">0.00</text>
      <text className="chart-label" x={padding.left - 10} y={y(yMin) + 4} textAnchor="end">{yMin.toFixed(2)}</text>
    </svg>
  );
}
