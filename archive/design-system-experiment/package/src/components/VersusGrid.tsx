import type { ReactNode } from 'react';

export interface VersusGridProps {
  leftTitle: string;
  leftCount?: number;
  leftDescription?: string;
  leftChildren?: ReactNode;
  rightTitle: string;
  rightCount?: number;
  rightDescription?: string;
  rightChildren?: ReactNode;
}

export function VersusGrid({
  leftTitle,
  leftCount,
  leftDescription,
  leftChildren,
  rightTitle,
  rightCount,
  rightDescription,
  rightChildren,
}: VersusGridProps) {
  return (
    <div className="ds-versus-grid">
      <div className="ds-versus-side ds-versus-side--left">
        <div className="ds-versus-side__title">
          {leftTitle}
          {leftCount !== undefined && (
            <strong className="ds-versus-side__count">{leftCount}</strong>
          )}
        </div>
        {leftDescription && <p>{leftDescription}</p>}
        {leftChildren}
      </div>

      <div className="ds-vs-mark">VS</div>

      <div className="ds-versus-side ds-versus-side--right">
        <div className="ds-versus-side__title">
          {rightTitle}
          {rightCount !== undefined && (
            <strong className="ds-versus-side__count">{rightCount}</strong>
          )}
        </div>
        {rightDescription && <p>{rightDescription}</p>}
        {rightChildren}
      </div>
    </div>
  );
}
