import type { ReactNode } from 'react';

export interface ToolbarProps {
  label?: string;
  children: ReactNode;
}

export function Toolbar({ label, children }: ToolbarProps) {
  return (
    <div className="ds-toolbar">
      {label && <div className="ds-toolbar__label">{label}</div>}
      {children}
    </div>
  );
}
