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

## 状態

進行中。henoko-student-accidentを2026-09-19に本番反映→オーナー実地確認→
デザイン改訂5件（タブ形状・タブ間距離・「すべての意見」の区別・山なみの
背景表示化・背景の不透明度強化）を同日中に順次本番反映済み。本番
https://sns-reaction-map.jp/henoko-student-accident-reaction-map.html で
最終形を実機確認済み（デスクトップ・375px、山クリック時のスクロール・
立場タブ切り替え・論点タブを跨いだ連続切替、背景の山なみが実際に視認できる
ことも含む）。マージ時、別セッションのbike-blue-ticket起承転結再編・
ocean-layer修正（課題69・課題71）と競合したため、
`scripts/refresh_planet_section.py`の一般化された`_inject_landing_images()`へ
同じ修正を再適用して統合した（詳細は上記「マージ時の追記」）。fukushutoは
初版（丸ピル型）のdocs/を再生成し実機確認済みだが、v2〜v5デザインへの追従と
本番反映はまだ（オーナーの「辺野古だけ先に」指示の範囲外のため見送っている）。

残り8テーマ（bukatsu-chiiki / elderly-license-revocation / bike-blue-ticket /
school-nickname-ban / koshitsu-tenpakai / ai-copyright / takaichi /
constitutional-amendment・consumption-tax-cutは共通コード側は最終形まで
反映済みだがdocs/の再生成・本番反映はまだ。fukushutoは旧v1見た目のままdocs/再生成
のみ済み、v2〜v5への再生成が必要）は、オーナーが本番のhenoko-student-accidentページを
見て確認してから展開する。

## 次にすること

オーナーが本番の辺野古ページ（最終デザイン）を見て問題なければ、残りのテーマへ
同じ手順（各テーマの `build_<theme>_arena.py`（または対応するビルダー）を実行して
docs/を再生成→標準検査→`release`スキルで本番反映）で展開する。fukushutoは
v1のdocs/再生成が残っているため、再度ビルドし直してから展開する。

## 詳細

実装ブランチ: `task/issue-tabs-ui`（初版）・`task/issue-tabs-ui-v2`（タブ形状・
タブ間距離）・`task/issue-tabs-ui-v3`（「すべての意見」の区別）・
`task/issue-tabs-ui-v4`（山なみの背景表示化、drawPanel()クラッシュの修正含む）・
`task/issue-tabs-ui-v5`（背景の不透明度強化）。いずれもmainへマージ・反映済み。
worktreeは全て片付け済み。継続する場合は新しいworktreeを作る
