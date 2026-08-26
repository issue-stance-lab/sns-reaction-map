import type { ReactNode } from 'react';

export type NoticeVariant = 'default' | 'warn' | 'ok' | 'accent';

export interface NoticeAlertProps {
  children: ReactNode;
  variant?: NoticeVariant;
}

export function NoticeAlert({ children, variant = 'default' }: NoticeAlertProps) {
  const cls = variant === 'default' ? 'ds-notice' : `ds-notice ds-notice--${variant}`;
  return <div className={cls}>{children}</div>;
}
