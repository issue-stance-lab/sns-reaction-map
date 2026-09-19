# 課題74: 山なみ共通雛形のAIっぽい言い回し・AI帰属の誤りを残りテーマへ展開する

**登録日**: 2026-09-20
**状態**: 未着手（consumption-tax-cutのみ対応済み、別コミットで完了）
**優先度**: 低〜中（CIは落ちていない。ただしCの「AI帰属の誤り」はai-copyrightの公開ページに
実際に表示されており、事実として不正確）

## 何が起きたか

オーナー指摘で消費税減税ページの文章を通し読みし、AIっぽい言い回し・AI帰属の誤りを7か所
発見・修正した（2026-09-20、`task/ctc-wording`）。このうち3種類は山なみ形式（現行のメイン形式）
共通の雛形（`quality/prototypes/planet-prototype.template.html`・`scripts/build_planet_data.py`）
由来で、他テーマの公開ページにも同じ文言が残っている。

consumption-tax-cutは、共有雛形の既定文言そのものは変更せず、`render_page()`の
`theme_id`分岐でこのテーマだけ文言を個別に差し替える形で対応した（`henoko-student-accident`が
既に同じやり方で「資料にしかない話を見る」の説明文を個別修正済みで、その前例に倣った）。
共有雛形の既定文言を直接変えると、他テーマの「公開ページ再現検査」
（`test_published_page_matches_canonical`等）が軒並み失敗する（実際に一度失敗させて確認済み）。

## 確認結果（consumption-tax-cut・takaichi以外の9テーマ）

### A・B: 論点の内訳を開いたときの注記とボタン文言（`planet-prototype.template.html`由来）

| 残存箇所 | 現在の文言 | 対応済みの文言（consumption-tax-cutのみ） |
|---|---|---|
| 戻るボタン | 「← 全体へ戻る（Esc）」 | 「← 論点の一覧へ戻る（Esc）」（フォールバック表示の文言と統一） |
| 未読論点の注記 | 「AIが自動でつけた区分をここに並べることはしません。人が読んだ結果だけをまとめにします。」 | 「この論点の中身（内訳）は、編集部が確認してから表示します。」 |

残存テーマ: ai-copyright / bike-blue-ticket / bukatsu-chiiki / constitutional-amendment /
elderly-license-revocation / fukushuto / henoko-student-accident / koshitsu-tenpakai /
school-nickname-ban（9テーマ全部）

### C: 「この論点の全件をAIが本文再読した」（`configs/planet/{テーマ}.yaml`の`coverage_note`）

実際にその論点を1件ずつ読み直したのは編集部（人）で、AIではない
（consumption-tax-cutの場合`data/consumption-tax-cut_4issues-reread.json`の`method`に
「編集部が本文を1件ずつ読み、区分へ分類した」と明記されている）。他9テーマの
`coverage_note`は「投稿本文を読み、理由で分けました」のように編集部作業として書かれており、
この2テーマだけが「AIが」という誤った書き方のまま。

| テーマ | 読者への表示 |
|---|---|
| **ai-copyright** | 表示されている（`show_coverage_note`が既定のtrue） |
| elderly-license-revocation | 表示されていない（`show_coverage_note: false`のため実害なし） |

### D: 「資料にしかない話を見る」ボックスの説明文（課題73調査時に発見済み、今回のオーナー指摘とは別件）

「資料にあるのに、SNSにないことに、一次資料では争点なのにSNSではほとんど誰も話していない
ものがあります。」という、文の途中で言い方が変わる読みにくい一文。`henoko-student-accident`は
既に個別修正済み（2026-09-19、`build_planet_data.py`の`theme_id`分岐）。

残存テーマ: ai-copyright / bike-blue-ticket / bukatsu-chiiki / constitutional-amendment /
elderly-license-revocation / fukushuto / koshitsu-tenpakai / school-nickname-ban（8テーマ）

**注意**: constitutional-amendmentだけは共有雛形（`planet-prototype.template.html`）ではなく
専用の`constitutional-planet.template.html`を使っている。共有雛形をまとめて直しても
constitutional-amendmentには反映されず、個別にこのファイルを直す必要がある。

## 対応方針の案

consumption-tax-cutで確立した手順をテーマごとに繰り返す。

1. `render_page()`に`theme_id`分岐を追加し、対象テーマだけ文言を差し替える
   （A・Bは`scripts/build_planet_data.py`の2箇所＝JS雛形の文字列置換＋`static_fallback()`内の
   三項演算子、Dも同様。Cは`configs/planet/{テーマ}.yaml`の`coverage_note`を直接書き換えるだけでよい）
2. `python3 scripts/refresh_planet_section.py --topic <テーマ> --for-docs`で再生成
3. `python3 scripts/verify_adoption_registry.py`がNGになったら`build_adoption_registry.py`で
   台帳を作り直す（consumption-tax-cutと同じ、正常な差分）
4. 標準検査一式（`verify_theme_page.py`・`verify_number_provenance.py`・`verify_top_page.py`・
   `unittest discover`・`run_public_checks.py`）・実機でのページ確認・本番反映まで、
   consumption-tax-cutと同じ手順で行う

**進め方の判断が要る**: 9テーマ分をこの`theme_id`分岐方式で1つずつ個別対応するか、
ある程度テーマが片付いた時点で共有雛形の既定文言そのものを書き換えて残り全部を
まとめて再生成するか（後者は1回で片付くが、複数テーマの公開ページが同時に変わるため
確認の手間も増える）。

## 次にすること

優先度は低〜中。着手するときは、実際に読者に誤った内容（AI帰属の誤り）を見せている
**Cのai-copyright**から始めるのが妥当。それ以外（A・B・D）は表現の読みやすさの問題で
実害はない。

## 進捗

（未着手。2026-09-20にconsumption-tax-cutのみ対応・残り9テーマの現状調査のみ完了）
