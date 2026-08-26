import { VersusGrid, StatList } from 'issue-stance-ds';

export function ConstitutionalAmendment() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8' }}>
      <VersusGrid
        leftTitle="改憲推進側"
        leftCount={52}
        leftDescription="9条改正・自衛隊明記・緊急事態条項の新設を支持する反応。"
        leftChildren={
          <StatList
            items={[
              { label: '9条・自衛隊明記に賛成', value: 47 },
              { label: '緊急事態条項に賛成', value: 3 },
              { label: '改憲全体に賛成', value: 5 },
            ]}
          />
        }
        rightTitle="護憲・慎重側"
        rightCount={61}
        rightDescription="現行憲法の維持や改憲手続きの不備を指摘する反応。"
        rightChildren={
          <StatList
            items={[
              { label: '護憲・9条改正反対', value: 22 },
              { label: '緊急事態条項に反対', value: 35 },
              { label: '改憲全体に反対', value: 4 },
            ]}
          />
        }
      />
    </div>
  );
}
