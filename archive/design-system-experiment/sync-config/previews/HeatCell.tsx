import { HeatCell } from 'issue-stance-ds';

export function WithValue() {
  const heatColors: [number, string][] = [
    [72, '#1769d1'],
    [45, '#4a8de0'],
    [20, '#8cbcf2'],
    [5, '#c3d9f9'],
  ];
  return (
    <div style={{ fontFamily: '-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif', padding: 16 }}>
      <table style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
        <thead>
          <tr>
            <th style={{ background: '#eef2f7', color: '#344054', fontSize: 12, fontWeight: 800, padding: '8px 12px', borderBottom: '1px solid #d7dce5', borderRight: '1px solid #d7dce5' }}>論点</th>
            <th style={{ background: '#eef2f7', color: '#344054', fontSize: 12, fontWeight: 800, padding: '8px 12px', borderBottom: '1px solid #d7dce5', borderRight: '1px solid #d7dce5' }}>支持</th>
            <th style={{ background: '#eef2f7', color: '#344054', fontSize: 12, fontWeight: 800, padding: '8px 12px', borderBottom: '1px solid #d7dce5', borderRight: '1px solid #d7dce5' }}>反対</th>
            <th style={{ background: '#eef2f7', color: '#344054', fontSize: 12, fontWeight: 800, padding: '8px 12px', borderBottom: '1px solid #d7dce5' }}>中立</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '8px 12px', borderBottom: '1px solid #d7dce5', borderRight: '1px solid #d7dce5', fontSize: 13, color: '#172033' }}>9条・自衛隊明記</td>
            <HeatCell value={heatColors[0][0]} bgColor={heatColors[0][1]} />
            <HeatCell value={heatColors[1][0]} bgColor="#b54708" textColor="#fff" />
            <HeatCell value={3} />
          </tr>
          <tr>
            <td style={{ padding: '8px 12px', borderBottom: '1px solid #d7dce5', borderRight: '1px solid #d7dce5', fontSize: 13, color: '#172033' }}>緊急事態条項</td>
            <HeatCell value={8} bgColor={heatColors[3][1]} />
            <HeatCell value={heatColors[0][0]} bgColor="#d97706" textColor="#fff" />
            <HeatCell value={0} />
          </tr>
          <tr>
            <td style={{ padding: '8px 12px', borderRight: '1px solid #d7dce5', fontSize: 13, color: '#172033' }}>国民投票法</td>
            <HeatCell value={0} />
            <HeatCell value={heatColors[1][0]} bgColor="#b54708" textColor="#fff" />
            <HeatCell value={heatColors[2][0]} bgColor={heatColors[2][1]} />
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export function Variants() {
  return (
    <div style={{ fontFamily: '-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif', padding: 16 }}>
      <table style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
        <tbody>
          <tr>
            <HeatCell value={72} bgColor="#1769d1" textColor="#fff" />
            <HeatCell value={45} bgColor="#4a8de0" textColor="#fff" />
            <HeatCell value={20} bgColor="#8cbcf2" textColor="#172033" />
            <HeatCell value={5} bgColor="#c3d9f9" textColor="#172033" />
            <HeatCell value={0} />
          </tr>
        </tbody>
      </table>
    </div>
  );
}
