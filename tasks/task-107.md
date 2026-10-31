# 課題107: 投票サーバーに接続できない

**登録**: 2026-10-31。オーナーから依頼された公開サイト全体点検で発見。
**状態**: 進行中。接続障害は確認済み。原因調査と復旧は未着手。
**優先度**: 最優先。

## 確認したこと

- 公開中の`vote-config.js?v=1`が使う接続先は`qslrlprzoucrlptnhsmi.supabase.co`。
- 手元の名前解決に失敗。Google Public DNSとCloudflareのDNS-over-HTTPS照会でも、両方がStatus 3（NXDOMAIN、該当するサーバー名なし）、Answerなしを返した。
- 公開中の部活動ページから、共通クライアント`VoteStore.getCounts('bukatsu-chiiki')`を実行すると、remote=trueで`TypeError: Failed to fetch`。
- KPI一括取得もSupabaseの取得で終了。GA4・Search Consoleは個別に取得できた。
- `vote-store.js`の集計GETと投票POSTは同じサーバー名を使うため、全テーマの投票にも影響する可能性が高い。

投票は送信していない。障害の開始日、プロジェクトの停止・削除・URLの設定違いのどれか、既存投票の残存は未確認。原因を推測して新しいプロジェクトを作ったり、既存データを消したりしない。

## 次にすること

1. Supabaseの管理画面でプロジェクトの状態と接続先を確認する。
2. 既存の投票データが残っているか確認する。
3. 集計の読み取りを復旧し、公開ページの共通クライアントからも確認する。
4. 設定・公開ファイルの変更が必要なら候補を用意する。公開変更、支出・契約変更、データ削除は既存の承認ルールに従う。
5. 承認済みの試験で送信・保存・重複防止を確認する。試験票の扱いを決めてから送信する。
6. 管理画面で、設定ファイルの存在と投票サービスの稼働状態を区別する。接続監視を追加する場合はGETだけを使う。

## 完了条件

- 接続先が名前解決でき、公開ページから集計を取得できる。
- 既存データの状態を確認でき、承認済みの試験で送信・保存・重複防止が確認できる。
- 失敗時に投票完了として扱わず、利用者に状況が伝わる。
- KPI取得と管理画面が更新される。欠測を過去の25票で埋めない。

## 証拠と全体点検

調査保存先: `/Volumes/M2-WorkSpace/Projects/副業/UIデザイン調査/2026-10-31_SNS反応まっぷ_全体点検/`

- `evidence/vote-dns.json`
- `evidence/vote-public-dns.json`
- `evidence/vote-browser-get.json`
- `evidence/dashboard-live.html`
- 全体の優先順とWeb出典: `00_点検結果.md`

公開設定: https://sns-reaction-map.jp/vote-config.js?v=1

今回の調査では公開サイト・Supabaseの設定変更を行っていない。
