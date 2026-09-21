# 課題78: 高齢者免許返納・高市文春問題の正典がGit（公開リポジトリ）に追跡されたまま残っていた

**状態**: 完了（2026-09-21）。追跡解消・外付けバックアップ・main反映・CI緑化は2026-09-20に完了。過去分の履歴削除は影響調査のうえ見送りと決定し、これをもって完了とする
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

mainへマージ・push（`0f202ca`まで）。CIで検知された不具合と対応は次項。

## 2026-09-20: マージ後にCIが落ちた（非公開データが無い環境を想定できていなかった）

`run_public_checks.py`は手元（正典が復元済み）では全部OKだったが、push後のCI
「公開ファイルの検査」が失敗した。別セッション（課題77担当）からの指摘で発覚。
`test_refresh_topic.py`・`test_takaichi_adapter.py`・`test_issue_count_sync.py`の3件が
`social-samples/takaichi_hermes_arena_classified.json`を直接読んでおり、非公開データの
無い環境（CIと同じ）で`FileNotFoundError`になっていた（elderly-license-revocation側は
既存の`test_elderly_adapter`除外で問題なし）。

**この教訓は`release`スキルに既に書かれていた**（「同じ中身は同じ結果になるの保証ではない」）
にもかかわらず、push前にクリーンな環境で検査していなかったために踏んだ。

**対応（`task/canonical-gitignore-hotfix`、`0f202ca`）**:
- `data/verification/takaichi.json`を新設し、`THEMES.yaml`に`verification_file`として登録。
  他10テーマと同じく、`sync_issue_counts.py`が非公開正典を読まずに論点カード件数を
  検算できるようにした（実際の検証能力は落とさず、公開データ経由に付け替えただけ）
- `test_refresh_topic.py`のtakaichi専用テスト1件に`skipUnless`を追加
- `test_takaichi_adapter.py`（takaichi専用ファイル）を`PRIVATE_DATA_TESTS`へ追加
- **修正後、`git clone`した完全にクリーンな環境（非公開データ0件）で
  `run_public_checks.py`を実際に実行して確認してからpush**。CI結果も
  `gh run list`で緑を確認済み

## 残っている課題 → 2026-09-21: 影響調査のうえ、履歴削除は見送りと決定・完了

**過去にGitHubへpushされた分は、この対応では消えない。** Gitの変更履歴（過去のコミット）には
まだ両テーマの本文付きデータが残っている。完全に消すには履歴の書き換え（`git filter-repo`等＋
強制push）が必要。

**調査結果**:
- 最初に両テーマのデータが混入した時点（elderly-license: 2026-07-03 `dd94fbac`、takaichi:
  2026-07-07 `9b45d9a7`）から現在まで**2,378コミット**（全履歴2,443件の97%）が積まれている。
  履歴の書き換えは、この2,378件**すべて**のコミットID（識別子）が変わることを意味する
  （Gitは各コミットが1つ前のコミットのIDを含む数珠つなぎの構造のため、対象を2ファイルだけに
  絞っても、書き換えコストは「全部消す」場合と変わらない）
- 現時点で**作業ツリー（並行作業用のコピー）25個・確認できる並行セッション36個**がすべて
  書き換え前の履歴の上に乗っており、書き換えると全部を作り直す必要がある
- 対象リポジトリのフォーク（他アカウントへのコピー）は**0件**
- 実行専用ツール`git-filter-repo`は現在の作業機にインストールされていない
- 両ファイルは「使い捨ての過去データ」ではなく、`THEMES.yaml`の`sample_file`として
  **現在もページ生成に使われている現役データ**（ファイル名・場所とも不変）。
  データ量が増えたことを理由に「古い方を消す」形の整理はできない
  （消すと現在のページ生成に使っているデータ自体が無くなる）

**判断（2026-09-21、オーナー承認）**: 履歴書き換えは見送り、現状維持で完了とする。
理由は、投稿自体が元々公開情報でありフォークも無いこと、2026-09-20の対応で今後の追跡・
バックアップ漏れは既に止まっていること、に対して、25個の作業ツリー・36個の並行セッションを
止めて全履歴を作り直すコストが著しく大きく見合わないため。今後この判断を積極的に見直す
予定は無い。
