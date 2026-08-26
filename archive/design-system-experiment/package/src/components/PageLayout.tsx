import type { ReactNode } from 'react';

export interface PageLayoutProps {
  main: ReactNode;
  aside?: ReactNode;
}

export function PageLayout({ main, aside }: PageLayoutProps) {
  if (!aside) {
    return <div className="ds-page-main">{main}</div>;
  }
  return (
    <div className="ds-page-layout">
      <div className="ds-page-layout__main">{main}</div>
      <aside className="ds-page-layout__aside">{aside}</aside>
    </div>
  );
}
