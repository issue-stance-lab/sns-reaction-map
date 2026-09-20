# 課題78: 高齢者免許返納・高市文春問題の正典がGit（公開リポジトリ）に追跡されたまま残っていた

**状態**: 進行中（追跡は解消・外付けバックアップは確認済み。過去分の履歴削除は未着手）
**発見**: 2026-09-20（課題69系、高齢者免許返納の定期更新作業中に発見）
**関連**: 69（定期データ更新）

## 何が起きていたか

OPERATIONS.md・DATA_REFRESH.mdは「本文・URL付きの正典（元データ）はGit管理外にする」という
方針を明記しており、実際に9テーマ（bukatsu-chiiki / ai-copyright / constitutional-amendment /
school-nickname-ban / henoko-student-accident / consumption-tax-cut / fukushuto /
koshitsu-tenpakai / bike-blue-ticket）はこの方針どおり`.gitignore`対象になっていた。

残る2テーマだけこの方針が適用されておらず、`sample_file`が公開リポジトリ
（`github.com/issue-stance-lab/sns-reaction-map`、public）に実際に追跡・push済みだった。

| テーマ | ファイル | 件数 |
|---|---|---|
| elderly-license-revocation | `social-samples/elderly-license_2d_classified.json`（+`_v1_2d_only.json`） | 506件 |
| takaichi | `social-samples/takaichi_hermes_arena_classified.json`（+`.md`） | 761件 |

投稿本文・投稿URL（＝投稿者のXアカウントが分かる）・取得日時などが1ファイルにまとまった形で
公開リポジトリに存在していた。投稿自体は元々公開のX投稿だが、それを集約して誰でも
ダウンロードできる状態に置くのはプロジェクト自身が決めた方針に反する。

`scripts/backup_private_data.py`は「Gitが追跡していないsample_file」だけを対象にする作りのため、
この2テーマは外付けディスク（`/Volumes/HD-LE-B/issue-stance-private-backups`）への正式な
バックアップ対象からも漏れていた。

## 2026-09-20: 追跡解消・外付けバックアップ確認

作業ツリー`../isa-wt-canonical-gitignore-fix`（ブランチ`task/canonical-gitignore-fix`）で実施。

1. `.gitignore`に2テーマのパターンを追加（`social-samples/elderly-license_2d_classified*.*`・
   `social-samples/takaichi_hermes_arena_classified*.*`）
2. `git rm --cached`で4ファイルの追跡を解除（ローカルの実体は残す）
3. `OPERATIONS.md`⓪の手順で最新バックアップを復元し、11テーマ全ての正典が揃った状態で
   `backup_private_data.py --dest /Volumes/HD-LE-B/issue-stance-private-backups`を実行。
   新しいアーカイブ（`private-data-20260920T220332703836.tar.gz`、
   SHA-256: `edbd123ef3053ba22f7e29d76b0e58018a5e61d42d8ef477e9830351c6cddc6f`）に
   2テーマ分が含まれることを確認済み
4. `data_asset_inventory.py`で`company/data-assets.json`を再生成（Git追跡変更を反映）
5. `verify_data_asset_restore.py --backup-root /Volumes/HD-LE-B/issue-stance-private-backups`
   で復元検査OK。`company/data-restore-status.json`を更新
6. `unittest discover`986件（4件skip）・`run_public_checks.py`いずれもNG0件

このブランチはmainへのマージ・push（オーナー確認後）待ち。

## 残っている課題（未着手）

**過去にGitHubへpushされた分は、この対応では消えない。** Gitの変更履歴（過去のコミット）には
まだ両テーマの本文付きデータが残っている。完全に消すには履歴の書き換え（`git filter-repo`等＋
強制push）が必要で、現在進行中の26個の並行作業ツリー・ブランチすべてに影響が及ぶ大掛かりな
作業になる。

**次にすること**: 履歴からの完全削除に着手するかどうか、影響範囲（既存の全worktree・
未マージブランチへの影響、force-pushのタイミング調整）を洗い出したうえでオーナーへ
方針を確認する。急ぎではないが、投稿自体は元々公開情報とはいえ「集約データを公開リポジトリの
履歴に残したまま」の状態は残るため、先送りしすぎない。
