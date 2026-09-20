# 課題69: ai-copyright 定期収集・本番反映の詳細（2026-09-20）

tasks/task-69.md が400行上限のため切り出した。

## 収集

Yahooリアルタイム検索478件を取得、重複10件を除く新規468件をHermes（kimi-k2.6）で
分類。関連354件・意見272件。累積正典3,812→4,280件・意見2,593→2,865件へ統合。
取得期間2026-06-22〜2026-09-20（`sample_period_source: recovered_fetched_at_utc`）。
次回収集は9/27。8日超過していた収集停止を解消（`collect_at`/`refresh_at`とも
2026-09-12で止まっていた）。

## 分類器のバグを発見・修正

`classify_aicopyright_arena_hermes.py` の `parse_response()` が468件中180件目で
`RuntimeError: Hermes batch failed: Invalid control character` で停止。原因は
投稿本文のハイライトマーカー `\tSTART\t...\tEND\t`（Yahooリアルタイム検索の強調表示
由来）がHermesの要約・理由フィールドへそのまま引用された際、生のタブ文字を含む
JSON文字列を標準の `json.loads()`（既定 `strict=True`）が拒否したこと。
`strict=False` へ変更し、`--resume` で残り288件を再分類して解消。分類基準・
プロンプト・taxonomyは無変更（`script_sha256`は変わるため、`refresh_topic.py`が
保存した `classification-provenance.json` の `output.classified_sha256` 欠落
（`--resume`未完了扱い）を、実際に完了した`classified-wave.json`のSHA256で
手動補完して解消した）。

他の10テーマの分類スクリプトも同じ `json.loads(match.group(0))`（strict指定なし）
パターンを使っており、同種の投稿本文ハイライトマーカーを含む可能性があるため、
同じ不具合を踏む余地が残っている（今回はai-copyrightのみ修正、横展開は未実施）。

## 「語られていない争点」4件の母数更新

新規272件（意見）を各争点の検索語（廃棄|除去請求／パブリシティ／電子透かし|C2PA|
来歴／robots.txt|クローラ|オプトアウト）で再検索し、新規の一致なしを確認（関連投稿
全体でも1件のみヒットしたが意見でなく別文脈のため対象外）。母数を2593→2865へ更新
（`data/verification/ai-copyright-sunk-continents.json`）。編集再読5論点はいずれも
未読率10%前後で上限40%に余裕があり、追い読みは不要と判断（koshitsu-tenpakai・
constitutional-amendmentと同型の軽量な再読で足りた）。

## 山なみ区画の外にあるのに件数を持つ箇所を発見・解消

「論点ごとのX投稿」（`#issue-cards`）の件数バッジ・ヒーローの「議論の中心」・
「編集・分析情報」内の収集件数説明文が、`build_ai_copyright_arena.py` の山なみ
移行後ガード（山なみページには`apply_background()`以外の書き換えを行わない設計）の
対象外のまま初回変換（2026-09-14）以来一度も更新されていなかった。
`refresh_planet_section.py` に `_sync_ai_copyright_method_text()` を新設し
`TOPIC_METHOD_TEXT` へ登録して解消（他テーマの `_sync_bike_method_text` 等と同型）。

あわせて2件の見落としを解消:
- `number_provenance.exclude_selectors` に `note` が無く「本文確認後に追加された
  投稿N件は、本文確認の対象外です」の注記が説明できない数字として検出されていた
  （constitutional-amendment・henoko-student-accidentと同型）
- 山なみでは無害・未使用のアリーナデータJS（`docs/ai-copyright-arena-data.js`）が
  正典追従から漏れており `test_published_page_matches_canonical` が失敗。
  `build_ai_copyright_arena.py`（`--skip-issue-counts`のみ、`--public-counts-only`
  ではない）を実行して解消

## マージ時の衝突

`scripts/refresh_planet_section.py` の `TOPIC_METHOD_TEXT` 辞書で、並行して
fukushuto・koshitsu-tenpakai用エントリを追加していた別セッションと衝突（同じ辞書へ
別々の新規キーを追加しただけの単純な衝突、両方保持で解消）。`company/
data-backup-status.json` は通常どおり `--ours` 採用後 `backup_private_data.py` で
作り直し。

マージ直後、課題77案1（`docs/data/`ミラー・`docs/data/catalog.json`）と採用台帳が
ai-copyrightブランチの分岐後にmainへ入っていたと判明し、`build_public_registry.py
--all`・`build_adoption_registry.py` を再実行して解消（`test_docs_mirror_exists_
and_matches_byte_for_byte`・`verify_adoption_registry.py`）。

## 検査・確認

標準4検査（`verify_theme_page.py`／`verify_number_provenance.py`／
`verify_themes_yaml.py`／`verify_update_provenance.py`）・unittest 1007件
（マージ後のmain）・`run_public_checks.py`・`verify_top_page.py
--allow-overdue-collect`いずれもNG0件（elderly-license-revocationの期限超過NGの
みマージ前後とも残るが本テーマと無関係の既知の状態）。ローカルサーバーで
デスクトップ・375px幅とも実機確認（意見数・議論の中心・論点別内訳・論点ごとの
X投稿・編集分析情報の件数、コンソールエラー0件、横スクロールなし）。push後の
CI（公開ファイルの検査／Deploy to GitHub Pages）・公開サイト・トップページの
反映も確認済み。

note記事の更新要否: 前回公開時（意見2593件）との比較でスタンス・論点とも比率
変化は最大0.5pt。更新不要と判断しスキップ。

## 残作業・持ち越し

- 分類器の生タブ文字バグは他10テーマへの横展開が未実施（踏む前提は不明、発生時に
  同じ対処＝`strict=False`で解消できる）
- 旧worktree `../isa-wt-ai-copyright-20260907`（mainと差分ゼロ、2026-09-05最終
  コミット）が削除されずに残存していたのを発見。今回のタスクの範囲外のため未着手
