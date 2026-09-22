# 課題89: 「世論の潮目」の図でラベルが重なる不具合を残り9テーマで直す

**状態**: 未着手
**発見**: 2026-09-22（部活動の地域移行の定期更新を公開前に画面確認していて発見）
**関連**: 69（定期更新。発見のきっかけ）

## 何が起きているか

「世論の潮目」の図（前回→今回の構成比を線で結ぶ図）で、値が近い2つの行の
ラベルが重なって読めなくなる。2026-09-22の部活動では、左側の「慎重・反対 19.0%」と
「条件・改善要求 14.0%」が重なった。

図のJSには重なり防止の処理（`resolveLabelYs`）があるが、ずらす間隔が
`const minGap = 34;` で足りない。1行ぶんの表示は「ラベル（上）」と「割合（下）」の
2段で、高さが約41pxある（ラベルの文字位置 y-5、割合の文字位置 y+17、文字の高さ約20px）。
34pxずらしても、上の行の割合と下の行のラベルが重なる。

値が離れている回は起きないため、更新のたびに出たり消えたりする。
機械検査（`verify_theme_page.py` 等）は図の見た目を見ないので検出できない。

## 対応済み

- **bukatsu-chiiki**: `scripts/update_bukatsu_tide.py` の `minGap` を44へ変更し、
  2026-09-22に本番反映（`76dfae37`）。44pxで「論点の変化」タブ（5行）も
  図の枠（高さ340）に収まることをブラウザで確認済み

## 残り

`const minGap = 34;` が次の9ページに残っている（2026-09-22、`grep -l` で確認）。

- ai-copyright / bike-blue-ticket / constitutional-amendment / consumption-tax-cut /
  elderly-license-revocation / fukushuto / henoko-student-accident /
  koshitsu-tenpakai / school-nickname-ban

**部活動と違い、この9テーマには図を作る生成スクリプトが無い。** 処理は
`docs/*.html` に直接書き込まれている（`scripts/` 配下に `minGap` は
`update_bukatsu_tide.py` しか無い）。見本の `quality/prototypes/*-section-refresh-preview.html`
4件にも同じ値がある。

## 進め方の案

1. 9ページの `const minGap = 34;` を `44` に置き換える（1ページ1か所）
2. 各テーマの定期更新（adapter・`refresh_planet_section.py`）で書き戻されないか確かめる
   （同じ入力で2回更新して `minGap = 44` が残るか）。書き戻されるなら、その書き手を直す
3. 行数が多いテーマ（論点が7つ以上）で、44pxずらした一番下のラベルが
   図の枠（viewBox の高さ）からはみ出さないかブラウザで確かめる。はみ出すなら
   viewBox の高さも合わせて広げる
4. 再発防止として、`minGap` が44未満のページを落とす検査を足すか検討する
   （指示文のルールは別セッションで破られるため、検査にして残す）

完了の形: 9ページすべて `minGap = 44` 以上で、値が近い回でもラベルが重ならず、
標準検査・unittest・`run_public_checks.py` が通ること。
