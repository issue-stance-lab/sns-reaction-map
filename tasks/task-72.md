# 課題72: 論点タブUI（山なみへ戻らず他の論点へ切り替え）

## 背景

オーナーから、henoko-student-accidentページのスクリーンショット（手書き注釈付き）で要望。
論点カード（例:「🏛️ 政治利用・基地問題」）の内訳を見るたびに山なみチャートへ戻って
クリックし直すのが面倒。見出しの下に、他の論点へ直接切り替えられる手描き風タブを
追加したい、という依頼（2026-09-19）。

## 実装

- 共通テンプレート `quality/prototypes/planet-prototype.template.html` と
  そのフォーク `quality/prototypes/constitutional-planet.template.html` の
  `drawPanel()` に `issueTabs(m)` を追加。`<h2>` 直後・`<p class="sub">` 直前に
  常に挿入する（テーマ間で位置を統一する）。押すと `land(i)` で即座に切り替わる
  （既存の `.issue-list`/`buildList()` と同じ経路。状態管理・aria-pressedの
  扱いを流用しただけで、新しい状態は増やしていない）。
- 見た目は `.modes`（立場フィルター）と同じ選択色言語（`var(--accent)`）を使い、
  角丸を非対称にして手描き感を出した（CSSのみ。新規フォント・画像・JSライブラリは
  追加していない）。

## 見つけた副作用と対処

影響範囲の洗い出し中、fukushuto・constitutional-amendment・consumption-tax-cutの
3テーマが持つ「論点ごとの図解画像」の後付け補完処理（`apply_landing_images()`等、
[[reference_planet_regen_wipes_hand_edits]]と同じパターン）が、`drawPanel()`内の
同じ挿入位置（`<h2>`直後）を文字列一致で探していた。fukushutoは実際に
`verify_builder_rebuildability.py`でクラッシュを検出（他2テーマはたまたま
アンカー文字列が短く、クラッシュはしないが「見出し→画像→タブ」という
意図しない順序になっていた）。3スクリプトとも「見出し→タブ→画像→統計」の順で
固定されるようアンカー文字列を修正した:

- `scripts/build_fukushuto_arena.py`（`apply_landing_images`）
- `scripts/build_constitutional_arena.py`（`apply_landing_images`）
- `scripts/refresh_planet_section.py`（`_inject_landing_images`、consumption-tax-cut・
  bike-blue-ticket共通担当）

**マージ時の追記（2026-09-19）**: mainへの反映直前に、別セッションが
`scripts/refresh_planet_section.py`の同じ関数（当時の名前は`_inject_ctc_landing_images`）を
「bike-blue-ticketにも同じ図解画像パッチを適用できるよう一般化する」形で作り直し、
`_inject_landing_images(block, data, topic, images, js_prefix)`へ先に統合していた
（課題69のbike-blue-ticket起承転結再編の一部）。競合したため、向こうの一般化された
関数に対して同じ「見出し→タブ→画像」の順の修正を再適用した。中身が対立していた
わけではなく、たまたま同じ場所を触っていただけだったため、両方の変更が両立する形へ
統合した。

## 検証済み

- henoko-student-accident: ブラウザで実際にタブ切り替えを確認（デスクトップ・375px
  モバイル幅とも正常、タブを押すと即座に見出し・統計・ヒートマップが切り替わる）。
  `verify_theme_page.py` OK（37件）・`verify_number_provenance.py` OK
- fukushuto: 図解画像付きの論点（都構想・維新）で「見出し→タブ→画像→統計」の順を
  実機確認。`verify_theme_page.py` OK（38件）
- 全11テーマ: `verify_builder_rebuildability.py` NG 0件（fukushuto修正前はNG 1件）
- 全テーマ: `verify_page_originality.py` OK・`validate_theme_seo.py` OK
- 関連ユニットテスト95件 OK（`test_henoko_planet` / `test_henoko_verified_refresh` /
  `test_henoko_public_counts` / `test_constitutional_planet_refresh` /
  `test_constitutional_public_counts` / `test_fukushuto_public_counts` /
  `test_planet_data` / `test_planet_page_preview`）
- THEMES.yamlのupdated_at・docs/sitemap.xmlのlastmod・configs/theme-seo.jsonの
  dateModifiedをhenoko-student-accident分だけ2026-09-19へ揃え、
  `validate_theme_seo.py` OKを確認

**既知の一時的な差分（対応不要・追跡中）**: マージ統合後、`python3 -m unittest discover -s tests`が
5件FAILのまま残る。全て「公開済みページが、いま正典から作り直した内容と一致すること」を
確認する系のテストで、対象は全て**このタスクで意図的にdocs/を再生成していない**（＝
オーナーがhenoko-student-accidentの本番を確認してから展開する）3テーマに限られる:

- `tests/test_bike_planet_refresh.py::test_refresh_runs_on_published_page_without_changes`
  （bike-blue-ticket）
- `tests/test_koshitsu_adapter.py::KoshitsuAdapterTests::test_published_page_matches_canonical`
  （koshitsu-tenpakai）
- `tests/test_nickname_adapter.py::NicknameArenaBuilderTests::test_planet_is_regenerated_instead_of_preserved`
  ／`test_published_page_matches_canonical`、`tests/test_nickname_public_counts.py::
  test_public_json_reproduces_published_page`（school-nickname-ban）

3テーマとも、実際の差分をその場で`difflib`により直接計算して確認済みで、
`issueTabs(m)`の追加（`.issue-tabs`のCSS・JS関数・`land(i)`への配線）だけで、
他の変更は無い。koshitsu-tenpakaiは専用の`refresh_verified_planet()`/
`apply_koshitsu_extras()`（`build_koshitsu_arena.py`内）が正しい比較対象で、
共通の`refresh_planet_section.refresh()`で比較すると無関係な差分が出るため
注意（実際に一度誤診断しかけた）。

いずれも非公開データ（`social-samples/`）が無いと`skipUnless`でスキップされる
仕様（CI「公開ファイルの検査」には含まれない）ので、公開への影響はない。
各テーマへのタブ展開時に自然に解消する。main単体（マージ前）ではこの5件は
全てPASSすることを確認済みで、原因は今回の統合作業に限定されている。

**解消（2026-09-19、残り7テーマ展開）**: 上記3テーマ（bike-blue-ticket・
koshitsu-tenpakai・school-nickname-ban）へ実際にタブUIを展開し、この5件は
全てPASSに戻った。詳細は下記「残りテーマへの展開（2〜8テーマ目）」参照。

## デザイン改訂（v2、2026-09-19・オーナーの実地フィードバック2件）

henoko-student-accident本番反映後、オーナーが実際の画面を見て2件指摘し、その場で
両方直して再反映した（ブランチ`task/issue-tabs-ui-v2`）。

1. **「本当のタブのようなデザインにはならないの？」**: 初版は丸いピル型（`.modes`と
   同じ形）で、タブというよりフィルターチップに見えていた。上だけ角丸・下は直線の
   台形シルエットに作り直し、選んでいるタブだけ下の縁をパネルと同じ色にして本文と
   地続きに見せ、選んでいないタブは`translateY(3px)`で少し下げて背後にあるように
   見せた（実際のブラウザタブ・ファイルフォルダのタブと同じ視覚言語）。
2. **「二つのタブの位置が遠いので使いずらい」**: `.modes`（立場フィルター）の直後に
   山なみチャート本体（数百px）が挟まり、論点タブ（パネル内）までの距離が遠かった。
   `.stage`内の`.chart-box`と`.panel`にCSS `order`を設定し、表示順だけを
   panel→chart-boxへ入れ替えた（DOM順・JSは無変更）。結果、立場フィルターと論点
   タブが案内文1行を挟むだけの近さになった。

ついでに、`.modes`自体も論点タブと同じタブ形状へ揃えた（指摘1はタブ全般の形の話
だったため）。LIGHT_SKIN側の旧上書き（`.modes button[aria-pressed=true]{background:
#e4edff}`）は新CSSと衝突するため削除した。

## デザイン改訂（v3、2026-09-19・オーナーの実地フィードバック3件目）

**「全ての意見は第分類なので区別してタブ表示した方が良いのでは」**: 「すべての意見」は
実際の立場（文科省判断を支持/反発・論点を切り分ける・中立）の1つではなく絞り込み
無しを表す別種の項目であることを、間隔（`margin-right:14px`）と薄い仕切り線
（`::after`擬似要素）で示した。`buildModes()`が既に付与している`data-m="all"`属性を
そのままCSSセレクタに使ったため、JS側の変更は不要だった（ブランチ
`task/issue-tabs-ui-v3`）。

## デザイン改訂（v4、2026-09-19・オーナーの実地フィードバック4件目）

**「意見をクリックすると下の図にスライドして見ずらい。図も下だと見ずらい。
クリックした後は、図をマトリックス図の後ろに薄くすかせて表示させたりは
できますか？」**: 論点を選んだ後、山なみ（chart-box要素）を升目カード
（`#dotbox`）の背後へ移し、`opacity:.22`・`pointer-events:none`で薄く重ねる
ようにした。別セクションへスクロールしなくても山の形が升目カードの余白に
うっすら見える。要素を作り直さず同じchart-boxを動かす方式（`placeChart()`/
`evacuateChart()`、ブランチ`task/issue-tabs-ui-v4`）。

**実装中に見つけた不具合（本番反映前にローカルで検出・修正済み）**:
`drawPanel()`は`#panel`のinnerHTMLを丸ごと作り直すため、chart-boxが
`#dot-slot`の中（`#panel`の子孫）にいる状態で`drawPanel()`を呼ぶと
chart-boxごと消え、直後の`render()`が`#chartdesc`等を見失って
`TypeError: Cannot set properties of null`が発生していた。論点タブで
別の論点へ切り替えたとき（2回目以降の`land()`）に実際にクラッシュを再現し、
コンソールエラーで発見した。`evacuateChart()`を新設し、`land()`・`orbit()`・
`morphTo()`（立場フィルター切替で`st.landed`が0件にならず残るケース）の
`drawPanel()`呼び出し全てで、呼ぶ前に必ずchart-boxを`.stage`側へ退避させる
よう修正。`#dotbox`の背景（LIGHT_SKIN）も完全不透明だと山なみを隠すため
`rgba(242,246,253,.82)`に変更した。

## デザイン改訂（v5、2026-09-19・オーナーの実地フィードバック5件目）

**「透けてないです、全然見えません」**: v4の`opacity:.22`（chart-box）×
`rgba(...,.82)`（`#dotbox`背景）の組み合わせは、掛け合わせると実効的な
可視度が約4%しかなく、意図に反してほぼ見えていなかった。chart-boxを`.42`、
`#dotbox`の背景を`rgba(242,246,253,.4)`まで引き上げ、可視度を約25%へ
大幅に強めた（ブランチ`task/issue-tabs-ui-v5`）。件数・割合等の数値は
`.ro`/`.dot-mech`側の個別の不透明背景で別途確保されているため、この変更で
読みにくくなる数値表示は無い。

## デザイン改訂（v6、2026-09-19・オーナーの実地フィードバック6件目）

**「全ての意見などクリックした時のスクロール位置が下すぎるので、位置を確認」**:
`morphTo()`（立場フィルター切替）の狭い画面向けスクロールが、`#section`
（山なみの図そのもの）を対象にしたままだったのが原因。v4でchart-boxを
升目カードの背後の背景要素（`as-backdrop`）にした際、これは`height:100%`で
`#dot-slot`の高さいっぱい（実測688px、モバイル画面の8割超）まで伸びるため、
これを中心に合わせようとする`bringIntoView()`の計算が`scrollY`を大きく
ずらし、`.modes`が画面上端より453px上に押し出されていた（実機再現・計測済み）。
`land()`と同じくパネルの見出し（`#panel h2`）へ運ぶよう変更（ブランチ
`task/issue-tabs-ui-v6`）。

## デザイン改訂（v7、2026-09-19・オーナーの実地フィードバック7件目）

**「資料にしかない話を見る、を推してもどこに出たかわかりにくい、アニメーションして
出てくるようにできる？」**: 「資料にしかない話を見る」ボタンは一次資料クイズの下という
離れた場所に`#ocean`セクションを開くが、スクロール自体は起きていた（実測確認済み）ため
「起きたことが分かりにくい」が実態だった。スクロール先の見出しに、ふわっと現れる動き
（0.5s フェード+上からのスライド）と帯の点滅（1.8s、`--reveal-flash:#e4edff`から透明へ）を
追加し、到着点を分かりやすくした。閉じてすぐ開き直しても再生されるよう、
`just-revealed`クラスを一度外して強制再描画してから付け直す（ブランチ
`task/issue-tabs-ui-v7`）。

**実装中に見つけた不具合（本番反映前にローカルで検出・修正済み）**: 新設した
`@keyframes isa-ocean-reveal`/`isa-ocean-flash`を、共通テンプレート
（`quality/prototypes/*.template.html`）の`<style>`内にそのまま書いたところ、生成後の
HTMLで`#planet-block @keyframes isa-ocean-reveal{...}`という無効なCSSになり、
アニメーションが発火しなかった。原因は`scripts/build_planet_page_preview.py`の
`scope_css()`が「直前の`}`の次の1文字が`@`かどうか」だけで`@keyframes`を判定する実装
のため、改行を1つ挟むだけで通常のセレクタと誤認され`#planet-block`が誤って
前置されていた。`scope_css()`を経由しない`LIGHT_SKIN`側（同スクリプト内、既存の
`@keyframes isa-pnum-pop`と同じ場所）へ移し、`#planet-block`を手動で前置することで
回避した（`scope_css()`自体は共有の既存関数のため変更していない）。

**検証**: henoko-student-accidentのローカルプレビューでデスクトップ・375pxモバイル幅
とも、`getComputedStyle`によるアニメーション再生確認（`opacity`0→1、背景色が
`--reveal-flash`から透明へ推移）とスクロール先（`scrollY`の到達値が一致）を確認。
`verify_theme_page.py`・`verify_number_provenance.py`ともOK。本番反映後、実機で
スクロール（0→4689px、見出しが画面内に到達）とアニメーション登録
（`getComputedStyle().animationName`が`isa-ocean-reveal, isa-ocean-flash`）を再確認。

## デザイン改訂（v8、2026-09-19・オーナーの実地フィードバック8件目）

**「その下の編集部の横断整理との差があまりないから出たのかどうかがわかりずらい／
ふあっと出るけど、短い／カードなどを駆使してもっとわかりやすくして」**: v7で
到着演出（アニメーション）は付けたが、アニメーションが終わった後の見た目が、
すぐ下にある常時表示の「編集部の横断整理」(`#editorial`)とほぼ同じだった。
両セクションとも同じ`h3.sec`見出し・ほぼ同じカード配色
（`.sunk`/`.vein`と`.findings li`はどちらも`background:var(--panel)`、
角丸10px、薄い枠線）を使っており、一時的な点滅が終わると見分けがつかなく
なるのが実態だった（ブランチ`task/issue-tabs-ui-v8`）。

- `#ocean`セクション全体を、薄い青の背景・枠線・角丸14px・影を持つ1枚の
  カードに変更（常時。アニメーションが終わっても残る）。`#editorial`は
  白背景のまま変更せず、`#ocean`だけを「特別な内容」として浮き上がらせた
- 見出し直下に「🔍 資料にしかない話」のバッジ（濃い青の丸ピル）を追加
  （`scripts/build_planet_data.py`の`static_ocean()`。この関数は全テーマ
  共通のため、展開時は自動的に同じバッジが付く）
- 到着演出の継続時間を伸ばした（フェード0.5s→0.7s、点滅1.8s→2.6s）。
  点滅の着地点も「透明」から「常時の背景色（薄い青）」に変更し、光った後も
  色が消えずに残るようにした（`scripts/build_planet_page_preview.py`の
  `LIGHT_SKIN`）

**検証**: henoko-student-accidentのローカルプレビューでデスクトップ・375px
モバイル幅とも、`#ocean`終端と`#editorial`開始の境界が色で明確に分かることを
スクリーンショットで確認。アニメーションは`getComputedStyle`で開始色
（`--reveal-flash`）から常時色（`--ocean-bg`）への推移を確認（自動テストの
ポーリングでは描画が進まず値が固まって見える環境依存の癖があったため、
実際に画面を描画させるスクリーンショット越しの計測で確認し直した）。
`verify_theme_page.py`・`verify_number_provenance.py`ともOK。本番反映後、
実機でバッジ・カード・スクロール到達を再確認。

## 残りテーマへの展開（1テーマ目: bukatsu-chiiki、2026-09-19）

オーナー指示「まず地域テーマから進めて」を受け、残り8テーマのうち
bukatsu-chiiki（部活動の地域移行）から展開を開始した（ブランチ
`task/bukatsu-chiiki-planet-rollout`）。

- `scripts/refresh_planet_section.py --topic bukatsu-chiiki --for-docs` で
  共通テンプレートの最終形（v2〜v8）を反映。bukatsu-chiiki専用の後付け処理
  （`_inject_bukatsu_go_cards`）は`<div class="extras" id="extras-{id}">`を
  アンカーにしており、新設の`issueTabs(m)`（`<h2>`直後に挿入）とは挿入位置が
  重ならないため、fukushuto等で起きた「見出し→タブ→画像」の順序不具合
  （上記「見つけた副作用と対処」参照）は再発しなかった
- `verify_theme_page.py`・`verify_number_provenance.py`・`verify_page_originality.py`
  とも OK。`python3 -m unittest discover -s tests`は983件中、bike-blue-ticket・
  koshitsu-tenpakai・school-nickname-banの既知5件のみ残存（bukatsu-chiiki分は
  0件、既知の差分に変化なし）
- ローカルプレビュー（一時HTTPサーバー経由）でデスクトップ・375pxモバイル幅とも
  実機確認: 山をクリックすると論点タブが7つ表示され論点名・アイコンが正しいこと、
  タブ間の直接切り替え（山なみへ戻らない）が機能すること、山なみが升目カードの
  背後にうっすら見えること、「資料にしかない話を見る」を押すと薄い青のカードが
  常時表示され`#editorial`（白背景のまま）との境界が色で明確なこと、を確認
- 本番反映後、同じ内容を`javascript_tool`でも再確認（論点タブ7件・バッジ文言・
  カード背景色・アニメーション登録）
- **追加で見つけた差分**: デザイン反映だけでは`THEMES.yaml`のupdated_at・
  `docs/sitemap.xml`のlastmod・`configs/theme-seo.json`のdateModified・
  ページ自身のJSON-LD dateModified・可視の「最終更新日」表示が2026-09-15の
  まま揃っておらず、`scripts/seo/validate_theme_seo.py`がJSON-LD不一致と
  可視日付欠落を検出した。5箇所を2026-09-19へ揃えて解消（[[reference_updated_at_cascade]]
  と同じ落とし穴）。henoko-student-accidentのv1反映時にも同じ調整をしていたが、
  今回は「デザインのみの反映では自動で揃わない」ことを実際に踏んで再確認した形

### CI障害の発見と修正（2026-09-19、オーナーの失敗通知メールで発覚）

bukatsu-chiiki反映後の報告直後、オーナーからGitHub Actions「公開ファイルの検査」
failureメールのスクリーンショットが届いた。`gh run list`で確認すると、実は
**`task/issue-tabs-ui-v6`のマージ（2026-09-19 03:07頃）以降ずっと赤いまま**
だったと判明（v6〜v8・bukatsu-chiikiのどの反映報告のときも、ローカルの
`run_public_checks.py`が「既知の2件（bike-blue-ticket・school-nickname-ban）
だけのNG」と一致していたため、CIも同じだと思い込み`gh run list`で実際のCI結果を
確かめていなかった。[[reference_planetpage_rollout]]に書かれている「CIが赤いまま
放置されていないか、pushする前にgh run listで確かめる」という教訓を今回も
怠っていた）。原因は2つあり、両方とも修正・push・グリーン化を確認した:

1. **自分の作業による回帰（2件）**:
   - TASK_BOARD.mdの課題72行を更新した際、「状態」「次にすること」が文字数上限
     （120文字、`tests/test_task_board.py`）を超えていた。索引側を短縮し詳細は
     本ファイルへ寄せて解消
   - `THEMES.yaml`のbukatsu-chiiki.updated_atを2026-09-19へ揃えた際、連鎖先の
     `DATA_SHEET.md`（`scripts/build_data_sheet.py`）と`docs/index.html`の
     更新バー・埋め込みJS（`scripts/sync_portal_stats.py`）の再生成を忘れていた
     （`validate_theme_seo.py`と`verify_top_page.py`は確認したが、この2つは
     どちらの検査対象にも入っておらず、手元の`unittest discover`をSEO修正後に
     再度回すまで気づけなかった）。両スクリプトを再実行して解消
2. **課題72と無関係の既存不具合（1件、修正はしたが本来は別課題）**:
   `tests/test_ocean_layer.py::test_existing_koshitsu_tenpakai_sunk_continents_passes`
   （課題71「海面より下データの検査不具合を修正」で2026-09-19に新設された
   テスト、v6反映と同時期）が、非公開正典（`social-samples/`）が無い環境では
   `skipped`が必ず0件でなくなる作り（`verify_ocean_layer.load_canonical_hashes()`
   がNoneを返すと`verify_editorial_confirmation_rule()`は常に`skipped=True`を
   返す）にもかかわらず、他の非公開データ依存テストと違い`skipUnless`で
   CIから除外されていなかった。同じ`skipUnless`パターンを追加して解消
   （ブランチ`fix/ocean-layer-ci-skip`）。この不具合自体はbukatsu-chiikiの
   反映内容とは無関係で、たまたま同じタイミングで気づいた

いずれも`gh run list`でグリーン化（`公開ファイルの検査`が`success`）を実際に
確認済み。**教訓**: ローカルの`run_public_checks.py`が「既知のNGと一致している」
ことは、CIが同じ理由で落ちていることの証明にはならない。今回はたまたま別の
原因（ローカルでは非公開正典がありCI専用の不具合が再現しない）で同じ「NG 1件」
という表示になっていただけだった。**push後は`gh run list`で実際のCI結果を
見るまで安心しない**こと。

## 残りテーマへの展開（2〜8テーマ目、2026-09-19）

オーナー指示「残り7テーマも続けて進めて」を受け、bukatsu-chiiki以外の残り7テーマ
（elderly-license-revocation・bike-blue-ticket・school-nickname-ban・
koshitsu-tenpakai・ai-copyright・constitutional-amendment・consumption-tax-cut）
へ一括展開した（ブランチ`task/planet-rollout-batch2`）。takaichiは対象外
（下記「takaichiは対象外」参照）。

**テーマごとに再生成経路が違う**（着手前に必ず確認すること）:
- 汎用（`refresh_planet_section.py --topic <theme> --for-docs`）:
  elderly-license-revocation・bike-blue-ticket・ai-copyright・consumption-tax-cut
- 専用ビルダー・無引数で実行: `build_nickname_arena.py`（school-nickname-ban）・
  `build_constitutional_arena.py`（constitutional-amendment）
- 専用ビルダー・`--public-counts-only`付きで実行: `build_koshitsu_arena.py`
  （koshitsu-tenpakai。他2つの`--public-counts-only`とは意味が違うので注意）

7テーマとも`verify_theme_page.py`・`verify_number_provenance.py`・
`verify_page_originality.py`OK。ブラウザでの実機確認は3経路を代表して
elderly-license-revocation（汎用）・school-nickname-ban（専用・無引数）・
koshitsu-tenpakai（専用・`--public-counts-only`）を選び、山クリック→論点タブ
7件切り替え→「資料にしかない話を見る」のカード表示までデスクトップで確認
（コードは全テーマ共通のため、残り4テーマは`verify_theme_page.py`等の
スクリプト検査とJS越しの構造確認〈タブ数・ocean存在・fukushuto系3テーマの
「見出し→タブ→画像」順序〉で代替）。`unittest discover`は983件が**全通過**
（bike-blue-ticket・koshitsu-tenpakai・school-nickname-banの既知5件の差分も
これで解消——task-72.md冒頭の「既知の一時的な差分」節は本ラウンドで解消済み）。

**「最終更新日」の連鎖で、bukatsu-chiiki単体のときには気づけなかった不具合を
3つ踏んだ（全て解消済み）**:
1. `THEMES.yaml`の`updated_at`は、`build_planet_data.py`がPLANET_SECTION内の
   「／更新 」キャプションに焼き込む。updated_atを先に変えてからPLANET_SECTIONを
   作り直さないと、キャプションだけ古い日付のまま残る（一度、逆順で踏んで
   全7テーマを再生成し直した）
2. `updated_at`は`data/public/themes/{theme}.json`の`updated_on`
   （`public_registry_common.py`）にも焼き込まれる。`build_public_registry.py
   --all`で作り直さないと、`apply_public_counts()`の正典照合が
   「公開JSONが現在の正典・照合資料と一致しません」で落ちる
   （constitutional-amendment専用テストが検出）。このとき、henoko-student-accident・
   bukatsu-chiikiのpublic JSON（過去の反映時に取り残されていた分）もあわせて
   最新化された
3. bike-blue-ticket・elderly-license-revocationは`sample_period_source:
   owner_confirmed`で取得期間が手動固定されており、`updated_at`を
   `sample_period`終端より後ろへ進めると`verify_sample_periods.py`が
   「取得期間の終わりが最終更新日と違う」で落ちる。この2テーマだけ`updated_at`を
   元の値（2026-09-12・2026-09-04）へ戻した。**データ収集を伴わないデザインだけの
   反映では、この2テーマの「最終更新日」表示は据え置くのが正しい**
4. （テスト自体には出ないが同種）`data/verification/adoption/registry.json`
   （採否根拠のsnapshot fingerprint）も、`build_public_registry.py --all`で
   変わった7ファイル分が食い違い`verify_adoption_registry.py`がNGになった。
   `build_adoption_registry.py`で再スナップショットして解消

bukatsu-chiiki自身も、前ラウンドの反映時に上記1・2を踏んでおり
（PLANET_SECTIONのキャプションとpublic JSONのupdated_onがTHEMES.yaml側
（09-19）に追従していなかった）、このラウンドであわせて再生成し解消した。

本番反映後、7テーマとも`curl`で「issue-tabs」文字列の出現を確認。
`gh run list`で「公開ファイルの検査」がgreenであることも確認済み
（release スキルの新設⑤.5）。

**takaichiは対象外**: `THEMES.yaml`で`published: unlisted`（サイト内ナビ・
sitemap.xmlに載らない）かつ`docs/takaichi-reaction-map-standard.html`は
そもそもPLANET_SECTIONマーカーを持たない別形式のページで、他10テーマの
「山なみ」変換（課題54）を経ていない。今回の「デザイン再生成」の対象ではなく、
含めるなら課題54相当の新規変換が要る別スコープの作業。オーナーへ報告のうえ
このラウンドでは触れていない。

## 状態

henoko-student-accident・bukatsu-chiiki・elderly-license-revocation・
bike-blue-ticket・school-nickname-ban・koshitsu-tenpakai・ai-copyright・
constitutional-amendment・consumption-tax-cut（9テーマ）に共通テンプレート
最終形（論点タブ・山なみの背景表示・「資料にしかない話」のカード化）を
本番反映済み。残るのはfukushuto（v1のまま、v2〜v8への再生成が必要）と
takaichi（別スコープ、上記参照）の2テーマ。

## 次にすること

fukushutoへの展開（`build_fukushuto_arena.py`、`apply_landing_images()`の
「見出し→タブ→画像」順序は既に対応済み）をオーナーに確認のうえ進める。
takaichiは山なみ変換自体が別スコープのため、着手するかどうかオーナー判断。

## 詳細

実装ブランチ: `task/issue-tabs-ui`（初版）・`task/issue-tabs-ui-v2`（タブ形状・
タブ間距離）・`task/issue-tabs-ui-v3`（「すべての意見」の区別）・
`task/issue-tabs-ui-v4`（山なみの背景表示化、drawPanel()クラッシュの修正含む）・
`task/issue-tabs-ui-v5`（背景の不透明度強化）・`task/issue-tabs-ui-v6`
（立場フィルター切替時のスクロール先修正）・`task/issue-tabs-ui-v7`
（「資料にしかない話を見る」の到着演出、scope_css()の@keyframes不具合の発見と回避
含む）・`task/issue-tabs-ui-v8`（同演出の常時カード化・バッジ追加、演出の
継続時間延長）・`task/bukatsu-chiiki-planet-rollout`（残りテーマ展開の1テーマ目、
SEO日付整合の修正含む）。いずれもmainへマージ・反映済み。worktreeは全て
片付け済み。継続する場合は新しいworktreeを作る
