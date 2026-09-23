# 課題77 — bukatsu-chiiki連動表示・工程1〜5の完了記録（全文）

`tasks/task-77.md`の400行上限のため退避。内容は`tasks/task-77.md`に元あった記述から無変更。

## bukatsu-chiikiへの移植・工程1完了（2026-09-22）

作業ツリー`../isa-wt-task77-bukatsu`（ブランチ`task/task77-bukatsu-connected-layout`）で工程1完了。
**結論**: 原材料（沈んだ大陸・地下水脈・事実確認・論点別X投稿14件・理由5論点計43・クイズ7問等）は
ほぼ既存、無いのは連動画面のみ。投票は投票専用3立場で7×3=21通り、claim-audit論点タグは公開JSONに
既存、と当初の推定を訂正済み。理由別X投稿機能はtaxより規模大（最大43）のため独立工程とする方針。
**成果物**: [内容確定書](../designs/2026-09-22-task77-bukatsu-chiiki-content-contract.md)＋
[JSON](../designs/2026-09-22-task77-bukatsu-chiiki-content-contract.json)、
[taxスキーマ参照](../designs/2026-09-22-task77-consumption-tax-schema-reference.md)、
[6工程計画](../../configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md)。工程2〜6は未着手、公開への変更なし。

## bukatsu-chiikiへの移植・工程2完了（2026-09-23）

未確認事項3点を確認: 山なみ本体は通常更新で自動再生成されない、`bukatsu-background`/`bukatsu-check`は
両テーマ共通の部品名、tax版の連動表示も`verify_builder_rebuildability.py`の対象外で同じ扱いに揃えた。
`scripts/bukatsu_connected.py`・橋渡しJS・最小限のCSSを実装し`refresh_adapters/bukatsu.py`へ登録
（マーカー未挿入のため現在は無効化のまま）。語られていない争点3件は編集部推定をせず未タグで維持。
実機確認でSTANCE_GLANCEと山の立場フィルターの双方向連動を確認し、挿し込み位置に起因する空振り
バグを1件発見・修正した。新規テスト9件、全体1091件でOK。
**記録**: [実装内容・検証結果・次工程への引き継ぎ](2026-09-23-task77-bukatsu-chiiki-foundation.md)。
**範囲**: 生成器への登録まで。公開ページ・公開データ・投票への変更なし。工程3〜6は未着手。

## bukatsu-chiikiへの移植・工程3完了（2026-09-23）

論点を選んだときの読書面（理由・投稿例・資料照合・共通の心配・語られていない争点）を7論点分実装。
`#issue-cards`・`#fallback`など既に生成済みの静的内容を読んで使い、選定ロジックは複製していない。
`drawPanel()`だけを差し替える設計（`land()`/`orbit()`/`morphTo()`全てがこれを呼ぶため1箇所で足りる）。
7論点×5表示（すべて＋4立場、計35通り）を自動確認し異常なし。実機確認で2件の思い込み
（`show_coverage_note`/`show_unreviewed_note`という既存の表示フラグを見ておらず、
現行ページに無い注記を新たに増やしていた）を発見・修正した。
当初3点未達だったが、同日中にオーナー依頼で全て追加実装・完了: 山の変化アニメーション
（tax版のtaxAnimate/taxLayoutを移植、layout()だけ差し替えrender()は無変更。実機で幅の補間・
連打時の収束・キーボードフォーカスの維持を確認）、初期表示の自動着地（tax版の本番ページを
実機確認し「最初の1回は運ぶ先が無くスクロール不要」と判断、land()自体は変えず最初の1回だけ
bringIntoView()を無効化。ページ末尾のtemplateがまだパースされていないうちにsetTimeout(0)が
発火するバグを発見しDOMContentLoaded待ちに修正）、予想2問②の回答→論点移動リンク
（buildGuesses()自体は上書きせず#guessesへのイベント委譲、既表示の答え文から論点名を抽出）。
計画書のチェックリストは全項目達成。
**記録**: [実装内容・検証結果・次工程への引き継ぎ](2026-09-23-task77-bukatsu-chiiki-experience.md)。
**範囲**: 生成器・候補内部まで。公開ページ・公開データ・投票への変更なし。工程4〜6は未着手。

## bukatsu-chiikiへの移植・工程4完了（2026-09-23）

計画書が判断を求めていた年表6件の論点連動を、消費税の実際の作り（読書面側に関連項目を追加表示、
タグ無しでは検査が止まる厳格さ）をオーナーへ報告のうえ、年表本文を読んで作った論点タグ案を確認
していただいて確定（6件全てに論点id、地域格差・その他は該当なしのまま。無理な割り当てなし）。
`data/verification/bukatsu-chiiki-background.json`にissue_idsを追加し、読書面に「年表のどこが
関係する？」を実装。加えて、issue-cards・授業節・ブラウザの戻る/進む・引用URLがバラバラだった
論点選択の経路を`hashchange`1箇所に統一、一次資料クイズの答えから関係論点への移動（1主張が2論点に
またがる場合は2本リンク）、論点表示・出典操作のGA4計測（立場・自由記述は送らない）を実装。
投票の2立場体系混同・進捗バーの二重加算は実装前の調査で元から起きていないことを確認済み
（コード変更なし）。新規テスト2件（計15件）、全体1097件でOK。`verify_theme_page.py`もOK。
**記録**: [実装内容・検証結果・次工程への引き継ぎ](2026-09-23-task77-bukatsu-chiiki-integration.md)。
**範囲**: 生成器・候補内部まで。公開ページ・公開データ・投票への変更なし。
**訂正（オーナー指摘、記録に反映済み）**: 授業節の印刷ボタンは「未実装」と誤って報告していたが、
全テーマ共通の`topic-modern.js`/`topic-modern.css`が既に印刷（`window.print()`・A4向けCSS・
`classroom_print`計測）を実装済みで、bukatsu-chiikiも他テーマと同じくそのまま動いていた
（実機で確認、対応不要）。潮目カードへの片道リンクは消費税版にも計画書本体にも前例が無い独自追加と
判明し、オーナー指摘で削除済み（`renderReading()`から該当ブロックを削除、テスト15件・実機とも
再確認OK）。

## bukatsu-chiikiへの移植・工程5完了（2026-09-23）

**重大な発見・修正**: 山なみ全10テーマ共通の`scripts/refresh_planet_section.py`の仕上げ処理が、
連動表示の再適用を消費税テーマだけに決め打ちしており（`from consumption_tax_connected import apply`
を無条件呼び出し）、bukatsu-chiikiではエラーにならないまま素通りされていた。`bukatsu_connected.apply()`
を呼べる唯一の経路（`refresh_adapters/bukatsu.py`の`_build_once()`）は`docs/`へ書き込まれる実経路
（`DATA_REFRESH.md`のbukatsu-chiiki定期更新手順）に含まれておらず、**公開後の次回定期更新で
連動表示が更新されなくなる**という欠落だった。オーナー承認のうえ、既存の`TOPIC_ENRICH`と同じ
テーマ別対応表の考え方で`_apply_connected_display()`を新設し修正（`scripts/bukatsu_connected_content.py`
の絶対importにはリポジトリ直下もsys.pathに要ることが原因と判明、`from bukatsu_connected import apply`
という単純なbare importでは同じ`ModuleNotFoundError`を再現するのみで解決しないことを実機で確認して
から実装）。消費税・bike-blue-ticketの既存回帰検査と山なみ全10テーマの`verify_theme_page.py`を
再実行し、他テーマへの影響が無いことを確認。

その他: 投票7×3=21通りを実クリックし送信データ・保存内容が正しいことを確認（本番送信0件）、
320/375/PC幅×7論点×5表示=105通りの実機確認（横はみ出し・コンソールエラーとも0件）、動きを
減らす設定でアニメーションが即時反映されることを実測、入力（件数・順位）が変わっても表示は
追従し投票の保存式は変わらないことを検査化。計画書の検証表11項目すべて合格。
新規テスト: Python6件（計17件）、Playwright2ファイル（投票21通り・表示品質）。全体テスト
1103件でOK、山なみ全10テーマ`verify_theme_page.py`・`run_public_checks.py`ともOK。
**記録**: [実装内容・検証結果・次工程への引き継ぎ](2026-09-23-task77-bukatsu-chiiki-quality.md)。
**範囲**: `scripts/refresh_planet_section.py`（山なみ共通、テーマ別分岐の追加のみ）を含む。
公開ページ・公開データ・投票への変更なし。工程6は未着手。
