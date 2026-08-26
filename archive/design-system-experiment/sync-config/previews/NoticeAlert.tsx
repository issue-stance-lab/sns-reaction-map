import { NoticeAlert } from 'issue-stance-ds';

export function AllVariants() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16, background: '#f4f6f8' }}>
      <NoticeAlert>
        このページの件数はYahooリアルタイム検索で取得した192件のサンプル内分類です。検索語に「賛成」「反対」「国民投票法」などを含むため、世論比率としては扱えません。
      </NoticeAlert>
      <NoticeAlert variant="warn">
        未確認・過激表現を含む投稿が8件含まれます。記事化前に内容を確認してください。
      </NoticeAlert>
      <NoticeAlert variant="ok">
        分類検証完了。192件中190件が有効データとして確認されました。
      </NoticeAlert>
      <NoticeAlert variant="accent">
        新規トピック「辺野古基地問題」のデータを追加しました。
      </NoticeAlert>
    </div>
  );
}
