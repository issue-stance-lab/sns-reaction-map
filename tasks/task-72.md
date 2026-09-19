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

## 状態

進行中。henoko-student-accidentとfukushutoでdocs/を実際に再生成し、実機確認・標準検査を
通した。オーナーの指示で、まずhenoko-student-accidentだけを先に本番反映する
（2026-09-19、「辺野古だけ先に公開してチェックします」）。残り8テーマ
（bukatsu-chiiki / elderly-license-revocation / bike-blue-ticket /
school-nickname-ban / koshitsu-tenpakai / ai-copyright / takaichi /
constitutional-amendment・consumption-tax-cutは共通コード側は修正済みだが
docs/の再生成はまだ）は、オーナーが本番のhenoko-student-accidentページを見て
確認してから展開する。

## 次にすること

オーナーが本番の辺野古ページを見て問題なければ、残り8テーマへ同じ手順
（各テーマの `build_<theme>_arena.py`（または対応するビルダー）を実行して
docs/を再生成→標準検査）で展開し、`release` スキルで本番反映する。

## 詳細

ブランチ: `task/issue-tabs-ui`（worktree: `isa-wt-issue-tabs`、
`/Volumes/M2-WorkSpace/Projects/副業/isa-wt-issue-tabs`）
