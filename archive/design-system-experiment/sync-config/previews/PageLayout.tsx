import { PageLayout, Panel, StatList, PostCard, BarList } from 'issue-stance-ds';

export function TwoColumn() {
  return (
    <PageLayout
      main={
        <>
          <PostCard
            num={1}
            topic="9条・自衛隊明記"
            stance="賛成"
            stanceVariant="support"
            summary="自衛隊の憲法上の地位を明確化すべきという立場から改憲を支持。"
            quote="自衛隊が違憲かもしれないという状態を放置するのは国として無責任だ。"
            postedAt="2026-06-18"
            likes={142}
          />
          <PostCard
            num={2}
            topic="緊急事態条項"
            stance="反対"
            stanceVariant="oppose"
            summary="緊急事態条項の新設は権力集中と人権制限のリスクがあるとして強く反対する立場。"
            postedAt="2026-06-17"
            likes={89}
          />
        </>
      }
      aside={
        <Panel title="スタンス別集計">
          <StatList
            items={[
              { label: '推進側', value: '52件' },
              { label: '護憲・慎重側', value: '61件' },
              { label: '手続き重視', value: '71件' },
              { label: '保留・注意', value: '8件' },
            ]}
          />
          <div style={{ marginTop: 16 }}>
            <BarList
              items={[
                { label: '推進側', value: 52 },
                { label: '護憲・慎重', value: 61 },
                { label: '手続き', value: 71 },
              ]}
            />
          </div>
        </Panel>
      }
    />
  );
}
