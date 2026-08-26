import { StatList, Panel } from 'issue-stance-ds';

export function InPanel() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 360 }}>
      <Panel title="収集概要">
        <StatList
          items={[
            { label: '収集期間', value: '2026-06-10〜06-18' },
            { label: '総件数', value: '192件' },
            { label: '有効件数', value: '190件' },
            { label: '分類完了', value: '192/192' },
            { label: '取得元', value: 'Yahoo!リアルタイム検索' },
          ]}
        />
      </Panel>
    </div>
  );
}

export function Standalone() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 360 }}>
      <StatList
        items={[
          { label: '改憲推進側', value: '52件' },
          { label: '護憲・慎重側', value: '61件' },
          { label: '手続き重視', value: '71件' },
          { label: '保留・注意', value: '8件' },
        ]}
      />
    </div>
  );
}
