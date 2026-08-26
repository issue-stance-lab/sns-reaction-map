export interface HeatCellProps {
  value: number;
  bgColor?: string;
  textColor?: string;
}

export function HeatCell({ value, bgColor, textColor }: HeatCellProps) {
  const zero = value === 0;
  return (
    <td
      className={`ds-heat-cell${zero ? ' ds-heat-cell--zero' : ''}`}
      style={bgColor && !zero ? { backgroundColor: bgColor, color: textColor ?? '#fff' } : undefined}
    >
      <span>{value}</span>
    </td>
  );
}
