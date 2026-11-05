# 課題108: 連動表示の検査が `<template>` の中身を CSS セレクタで数えている

**状態**: 未着手（2026-11-04 に `soupsieve<4` で固定してCIの赤は止めた。固定を外せる形にするのが本題）
**優先度**: 中（いまは固定で止まっているが、固定は恒久策ではない）
**次にすること**: `select()` で template 内を数えている検査・スクリプトを template 対応に直す
**判断待ち**: なし
**関連テーマ**: 皇室典範・辺野古・憲法改正・生成AIと著作権・自転車・消費税減税

---

## 経緯

2026-11-04、GitHub Actions の「公開ファイルの検査」が、コミットの内容と関係なく
failures=4 / errors=3 の同じ7件で赤くなった（11-03 時点で緑だったコミットを再実行しても同じ）。
手元では全件通る。原因は依存ライブラリの更新だった。

- `beautifulsoup4` の `.select()`（CSSセレクタ）の中身は **soupsieve** が担っている。
- soupsieve **4.0** から、HTML の仕様どおり `<template>` の中身を別の文書として扱うようになり、
  `soup.select('[data-aic-post-url]')` のようなセレクタが template 内の要素を拾わなくなった。
- 連動表示（「実際の投稿を読む」の投稿例・理由別件数）は投稿要素を `<template>` の中に置いて
  遅延表示している。検査はその中の要素を `select()` で数えていたので **0件** になり落ちた。
- `requirements-dev.txt` は soupsieve を固定しておらず、CI は毎回最新を入れるため CI だけが赤くなった。

切り分けの記録:

- コミット済みファイルだけの使い捨てコピー（`git archive HEAD`）＋手元のライブラリ
  → **7件すべて通る**。「非公開データが無いから落ちる」「公開ページが古い」は**否定された**。
- 同じコピー＋CI と同じ版（beautifulsoup4 4.15.0 / soupsieve 4.0）
  → **failures=4 / errors=3 で CI と完全一致**。
- soupsieve だけ 3.0 に落とす（beautifulsoup4 は 4.15.0 のまま）→ **全件通る**。
  beautifulsoup4 の版は無関係で、soupsieve 4.0 が単独の原因。

## いまの対処（2026-11-04、main 反映済み c7993ed2）

`requirements-dev.txt` に `soupsieve<4` を追記した。理由はファイル内のコメントに書いてある。
公開ページ・データは一切変えていない。CI は soupsieve-3.0.4 で緑に戻った。

## 本来の直し方

検査側を template 対応にする。`select()` の代わりに、template 要素を取り出して
その中身を改めて解析する（`BeautifulSoup(template.decode_contents(), "html.parser")`）か、
`find_all(attrs={...})`（こちらは 4.0 でも template 内を拾う）に置き換える。

対象（`data-*-post-url` / `data-henoko-claim` などを `select` している所）:

- テスト: `tests/test_koshitsu_public_copy.py` / `test_koshitsu_connected.py` /
  `test_henoko_connected.py` / `test_constitutional_connected.py` /
  `test_ai_copyright_connected.py` / `test_ai_copyright_issue_media.py`
- スクリプト: `scripts/henoko_count_provenance.py` /
  `scripts/bike_blue_ticket_count_provenance.py` / `scripts/consumption_tax_connected.py` /
  `scripts/koshitsu_connected*.py` / `scripts/constitutional_connected*.py` /
  `scripts/ai_copyright_connected*.py` / `scripts/henoko_connected*.py`

直したら soupsieve 4 系と 3 系の両方で検査を回し、どちらでも通ることを確かめてから固定を外す。
手元で CI と同じ条件を作る手順は `.claude/skills/release/SKILL.md`
「コラム: 手元は通るのにCIだけ赤いとき」にある。
