import { Badge } from 'issue-stance-ds';

export function AllVariants() {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: 16 }}>
      <Badge>9条・自衛隊明記</Badge>
      <Badge>国民投票法</Badge>
      <Badge variant="warn">要確認</Badge>
      <Badge variant="ok">確認済み</Badge>
      <Badge variant="muted">分類保留</Badge>
      <Badge variant="purple">手続き重視</Badge>
    </div>
  );
}

export function InContext() {
  return (
    <div style={{ display: 'flex', gap: 8, padding: 16, alignItems: 'center' }}>
      <Badge>憲法改正</Badge>
      <span style={{ fontSize: 14, color: '#172033' }}>2026-06-18 • 192件収集</span>
    </div>
  );
}
