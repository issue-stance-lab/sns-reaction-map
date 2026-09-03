# 課題29: ページ内件数表示と sample_file の突き合わせ

**状態**: **完了（2026-08-08）**。全11テーマの論点件数を正典 `sample_file` から再現できる状態にし、`data/issue-counts/` を削除した
**概要**: S1 で「分類済み投稿数」をトップに出す根拠を `sample_file` の実レコード数に統一したが、THEMES.yaml のコメント記載や各テーマページ内の件数表示と食い違うテーマがある。トップとテーマページで違う数字が出ると、S1 で解消した矛盾が別の場所で再発する
**乖離の例**:

| テーマ | THEMES.yaml コメント | sample_file 実数 |
|---|---|---|
| bukatsu-chiiki | 旧2D 245件 | 467 |
| constitutional-amendment | 552件 | 646 |
| school-nickname-ban | 134件 | 374 |
| henoko-student-accident | 356件 | 363 |
| consumption-tax-cut | classify2d: n-a | 667 |

**手順**: ①各テーマページが表示している件数がどの数字か（2D分類 / Hermes論点分類 / 収集総数）を特定 ②`sample_file` の数と一致するか確認 ③一致しない場合、どちらが「分類済み投稿」の定義に合うかを決めて統一 ④`verify_top_page.py` に「トップの件数と各テーマページの件数が矛盾しない」検査を追加
**備考**: 2D分類と Hermes 論点分類で対象件数が違うのは妥当な可能性が高い。その場合はページ側の表記を「論点分類 ○件」等に変えて、何を数えた数字かを明示する

**2026-08-02（S8）に判明した、①の調査結果**

課題30の件数併記のために全11テーマの論点別件数の出所を洗ったところ、**7テーマは `sample_file` から再現できたが、4テーマは再現できるファイルがリポジトリに残っていなかった**。

| テーマ | 論点別件数の出所 | `sample_file` から再現できるか |
|---|---|---|
| ai-copyright | sample_file（全件） | ✅ 126/79/73/46/40/31 |
| bukatsu-chiiki / consumption-tax-cut / school-nickname-ban / takaichi | sample_file（`is_opinion` のみ） | ✅ |
| fukushuto | sample_file（全件） | ✅ |
| bike-blue-ticket | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |
| **constitutional-amendment** | ページ内 `const P`（422件） | ❌ sample_file は646件（旧422件の分類が残っている） |
| **henoko-student-accident** | `docs/henoko-arena-data.js`（265件） | ❌ sample_file は363件 |
| **koshitsu-tenpakai** | ページ内 `SM_RAW` + JS の `arenaIssueOf()`（268件） | ❌ sample_file は347件。しかも公開中の h3 件数は `koshitsu-tenpakai_hermes_prev_synthetic.json` 由来 |
| **elderly-license-revocation** | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |

**暫定措置**: 上記4テーマ分を `scripts/extract_arena_issue_assignment.py` でページから1度だけ取り出し、`data/issue-counts/{theme}.json` に固定した。件数併記と検査はこのファイルを読む（ページのHTMLは読まないので、spanを手で書き換えれば検査が落ちる）。

**2026-08-07 対応済み（2テーマ）**: elderly-license-revocation（211件）と bike-blue-ticket（181件）を Hermes で再分類し、結果を正典 `sample_file` の各レコードへ `classification`（main_issue / stance / intensity / summary / reason / confidence / article_usable / risk）として格納した。あわせて次を実施。

- 論点定義を `scripts/elderly_license_taxonomy.py` / `scripts/bike_blue_ticket_taxonomy.py` に切り出し、分類スクリプトと共有（`tests/test_*_taxonomy.py` で固定）
- `configs/{theme}-reaction-map.json` の `issue_counts.source` を削除し、sample_file へ戻した
- 凍結ファイル `data/issue-counts/elderly-license-revocation.json` を削除。bike が依存していた `social-samples/bike_arena_hermes_classified.json` への参照も解消（ファイル自体はGit管理外に残置）
- 再分類前の2D分類のみの正典を `social-samples/{theme}_2d_classified_v1_2d_only.json` として保存
- 再分類でラベルが動いたため、`THEMES.yaml` の `main_issue` 行の内訳も実数へ更新した（elderly 139→95 等）
- 同日に main 側で ai-copyright（7論点・1,606件）と fukushuto も単一ソース化されたため、マージ後は `tests/test_taxonomy_continuity.py` の taxonomy不一致テーマが **0件** になった

**2026-08-07 に判明した未解決点（elderly / bike）**: 論点カードの件数は正典へ揃ったが、**同じページのアリーナ散布データ `SM_RAW` のセクター `i` は旧分類のまま**で、同一ページ内に2つの内訳が並んでいる。

| テーマ | SM_RAW の件数・内訳 | 正典（`classification.main_issue`） |
|---|---|---|
| elderly-license-revocation | 211件 / 139・24・20・9・7・12 | 211件 / 95・14・19・10・9・64 |
| bike-blue-ticket | **268件** / 54・56・16・28・20・94 | 181件 / 38・29・14・14・18・68 |

bike は件数自体も食い違う（SM_RAW は収集総数268件、分類済みは181件）。`verify_theme_page.py` は SM_RAW を検査していないため exit 0 のまま通る。
**発注書**: `configs/prompts/codex/20260807_elderly-bike-arena.md`（`build_elderly_arena.py` / `build_bike_arena.py` の新設と SM_RAW 再注入、検査追加。ブランチ `task/elderly-bike-arena`）

**2026-08-08 対応済み（憲法改正）**: constitutional-amendment は646件を同一条件で再分類し、意見577件に統一した。`scripts/build_constitutional_arena.py` を新設して SM_RAW・論点別の声・スタンス・詳細表を同じ意見集合から再生成し、`issue_counts.source` と凍結ファイルを削除した。

**2026-08-08 対応済み（辺野古）**: henoko-student-accident は363件を意見性付きで再分類し、意見のみをマップと論点件数の母数に統一。`issue_counts.source` と凍結件数ファイルへの依存を解消した。

**残作業なし。** 最後の `data/issue-counts/henoko-student-accident.json` を削除し、`data/issue-counts/` ディレクトリごと不要になった。**課題29は完了。**

**2026-08-08 検査固定**: 全11テーマでマップ・論点・賛否の母数を「意見のみ」に統一。`verify_theme_page.py` に母数一致、ページ全体の管理対象外件数、最大勢力バッジ、昇格順後のビルダ再生成可能性を追加した。差分は config に件数と理由が無ければ許可しない。`DATA_SHEET.md` の再生成忘れも unittest で検出する。
**横展開の完了条件に追加（2026-08-02）**: constitutional / henoko の `data/issue-counts/` 依存は、それぞれのadapter・ビルダー整備と同時に解消する。累積正典またはGit管理する仮名化検証データから論点件数を再現できることをadapter昇格条件とし、暫定ファイルだけを残さない。
