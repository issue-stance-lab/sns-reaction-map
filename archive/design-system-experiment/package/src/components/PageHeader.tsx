import type { ReactNode } from 'react';

export interface NavLinkItem {
  href: string;
  label: string;
  current?: boolean;
}

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  lead?: string;
  nav?: NavLinkItem[];
  children?: ReactNode;
}

export function PageHeader({ title, subtitle, lead, nav, children }: PageHeaderProps) {
  return (
    <header className="ds-page-header">
      {nav && nav.length > 0 && (
        <nav className="ds-top-nav">
          {nav.map((link, i) => (
            <a key={i} href={link.href} aria-current={link.current ? 'page' : undefined}>
              {link.label}
            </a>
          ))}
        </nav>
      )}
      <h1>{title}</h1>
      {subtitle && <h2>{subtitle}</h2>}
      {lead && <p className="ds-lead">{lead}</p>}
      {children}
    </header>
  );
}
