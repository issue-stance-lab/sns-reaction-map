# 課題57 段階3：公開データ生成器の実装・完全照合

作成日: 2026-08-31
状態: 段階3完了。公開ページ・sitemap・trop・一般公開は変更していない

## 実装したもの

- `scripts/public_registry_common.py`: 正規化・ハッシュ・不変条件検査・最小限のJSON Schema検証の共通ロジック
- `scripts/build_public_registry.py`: `--topic <id>` / `--all` で公開テーマJSONとcatalogを生成
- `scripts/verify_public_registry.py`: `--public-only`（非公開正典不要）/ `--against-private`（完全照合）
  終了コードは仕様どおり `0=一致 / 1=不一致 / 2=非公開正典なし` に固定した
- `tests/test_public_registry_build.py`: 正規化ロジックの単体検査と、コミット済み公開JSONに対する
  Schema・不変条件検査（非公開正典が無くても実行できる）

## 手順（設計書の順）

1. `build_public_registry.py --topic bukatsu-chiiki` で最初に部活動だけを生成し、
   `verify_public_registry.py --public-only` と `--against-private` の両方が通ることを確認した
2. 部活動の件数・論点別内訳・賛否別内訳が `THEMES.yaml` の 2026-08-27 更新メモ（人が手で書いた集計）と
   完全一致することを確認した（教員の働き方283、制度・移行プロセス227、…、移行支持414、慎重・反対329、…）
3. 残り9テーマを `--all` で生成し、10テーマ全件で `--public-only` と `--against-private` を実行、両方成功
4. 同じ入力から2回生成し、`data/public/` 配下のバイト列（SHA-256）が完全一致することを確認した
5. `python3 -m unittest discover -s tests` を実行。327件中326件成功。唯一の失敗
   `test_top_page_matches_canonical_stats` は本作業と無関係な既存の遅れ（ai-copyright / constitutional-amendment /
   fukushuto の `collect_at` 期限超過、2026-08-30）で、共有ツリー（main）でも同じ失敗が出ることを確認済み

## 実装中に見つかった調査済み以外の分岐

`bike-blue-ticket` の正典は `is_opinion` をレコード直下に持つ一方、`is_relevant` フィールド自体が
存在しない（段階2提案書は「is_relevant/is_opinion をレコード直下に置く」と記載していたが、実際は
is_opinion のみ）。既存の `scripts/build_bike_arena.py` の `is_opinion()` と同じ規則
（`is_relevant` が無ければ `is_opinion` だけで判定）を採用し、意見384件という既知の数字と一致することを確認した。

## 結果（10テーマ・catalog）

| テーマ | 収集数 | 意見数 | 主要論点数 |
|---|---:|---:|---:|
| ai-copyright | 2,904 | 1,924 | 6 |
| bike-blue-ticket | 384 | 384 | 5 |
| bukatsu-chiiki | 1,216 | 993 | 6 |
| constitutional-amendment | 1,105 | 966 | 6 |
| consumption-tax-cut | 3,194 | 2,852 | 6 |
| elderly-license-revocation | 394 | 258 | 5 |
| fukushuto | 1,441 | 1,199 | 6 |
| henoko-student-accident | 445 | 341 | 6 |
| koshitsu-tenpakai | 1,289 | 1,026 | 5 |
| school-nickname-ban | 420 | 87 | 6 |
| **合計** | **12,792** | **10,030** | — |

合計12,792件・10,030件は、設計書が「廃棄対象」として名指しした旧固定テスト
（`12,792件・10,030件を固定した恒久テスト`）と同じ値である。今回は固定値としてではなく、
非公開正典から毎回数え直した結果として一致した。

## 未確定のまま進めた判断（次段階の前に確認してほしい）

各テーマの読者向け「問い」（`question`）は `configs/public-data-taxonomy.json` ではなく
`scripts/public_registry_common.py` の `QUESTIONS` 辞書に置いた。部活動は課題54の承認済み表現を転記、
残り9テーマは各テーマの公開済み `vote_intro` / `subtitle`（`configs/*-reaction-map.json`、既に公開中）の
論点をそのまま短い問いに言い換えたもので、新しい主張は加えていない。ただし文言そのものはCEO確認を
受けていない。段階4でどのページにも表示する前に、独立レビューまたはCEO確認で文言を確認すること。

## 完了条件との対応

- 公開10テーマのJSONとcatalogが生成される: 満たす
- 非公開正典が無い環境でも、コミット済み公開JSONから検査できる（`--public-only`）: 満たす
- 非公開正典が無い状態を完全監査成功として扱わない（`--against-private` は exit 2）: 満たす（実地テスト済み）
- 3Dは作らない、一般公開は行わない: 満たす（`docs/` は未変更）

## 次にすること

段階4（トップ・10テーマ・sitemapの公開候補を公開データJSONへ接続する）に進む前に、
上記「問い」の文言をCEO確認または独立レビューへ出す。
