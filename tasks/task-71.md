# 課題71: 論点タブUI（山なみへ戻らず他の論点へ切り替え）

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
固定されるようアンカー文字列を修正済み:

- `scripts/build_fukushuto_arena.py`（`apply_landing_images`）
- `scripts/build_constitutional_arena.py`（`apply_landing_images`）
- `scripts/refresh_planet_section.py`（`_inject_ctc_landing_images`、consumption-tax-cut担当）

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

## 状態

進行中。henoko-student-accidentとfukushutoでdocs/を実際に再生成し、実機確認・標準検査を
通した。残り8テーマ（bukatsu-chiiki / elderly-license-revocation / bike-blue-ticket /
school-nickname-ban / koshitsu-tenpakai / ai-copyright / takaichi /
constitutional-amendment・consumption-tax-cutは共通コード側は修正済みだが
docs/の再生成はまだ）は、オーナーが手描き風タブの見た目を確認してから展開する
（新しいビジュアル要素のため、10テーマ分を先に展開してから見た目を直すより、
1テーマで確認を取ってからのほうが手戻りが少ないと判断）。

## 次にすること

オーナーがスクリーンショットを見て問題なければ、残り8テーマへ同じ手順
（各テーマの `build_<theme>_arena.py`（または対応するビルダー）を実行して
docs/を再生成→標準検査）で展開し、`release` スキルで本番反映する。

## 詳細

ブランチ: `task/issue-tabs-ui`（worktree: `isa-wt-issue-tabs`、
`/Volumes/M2-WorkSpace/Projects/副業/isa-wt-issue-tabs`）
