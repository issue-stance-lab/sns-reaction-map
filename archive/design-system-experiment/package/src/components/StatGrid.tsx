import type { ReactNode } from 'react';

export interface StatGridProps {
  children: ReactNode;
}

export function StatGrid({ children }: StatGridProps) {
  return <div className="ds-stat-grid">{children}</div>;
}
