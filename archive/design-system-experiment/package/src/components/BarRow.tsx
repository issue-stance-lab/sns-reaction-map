export interface BarRowProps {
  label: string;
  value: number;
  max?: number;
  count?: string;
}

export function BarRow({ label, value, max = 100, count }: BarRowProps) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="ds-bar-row">
      <div className="ds-bar-meta">
        <span>{label}</span>
        <strong>{count ?? value}</strong>
      </div>
      <div className="ds-bar-track">
        <div className="ds-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
