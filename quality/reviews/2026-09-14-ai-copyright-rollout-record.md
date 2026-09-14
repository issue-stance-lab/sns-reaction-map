# 生成AI（ai-copyright）の編集再読・山なみ展開・本番反映記録（2026-09-14）

`tasks/task-54.md` の400行上限維持のため、本文をここへ切り出した。

## 編集再読・完了確認

[指示文](../quality/designs/2026-09-13-ai-copyright-reread-brief.md)どおり、別AIが
学習データ・無断利用(657)／クリエイター保護・権利(303)／その他(223)／AI生成物の権利・
創作性(165)／技術競争・推進(117)の5論点・意見1,465件（56.5%）を全件読了。上記表の
「1,300件・782件」試算は使わず、指示文で置き換えた56.5%・全件読了を実施した。

`configs/planet/ai-copyright.yaml`（初回作成）と`data/ai-copyright_issues-reread.json`を検証:
ランダム抽出40件で本文ハッシュ・main_issue・stanceの不整合0件、バケット割当も本文と照らして
妥当（機械的な要約流用ではなく実際の論拠で分かれている）、重複ID・自動分類混入フラグ0件。
`build_planet_data.independence_gate()`を実際に実行し、残るNGは指示文で対象外とした
「一次資料との突き合わせが無い」1件のみ（想定どおり）。50%条件・論点ごとの4割条件はいずれも
クリア。作業中に`scripts/build_planet_data.py`（共通コード）へ無関係な差分（static_fallbackの
書き方変更、出力は同一と確認済み）が混入していたため、検証時に元へ戻した。

**残作業（この時点）**: 一次資料との突き合わせ（`quality/research/ai-copyright-primary-sources.md`から
`data/ai-copyright_claim_posts.json`を作る、指示文の対象外1）、`editorial-adoption-current.json`の
149件の分類確認（対象外2、`quality/designs/body-review/`の別工程）、山なみページの実際の生成・
標準検査・本番反映（対象外3）はいずれも未着手。

## ローカルページ生成・検査完了（本番反映はまだ）

一次資料突き合わせ（`data/ai-copyright_claim_posts.json`、6主張・代表投稿12件）と編集部の横断整理
（`data/verification/ai-copyright-editorial.json`、5件・3観点とも有）を新規作成し、
`independence_gate`が**通る**ことを確認。`build_planet_page_preview.py --topic ai-copyright --for-docs`で
山なみへ差し替え。差し替え時に2件修正: ①`verify_preserved`が旧アリーナの論点フィルタ欄
（`<aside class="sm-controls">`）を編集通知と誤認識していたため`clean_aicopyright_layout()`を新設
（henokoの`clean_henoko_layout()`と同形、ai-copyright専用分岐）②`build_ai_copyright_arena.py`の
`build()`/`apply_public_counts()`両方に他テーマ同型の`PLANET_SECTION_START`ガードを追加（後者は
「調査条件」の貼り直しだけ残す設計に）。

標準検査を実行。数字の出所検査は当初71件「説明できない」だったが、山なみ新設の内訳表示を
`configs/ai-copyright-reaction-map.json`の`number_provenance`へ追加し0件（他テーマ共通の9項目）。
ai-copyright固有の単体テスト4ファイルを新形式へ更新（旧「question spine」実験の回帰テストは
山なみに置き換わったため`skipTest`で退役）。400行超過分は[副首都の記録](../quality/reviews/2026-09-14-fukushuto-reread-513-record.md)と
[共有ツリー分岐の記録](../quality/reviews/2026-09-13-shared-tree-divergence-css-bug.md)へ切り出した。

**確認済み**: `independence_gate`通る、標準3検査NG0件、ai-copyright関連の単体テスト全件OK、
2回生成の差分0。**未確認**: 実機スマホ、全テーマ通しの単体テスト（このワークツリーは他9テーマの
非公開正典を複製していないため実行不可。ai-copyright以外の失敗は環境固有で無関係と判断）。
**2026-09-14 本番反映済み**（マージ`03c86f2`・push・公開確認）。マージ後のmainで標準検査・
単体テスト966件を再実行し無関係な既存1件のみ残存を確認。公開サイトで山なみ形式を実機確認済み。
ai-copyright-planetの作業ツリーは片付け済み。生成AIは8テーマ目として本番公開中。
