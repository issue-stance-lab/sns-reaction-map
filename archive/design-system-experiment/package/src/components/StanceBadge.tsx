export type StanceVariant = 'neutral' | 'support' | 'oppose' | 'cautious';

export interface StanceBadgeProps {
  stance: string;
  variant?: StanceVariant;
}

export function StanceBadge({ stance, variant = 'neutral' }: StanceBadgeProps) {
  return (
    <span className={`ds-stance ds-stance--${variant}`}>{stance}</span>
  );
}
