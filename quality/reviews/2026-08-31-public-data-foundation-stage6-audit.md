# 課題57 段階6：総合検査と独立レビュー

作成日: 2026-08-31
状態: 完了。公開可否に関わる検査すべて成功、重大指摘0件
対象: 公開10テーマ、トップ、sitemap、公開データ契約全体

---

## 1. 実行した検査（設計書「段階6」の10項目）

| # | 検査 | コマンド | 結果 |
|---|---|---|---|
| 1 | 公開データSchema・完全照合 | `verify_public_registry.py --public-only` / `--against-private` | OK（10テーマ、catalog整合／非公開正典と完全一致） |
| 2 | 公開10テーマの `verify_theme_page.py` | 引数なし（全テーマ） | 再生成可能性 11テーマ／NG 0件、全テーマ結果 11件／NG 0件 |
| 3 | `verify_top_page.py` | `--allow-overdue-collect`（公開経路と同じ引数） | WARN 1件（下記6節）、exit 0 |
| 4 | `verify_number_provenance.py` | 引数なし | 数字の出所 全テーマ／NG 0件 |
| 5 | SEO・sitemap検査 | `seo/validate_theme_seo.py` / `seo/check_source_links.py` | いずれも exit 0 |
| 6 | ドメイン移行回帰テスト | `unittest tests.test_domain_migration` | 成功 |
| 7 | 投票・GA4・AdSense・Supabase・OGP・topicId・選択肢順序の回帰テスト | `unittest tests.test_supabase_votes tests.test_share_utm` ほか関連24件、投票の`vote-store.test.mjs` | すべて成功 |
| 8 | 全unittest | `unittest discover -s tests` | **353件成功** |
| 9 | 2回生成差分0 | 生成器チェーンを2周実行（下記2節） | 1周目・2周目とも `git status` に変化なし |
| 10 | `git diff --check` | | 指摘なし |

## 2. 「2回生成して差分ゼロ」の実地確認（10テーマ横断）

段階4までは各テーマの `--check` で個別に確認していたが、段階6では公開経路の
生成チェーン全体を通しで2周実行した。

```
build_public_registry.py --all
sync_issue_counts.py
seo/apply_theme_trust.py
sync_portal_stats.py
seo/generate_seo_assets.py --site-url https://sns-reaction-map.jp/
verify_sample_periods.py --generate
build_data_sheet.py
```

1周目実行後・2周目実行後のどちらも `git status --short` に差分が出ない。
`refresh_topic.py` の候補生成が実際に呼ぶ順序（`prepare_public_candidate_bundle`）と
同じ並びで確認した。

## 3. 独立レビュー観点

設計書が挙げる5観点を確認した。

**正典の重複** — `issue_counts.source` を持つ旧方式の残存は0件
（`configs/*-reaction-map.json` を全件grep）。`data/issue-counts/` ディレクトリは
既に存在せず、DATA_REFRESH.mdの課題29対応が反映済み。

**旧HTML・旧SQLite・旧ルートからの逆流** — `data/reaction_map.sqlite3` を読む
生成スクリプトは無い（`import_reactions_to_sqlite.py` が書き込み専用で存在するのみ、
どこからも呼ばれていない）。旧ルート（`issue-stance-lab.github.io`）への参照は
生成器コードに無い。

**公開JSONへの内部情報混入** — `data/public/` 配下11ファイルの全キーと全文字列を
走査し、投稿URL（x.com/twitter.com）・`social-samples/`・`configs/` のパス・
スクリプトファイル名・@ユーザー名・ペルソナ関連語のいずれも0件を確認。
公開JSONのキーは `collected_count` / `opinion_count` / `issues[].{label,count,stances,intensities}`
など、集計値と固定ID・ラベルだけで構成される。

**10テーマの契約適合** — `test_public_data_contract.py` で
①public-data-taxonomy.json のテーマ集合が `published: done` の10テーマと完全一致
②各テーマの論点に「その他」が1つずつ、IDにテーマ接頭辞の重複なし
③段階4で追加した「全10テーマの`basis`が`public_json`」「全10テーマのadapterに`finalize`」
を確認。takaichi（`published: unlisted`）はcatalog・taxonomyのどちらにも含まれない
ことも確認した。

**既存機能の保全** — 投票（`vote-store.test.mjs` 3件）、Supabase、UTM共有、
論点順・投票choiceIdxの固定検査（bike / elderly / fukushuto の taxonomy テスト）を
含む353件のunittestが全て成功。

## 4. 課題54への引き渡し観点（先行確認）

段階7の前に、課題54（3D実装）が読むはずのものが揃っているかを確認した。

- `data/public/catalog.json` … 10テーマの集計サマリ、totalsに `theme_count=10` /
  `opinion_count=10030` / `collected_count=12792`
- `data/public/themes/{theme}.json` … テーマ別の論点・立場・強度分布、
  `source_sha256` で非公開正典との鮮度を確認可能
- `configs/public-data-taxonomy.json` … 安定した論点／立場ID
- いずれもHTMLや設計書に固定数字を書いていない（値は全て生成器の出力）

## 5. 一般公開・Search Console再確認・AdSense再申請

いずれも実施していない。今回の変更はすべて `docs/school-nickname-ban-reaction-map.html`
を含め、main未pushのブランチ上で完結している（`git log --oneline origin/main..main`
で確認、本レビュー時点で17コミット）。

## 6. WARN 1件（公開物の整合不良ではない）

```
WARN  collect_at 期限超過: ai-copyright（2026-08-30）, constitutional-amendment（2026-08-30）,
      fukushuto（2026-08-30）
```

段階5で実装済みの「運用警告と公開停止の分離」（`--allow-overdue-collect`）により
`WARN` として表示され、`verify_top_page.py` はexit 0。3テーマの収集予定日超過は
データ更新側の遅れであり、公開データ契約・公開10テーマの整合とは別の課題として
`TASK_BOARD.md` の通常運用（`DATA_REFRESH.md`）側で扱う。

## 結論

**段階6の成功条件を満たした。**

- 公開可否に関わる検査がすべて成功
- 警告（収集予定日超過）と失敗（整合不良）が分離されている
- 独立レビューの重大指摘は0件
- 生成チェーンの2周実行記録・全353件unittest成功を本記録に保存
