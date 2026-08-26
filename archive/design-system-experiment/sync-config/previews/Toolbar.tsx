import { Toolbar, ChipRow } from 'issue-stance-ds';

export function WithChips() {
  return (
    <div style={{ background: '#f4f6f8', padding: 0 }}>
      <Toolbar label="論点で絞り込む">
        <ChipRow
          chips={[
            { label: 'すべて', active: true },
            { label: '9条・自衛隊明記' },
            { label: '緊急事態条項' },
            { label: '国民投票法' },
            { label: '改憲全体' },
          ]}
        />
      </Toolbar>
    </div>
  );
}
