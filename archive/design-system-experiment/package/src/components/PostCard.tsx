import { Badge } from './Badge';
import { StanceBadge, type StanceVariant } from './StanceBadge';

export interface PostCardProps {
  num?: number;
  topic?: string;
  stance?: string;
  stanceVariant?: StanceVariant;
  summary: string;
  quote?: string;
  reason?: string;
  href?: string;
  postedAt?: string;
  likes?: number;
  retweets?: number;
}

export function PostCard({
  num,
  topic,
  stance,
  stanceVariant = 'neutral',
  summary,
  quote,
  reason,
  href,
  postedAt,
  likes,
  retweets,
}: PostCardProps) {
  return (
    <article className="ds-post-card">
      <div className="ds-post-card__head">
        {num !== undefined && <span className="ds-post-card__num">#{num}</span>}
        {topic && <Badge>{topic}</Badge>}
        {stance && <StanceBadge stance={stance} variant={stanceVariant} />}
      </div>
      <p className="ds-post-card__summary">{summary}</p>
      {quote && <blockquote>{quote}</blockquote>}
      {reason && <p className="ds-post-card__reason">{reason}</p>}
      {(href || postedAt || likes !== undefined || retweets !== undefined) && (
        <div className="ds-post-card__meta">
          {postedAt && <span>{postedAt}</span>}
          {likes !== undefined && <span>♥ {likes}</span>}
          {retweets !== undefined && <span>↩ {retweets}</span>}
          {href && (
            <a href={href} target="_blank" rel="noopener noreferrer">
              元投稿を開く
            </a>
          )}
        </div>
      )}
    </article>
  );
}
