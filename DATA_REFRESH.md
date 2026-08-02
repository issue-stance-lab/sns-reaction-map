# データ更新の運用手順

## 基本方針

- `collect_at` は収集・分類・更新回保存の内部期限。ページを公開できないテーマも予定どおり実行する。
- `refresh_at` は公開まで昇格できるテーマだけに設定する。
- 収集・分類は全テーマで `scripts/refresh_topic.py --topic ...` を使う。
- ページ生成だけを `scripts/refresh_adapters/` のテーマ別adapterへ委譲する。
- `--promote` を付けない限り、累積正典、公開HTML、`updated_at`、`refresh_at` は変更しない。

## 実行前ゲート

本文付き正典と更新回履歴の正規保存先は、次の外付けディスク上のディレクトリとする。

`/Volumes/HD-LE-B/issue-stance-private-backups`

個人サイトとして運用するオーナー判断により暗号化は行わない。生成するtar.gz自体も暗号化されない。ディスクを共有・譲渡・廃棄するときは、保存済みアーカイブを先に削除する。別環境での復元確認が終わるまで本収集は開始しない。

## staging止まりの更新

migration、manual、adapter_candidateのテーマも同じコマンドで収集・分類する。

```sh
python3 scripts/refresh_topic.py \
  --topic consumption-tax-cut \
  --date 2026-08-04 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

処理内容:

1. 先頭1検索語で疎通確認
2. 正典の `refresh_config` にある全検索語で収集
3. tweet_id → URL内status ID → URL → 本文ハッシュの順で重複判定
4. 10件の試験分類後に全件分類
5. 集合・件数・許可ラベル・エラー率を検査
6. `social-samples/updates/<topic>/<date>/` に非公開更新回を保存
7. 保存直後に非公開データをバックアップし、復元検査
8. 仮名化した更新回サマリを `data/verification/updates/` に保存
9. 成功時だけ `last_refresh_attempt_at` と次回 `collect_at` を更新

バックアップが失敗した場合は更新回を確定せず、`collect_at` も進めない。新規0件でも収集成功回として履歴を残すが、公開更新にはしない。

## 公開まで行う更新

`page_update_mode: adapter` のテーマだけ `--promote` を付けられる。

```sh
python3 scripts/refresh_topic.py \
  --topic takaichi \
  --date 2026-08-06 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups \
  --promote
```

更新回保存後にadapterを使って候補ページを2回生成し、冪等性、投票互換性、保護タグを検査する。全検査合格時だけ累積正典・ページ・台帳・SEO・トップ・sitemapを一括昇格する。昇格後にもう一度バックアップし、失敗時は公開側を昇格前へ戻す。

## 周期

- 既定14日
- 新規意見50件以上なら次回だけ7日
- 新規意見20件未満が2回連続なら28日
- 新規0件が2回連続なら `collect_mode: event-driven` に切り替え、`collect_at` を空欄にする
- 収集失敗時は期限を進めず、`verify_top_page.py` の期限超過NGを残す

## ページadapter整備時の追加条件

課題29の暫定的な論点件数ソースも同時に解消する。

- bike-blue-ticket: `social-samples/bike_arena_hermes_classified.json` 依存
- constitutional-amendment: `data/issue-counts/constitutional-amendment.json` 依存
- elderly-license-revocation: `data/issue-counts/elderly-license-revocation.json` 依存
- henoko-student-accident: `data/issue-counts/henoko-student-accident.json` 依存

累積正典またはGit管理する仮名化検証データから論点件数を再現できる状態をadapter昇格条件とする。
