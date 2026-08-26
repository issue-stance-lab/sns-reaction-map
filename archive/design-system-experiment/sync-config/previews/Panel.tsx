import { Panel, BarList } from 'issue-stance-ds';

export function WithTitle() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <Panel title="親論点別" count="192件">
        <BarList
          items={[
            { label: '国民投票法・広告規制', value: 71 },
            { label: '9条・自衛隊明記', value: 51 },
            { label: '緊急事態条項', value: 35 },
            { label: '改憲全体', value: 27 },
            { label: '保留・注意領域', value: 5 },
          ]}
        />
      </Panel>
    </div>
  );
}

export function Stacked() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <Panel title="投稿の性質">
        <BarList
          items={[
            { label: '意見表明', value: 176 },
            { label: '情報共有', value: 4 },
            { label: '政党・議員批判', value: 3 },
            { label: '要確認・保留', value: 6 },
          ]}
        />
      </Panel>
      <Panel title="スタンス別">
        <BarList
          items={[
            { label: '改憲推進・支持', value: 52 },
            { label: '改憲慎重・反対', value: 61 },
            { label: '手続き重視', value: 71 },
            { label: '中立・その他', value: 8 },
          ]}
        />
      </Panel>
    </div>
  );
}
