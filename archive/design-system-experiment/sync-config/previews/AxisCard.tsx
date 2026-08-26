import { AxisCard } from 'issue-stance-ds';

export function AllVariants() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, padding: 16, background: '#f4f6f8' }}>
      <AxisCard
        variant="positive"
        kicker="推進側"
        title="改憲推進側"
        count={52}
        description="改憲全体、9条・自衛隊明記、緊急事態条項への賛成を含む親カテゴリ。"
        tags={['9条改正', '自衛隊明記', '緊急事態']}
      />
      <AxisCard
        variant="negative"
        kicker="慎重・反対側"
        title="改憲慎重・反対側"
        count={61}
        description="護憲、9条改正反対、緊急事態条項への警戒を含む親カテゴリ。"
        tags={['護憲', '9条反対', '条項反対']}
      />
      <AxisCard
        variant="ok"
        kicker="手続き"
        title="手続き重視"
        count={71}
        description="国民投票法、広告規制、資金、SNS上の情報環境を重視する反応。"
        tags={['国民投票法', '広告規制', '情報環境']}
      />
      <AxisCard
        variant="warn"
        kicker="注意"
        title="保留・注意領域"
        count={8}
        description="政党批判、未確認・過激表現、分類保留。記事化前の確認対象。"
      />
    </div>
  );
}

export function Minimal() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 320 }}>
      <AxisCard
        variant="positive"
        kicker="賛成"
        title="9条・自衛隊明記に賛成"
        count={47}
        description="自衛隊明記や国防上の必要性から憲法改正を支持する反応。"
      />
    </div>
  );
}
