import { StanceBadge } from 'issue-stance-ds';

export function AllVariants() {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: 16 }}>
      <StanceBadge stance="支持" variant="support" />
      <StanceBadge stance="反対" variant="oppose" />
      <StanceBadge stance="慎重" variant="cautious" />
      <StanceBadge stance="中立" variant="neutral" />
    </div>
  );
}

export function WithLabels() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16 }}>
      {(
        [
          ['support', '支持', '改憲を積極的に支持する立場'],
          ['oppose', '反対', '改憲に反対する立場'],
          ['cautious', '慎重', '手続きや条件を重視する立場'],
          ['neutral', '中立', 'どちらでもない・判断保留'],
        ] as const
      ).map(([v, stance, desc]) => (
        <div key={v} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <StanceBadge stance={stance} variant={v} />
          <span style={{ fontSize: 13, color: '#667085' }}>{desc}</span>
        </div>
      ))}
    </div>
  );
}
