import type { ReactNode } from 'react';

export type BadgeVariant = 'default' | 'warn' | 'ok' | 'muted' | 'purple';

export interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
}

export function Badge({ children, variant = 'default' }: BadgeProps) {
  const cls = variant === 'default' ? 'ds-badge' : `ds-badge ds-badge--${variant}`;
  return <span className={cls}>{children}</span>;
}
