# 課題77 — 消費税の連動表示を公開

2026-09-22、オーナーが修正版の確認後「公開して」と明示的に承認。
`approval-20260922-001` をapprovedへ更新し、同日に公開・配信・公開URLでの操作確認を完了した。

## 公開対象

- 承認候補: `.staging/task77-tax-selection-motion/candidate.html`
- HTML SHA-256: `27b2632daaadbb4c5c173f14626a7c27fe82c224b03ed4f2dfcf23ffd461d530`
- 表示ファイル: consumption-tax-connected JS/CSS/page JS v8、topic-modern.js v14。
- 対象URL: https://sns-reaction-map.jp/consumption-tax-cut-reaction-map.html
- 独立監査: [選択動作の修正記録](2026-09-22-task77-tax-selection-motion.md)、ready_for_ceo。

バー・立場・山・論点を一続きにし、理由25項目のX投稿、資料3タブ、クイズ6問、年表、引用・授業・投票を接続する。
予想の答え・古い観察記録・事業者の順位表現は内容確定書の訂正文へ変更し、`correction-20260922-001` に記録。
投票番号と保存形式、収集4386件・意見3890件、制度9/19・資料照合8/19・編集整理9/14の確認日は維持する。
データ更新ではないため、THEMES.yamlの収集予定・データ更新日、sitemapのデータ更新日を進めない。

## 公開直前の確認

最新mainから専用作業ツリーを作成。旧公開HTMLの指紋、表示4ファイル、消費税の非公開データが承認時から変わっていないことを確認。
公開位置へ配置したHTMLは、承認候補とバイト単位で一致する。別テーマの変更は含めない。
検査ログと配信検証結果は `.staging/task77-tax-publication/` に保存する。

統合後のmain `6bff462c` で全テーマ・数値の出所・トップが合格。消費税の数値出典は220/220。
全体1082件・公開用914件（それぞれ既存4件スキップ）が合格してからpushした。

## 公開結果

- [公開ファイルの検査](https://github.com/issue-stance-lab/sns-reaction-map/actions/runs/35738899972): success。
- [GitHub Pagesへの配信](https://github.com/issue-stance-lab/sns-reaction-map/actions/runs/35738899864): success。
- 公開HTML・表示4ファイル・トップはHTTP 200。配信時の接続設定の差分を除き、手元の公開対象とすべて一致した。
- Chromium・WebKitの1280/375/320pxで、立場→論点の選択、濃色表示、理由の開閉、要旨と元投稿リンク、資料3タブと横断4項目、クイズ、図解の開閉を確認。横はみ出し・JavaScript例外なし。
- Chromium 375pxでは公式Xカードの読み込みも確認。その他の幅では要旨と元投稿リンクを確認した。実スマホ端末・製品版Safariは未確認。
- 本番へのテスト票の送信なし。集計と確認日は変更しない。
- 統合済みmainで非公開データ280ファイルを外付け保存先へバックアップし、復元確認OK。記録は `company/data-backup-status.json`。

実URLの検証ログ・画像・ファイル照合結果は `.staging/task77-tax-publication/` に保存した。

## 公開後の確認

最初の観察期間は公開後7〜14日（9/29〜10/6）を目安にする。
ページ閲覧、reason_post_open、source_only_tab_open、cite_copy、classroom_printを見る。
理由や立場・投稿URLをイベントへ付けず、中央タブの操作を資料本文全体の読了人数とは扱わない。
母数が少ない間は操作のつまずきを優先する。案1・2の10/19振り返りとは分け、自動通知は追加しない。

不具合時は、最新の正典・投票番号を保持したまま旧配置へ再生成する。古い集計HTMLやリポジトリ全体へ巻き戻さない。
