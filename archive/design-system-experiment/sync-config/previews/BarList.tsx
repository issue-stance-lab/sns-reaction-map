import { BarList } from 'issue-stance-ds';

export function TopicBreakdown() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <BarList
        items={[
          { label: '国民投票法・広告規制を重視', value: 71 },
          { label: '9条・自衛隊明記に賛成', value: 47 },
          { label: '緊急事態条項に反対', value: 35 },
          { label: '改憲反対・護憲', value: 22 },
          { label: '改憲賛成・推進', value: 5 },
          { label: 'その他・分類保留', value: 5 },
          { label: '9条・自衛隊明記に反対', value: 4 },
          { label: '政党・議員批判', value: 3 },
        ]}
      />
    </div>
  );
}

export function Short() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <BarList
        items={[
          { label: '意見表明', value: 176 },
          { label: '要確認・保留', value: 6 },
          { label: '情報共有', value: 4 },
          { label: '政党・議員批判', value: 3 },
        ]}
      />
    </div>
  );
}
