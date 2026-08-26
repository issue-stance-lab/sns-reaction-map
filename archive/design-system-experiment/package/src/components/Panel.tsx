import type { ReactNode } from 'react';

export interface PanelProps {
  title?: string;
  count?: string;
  titleLevel?: 2 | 3;
  children: ReactNode;
}

export function Panel({ title, count, titleLevel = 2, children }: PanelProps) {
  const H = `h${titleLevel}` as 'h2' | 'h3';
  return (
    <section className="ds-panel">
      {title && (
        <div className="ds-panel__title">
          <H>{title}</H>
          {count && <span className="ds-panel__count">{count}</span>}
        </div>
      )}
      {children}
    </section>
  );
}
