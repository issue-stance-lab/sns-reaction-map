export type AxisVariant = 'default' | 'positive' | 'negative' | 'ok' | 'warn';

export interface AxisCardProps {
  kicker?: string;
  title: string;
  count: number;
  unit?: string;
  description?: string;
  tags?: string[];
  variant?: AxisVariant;
}

export function AxisCard({
  kicker,
  title,
  count,
  unit = '件',
  description,
  tags,
  variant = 'default',
}: AxisCardProps) {
  return (
    <article className={`ds-axis-card${variant !== 'default' ? ` ds-axis-card--${variant}` : ''}`}>
      {kicker && <div className="ds-axis-card__kicker">{kicker}</div>}
      <h3>{title}</h3>
      <div className="ds-axis-card__count">
        {count}
        <span>{unit}</span>
      </div>
      {description && <p>{description}</p>}
      {tags && tags.length > 0 && (
        <div className="ds-axis-tags">
          {tags.map((tag, i) => (
            <span key={i}>{tag}</span>
          ))}
        </div>
      )}
    </article>
  );
}
