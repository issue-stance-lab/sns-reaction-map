# 課題73: 旧アリーナ形式の死んだデータ（SM_RAW）を残り5テーマから削除する

**登録日**: 2026-09-20
**状態**: 未着手（consumption-tax-cutのみ対応済み、別コミットで完了）
**優先度**: 中（CIは落ちていない。ただしai-copyrightは読者が毎回402KBを無駄にダウンロードしており、
体感速度への実害がある）

## 何が起きたか

consumption-tax-cutの「見た目が重い」という指摘をきっかけに、ページのソースに
`SM_RAW`という名前の巨大なデータ（投稿1件＝1点、Xユーザー名・投稿ID・AI要約を持つ配列）が
埋め込まれたまま、それを描画する画面（散布図とツールチップ、通称「論点アリーナ」）が
どこにも存在しない状態になっているのを発見・削除した（842KB→225KB、73%減）。

「山なみ」形式（現行のメイン形式）へ移行する際、旧アリーナ形式の名残であるこのデータブロックの
削除だけが漏れていた。他のテーマにも同じ漏れがないか、全10テーマ（consumption-tax-cut以外）を
1つずつ確認した。

## 確認結果（全11テーマ）

| テーマ | 状態 | 形態 | サイズ |
|---|---|---|---|
| consumption-tax-cut | ✅ 対応済み | インライン埋め込み→削除済み | (617KB削除, 2026-09-20) |
| **ai-copyright** | 🔴 死んでいる | 外部JSファイル（`<script src>`で**毎回読み込まれる**） | **402KB** |
| **fukushuto** | 🔴 死んでいる | インライン埋め込み | 213KB（ページの54.9%） |
| **bukatsu-chiiki** | 🔴 死んでいる | インライン埋め込み | 174KB（ページの40.0%） |
| **bike-blue-ticket** | 🔴 死んでいる | インライン埋め込み（別スキーマ・別生成スクリプト） | 73KB（ページの21.9%） |
| **elderly-license-revocation** | 🔴 死んでいる | インライン埋め込み | 63KB（ページの18.9%） |
| henoko-student-accident | 🟡 孤立ファイル | 外部JSだが、どのページからも読み込まれていない | 85KB（未使用のまま公開ディレクトリに存在） |
| school-nickname-ban | 🟡 孤立ファイル | 外部JSだが、どのページからも読み込まれていない | 18KB（同上） |
| takaichi | ✅ 問題なし | 外部JS・`<canvas id="takaichi-arena">`が実在し現役 | — （旧アリーナ形式のページ自体がまだ現役） |
| koshitsu-tenpakai | ✅ 問題なし | 該当データなし（既に整理済み） | — |
| constitutional-amendment | ✅ 問題なし | 該当データなし（既に整理済み） | — |

**判定方法**: (1) ページに`const SM_RAW = [...]`が有るか（インライン）、または`arena-data.js`を
`<script src>`で読み込んでいるか（外部）。(2) 有る場合、それを描画するはずの
`<canvas id="arenaMain">`等の要素が実際にHTML中に存在するか。存在しなければ、
描画コード側のガード（`if(!canvasMain||!canvasHeat)return;`）により何も表示されず、
データは完全に無駄になっている。

**🔴 死んでいる（5テーマ）** と **🟡 孤立ファイル（2テーマ）** の違い: 🔴はページ本体に
埋め込まれている（読者が必ずダウンロードする）か、`<script src>`で毎回読み込まれる。
🟡はファイル自体はdocs/配下（公開領域）に残っているが、どのページからもリンクされておらず、
普通に読者がページを見る分には一切ダウンロードされない（ただしURLを知っていれば誰でも見られる
状態ではある）。

## 対応方針の案（次のセッションへの申し送り）

consumption-tax-cutで確立した手順をそのまま横展開する。

1. HTMLから該当ブロック（またはscript読み込みタグ＋外部ファイル）を削除
2. 生成スクリプト側（`build_{テーマ}_arena.py`や`build_{テーマ}_page.py`等）の
   「SM_RAWを書き込む処理」を削除し、「SM_RAWが存在しないこと」を確認する検査に置き換える
   （再発防止。consumption-tax-cutでは`build_consumption_tax_page.py`の`verify()`で実施）
3. `DATA_SHEET.md`が該当テーマの件数を数えている場合は`scripts/build_data_sheet.py`で作り直す
4. 標準検査一式・実機でのページ確認・本番反映まで、consumption-tax-cutと同じ手順で行う

**テーマごとの留意点**:
- **ai-copyright**: 唯一、外部JSが`<script src>`で毎回読み込まれる形。生成元は
  `scripts/build_ai_copyright_arena.py`（`docs/ai-copyright-arena-data.js`へ書き出し）。
  読者への実害が最も大きいため、優先して着手する価値がある
- **bike-blue-ticket**: 生成元が他テーマと違うスクリプト（`build_bike_arena_points.py`）で、
  データのスキーマも異なる（`y`フィールドを持つ）。同じ手順が通用するか個別に確認が要る
- **henoko-student-accident / school-nickname-ban**: 読者への影響は無いため優先度は低いが、
  生成元（`build_henoko_arena.py`・`refresh_adapters/henoko.py`／`build_nickname_arena.py`・
  `refresh_adapters/nickname.py`）が今も定期収集のたびにこの孤立ファイルを書き直している。
  ファイル削除よりも、生成自体を止める方が本質的な対応になる

## 次にすること

優先度は中（CIは落ちていない）。着手するときは、読者への実害が最も大きい
**ai-copyright**から始めることを推奨する。1テーマ片付けるごとに標準検査・実機確認・
本番反映まで行い、次のテーマへ進む（consumption-tax-cutと同じ進め方）。

## 進捗

（未着手。2026-09-20に全11テーマの現状調査のみ完了）
