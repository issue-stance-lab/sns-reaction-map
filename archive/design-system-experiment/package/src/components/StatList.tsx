export interface StatListItem {
  label: string;
  value: string | number;
}

export interface StatListProps {
  items: StatListItem[];
}

export function StatList({ items }: StatListProps) {
  return (
    <ul className="ds-stat-list">
      {items.map((item, i) => (
        <li key={i}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </li>
      ))}
    </ul>
  );
}
