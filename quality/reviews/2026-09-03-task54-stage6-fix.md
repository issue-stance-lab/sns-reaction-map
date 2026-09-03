# 課題54 段階6 レビュー指摘の修正記録（2026-09-03）

対象レビュー: `quality/reviews/2026-09-03-task54-stage6-review.md`（`task/planet-stage6-review`、指摘1〜6）
作業ブランチ: `task/planet-stage6-fix`（`task/planet-stage6` から分岐）
公開ページ・公開JSONへの接続は無し（`docs/`・`data/public/` 差分0）。

## 指摘の再現（修正前に実測）

| 指摘 | 再現結果 |
|---|---|
| 1 立場を表示ラベルで集計 | `慎重・反対` を言い換えて生成 → 立場合計 1139→**749**、`top_stance` が7論点中4つで変化（教育的意義・受け皿・費用・地域格差）。例外も警告も出ない |
| 3 未登録の論点idを黙って捨てる | 未登録論点50件を足すと `totals.opinions` 1189・論点別合計 1139 |
| 5 生成器を通るテストが無い | `tests/` に `build_planet_data` の参照0件 |

## 直したこと

1. **指摘1**: `configs/planet/bukatsu-chiiki.yaml` の各立場へ公開JSONの `stances[].id` を追記し、
   集計を **id だけ**で結ぶようにした。公開JSONに未登録の立場idがあれば生成を止める。
   設定にあって公開JSONに現れない立場は、件数0か id の誤りか機械では区別できないため警告に留める
2. **指摘3**: 未登録の論点idを検出したら、追記先（`configs/planet/{topic}.yaml`）を示して停止。
   あわせて「論点別の合計 = `issue_assigned_count` = `opinion_count`」を不変条件として確認する
3. **指摘2**: レビューの案（母数を台帳に書かず生成時に公開JSONから採る）は採らなかった。理由は2つ。
   ①`scripts/verify_ocean_layer.py` が `sns_base` を必須項目として要求している（段階5・指摘8で
   main に入れた検査）②`sns_count` は**その母数のもとで人が本文を読んで確定した件数**であり、
   母数だけを新しい数字へ差し替えると、どの時点でもない比率が画面に出る。
   代わりに**照合して知らせる**形にした: 台帳の `sns_base` はそのまま残し、生成時に現在の
   `opinion_count` と突き合わせて `base_stale` / `opinion_count_now` を出力、標準出力へ警告、
   さらに独自性の検査（`independence_gate`）で**公開ページの出力を止める**（`--prototype` は可）
4. **指摘4**: 台帳の `issue_ids` を使い、各論点へ `veins`（その論点に結ばれた地下水脈のid）を出力。
   未登録の論点idを指す水脈があれば停止する
5. **指摘5**: `tests/test_planet_data.py`（14件）を新設
6. **指摘6**: 未知の判定語は `KeyError` ではなく、使える語を示す停止メッセージにした

## 確認したこと

- 部活動の生成結果は**数字・面積・標高・色・判定が修正前と完全一致**（差分は追加項目のみ:
  `stances[].id` / `issues[].veins` / `ocean.sunk_continents[].base_stale`・`opinion_count_now`）
- 立場ラベルを言い換えても件数・`top_stance` が変わらない（テストで固定）
- 未登録論点を足すと停止し、足すべきidが表示される（テストで固定）
- 台帳の母数を書き換えると `base_stale` が立ち、独自性の検査が公開を止める（テストで固定）
- `verify_ocean_layer.py` OK / `verify_claim_verdicts.py` OK / `verify_public_registry.py`
  （`--public-only`・`--against-private` とも exit 0）/ `verify_theme_page.py bukatsu-chiiki` OK
- 全**398テスト** OK（384＋新規14、skipped=4）、2回生成の差分0、`docs/`・`data/public/` 差分0
