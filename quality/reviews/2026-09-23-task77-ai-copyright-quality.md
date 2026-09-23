# 課題77 — ai-copyright連動表示・工程5（機能と見た目の検証）

実施日: 2026-09-23。[6工程計画](../designs/2026-09-22-task77-connected-layout-rollout-guide.md)の工程5。
[工程4の記録](2026-09-23-task77-ai-copyright-full-log.md)の続き。消費税の参照版:
`docs/consumption-tax-cut-reaction-map.html`（本番公開済み、bukatsu-chiikiと同じ位置づけの記録は
`2026-09-23-task77-bukatsu-chiiki-quality.md`）。

## 結論（先に）

**機能検査11項目・外観V01〜V12いずれも合格。比較の過程で見た目の不一致を2件発見し、その場で
修正した（工程3・4の担当分に該当するため、この工程で解決してから合格とした）。** 公開・push・
実投票は行っていない。候補はローカルサーバーへ一時配置して確認し、`docs/ai-copyright-reaction-map.html`
はバイト単位で無変更のまま。

## 見つけて直した問題

| 問題 | 原因 | 修正 |
|---|---|---|
| 立場バー（STANCE_GLANCE、内訳の棒グラフ＋結果文）が、山・立場ボタンから遠く離れた位置（ページ下部、約4000px先）に取り残される | `bar.before(mountain)`だけでは山側をバーの直前へ運ぶのみで、バー自体は元の位置に残る。参照実装（`docs/consumption-tax-connected.js`）は続けて`stage.before(bar)`相当でバーを山側へ運んでいるが、`docs/ai-copyright-connected.js`にこの2手目が無かった（bukatsu-chiikiの`bukatsu-connected.js`にも無く、そちらを土台にしたため引き継いだ） | `docs/ai-copyright-connected.js`にバーを`#modes`の直前へ移す処理を追加。重複する「◯件の立場別内訳」見出し（`.sg-headline`）は棒グラフ自体と内容が重なるため非表示に。バー→立場ボタン→山が隙間なく一続きになることを確認（V02） |
| スマホ幅（375px）で「すべて」ボタンが他の3ボタンと同じ半分幅になり、全幅表示にならない | 参照実装・bukatsu-chiiki双方にある`#modes [data-m="all"]{grid-column:1 / -1}`のCSSルールを、`docs/ai-copyright-connected.css`の作成時に書き落としていた | 同じルールを追加。375pxで「すべて」が全幅、他3つが2列になることを実機確認（V02） |

いずれも工程3・4で作った配置ファイル（`docs/ai-copyright-connected.js`・`.css`）の見落としで、
データ層・読書面（`ai_copyright_connected.py`・`_content.py`・bridge.js）には影響しない。

## 機能結果表

| 検証 | 結果 |
|---|---|
| 全論点×全立場 | 7論点×4表示（すべて＋3立場）=28通りをブラウザで一巡し、NaN/undefined/Infinityの混入0件・見出し欠落0件・コンソールエラー0件を確認 |
| 0件表示 | 実データには0件セルが存在しない（全28通りで最小1件以上、`data.modes[].counts`を直接確認）。合成的に1セルを0件へ書き換えて`data-aic-zero`が正しく表示され件数が「0」（NaN等ではない）になることを確認 |
| 動き・操作 | 480msのなめらかな変化（連打後は最後に押した立場へ収束）、山の選択色（選択0.9／非選択0.23、規制#ff5426・中立#64748b・推進#075ef2）、キーボード（hillへフォーカス後Enterで着地）、論点リンク（授業節`#issue-{id}`・戻る`history.back`相当のhashchange）を実機確認。※動きを減らす設定（`prefers-reduced-motion`）は本環境のブラウザツールに直接エミュレートする手段が無く未確認（コードは既存の`reduce`変数を再利用するのみで新規ロジックは無い） |
| 読書面 | 3タブ切替（資料を読む／x投稿で語られない話・4件／一次資料クイズ・6問）、クイズの全問回答と論点自動切替（`compensation_required`の問いで実際にクリエイター保護・権利へ切り替わることを確認）、予想②の答えからの論点移動リンクを確認 |
| JavaScriptなし | `#fallback`は`apply()`適用前後でバイト単位で完全に同一。GA_TAG/canonical/OGP/AdSenseタグの個数も前後で一致（増減なし） |
| 通常更新 | `refresh_adapters/ai_copyright.py`・`refresh_planet_section.py`の両経路とも`tests/test_ai_copyright_connected_refresh.py`（5件）で再適用・冪等性を確認済み（工程2で作成、本工程で再実行しOK） |
| 入力が変わる場合 | 最多論点と最少論点の件数を入れ替えた隔離データで、読書面は7論点分そろって追従し、投票のVOTE_ISSUES/STANCES/choiceIdx式（バイト単位）は変わらないことを確認（`tests/test_ai_copyright_connected.py::test_display_adapts_to_changed_counts_while_vote_payload_stays_fixed`、工程2作成分を再実行） |
| 他テーマ | `verify_theme_page.py`で全10テーマNG 0件。`ai_copyright_connected.apply()`は`topic!=ai-copyright`で即座に無操作（`test_activation_is_explicit_and_other_themes_are_unchanged`で9テーマ分を確認） |
| 未再読論点 | 利用者モラル・倫理／法制度・規制整備を実機確認。「まだ編集部が投稿を1件ずつ読み直していません」の断り書きのみで、AIが自動でつけた区分は並ばないことを確認 |
| 投票 | 連動表示の適用前後でVOTE_ISSUES/STANCES/choiceIdx式が一致（`test_vote_registry_is_unaffected_by_the_connected_layout`）。今回の作業では投票UIそのものへの変更は無い |
| 印刷 | `docs/ai-copyright-connected-page.js`の`beforeprint`/`afterprint`ハンドラで折りたたみを全展開・fallback見出しを差し替える構造は工程4で実装済み。PDF化しての文字抽出までは行っていない（範囲外、後述） |
| 引用・授業 | 授業節の論点リンク（6リンク中1件を実クリックし到達を確認）。ai-copyrightには消費税版のような専用「引用コピー」機能は無く、この項目は該当なし（bukatsu-chiikiと同じ扱い） |

## 外観結果表（V01〜V12、消費税参照版との比較）

比較対象: `docs/consumption-tax-cut-reaction-map.html`（本番、確認日2026-09-23）と、
候補`docs/ai-copyright-reaction-map.html`に`ai_copyright_connected.apply(activate=True)`を
適用したもの（同日、ローカル配置）。1280px・375pxの2幅で確認（320pxは未確認、後述）。

| ID | 判定 | 根拠 |
|---|---|---|
| V01 | 合格 | 制度の短い現状→山・読書面→背景（年表）→旧節の折りたたみ→投票の順。参照版と対応する節の並びが一致 |
| V02 | 合格（差分に根拠あり） | バー→立場ボタン→山→論点ボタンが隙間なく一続き（本工程で修正、上記参照）。列数は参照版PC5列／ai-copyright PC4列で異なるが、これは立場が4種→3種という対象データの違いによるもの（ガイド「対象の選択肢数に応じた差は記録する」に該当）。375pxは両者とも2列＋「すべて」全幅で一致 |
| V03 | 合格 | 山の実寸210px（375px時180px）、0/50/100%軸、固定順、いずれも参照版と数値一致。海面下の演出を先に隠してから`getBBox()`で測る対応は工程3で実装済み（bukatsu-chiikiが後から踏んだ落とし穴を未然に回避） |
| V04 | 合格 | 論点ボタンPC4列・スマホ2列、名称と件数を別行表示。参照版と同じグリッド構成 |
| V05 | 合格 | 選択即座に濃紺・白文字（`#modes button[aria-pressed="true"]`）、山は選択立場の色、選択0.9・非選択0.23の濃淡、件数・割合の表示、いずれも実測・実機で一致 |
| V06 | 合格 | 理由・投稿と制度・資料を同じ読書面へ配置。PC2カラム／スマホ1カラム（上下）、図解は小さな入口から拡大、未再読・0件の表示も確認済み |
| V07 | 該当なし（根拠あり） | 理由別X投稿はai-copyrightに理由別の投稿データが存在しない（`configs/ai-copyright-reason-posts.json`等が無く、工程1内容確定書で確認済み）。bukatsu-chiikiも同じ理由で未実装のまま出荷された前例と同型 |
| V08 | 合格 | 「資料を読む／x投稿で語られない話／一次資料クイズ」の3タブ、論点内の「資料にあり収集投稿に無いこと」も保持、クイズは独立節を重複表示しない（旧`#quiz`は工程4でDOMから除去し3タブ内へ統合） |
| V09 | 合格 | `#bukatsu-check`（制度確認）・`#ai-copyright-audit`（claim-audit）・`#issue-cards`・`#ocean`の4旧節を通常画面で非表示（工程4）。統合先（読書面）・出典・印刷時の復元をそれぞれ確認済み |
| V10 | 概ね合格（未精査あり） | 山・ボタン・読書面の余白感、フォントサイズは参照版と同じCSS変数・クラス構造を採用しているため定性的に近い。文字倍率を変えた場合の崩れ確認までは行っていない（範囲外、後述） |
| V11 | 合格 | 480msの変形、連打後の収束、キーボード操作を確認。動きを減らす設定は本環境では未確認（範囲外） |
| V12 | 合格 | JS無効時の`#fallback`はバイト単位で不変。初期化失敗時のフォールバック（`readingTemplateFor()`が無ければ旧描画に後退する設計）はコードレビューで確認、実際に例外を注入しての実機確認までは行っていない（範囲外）。GA4/AdSense/canonical/OGPタグは前後で個数一致 |

## 範囲外・確認できなかったこと

- 320px幅での確認（1280px・375pxのみ実施）
- Chromium以外のエンジン（WebKit等）での確認。本環境はChromium系の組み込みブラウザのみ
- `prefers-reduced-motion: reduce`の直接エミュレート（本環境のブラウザツールに専用の設定項目が無い）
- 印刷プレビューのPDF化・文字抽出による内容照合（構造上正しいことの確認にとどめた）
- 初期化失敗（テンプレート欠落・接続JSON破損等）を実際に注入しての実機確認（コード上のフォールバック分岐の確認にとどめた）
- 文字サイズ変更（ブラウザの拡大表示）時の崩れ確認

## 保存物

比較・確認に使った候補HTML・スクリーンショットは一時的なローカルサーバー上でのみ確認し、
恒久的な保存はしていない（作業ツリー外への配置なし）。次工程（公開判断）に必要な識別値:
候補は本コミット時点の`scripts/ai_copyright_connected*.py`・`scripts/templates/ai_copyright_connected_bridge.js`・
`docs/ai-copyright-connected*.{css,js}`から生成したもの。

## 次にすること

工程6（完成確認と公開）。オーナーへ完成版と本記録を提示し、公開の判断を受ける。
公開時は`.claude/skills/release/SKILL.md`の手順に従う。
