import { PageHeader } from 'issue-stance-ds';

export function WithNav() {
  return (
    <PageHeader
      title="SNS反応まっぷ"
      lead="Yahooリアルタイム検索で収集したX反応を論点ごとに分類・可視化します。"
      nav={[
        { href: '#', label: 'トップ', current: true },
        { href: '#', label: '反応マップ' },
        { href: '#', label: 'ダッシュボード' },
        { href: '#', label: 'まとめ' },
      ]}
    />
  );
}

export function WithSubtitle() {
  return (
    <PageHeader
      title="高市文春問題"
      subtitle="SNS反応まっぷ"
      lead="文春砲に対するX上の反応192件を立場・感情・論点ごとに集計。"
      nav={[
        { href: '#', label: 'トップ' },
        { href: '#', label: '高市事例', current: true },
        { href: '#', label: '憲法改正' },
      ]}
    />
  );
}

export function Minimal() {
  return (
    <PageHeader
      title="憲法改正論議 論点ダッシュボード"
      lead="賛否を単純比較せず、改憲全体・項目別・手続き・投稿の性質に分けて表示します。"
    />
  );
}
