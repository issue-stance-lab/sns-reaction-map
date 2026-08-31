# 課題57 段階4：学校でのあだ名禁止を公開データJSONへ接続（段階4の最後の1テーマ）

作成日: 2026-08-31
状態: 接続完了。公開ページのHTMLは1バイトも変わらない（数字の出所だけが変わった）
対象: school-nickname-ban。前回の調査記録
`quality/reviews/2026-08-31-public-data-foundation-stage4-school-nickname-ban.md` の続き

---

## 1. なぜ今なら接続できるのか

前回（同日）は接続を見送った。理由は「このテーマには昇格確定後に正典から数え直す
後工程（`finalize`）が無く、候補生成そのものが候補ファイルから直接件数を計算している。
公開JSONは手動生成なので、繋ぐと次回のデータ更新で古い件数のまま候補ページが作られる」
だった。

段階5でこの前提が消えた。`refresh_topic.py` の `prepare_public_candidate_bundle()` は
隔離した候補ツリーの中で

1. 候補の累積正典を `sample_file` の位置へ置く
2. `build_public_registry.py --all` で公開JSONを作り直す（＝候補の件数になる）
3. adapter の `finalize()` を呼ぶ
4. `sync_issue_counts.py` を走らせる

の順で動く。つまり `finalize()` の時点で公開JSONは候補と同じ新しい件数を持っている。
このテーマに `finalize()` を足せば、前回心配した「古い件数のまま候補が作られる」は起きない。

## 2. 実装

| 変更 | 内容 |
|---|---|
| `configs/school-nickname-ban-reaction-map.json` | `issue_counts.basis` を `opinion` → `public_json` |
| `scripts/build_nickname_arena.py` | `apply_public_counts()` と `--public-counts-only` を追加 |
| `scripts/refresh_adapters/nickname.py` | `finalize()` を追加（`--public-counts-only` を呼ぶ） |
| `tests/test_nickname_public_counts.py` | 新設（4件） |
| `tests/test_public_data_contract.py` | 全公開テーマ横断の検査を2件追加 |
| `tests/test_issue_count_sync.py` | マップ見出しと公開JSONの一致検査を1件追加 |

### ビルダーのどの関数が公開JSONに置き換わり、どれが残ったか

`apply_public_counts()` が公開JSONから貼り直す（＝数字の出所が公開データ契約へ移った）:

| ページ上の場所 | 使う関数 |
|---|---|
| リード文 | `build_lead` |
| 調査条件（収集件数・取得期間） | `build_research_conditions` |
| 注目ポイント4枚 | `build_stats` |
| 論点カード6枚と内訳文 | `build_explainer_cards` / `explainer_desc` |
| SNS反応マップ見出しの件数 | （直接置換） |
| 投票STEP1とアリーナの `var issues=[...]` の `count` | `build_vote_issues` |
| 論点ナビ | `issue_nav`（今回 `build_issue_blocks` から切り出し） |
| 論点ブロック6つの見出し件数・温度バー・凡例 | `issue_block_head`（今回切り出し） |
| 詳細データの論点別件数表 | `build_details` |

**正典（非公開の投稿データ）から作り続ける**もの。公開JSONには投稿本文・URL・
confidence が入らないため、公開JSONからは作れない:

| ページ上の場所 | 使う関数 |
|---|---|
| アリーナの点（`school-nickname-ban-arena-data.js`） | `build_arena_data` |
| 論点ブロックの代表投稿（`issue-x-grid` の中身） | `representative_posts` / `embed_html` |
| 「世論の潮目」ウィジェット | `refresh_adapters/nickname.py` の `_apply_tide`（更新回どうしの比較。公開JSONは累積しか持たない） |

この切り分けは、先に接続した henoko・constitutional・koshitsu と同じ方針
（点と代表投稿は候補正典から、集計表示は候補公開JSONから）。

### 番号→固定IDの対応表

前回の記録の1節と同じ。今回の変更で論点の並び・`key`・`topic_id`・
`VOTE_CHOICES=18` はいずれも変えていない（`vote_fingerprint` は `count` を
指紋に含めない設計なので、件数が変わっても投票互換性は動かない）。

## 3. 古い公開JSONで貼ってしまう事故を止める

`apply_public_counts()` は、既定の公開JSONを読むときに
`count_by_issue_from_public_json()` を通す。この関数は公開JSONの `source_sha256` を
非公開正典の現在内容と突き合わせ、古ければ `IssueCountError` で止まる。

実地確認: `source_sha256` を壊した公開JSONを置くと

```
ERROR: school-nickname-ban: 公開データJSONのsource_sha256が非公開正典の現在内容と
不一致です（scripts/build_public_registry.py --topic school-nickname-ban を再実行する）
```

で `--public-counts-only` も `sync_issue_counts.py --check` も止まる（確認後、
公開JSONは元に戻した）。

前回の記録が指摘した「2回生成して差分ゼロは通るのに数字だけ古い」という
自動検査のすり抜けは、`tests/test_nickname_public_counts.py` の
`test_new_opinion_reaches_every_count_on_the_page` で塞いだ。公開JSONの件数を
1件増やすと、リード文・マップ見出し・調査条件・論点ブロックの見出し・投票の
`var issues` の5か所すべてが増えることを検査する。増えなければ落ちる。

## 4. 段階4の完了を戻せなくする検査（全テーマ横断）

`tests/test_public_data_contract.py` に2件追加した。1テーマでも元へ戻すと落ちる。

- `test_every_public_theme_reads_its_counts_from_public_json`
  — 公開10テーマすべての `issue_counts.basis` が `public_json`
- `test_every_public_theme_repastes_counts_after_the_public_json_is_rebuilt`
  — 公開10テーマすべての adapter が `finalize` を持つ（無いテーマは候補生成時点の
  数字で止まり、今回塞いだのと同じすり抜けが起きる）

## 5. 検査結果

| 検査 | 結果 |
|---|---|
| `build_nickname_arena.py --check`（正典とページの一致） | OK: 差分なし |
| `apply_public_counts()` を公開ページへ適用 | **バイト一致（`git diff` に `docs/` が出ない）** |
| `sync_issue_counts.py school-nickname-ban --check` | OK（6カード + headings/nav/conclusion） |
| `verify_theme_page.py school-nickname-ban` | OK 16項目、NG 0件（母数は `basis=public_json`（87件）） |
| `verify_theme_page.py`（全テーマ） | 11テーマ / NG 0件、再生成可能性も NG 0件 |
| `verify_number_provenance.py school-nickname-ban` | 拾った72 / 説明できた72 / 説明できない0 |
| `verify_public_registry.py --public-only` | OK 10テーマ、catalog整合 |
| `verify_public_registry.py --against-private` | OK 10テーマが非公開正典と完全一致 |
| 全unittest | 353件すべて成功 |
| `git diff --check` | 指摘なし |

**公開ページのHTMLは変わっていない。** 変わったのは「その数字をどこから作るか」だけ。

## 6. 段階6へ引き継ぐ申し送り

`verify_top_page.py` が現在 exit 1 で落ちる。理由は本作業と無関係で、

```
NG  collect_at 期限超過: ai-copyright（2026-08-30）, constitutional-amendment（2026-08-30）,
    fukushuto（2026-08-30）
```

段階5では「収集予定日超過は `WARN`、公開物の整合不良とは分けて表示する」と決めたが、
`verify_top_page.py` は同じ状態を `NG`（exit 1）として扱っている。段階6の成功条件
「警告が失敗と明確に分離されている」に直接ぶつかるので、段階6でどちらかへ揃える。
