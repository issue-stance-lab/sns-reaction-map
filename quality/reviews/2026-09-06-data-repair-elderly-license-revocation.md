# 高齢者免許返納：取得履歴114件の修復候補（63-M2）

2026-09-06 / 基準main `3887c9863150a69869573646791ae755036547f7` / 専用ブランチ `task/data-repair-elderly-20260906`。
**候補作成済み・未適用。114件修復、保留0件、根拠なし0件、未処理0件。** 正典・公開HTML・台帳の工程日は変更していない。

## 結果

| 項目 | 修復前 | 候補 |
|---|---:|---:|
| 投稿数／一意の投稿ID数 | 506 / 506 | 506 / 506 |
| 意見数 | 353 | 353 |
| 取得日時の欠損 | 114 | 0 |
| 検索語の欠損 | 114 | 0 |
| 取得元の欠損 | 114 | 0 |
| 再読済みの投稿 | 250 | 250 |
| 記録された取得日の最小〜最大 | 2026-07-12〜2026-09-04 | 2026-06-28〜2026-09-04 |

監査時点の114件から増減なし。変更は欠損した3項目、計342値の追加だけ。投稿ID・順番・本文・URL・既存分類・既存の取得情報・再読ファイルを保存前後で照合し、変更がないことを確認した。

## 採用根拠と複数観測

114件すべてについて、旧 `elderly-license-revocation_classified.json` の同じ投稿ID・本文が完全一致し、2026-06-28の取得日時・検索語・`yahoo_realtime` を持つ。取得直後の `elderly-license-revocation_samples.json` でも同じIDと3項目が一致する。

rawの本文はYahooの強調マーカーを含むため、完全一致とは数えていない。既存の `scripts/merge_reaction_samples.py:normalized_text` を両側へ適用すると114件一致する。107件はrawだけの正規化でも一致し、残7件は正典側の全角空白・改行しない空白なども正規化すると一致する。差分を確認し、語句の加除はない。本文は変更していない。

`scripts/classify_2d_elderly_license.py` の旧変換は入力を旧分類ファイルとし、出力へ本文・ID・URL・分類結果をコピーする一方、取得情報3項目を含めていない。旧分類ファイルは要約欄ではなく投稿本文と取得直後の記録をつなぐ中間証拠として使用した。取得元の意味は `fetch_yahoo_realtime_node.mjs` がYahoo検索の `displayTextBody`、その場の時刻、実際のqueryを保存する実装と照合した。合成投稿・AIの要約は証拠としていない。

今回採ったのは、この旧入力に対応する6月28日の観測記録である。最古の日付を機械的に選んで真の初回取得と断定したものではない。114件中82件は1観測日、31件は2観測日、1件は3観測日を保存資料に持つ。7月12日・26日の再取得を含む全ファイル位置・本文一致方式・3項目を非公開の処置一覧へ残した。日付と別に検索語・取得元も原本同士の一致を確認した。

## 再読と期間の扱い

主要2論点の再読は「義務化・事故防止」221件、「地方の足・移動権」29件で、現在の正典の対象集合と一致する。修復対象との重複は82件。最新mainの `split_unread` をそのまま呼び、両論点とも修復前後で読み飛ばし0件・読了後追加0件だった。新規再読は行っていない。

読了直前の正典コミット `5da3a48` の506件が現在の修復前正典と全内容一致することも確認・保存した。今回はこの正典版と読了済みID集合が採用・再読の根拠になる。一般論として取得日時は正典採用日時を表さず、この修復だけで未読を読み飛ばしと断定してはならない。

`sample_period: 2026-06-27〜2026-09-04` と `owner_confirmed` は維持した。観測記録の下限6月28日だけで、オーナー確認済みのテーマ全体の期間を変更する根拠にはならない。真の初回取得と6月27日の全体範囲の裏付けは今回確定していない。

## 検査

- 投稿ID一意・ID集合／順序・本文／既存分類／再読ファイル不変：合格。
- `verify_sample_periods.py` の `summarize` と `verify`：候補から新規集計し、テーマ読込だけ高齢者に限定して合格。検査条件は変更していない。
- `verify_theme_page.py elderly-license-revocation`：合格。
- `verify_number_provenance.py elderly-license-revocation`：180箇所すべて説明可能、NG 0。
- 再読250件の集合照合と最新 `split_unread` の前後比較：合格。新ページ設定 `configs/planet/elderly-license-revocation.yaml` は未作成のため、ページ全体の新生成器実行は未実施。
- 非公開バックアップ26ファイルのSHA-256一致、保存先から一時ディレクトリへ復元し再照合、復元候補506件の不変条件確認：合格。

候補だけ差し替えた最初のページ・数字検査は、公開JSONの `source_sha256` が旧正典を指しているため停止した。修復前の原本では両検査とも合格。検査用に対象テーマの公開JSONだけを既存生成関数で再生成すると、差分は `/source_sha256` と `/data_version` の2項目だけとなり、両検査が合格した。検査終了時に専用worktreeの正典・公開JSONを元に戻した。共通コード・他テーマ・HTMLは変更していない。公開採用時にはこの集計再生成を統合候補で行う必要がある。

既存の「ページ上の論点数6、catalogのnamed_issue_countは5（その他を除く）」という注意表示は修復前後とも同じ。今回の修復とは別で、NGではない。

## 原本の指紋と保管

最新バックアップ `private-data-20260906T095255889147.tar.gz` をOPERATIONSの手順で専用worktreeへ復元した。SHA-256は `0e07a3e546b1d995d4990e758b42b8e01067a9cc333110659b3c4bbd54f493c0`。対象正典はGit追跡済みで、原本・照合に使う各証拠ファイルは共有側の最新コピーと件数・指紋が一致した。共有側からの差分持込みはない。

| ファイル | 件数 | SHA-256 |
|---|---:|---|
| 正典 `elderly-license_2d_classified.json` | 506 | `44a6d04bc6e95ebfdd4c77983bbe06f4368fc31119e3f0c90741172ec3a7f56a` |
| 修復候補 `candidate.json` | 506 | `f3d2af2d961b9ca6358b75a651e89379e83d2a20c1cf3477daae878aa64a4836` |
| 再読 `elderly-license_issues-reread.json` | 250 | `89dd1ffc4f66abda683edb44a8c46c3bd3f14d587ea1d23ae873165db190dcfd` |
| 旧分類 `elderly-license-revocation_classified.json` | 183 | `57c8ae07676adea535e2a85f7d833578490d13b957321ba7da166f2989bb56d2` |
| 取得raw `elderly-license-revocation_samples.json` | 285 | `64a6bce19b0ce153169528305473c42ab51a11b510d554b5b5187c8b59d019a6` |
| 結合raw `elderly-license-revocation_samples_merged_20260712.json` | 285 | `64a6bce19b0ce153169528305473c42ab51a11b510d554b5b5187c8b59d019a6` |
| 再取得raw `elderly-license-revocation_samples_refresh_20260712.json` | 156 | `d7212a70a63a9685b7bdfcc4fbfba977502cc0ce3420df319883968f4afd9696` |
| 再取得raw `elderly-license-revocation_samples_refresh_20260726.json` | 141 | `ec1052153983da002d6ace39359ac83d286ed8cce3b43d97092a4a6088dd91bb` |

非公開成果の永続保存先：

`/Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/elderly-license-revocation/20260906-63m2-3887c98/`

原本、候補、処置と根拠、参照した原本5本、再読直前の正典、観測履歴、検査ログ、再現コードを保存。`manifest.json` の指紋は `ae4e5ef46da78e4355e3425866a5faa4acf03dd6b14db0df01905e017d1aed39`。本文付き新候補・投稿ID付き一覧はGitへ追加していない。作成時の一時保存先は `.staging/data-repair/elderly-license-revocation/20260906-63m2-3887c98/`。

## 再現と引継ぎ

基準mainから専用worktreeを作り、OPERATIONSのバックアップ復元を済ませた環境で、以下は候補の作成・対象検査を行う。成功すると修復114、保留0、未処理0のJSONが出て、新しい非公開ディレクトリに証拠と検査ログができる。検査中だけ作業用の正典と公開JSONを差し替え、終了時に戻す。既存の保存回は上書きしない。

```sh
python3 quality/reviews/2026-09-06-data-repair-elderly-license-revocation.py \
  --root . \
  --shared '/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator' \
  --out .staging/data-repair/elderly-license-revocation/reproduction-63m2
```

入力が更新されれば、再読前正典との一致確認などで停止し得る。古い修復候補を新しい正典へ無条件に被せない。保存先の `manifest.json` を照合して `candidate.json` を作業用コピーへ復元できることは今回実施済み。

統合担当への状態更新案：**63-M2＝候補作成済み／未適用。取得履歴114件修復、保留・未処理0、再読250件継承、外付け復元確認済み。課題28の全体期間は別評価を維持。** 課題索引・共通の課題63ファイルは編集していない。

次の作業は、統合担当が他テーマの修復候補と合わせて採用レビューし、正典への採用と対象集計の更新を一つの候補として扱うこと。main取り込み・共有正典への適用・一般公開は未実施。
