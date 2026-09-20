# 課題69: consumption-tax-cut（5テーマ目）を収集から本番反映まで実施（2026-09-18）

tasks/task-69.md が400行上限のため切り出した。

## 収集

新規624件（意見532件）を取得、累積正典4,386件・意見3,890件へ統合。次回収集は9/24。

## 山なみ変換後、初のページ生成で不具合発見・修正（5件目の同型不具合）

`build_consumption_tax_page.py`が9/14の山なみ形式への切り替え（`4b973a4`）で
無くなった旧セクション（「6つの論点とXの声」「この争点の背景」）を書き換える
前提のまま残っており、`html.index()`が例外で止まっていた。同じ内容は山なみの
論点別パネルと投票セクションの導入文に統合済みと確認し、該当ブロックとその
専用検証（temp-bar-wrap基準）を削除して解消（`54d4888`）。

## 4論点795件の編集再読

対象範囲・効果・給付比較・事業者負担の4論点で、独自性検査の上限（40%）に対し
合計795件（今回分＋以前からの積み残し）が未読だった。bukatsu-chiikiで確立した
並列読み込み手順（対象件数÷25件を並列数の目安に）をそのまま適用し、33バッチ・
新規サブエージェントで既存区分（bucket）へ割り当て。完了後、機械検査（件数・
ID集合・重複・区分の妥当性）に加え、バケット分布が偏った2バッチを本文まで戻して
個別確認、論点ごと12件以上の抜き取りも実施し、全て正しい割り当てと確認した。

## 本番反映

`--apply-promotion`は成功したが、正典を事前に候補へ手動差し替えたため
`collect_delta`が0になる自己招来の事象が発生（fukushuto・koshitsuと同型）。
実際の新規件数624件へ手で修正し`sync_portal_stats.py`で作り直した。マージ時に
`company/data-backup-status.json`・`docs/index.html`で衝突（別セッションの
X投稿日次記録との重複、bukatsu-chiiki等と同型）。オーナー確認のうえ
`sync_portal_stats.py`／`backup_private_data.py`で作り直して解消。マージ後の
`verify_adoption_registry.py`もmain側の変更で台帳が古くなっておりNGだったため
`build_adoption_registry.py`で作り直した。標準検査（4種）・`unittest`970件・
`run_public_checks.py`いずれも最終的にNG0件。公開サイトで件数・トップページの
「+624件」表示を確認済み。作業ツリー（`../isa-wt-task69-consumptiontax`）は
反映後に削除済み。

## 残り課題（持ち越し）

bike-blue-ticket・constitutional-amendmentも`refresh_adapters/*.py`が専用の
`*_process_sections.py`を自動実行する構成だが、2026-09-18の確認でFACT_CHECK系
マーカーは最初から存在していたと判明済み（koshitsu-tenpakaiの訂正記録を参照）。
この2テーマの定期更新に着手する際は「マーカー消失」ではなく、
apply_public_countsの山なみ分岐漏れ・正典先行差し替え・number_provenance
同期漏れの3点を個別に確認すること。
