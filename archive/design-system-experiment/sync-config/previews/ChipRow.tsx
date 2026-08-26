import { ChipRow } from 'issue-stance-ds';

export function TopicFilter() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#667085', marginBottom: 8, fontFamily: '-apple-system,sans-serif' }}>論点で絞り込む</div>
      <ChipRow
        chips={[
          { label: 'すべて', active: true },
          { label: '9条・自衛隊明記' },
          { label: '緊急事態条項' },
          { label: '国民投票法' },
          { label: '改憲全体' },
        ]}
      />
    </div>
  );
}

export function StanceFilter() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#667085', marginBottom: 8, fontFamily: '-apple-system,sans-serif' }}>スタンスで絞り込む</div>
      <ChipRow
        chips={[
          { label: 'すべて' },
          { label: '支持', active: true },
          { label: '反対' },
          { label: '慎重' },
          { label: '中立' },
        ]}
      />
    </div>
  );
}
