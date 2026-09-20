# 課題80: 副首都ページの論点画像7枚が本番から消えている（課題74反映で脱落）

**登録日**: 2026-09-20
**状態**: 未着手。課題77 Part A の再生成で画像は戻る見込みだが、脱落した経路そのものは未修正
**優先度**: 中（オーナーが課題70で了承し「本番反映」を指示した図が、現在の本番ページに出ていない）
**関連**: 70（図解の点検・差し替え）/ 74（脱落が起きた反映）/ 77（再生成で戻る）

## 何が起きたか

課題77 Part A の品質監査（`quality/reviews/2026-09-20-website-task77-parta.md`）で、作業ツリーで作り直した
副首都ページと本番ページの差分を比べたところ、本番ページに論点画像（`images/topics/fukushuto/fukushuto-infographic-wide-*.webp`）が
1枚も無いことが分かった。

コミットごとの本番ページの状態（`git show <commit>:docs/fukushuto-reaction-map.html` で数えた）:

| コミット | 内容 | wide 図の参照 | `images/topics/fukushuto/` の参照 |
|---|---|---|---|
| 7249d23（15:20） | 投票セクションと「このページの作り方」を分ける | 8 | 13 |
| 134a6a0（17:37） | 課題74: 残り6テーマも戻るボタン統一と注記の非表示化 | 0 | 5 |
| 75c0865（23:13） | 課題79 C-5: 調査条件ボックス | 0 | 5 |

`build_fukushuto_arena.py` の画像差し込み（`landing-image`）はこの間ずっと残っている。つまり builder と本番ページが食い違い、
副首都の adapter は「候補を2回作って差分がないこと」しか見ないため、`verify_theme_page.py` では検出できない。

## 推定される原因（未確認）

134a6a0 は `build_planet_data.py` と `configs/planet/fukushuto.yaml` を変え、6テーマの山なみ区間を作り直している。
副首都の画像は `build_fukushuto_arena.py` の後付け処理（fd761be）で入るため、`refresh_planet_section.py` などの
共通経路だけで作り直すと落ちる。この経路の違いが原因かどうかは、134a6a0 を作ったセッションの手順を確認するまで断定しない。

## やること

1. 課題77 Part A のマージで画像が戻ったことを本番で確認する（`curl` で `fukushuto-infographic-wide` が 8 になる）
2. 共通経路（`refresh_planet_section.py`）で副首都を作り直しても画像が残るようにするか、
   副首都 adapter の検査に「本番ページ = builder 出力」の比較を足して再発を検出できるようにする
3. 同じ型の後付け処理を持つ他テーマ（皇室典範 `apply_koshitsu_landing_images` など）で同じ脱落が起きていないか確認する
