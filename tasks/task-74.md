# 課題74: 山なみ共通雛形のAIっぽい言い回し・AI帰属の誤りを残りテーマへ展開する

**登録日**: 2026-09-20
**状態**: A・Bは完了（2026-09-20、山なみ形式の全10テーマ＝takaichi以外すべて）。
Cもai-copyright（読者表示あり）は対応済み、elderly-license-revocationは
表示されていないため実害なし。残るのはD（8テーマ、別件・低優先度）のみ
**優先度**: 低（AとBは全テーマで解消。Cの実害があった箇所も解消済み。
残るDは読みやすさの問題で実害なし）

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

| 残存箇所 | 旧文言 | 対応状況 |
|---|---|---|
| 戻るボタン | 「← 全体へ戻る（Esc）」 | 「← 論点の一覧へ戻る（Esc）」に統一。**全10テーマ（takaichi以外）で対応済み**（2026-09-20完了） |
| 未読論点の注記 | 「AIが自動でつけた区分をここに並べることはしません。人が読んだ結果だけをまとめにします。」 | **全10テーマ（takaichi以外）で`show_unreviewed_note: false`により非表示化済み**（2026-09-20完了。ai-copyrightは当初、文言だけ差し替える方式で着手したが、オーナー指摘で非表示方式へ変更し、他テーマと統一） |

残存テーマ: なし。bike-blue-ticket・constitutional-amendment・elderly-license-revocation・
fukushuto・henoko-student-accident・school-nickname-banの6テーマも2026-09-20に対応完了
（`task/task74-remaining-6-themes`）。constitutional-amendmentは専用テンプレート
（`constitutional-planet.template.html`）だが、`render_page()`の文字列置換は
テンプレート本文に対して行うため、同じ`theme_id`分岐で問題なく反映できた。

### C: 「この論点の全件をAIが本文再読した」（`configs/planet/{テーマ}.yaml`の`coverage_note`）

実際にその論点を1件ずつ読み直したのは編集部（人）で、AIではない
（consumption-tax-cutの場合`data/consumption-tax-cut_4issues-reread.json`の`method`に
「編集部が本文を1件ずつ読み、区分へ分類した」と明記されている）。他9テーマの
`coverage_note`は「投稿本文を読み、理由で分けました」のように編集部作業として書かれており、
この2テーマだけが「AIが」という誤った書き方のまま。

| テーマ | 読者への表示 |
|---|---|
| **ai-copyright** | 対応済み（2026-09-20。文言も編集部作業として書き直した上で、最終的に`show_coverage_note: false`で非表示に） |
| elderly-license-revocation | 表示されていない（`show_coverage_note: false`のため実害なし。文言「この論点の全件をAIが本文再読した既存成果」は誤ったまま未対応。非表示のため優先度は低いまま） |

**なお**、残り6テーマの`coverage_note`はもともと編集部作業として正しく書かれていたが、
2026-09-20に全て`show_coverage_note: false`へ変更し、対応済みの4テーマと表示を統一した
（文言の正しさとは別に、この種の注記自体を出さない方針にオーナーが揃えたため）。

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

A・B・C（実害があった箇所）は全て解消済み。残るのはDのみ（8テーマ、`henoko-student-accident`
除く：ai-copyright・bike-blue-ticket・bukatsu-chiiki・constitutional-amendment・
elderly-license-revocation・fukushuto・koshitsu-tenpakai・school-nickname-ban）。
Dは「資料にしかない話を見る」ボックスの読みにくい一文で、実害はない。優先度は低いままで
急ぐ必要はないが、着手するときはconsumption-tax-cutのA・Bと同じ`theme_id`分岐方式でよい
（`henoko-student-accident`の既存修正が実例）。**注意**: constitutional-amendmentは
専用テンプレートのため、共有雛形をまとめて直しても反映されない。

## 進捗

- 2026-09-20 consumption-tax-cut対応（A・B・C全て。B・Cは注記ごと削除）
- 2026-09-20 koshitsu-tenpakai対応（A・B、非表示方式）
- 2026-09-20 ai-copyright対応（A・B・C）。当初Bは文言差し替え方式で着手したが、
  オーナーから「この表記を削除」と指摘があり非表示方式へ変更（B・Cとも
  `show_unreviewed_note`/`show_coverage_note: false`）。文言差し替え用に追加していた
  `render_page()`のtheme_id分岐コードは不要になったため削除
- 2026-09-20 bukatsu-chiiki対応（A・B、非表示方式。Bは元々3論点のみ表示状態だった）
- 2026-09-20 残り6テーマ（bike-blue-ticket・constitutional-amendment・
  elderly-license-revocation・fukushuto・henoko-student-accident・school-nickname-ban）に
  A・Bを一括対応（オーナー指示「残り6テーマも同じ非表示方式で対応して」、
  `task/task74-remaining-6-themes`）。これで山なみ形式の全10テーマ（takaichi以外）が
  戻るボタン・未読論点の注記とも同じ方式に揃った。coverage_noteが既にあった6テーマ分も
  `show_coverage_note: false`へ統一（wordingは元々正しかったため文言変更なし）
- 残るのはD（8テーマ）のみ。低優先度のため未着手
