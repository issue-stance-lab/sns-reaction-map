# 課題77 — ai-copyright連動表示・工程別の完了記録（全文）

`tasks/task-77.md`の400行上限のため退避。工程1の記述は元あった内容から無変更。
bukatsu-chiikiの同種の記録は[bukatsu-chiiki版](2026-09-23-task77-bukatsu-chiiki-full-log.md)。

## ai-copyrightへの移植・工程1完了（2026-09-23）

作業ツリー`../isa-wt-task77-ai-copyright`（ブランチ`task/task77-ai-copyright-connected-layout`）で工程1完了。
**結論**: 原材料（沈んだ大陸4件・地下水脈2本・資料照合6件・論点ごとのX投稿7論点×2件・編集部整理5件・
一次資料クイズ6問・年表6段階・授業節）はほぼ既存、無いのは連動画面のみ。bukatsu-chiiki・消費税に
無い独自要素が2つ（`#bukatsu-check`＝「法律と任意のルールを分ける」制度確認4項目、`#copyright-entry`＝
「判断の入口」3段階）あり、いずれも論点タグが無い真のギャップとしてドラフト対応案を用意した
（bukatsu-checkの後日タグ付けの二度手間を避けるため）。理由(reason)ごとの投稿例開閉機能は
bukatsu-chiiki同様、新設しない方針を提案。沈んだ大陸・claim-auditは全件が論点タグ済みで
bukatsu-chikiより状態が良い。
**副産物**: 山なみ移行後、潮目ウィジェット（`#ai-copyright-tide-widget`）が通常更新で自動更新
されなくなっている既存の不具合を発見し、課題77とは別に課題90として新規登録した
（課題77の範囲外、本移植では現状維持のまま位置と機能を運ぶ）。
**成果物**: [内容確定書](../designs/2026-09-23-task77-ai-copyright-content-contract.md)＋
[JSON](../designs/2026-09-23-task77-ai-copyright-content-contract.json)。
工程2〜6は未着手、公開への変更なし。

## ai-copyrightへの移植・工程2完了（2026-09-23）

`scripts/ai_copyright_connected.py`・橋渡しJS・最小限のCSSを実装し、`refresh_adapters/ai_copyright.py`
の候補生成（`_run_builder()`）と`refresh_planet_section.py`の`_apply_connected_display()`（通常更新時）の
両方の更新経路へ最初から登録した（bukatsu-chiiki工程5で発覚した「連動表示が通常のデータ更新の
どこからも再適用されない」欠落の再発防止を、今回は工程2の時点で先取りして両経路を登録。
マーカー未挿入のため現在は無効化のまま）。

工程1のドラフト対応案どおり、`data/verification/ai-copyright-background.json`のchecklist.items[]4件
（AI学習と著作権侵害→学習データ・無断利用、学習データの情報開示→学習データ・無断利用＋法制度・
規制整備、2026年の著作権法改正→法制度・規制整備、声・作風の保護→クリエイター保護・権利）へ
`id`と`issue_ids`を追加し接続した（bukatsu-checkのような後日タグ付けの二度手間を回避）。年表6件は
対応する論点が一意に定まらないため無タグのまま維持（V01の要件は日付切替のみで論点連動は必須では
ない。タグが増えれば`content_index()`が自動で拾う作り）。

STANCE_GLANCE（冒頭の立場バー）と山の立場フィルター（#modes）の双方向連動を実装。実機確認で
STANCE_GLANCEのボタンを押すと#modesと山の両方に反映されること、逆に#modesを押すとSTANCE_GLANCE
に反映されること、山なみが正しい件数で再描画されること（例: 「中立・情報」に絞ると最多論点が
「学習データ・無断利用」から「利用者モラル・倫理」へ変わる表示に追従）、コンソールエラーが無い
ことを確認した。

新規テスト18件（データ層13件`tests/test_ai_copyright_connected.py`・
`refresh_planet_section.py`経由の実更新5件`tests/test_ai_copyright_connected_refresh.py`）、
全体1123件でOK。`verify_theme_page.py`・`verify_number_provenance.py`・`verify_themes_yaml.py`・
`run_public_checks.py`・`verify_top_page.py`いずれもOK。

**範囲**: 生成器・アダプタ・山なみ更新スクリプトへの登録と、内部データ（background.json）への
タグ追加まで。公開ページ・公開データ・投票への変更なし
（`docs/ai-copyright-reaction-map.html`はバイト単位で無変更、git差分0）。

**次にすること**: 工程3（中心の見た目と選択体験）— 論点を選んだときの読書面を
`bukatsu_connected_content.py`を土台に実装する。予想2問（`#guesses`/`buildGuesses()`）・
一次資料クイズ（`#quiz`/`buildQuiz()`）はai-copyrightにも存在することを確認済み
（工程1で未確認だった項目、本工程で解消）。

## ai-copyrightへの移植・工程3完了（2026-09-23）

`scripts/ai_copyright_connected_content.py`を新設し、`bukatsu_connected_content.py`を土台に
論点ごとの読書面（`<template id="ai-copyright-reading-{id}">`、理由の内訳・投稿例2件・
制度確認・資料照合・共通の心配・語られていない争点）を生成。bukatsu-chiikiと異なり生データに
立場別の理由内訳が無いため、理由の件数・割合は「全立場」のみ表示する簡略版とした
（V05は山本体の選択色・件数で満たすため必須要件ではない）。年表は工程2の設計どおり無タグの
ため現状は空のまま（タグが増えれば自動反映）。

`scripts/templates/ai_copyright_connected_bridge.js`にdrawPanel()差し替え（読書面表示）・
山の選択色1色化（V05、選択0.9／非選択0.23）・480msの滑らかな変化（V11）・初期表示の自動着地
（未訪問時は1位論点、hash付きURL再訪問時はtemplate未パース競合の再着地も含む）を追加。
深いリンクの名前空間統一・クイズ/予想からの論点移動・出典計測はbukatsu-chiikiと同じ区切りで
工程4へ送る。新規`docs/ai-copyright-connected.js`（バー・山・論点ボタンの配置、V02〜V04。
予想2問の折りたたみ・X投稿カードの遅延読込を含む）と`docs/ai-copyright-connected.css`
（読書面の見た目＋`.ai-copyright-connected`のページ配置）を追加。

**実装中に発見・自己修正した問題（bukatsu-chiikiが工程5後に踏んだV03の落とし穴と同型）**:
山のSVGを`getBBox()`で実描画範囲に合わせて縮小する際、海面下の演出（`#seafloor`/`#seacover`と
無名の背景矩形・目盛り線）を先に非表示にしないまま測っていたため、viewBox高さが482のまま
（縮小前とほぼ同じ）になっていた。ブラウザ実機確認でグラフが縮んで見えないことに気づき、
bukatsu-chiikiのCSS（`.chart-box .dive/#seafloor/#seacover`等を`display:none`）と同じ非表示
ルールを追加してから再測定し、viewBox高さ482→313（実際の山の高さ相当）に是正。**bukatsu-chiikiは
この不具合を公開後にオーナー指摘で気づいたが、ai-copyrightでは実装中の自機確認で先に検知・
修正できた**（移植手順文書に事前追記されていた教訓が効いた）。

**確認内容**: ローカルサーバーで実機確認。①論点ボタン7件それぞれで読書面が正しい内容に
差し替わる（未再読2論点は「AIが自動でつけた区分は並べない」空状態、再読5論点は理由の内訳と
件数が表示）、②立場フィルター切替でSTANCE_GLANCE・#modes・山の色/件数/割合が同期し
`AiCopyrightConnectedMap.getState()`が正しい状態を返す、③山の全7島が選択立場の色1色に
塗り分けられ選択島のみopacity 0.9、④375px幅で#modesが2列・読書面が上下1カラムに切替、
⑤図解拡大モーダルが開く、⑥コンソールエラー無し、をそれぞれ確認。

新規テスト8件追加（読書面の生成・空状態・投稿抽出・制度確認・資料照合・図解解決・
異常系のvalidate）、既存の`validate()`にも読書面の接続検査を追加。全体1131件でOK。
`verify_theme_page.py`・`verify_number_provenance.py`・`verify_themes_yaml.py`・
`verify_top_page.py`・`run_public_checks.py`いずれもOK。

**範囲**: 生成器・アダプタ・山なみ更新スクリプトと、新規の静的CSS/JSファイルまで。
公開ページ・公開データ・投票への変更なし（`docs/ai-copyright-reaction-map.html`は
バイト単位で無変更、git差分0）。

**次にすること**: 工程4（ページ全体の再配置・統合）— 理由別X投稿・資料3タブ・旧セクション
（`#ai-copyright-audit`・`#issue-cards`・`#ocean`・`#bukatsu-check`・`#copyright-entry`）の
統合と非表示、`#copyright-entry`（判断の入口、ai-copyright独自）の配置確定。
