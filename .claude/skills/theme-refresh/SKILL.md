---
name: theme-refresh
description: >-
  テーマの定期収集（データ更新）を1回ぶん通す手順。収集→Kimi分類→今回分の全件本文確認（読み手2名の伏せ読み→
  突き合わせ→編集担当の確定）→新論点チェック→記録→候補生成→監査→オーナー承認→正典反映→本番反映（release スキル）。
  「◯◯を進めて」「定期収集を進めて」「◯◯の更新回を回して」「ループ回して」でデータ更新の番になったとき、必ずこのスキルを読むこと。
  2026-10-09の新ルール（今回分は同じ回で全件本文確認し、判断できない投稿は意見外として残す）と、
  2026-10-11からの新論点チェックを、別セッションでも同じ品質で回すための手順書。
---

# テーマの定期収集（新ルール＋新論点チェック）

## この作業は何か

`THEMES.yaml` の `collect_at` が来たテーマについて、Yahooリアルタイム検索で新しい投稿を集め、
今回の新規投稿を**全件、人（編集部AI）が本文を読んで**意見かどうか・論点・立場・理由区分を確定し、
公開ページまで反映する。1テーマ1セッション、公開直前にオーナー承認（`OPERATIONS.md` データ更新）。

所要の目安: 新規100件で2〜3時間（読み手は並行実行なので件数より待ち時間が支配的）。

## 最初に読む5行

- **自動分類（Kimi）の結果だけで意見数を決めない。** 読み手は自動分類を見ずに判定し、編集担当が突き合わせる。
- **判断できない投稿は保留にせず「意見外」として候補に残す**（10/9の新ルール）。保留は増やさない。
- **新論点チェック**: 読み手が「既存論点に収まらない」話題名を付け、`new_issue_check`（その他の割合・候補名ごとの件数）を評価記録に残す。
  目安は「その他が今回の意見の5%超、または同じ趣旨が20件以上」。超えても即新設ではなく、監査に書いてオーナーに提案する。
- **作業ツリーは専用に作る**（`OPERATIONS.md` ⓪）。非公開正典は最新バックアップから復元し、`node_modules` は共有ツリーから link する。
- テーマ固有の罠は `DATA_REFRESH.md` の「◯◯の定期更新」節と `configs/wave_review/<topic>.yaml` の `notes` に書いてある。初めてのテーマは必ず読む。

## 手順

### 1. 準備

```sh
cd <共有ツリー> && git fetch origin main && git rev-list --left-right --count main...origin/main   # 0 0 を確認
git worktree add ../isa-wt-<topic>-<MMDD> -b task/<topic>-refresh-<MMDD> main
cd ../isa-wt-<topic>-<MMDD>
tar -xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . && rm -f manifest.json
ln -s ../main/node_modules node_modules
rsync -anc --itemize-changes social-samples/ ../main/social-samples/ | grep -v '^\.'   # 何も出ないこと（出たら共有ツリーが新しい）
```

### 2. 収集とKimi分類（時間がかかるので裏で）

```sh
python3 scripts/refresh_topic.py --topic <topic> --date <YYYY-MM-DD> --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

成功の形: `.staging/refresh/<topic>/<run-id>/` に `new-only.json`・`classified-wave.json`・`report.json` ができる。
`report.json` の `new` が今回の新規件数。`<run-id>` は以後の `--run-id` に使う。
`sample_period_source: owner_confirmed` のテーマ（自転車・高齢者・生成AI）は `THEMES.yaml` の `sample_period` の終わりを今回の日付へ手で伸ばす。

### 3. 読み手の伏せ読み（収集と並行してよい）

```sh
python3 scripts/wave_review/wave_review.py batches --topic <topic> --stage .staging/refresh/<topic>/<run-id> --work <作業フォルダー>
```

成功の形: `batch-N.json`（本文だけ、自動分類なし）と、読み手A/B用の指示文 `prompt-batch-N-A.md` / `-B.md` ができる。
各バッチにつき **Sonnet のサブエージェントを2本（A・B）**、指示文をそのまま渡して並行実行する（55件×2本で約1分）。
出力は `out-batch-N-A.json` / `-B.json`。`configs/wave_review/<topic>.yaml` が無いテーマは、初回に作ってから回す
（論点・立場の説明、意見の線引き、新論点の例。既存5テーマのものを手本にする）。

### 4. 突き合わせと編集担当の確定

```sh
python3 scripts/wave_review/wave_review.py compare --topic <topic> --stage <stage> --work <作業フォルダー>
```

成功の形: `読み手一致 N 食い違い M / 区分未確定 K / Kimiと一致 J` と `review.txt`。
`review.txt` を**本文ごと読む**（DIFF と BUCKET CONFLICT は全件。KIMI DISAGREES は読み手2名が一致しているので、
気になるものだけ）。確定を `decisions.json` に書く:

```json
{"_normalize": {"読み手が付けた論点名": "統一した論点名"},
 "12": {"is_opinion": true, "main_issue": "…", "stance": "…", "bucket": "…", "note_add": "陰謀論的。代表投稿に使わない"},
 "27": {"is_opinion": false, "exclude_kind": "undecidable"},
 "45": {"bucket": "…"}}
```

```sh
python3 scripts/wave_review/wave_review.py decide --topic <topic> --stage <stage> --work <作業フォルダー> --decisions <作業フォルダー>/decisions.json
```

成功の形: `確定済み N件。次は apply`。未確定・不正があれば番号つきで止まる。

線引きの基準（これまでの回で固めたもの）:
- 同一文面の連投・署名の定型文は、1件ずつ主張を述べていれば1件1意見で数える。`note` に「同文の連投」と書き、監査に明記する。
- 皮肉で真意が取れない・問いだけ・断片は意見外（`undecidable`）。本文に自分の評価が読めれば中立の意見。
- 中傷・排外・陰謀論の表現は `note_add` に書く（apply が `article_usable: false` にする＝代表投稿に使わない）。
- テーマの主題でない投稿（例: 高齢者テーマで危険運転者への「免許返納しろ」、芸能人の返納）は `possibly_off_topic`。

### 5. 記録へ反映

```sh
python3 scripts/wave_review/wave_review.py apply --topic <topic> --stage <stage> --work <作業フォルダー> --date <YYYY-MM-DD>
```

成功の形: `補正 N件 → data/verification/<topic>-wave-review-<YYYYMMDD>.json`、
`証拠 … → quality/reviews/<date>-<topic>-wave-reading.json`、`新論点チェック: {...}`、`理由区分の追加: {...}`。
**自転車は apply の代わりに** `python3 scripts/wave_review/bike_plan.py --stage <stage> --work <作業フォルダー> --date <date>` →
`python3 scripts/build_bike_refresh_candidate.py --stage <stage> --plan <stage>/review-plan.json --update data/bike-blue-ticket_editorial-updates/<YYYYMMDD>.json`。

adapter に `review_candidate`（補正記録を候補へ適用する関数）が無いテーマは、`scripts/refresh_adapters/consumption_tax.py` の
`review_records_path` / `review_candidate` をテーマ名だけ替えて移植する（副首都・消費税・高齢者・憲法は済み）。

### 6. 候補生成・完了記録

```sh
python3 scripts/refresh_topic.py --topic <topic> --date <date> --run-id <run-id> --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --resume --prepare-promotion
# 1回目は「今回分の完了記録がありません」で止まる（候補 cumulative-candidate.json はできる）。
python3 scripts/wave_review/wave_review.py register --topic <topic> --stage <stage> --work <作業フォルダー> --date <date>   # 再読共通台帳があるテーマだけ
python3 scripts/refresh_completion.py prepare --topic <topic> --stage <stage>
python3 scripts/wave_review/wave_review.py fill --topic <topic> --stage <stage> --work <作業フォルダー> --date <date>
python3 scripts/refresh_completion.py check --topic <topic> --stage <stage>      # 専用再読ファイルを adapter が候補側に作るテーマ（自転車）は落ちてよい
python3 scripts/refresh_topic.py ... --resume --prepare-promotion                 # 2回目。promotion-manifest.json ができれば成功
```

ここで止まる定番と直し方:
- 「語られていない争点の母数が確認時点のまま」→ `wave_review.py sunk-check` で候補を出し、本文を読んで
  `data/verification/<topic>-sunk-continents.json` の `sns_base`（今回の意見数）・`checked_on`・`sns_note`・`machine_hits`/`excluded` を直す。
- 「主張の該当投稿数が照合データと違う」→ 事実確認の主張（`data/<topic>_claim_posts.json`）に今回の該当投稿を足したら、
  `build_<topic>_process_sections.py --input <候補> --html-template <元HTML> --output-html <捨て先> --verification-dest data/verification`
  で `-claims.json` の写しを作り直し、`CHECKED_AT` を今回の日付にする。
- 「制度の確認日 checked_on が主張の照合日より古い」（高齢者）→ 一次資料を取り直して `configs/<topic>-opening.json` の `checked_on` を進める（取り直した事実を一次資料メモに追記）。
- 「再読データの明細と立場の対応表の投稿が一致しません」（憲法・自転車）→ 候補コピー（`<stage>/public-candidate`）の中で
  `scripts/<topic>_reread_stances.py --made-on <date>` を回し、出力を作業ツリーの `data/` にコピーする。
- 「再読済み投稿の…対象集合が変わりました」→ register 漏れ、または生成器が候補ではなく正典を母数にしている（`DATA_REFRESH.md` 副首都・高齢者の節）。

### 7. 監査と承認依頼

候補ページ（`<stage>/public-candidate/docs/<topic>-reaction-map.html`）で収集・意見件数、取得期間、潮目のラベル、照合日を確認し、
`quality/reviews/<date>-<topic>-refresh-review.md` に監査を書く（数の表・読み方・新論点チェック・候補の確認・残るリスク）。
`themes/<topic>.md` 末尾に経緯を1段落追記。作業ツリーをコミットしてオーナーに報告し、**「公開して」を待つ**。
報告には必ず、取得/重複/新規、意見/意見外、Kimiからの補正数、累計、新論点チェックの結果、直した生成器、確認していないことを書く。

### 8. 反映（承認後）

```sh
python3 scripts/refresh_topic.py ... --resume --apply-promotion
python3 scripts/build_data_sheet.py && python3 scripts/build_adoption_registry.py && python3 scripts/sync_portal_stats.py
python3 scripts/backup_private_data.py --dest /Volumes/HD-LE-B/issue-stance-private-backups
python3 scripts/backup_adoption_evidence.py --dest /Volumes/HD-LE-B/issue-stance-private-backups
python3 scripts/data_asset_inventory.py && python3 scripts/verify_data_assets.py && python3 scripts/data_asset_inventory.py --check
```

全体テストで落ちる期待値テスト（件数・日付の固定値、読書面の試作ページ）は今回の値に合わせて直す。
作業ツリーで5検査（`verify_theme_page` / `verify_number_provenance` / `verify_top_page` / `unittest discover` / `run_public_checks`）を通してコミットし、
**`release` スキルへ**（main が進んでいれば先に作業ブランチへ取り込む）。

## やらないこと

- Kimi の `is_opinion` をそのまま意見数にしない。読み手の出力を見ずに決めない。
- 過去回の正典は触らない（線引きを変えたときは監査に「過去回に同種が残る可能性」と書く）。
- 新論点を黙って新設しない（ページの論点ナビ・山なみ・調査条件・note まで動く別作業）。
