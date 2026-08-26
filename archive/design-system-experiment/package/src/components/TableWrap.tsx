import type { ReactNode } from 'react';

export interface TableWrapProps {
  children: ReactNode;
  minWidth?: number;
}

export function TableWrap({ children, minWidth }: TableWrapProps) {
  return (
    <div className="ds-table-wrap">
      <table style={minWidth ? { minWidth } : undefined}>{children}</table>
    </div>
  );
}
