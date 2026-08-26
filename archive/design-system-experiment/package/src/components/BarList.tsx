import { BarRow } from './BarRow';

export interface BarListItem {
  label: string;
  value: number;
  count?: string;
}

export interface BarListProps {
  items: BarListItem[];
  max?: number;
}

export function BarList({ items, max }: BarListProps) {
  const resolvedMax = max ?? Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="ds-bar-list">
      {items.map((item, i) => (
        <BarRow key={i} label={item.label} value={item.value} max={resolvedMax} count={item.count} />
      ))}
    </div>
  );
}
