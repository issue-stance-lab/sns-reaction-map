# 課題57 段階4：学校でのあだ名禁止の調査（今回は接続を見送り）

作成日: 2026-08-31
状態: 調査完了。**コード接続はしない判断。** 理由は3節。公開ページは無変更
対象: school-nickname-ban（段階4の2本目。着手順は部活動→あだ名禁止→消費税減税→残り7テーマ）

---

## 1. 番号→固定IDの対応表

このテーマは10テーマ中唯一、論点を文字列ID（`key`）で参照する形式
（[[reference_theme_page_code_variance]] 表の3列目）。ページ内の `var issues=[...]`
（500行目・531行目の2箇所、内容は同一）が論点・地図・投票の3つに共通の並びを持つ
（部活動と違い、投票専用の別配列やV2I変換は無い）。

| page index（`issues.indexOf()`） | key | 表示タイトル（ページ） | main_issue（分類ラベル・固定ID対応表とも一致） | 固定ID |
|---|---|---|---|---|
| 0 | safety | いじめ・心理的安全 | いじめ・心理的安全 | `school-nickname-ban-psychological-safety` |
| 1 | effect | 一律禁止の実効性 | 一律禁止の実効性 | `school-nickname-ban-uniform-rule` |
| 2 | culture | 親しさ・呼称文化 | 親しさ・呼称文化 | `school-nickname-ban-naming-culture` |
| 3 | experience | 学校運用・現場体験 | 学校運用・現場体験 | `school-nickname-ban-school-practice` |
| 4 | gender | さん付け・ジェンダー配慮 | さん付け・ジェンダー配慮 | `school-nickname-ban-gender-consideration` |
| 5 | choice | 本人意思と柔軟運用（ページ表記）/ 本人意思・柔軟運用（分類ラベル） | 本人意思・柔軟運用 | `school-nickname-ban-individual-choice` |
| （配列に無し） | — | — | その他 | `school-nickname-ban-other`（現在0件のためページ非表示） |

投票の立場（3種、`var stances=[...]`, 503行目）は分類ラベルの4種（禁止支持／条件付き・個別対応／
一律禁止に反対／中立・情報）のうち3つに対応する別の配列。「中立・情報」は投票の選択肢に無い。

| vote stanceIdx | key | 表示タイトル | 対応する分類ラベル・固定ID |
|---|---|---|---|
| 0 | support | 一律ルールを支持 | 禁止支持 / `school-nickname-ban-ban-support` |
| 1 | conditional | 本人意思で柔軟に | 条件付き・個別対応 / `school-nickname-ban-conditional` |
| 2 | oppose | 一律禁止には反対 | 一律禁止に反対 / `school-nickname-ban-ban-oppose` |

`choiceIdx = issueIndex(0-5, issues.indexOf()) * 3(stances.length) + stanceIndex(0-2)`。
範囲0〜17（6×3=18）。`topic_id = school-nickname-ban-issue-stance-v1`。
`refresh_adapters/nickname.py` の `VOTE_CHOICES = 18` と一致することを確認済み。

## 2. 「唯一件数がページ内に埋まっている」問題の実態

オーナー指摘のとおり `"count":29` 形式の埋め込みが `var issues=[...]` に12箇所
（6論点×2ブロック）ある。ただし **`scripts/build_nickname_arena.py` は既にこの重複を
安全に扱っている。**

- `build_vote_issues(rows)` が1回だけ件数入りJSONを組み立て、投票用・アリーナ用の
  両方の正規表現に同じ文字列を差し込む（685-691行目）
- 実装コメント（679-684行目）に「片方だけを狙う正規表現にすると間のスクリプトを
  丸ごと飲み込む」という2026年時点の実装時の教訓が明記されている

**心配していた「不整合」は既に起きない設計になっていた。** 今回の調査でコードを
壊すリスクは見つからなかった。

## 3. 公開データJSONへ接続しない判断（今回の最重要の発見）

`build_nickname_arena.py` の論点別件数計算 `issue_counts(rows)` は、`rows` を
`load_opinions(input_path)` から受け取る。この `input_path` は呼び出し元によって変わる。

- **通常のデータ更新時**（`refresh_adapters/nickname.py` の `build()`）: `--input` に
  **昇格前の候補ファイル**（`stage/cumulative-candidate.json`）を渡す。この候補は
  「まだ `THEMES.yaml` の sample_file には入っていない、新しく追加されるはずの投稿」を
  含む。候補ページはこの新しい件数を表示する必要がある
- このテーマには部活動の `finalize()` のような「昇格が確定したあとに、もう一度
  正典から数え直す」専用の後工程が無い。候補生成の1回で完結する

**`data/public/themes/school-nickname-ban.json` は、最後に昇格が確定した時点の
sample_fileから作られる（段階3の生成器は手動実行）。** もし今回、`issue_counts(rows)` を
「常に公開データJSONを読む」実装に変えていたら、次回のデータ更新（このテーマの
`collect_at` はまさに本日 2026-08-31）で **候補ページに新しい投稿の件数が反映されず、
まだ昇格していない古い件数のまま候補が作られる。** `refresh_adapters/nickname.py` の
「同じ候補の2回目実行で差分ゼロ」検査は通ってしまう（2回とも同じ古い数字で一致するため）
ので、この不具合は自動検査をすり抜ける。

**結論: `issue_counts(rows)` は今回変更しない。** 課題57の公開データJSONを
候補生成の入力として安全に使うには、`build_public_registry.py` 自体を
`refresh_topic.py` の候補作成パイプラインへ組み込む必要がある。これは設計書が
最初から段階5として分けている作業（`quality/designs/public-data-foundation-rebuild.md`
「段階5：通常のデータ更新へ接続する」）であり、段階4の個別テーマ作業で先取りすると、
本日予定されているこのテーマの実収集で問題を起こしかねない。

**部活動との違い**: bukatsu-chiiki は `refresh_adapters/bukatsu.py` に
`finalize()`（昇格確定後、正典から数え直して調査条件を貼り直す専用工程）があり、
そこでのみ `card_counts()` を呼んでいたため、`source_sha256` の鮮度確認
（本記録と同日追加）を条件に接続できた。**同じ判断枠組みを機械的に他テーマへ
当てはめる前に、そのテーマの「いつ・どのrowsで」件数を計算しているかを必ず確認すること。**

## 4. 検査結果（無変更の確認）

- `python3 scripts/verify_theme_page.py school-nickname-ban` → 全項目OK（今回の調査で
  コードは1行も変えていないため、変化なし）
- 元の `issue_counts(rows)`（正典から直接計算）と `data/public/themes/school-nickname-ban.json`
  の件数を突き合わせ、完全一致を確認（下記）。接続はしないが、両者が今この瞬間は
  同じ値であること自体は確認済み

```
issue_counts(rows) [private]:  学校運用・現場体験8 / いじめ・心理的安全29 / 親しさ・呼称文化16 /
                                さん付け・ジェンダー配慮6 / 一律禁止の実効性22 / 本人意思・柔軟運用6
data/public/themes/school-nickname-ban.json: 同じ6件、完全一致
```

## 5. 今回の副産物：段階4全体に効いた修正

このテーマの調査中に、bukatsu-chiikiの接続（1本目）に潜在バグがあることに気づいた。
`build_public_registry.py` の再実行を昇格のたびに手動で行わないと、`data/public/themes/`
配下が古いまま残り、`count_by_issue_from_public_json()` が黙って古い件数を返す。
`scripts/issue_card_counts.py` に `source_sha256` の鮮度確認を追加し、古ければ止まるようにした
（別コミット、本記録と同日）。**bukatsu-chiikiの次回データ更新（`refresh_at: 2026-09-03`）の前に、
昇格後は必ず `build_public_registry.py --topic bukatsu-chiiki` を手動で再実行すること。**
これを忘れると、この鮮度確認によって `sync_issue_counts.py` / `finalize()` が失敗する
（安全に倒れる。古い数字が出たまま気づかれない、という最悪のケースは防いだ）。

## 6. 次にすること

段階4の3本目、consumption-tax-cut（消費税減税）へ進む。着手前に、このテーマの
ビルダー（`build_consumption_tax_page.py`）が候補生成でどの`rows`から件数を計算しているかを
最初に確認し、school-nickname-banと同じ「候補生成中は接続しない」判断が必要かどうかを見極める。

段階5（`refresh_topic.py`の候補作成へ`build_public_registry.py`を組み込む）を、
残り8テーマの接続作業より前に着手候補として検討する価値がある。今回2/10テーマで
「候補生成のタイミング問題」に当たっており、他のテーマでも同じ制約が出る可能性が高い。
