import { StatCard, StatGrid } from 'issue-stance-ds';

export function Single() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <StatCard label="収集件数" value="192" unit="件" />
    </div>
  );
}

export function Grid() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <StatGrid>
        <StatCard label="収集件数" value="192" unit="件" />
        <StatCard label="賛成・支持" value="52" unit="件" />
        <StatCard label="反対・慎重" value="61" unit="件" />
        <StatCard label="手続き重視" value="71" unit="件" />
      </StatGrid>
    </div>
  );
}

export function LargeNumbers() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <StatGrid>
        <StatCard label="総インプレッション" value="1,842,300" />
        <StatCard label="リツイート" value="4,721" />
        <StatCard label="平均いいね" value="23.4" />
      </StatGrid>
    </div>
  );
}
