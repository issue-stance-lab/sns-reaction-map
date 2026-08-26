import { TableWrap, HeatCell } from 'issue-stance-ds';

export function ReactionMap() {
  const stances = ['賛成・支持', '反対・慎重', '手続き重視', '中立'];
  const topics = [
    { label: '9条・自衛隊明記', values: [47, 4, 0, 0], colors: ['#1769d1', '#b54708', '', ''] },
    { label: '緊急事態条項', values: [3, 35, 0, 0], colors: ['#4a8de0', '#b54708', '', ''] },
    { label: '国民投票法', values: [0, 0, 71, 0], colors: ['', '', '#16885a', ''] },
    { label: '改憲全体', values: [5, 22, 0, 0], colors: ['#8cbcf2', '#d97706', '', ''] },
  ];
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <TableWrap>
        <thead>
          <tr>
            <th>論点</th>
            {stances.map((s) => <th key={s}>{s}</th>)}
            <th style={{ background: '#f2f4f7', fontWeight: 900 }}>合計</th>
          </tr>
        </thead>
        <tbody>
          {topics.map((row) => (
            <tr key={row.label}>
              <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 13, color: '#172033', fontWeight: 600 }}>{row.label}</th>
              {row.values.map((v, i) => (
                <HeatCell key={i} value={v} bgColor={row.colors[i] || undefined} textColor="#fff" />
              ))}
              <td style={{ background: '#f2f4f7', fontWeight: 900, fontVariantNumeric: 'tabular-nums', padding: '8px 12px', textAlign: 'center', fontSize: 13 }}>
                {row.values.reduce((a, b) => a + b, 0)}
              </td>
            </tr>
          ))}
        </tbody>
      </TableWrap>
    </div>
  );
}
