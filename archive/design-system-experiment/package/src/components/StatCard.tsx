export interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
}

export function StatCard({ label, value, unit }: StatCardProps) {
  return (
    <div className="ds-stat">
      <span className="ds-stat__label">{label}</span>
      <strong className="ds-stat__value">
        {value}
        {unit && <span className="ds-stat__unit">{unit}</span>}
      </strong>
    </div>
  );
}
