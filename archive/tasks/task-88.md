# 課題88: takaichi（高市文春問題）テーマの廃止（このサイト初のテーマ削除）

**状態**: 完了（2026-09-22、オーナー承認）
**発見**: 2026-09-22（課題87の一次資料照合後、公開の見込みが無いまま`unlisted`＋
`event-driven`で残すことの是非をオーナーに確認したところ、「削除と同じ」「催促の
ループに陥る」との指摘を受け、廃止を決定）
**関連**: 78（Git履歴からの完全消去は技術的に見送り済み）／87（廃止判断の根拠と
なった一次資料照合）

## 何が起きていたか

takaichiは2026-08-21に`published: unlisted`化（存命個人実名の疑惑が主題で
コンテンツが薄く、AdSense審査上不利という理由。検索・サイト内導線・sitemapから
除外、データ・ページは残置）。2026-09-22、8/20から1ヶ月超過していた定期収集を実施し
（147件新規・118件意見）、本文確認で実名侮辱表現1件・一次資料と食い違う断定2件を
発見（課題87で一次資料照合、いずれもeditorial_overrideで除外）。

この更新回を公開候補化しようとしたところ、`--prepare-promotion`が
2026-08-21のunlisted化で削除された`refresh_at`欄を前提としており、スクリプトエラーで
停止（正典・公開ページへの影響なし）。unlistedの理由は今回の本文確認でむしろ
裏付けられ、解消していないと判明したため、公開候補化を見送り、`collect_mode`を
`event-driven`へ切り替えて定期収集の催促を止めた。

この状態（非公開・event-driven）についてオーナーに「それなら削除と同じだし、
後から収集期限ですと催促されるループに陥る」との指摘を受け、テーマ自体の廃止を
決定した。

## 対応

専用worktree（`isa-wt-takaichi-retire-20260922`）で実施。読み取り専用の
Exploreエージェントで影響範囲を洗い出し（THEMES.yaml本体・scripts/testsの
ハードコード・configs・docs画像資産・data/verification・company・tasks・archive
〈触らず〉に分類）、以下を実施した。

### 削除したもの

- `THEMES.yaml`のtakaichiエントリ
- `docs/takaichi-reaction-map-standard.html`・`docs/takaichi-arena-data.js`
- `docs/images/topics/takaichi/`（画像25枚）・`docs/ogp/takaichi.png`
- 現行ページから無参照だった孤立画像4枚（`docs/takaichi-heatmap-*.png`等、
  テーマ削除より前から孤立していたもの。ついでに整理）
- `configs/topics/takaichi.yaml`・`configs/takaichi-reaction-map.json`・
  `configs/takaichi-summary-ui.json`
- `scripts/refresh_adapters/takaichi.py`・`scripts/upgrade_takaichi_arena.js`・
  `scripts/classify_takaichi_arena_hermes.py`・`scripts/classify_2d_takaichi.py`
- `data/verification/takaichi.json`・`data/verification/updates/takaichi/`（4更新回分）
- `tests/test_takaichi_adapter.py`

### 直したもの（消しただけでは壊れる箇所）

- `configs/refresh-pipeline.yaml`のtakaichiブロック
- `scripts/verify_builder_rebuildability.py`の`BUILDERS`タプル
- `tests/test_theme_hero_assets.py`の`REMAINING_HEROES`辞書
- `tests/test_refresh_topic.py`：冒頭の無条件import・専用テストメソッド・
  `AdapterImportTest`のタプル
- `scripts/recompute_public_unreviewed.py`の`expected_canonical_files=11`→`10`
  （**ユニットテストには捕捉されない「静かな罠」**。CLIのデフォルト引数で、
  実運用で走らせたときだけ`ValueError`になる）
- `scripts/inject_tide_widget.py`のTHEMES辞書からtakaichiエントリを削除
  （課題38「公開中のページを古いデータへ巻き戻す」のtakaichi分をこれで解消）
- `data/verification/adoption/decision-evidence.json`の`decisions.takaichi`と
  `cohorts.original_427.topics.takaichi`を削除（`verify_adoption_registry.py`が
  「decisionsのトピックは現行THEMES.yamlの部分集合」を要求するため。Git履歴には残る）
- `scripts/build_adoption_registry.py`に防御を追加（cohortsが現行THEMES.yamlに
  無いトピックを参照していても、KeyErrorでクラッシュせず静かに追跡対象から外す。
  今後同種の廃止をする際、decision-evidence.json側の対応漏れがあっても
  `verify_adoption_registry.py`のNGとしてはっきり気づけるようにするため）
- `run_public_checks.py`の`PRIVATE_DATA_TESTS`除外リストから、削除済みテスト名
  （`test_takaichi_adapter`）を除去（残したままだと`SystemExit`で止まる）
- `scripts/seo/apply_background_sources.py`の到達不能だった特別分岐を削除（衛生）
- `scripts/build_data_sheet.py`の見出し「11テーマ」を動的な件数表示へ変更
- `tasks/task-38.md`・`TASK_BOARD.md`の課題38エントリからtakaichiを除去
  （残るはai-copyright未対応のみ）
- `company/HANDOFFS.yaml`の`theme-refresh-20260827`を、テーマ廃止に伴う終了状態へ更新
  （実行不能になった`next_action`の書き換え、`canonical_sources`の参照先修正）
- `themes/takaichi.md`を`archive/themes/takaichi.md`へ移動し、廃止の経緯を追記

### 再生成したもの

`build_adoption_registry.py`・`verify_sample_periods.py --generate`・
`build_data_sheet.py`・`sync_portal_stats.py`・`data_asset_inventory.py`を実行し、
台帳・DATA_SHEET.md・company/data-assets.jsonを現行10テーマへ同期した。

### 削除しなかったもの

- 非公開正典（`social-samples/takaichi_*`）：Git追跡外のため対象外。外付けバックアップに残る
- Git履歴：完全消去は課題78で見送り済み。過去のコミットには本文付きデータが残り続ける
- `quality/research/takaichi-primary-sources.md`・`quality/reviews/`配下・
  `archive/`配下の過去記録：史実として維持
- `data/review-ledger.json`のtakaichiキー：`build_review_ledger.py`の再実行で
  自然に消える設計のため手動削除は不要と判断（未実施・次回の同スクリプト実行で解消見込み）

## 検査結果

`python3 -m unittest discover -s tests`（1046件）・`scripts/run_public_checks.py`・
`scripts/verify_theme_page.py`・`scripts/verify_number_provenance.py`・
`scripts/verify_top_page.py`・`scripts/verify_themes_yaml.py`・
`scripts/verify_task_board.py`、いずれも成功。表示されるテーマ数がすべて
「10テーマ」に更新されていることを確認。

## 再利用のための記録

今後同種の作業を行うときの手順として
[`.claude/skills/retire-topic/SKILL.md`](../.claude/skills/retire-topic/SKILL.md)
を新設した。
