# 課題72 詳細ログ: 升目カードと山なみ背景チャートの重なり解消（v9、2026-09-19）

[tasks/task-72.md](../../tasks/task-72.md) から400行上限のため切り出し。

## オーナー報告

消費税減税ページのスクリーンショット（手書き注釈付き）。論点を選んだ後に升目
（マトリックス）カードの背後へ薄く重ねて表示する山なみ（v4〜v5、`chart-box.as-backdrop`）
が、常に左寄せで描かれるため、順位1位の山（一番大きい）が固定230px幅の升目カード
（`#waffle`）とほぼ完全に重なって隠れていた。一方、山なみの右側には常に約50px、
何も描かれていない余白があった。「ずらして隙間を使えないか」という依頼。

## 調査（javascript_toolで実測）

- `#dot-slot`・`#dotbox`・`.chart-box.as-backdrop`は全て同一の矩形（`inset:0`で
  完全一致）。`#waffle`はその中で常に左端固定・230×230px
- 山なみSVG（viewBox「0 0 900 500」）の7論点の山は、SVG内の左余白64unit・右余白28unit
  で描かれており、レンダリング後は升目カードの右端（ローカルx=335px相当）に対し
  1位の山が173〜387pxとほぼ完全に重なる一方、右側は883〜934pxの51pxが空白だった

## 修正

`.chart-box.as-backdrop svg`に`transform-origin:right center;transform:scaleX(.78)`
を追加。右端を基準に78%へ縮めると、1位の山が升目カードの右側へ完全に外れ、右側の
空白も埋まる（実測: 1位の山が340px開始、升目カード右端335pxのすぐ右）。`#dot-slot`
の箱自体は変えないためレイアウトへの影響はない。スマホ幅（升目カード自体が
`#dot-slot`の大半を占める）では効果は小さいが、悪化はしない（実測・確認済み）。

9テーマ共通のテンプレート（`planet-prototype.template.html`・
`constitutional-planet.template.html`）を直し、`refresh_planet_section.py --topic
{theme} --for-docs`で対象9テーマ（ai-copyright・bike-blue-ticket・bukatsu-chiiki・
constitutional-amendment・consumption-tax-cut・elderly-license-revocation・
henoko-student-accident・koshitsu-tenpakai・school-nickname-ban）へ反映した。
fukushuto・takaichiは課題72の対象外（未展開）のため対象外。

## 再生成で見つけた既存の不具合2件（本番反映前にローカルで発見・修正済み）

1. **constitutional-amendmentの論点画像が消えた**: `refresh_planet_section.py`の
   `TOPIC_ENRICH`に未登録で、再生成のたびに黙って消えていた
   （[[reference_planet_regen_wipes_hand_edits]]と同型、9テーマ一括再生成で
   初めて発覚）。`_inject_constitutional_landing_images()`を新設し恒久的に解消
2. **論点IDに数字が入ると画像差し戻しが必ず失敗する**: 正規表現`[a-z-]+`が
   constitutional-amendmentの論点ID「article9」の数字を拾えず、期待件数チェック
   （landing-panelが7件必要）が常に1件少ないと誤検知していた。`[a-z0-9-]+`へ修正
3. **画像ファイル名の接頭辞が固定だった**: `_inject_landing_images()`は
   `images/topics/{topic}/{topic}-infographic-wide-{slug}.webp`という固定パターン
   だったが、constitutional-amendmentの画像ファイルだけ旧名「constitutional-」の
   ままだった（"constitutional-amendment-"ではない）。`filename_prefix`引数を
   新設（既定はtopicと同じ、既存2テーマは無変更）し個別指定できるようにした

## koshitsu-tenpakaiは今回フルの再生成を見送った

`refresh_planet_section.py --topic koshitsu-tenpakai --for-docs`を試したところ、
`TOPIC_ENRICH`未登録の独自の手当て（旧図解に「不正確です」注記を付けた画像4枚・
色の意味を説明する軸の注記文・「代表投稿10件の要旨を編集部が確認」という具体的な
review-note）が消えることが判明した。constitutional-amendmentと同型の問題だが、
除去された内容が多く、その場での正確な再現に自信が持てなかったため、フルの
再生成は行わず**`docs/`の該当CSS行だけを直接書き換えた**（データ側・他の手当ては
無傷）。TOPIC_ENRICHへの登録は別途フォローが必要（チップで提案予定）。

## 検証

標準検査4種・unittest 983件・`run_public_checks.py`いずれもNG0件。マージ・push・
CI（デプロイ・公開ファイルの検査）とも成功。9テーマ全てで本番反映を確認（curl）。
消費税減税・憲法改正論議でブラウザ実機確認（デスクトップ・モバイル、憲法改正論議
では論点画像「9条・自衛隊」の表示と画像URLの200 OKも確認）。作業ツリー
（`../isa-wt-ctc-chartshift`）は反映後に削除済み。
