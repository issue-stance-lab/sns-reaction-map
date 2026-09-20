# 課題76: 山なみ10テーマの構成監査 — 一次資料照合の消失・Xシェアボタン欠落など

**登録日**: 2026-09-20
**状態**: 未着手
**優先度**: 高（一次資料照合セクションの消失とconstitutional-amendmentのXシェアボタン欠落は
読者に実害があり、自動検査（verify_theme_page.py・verify_number_provenance.py・
再生成可能性検査）をすべてすり抜けている）
**関連**: 54（山なみ移行本体）/ 69（起承転結の再編、今回見つかった欠落の多くがこの過程で発生）/
73（死んだデータ）/ 74（AIっぽい言い回し）

## 何が起きたか

オーナー依頼「10テーマをチェックして、隅々まで見て違いがないか確認して」を受け、
「議論の山なみ」形式の10テーマ（takaichiを除く）の公開HTMLを横断監査した。
機械検査は全テーマ・全項目でNG0件だったが、目視の通読とgrepによる構造比較で、
検査が拾えない種類の欠落・数字の食い違いが複数見つかった。

**手法**: (1) 10テーマの`docs/*-reaction-map.html`を`grep`で見出し・後付けブロックの
マーカー（`<!-- XXXX_START -->`〜`<!-- XXXX_END -->`）を洗い出して構成マップ化・横比較、
(2) `git log -S`で各ブロックの内容がいつ変化したかを特定、(3) `ai-copyright`・
`elderly-license-revocation`・`school-nickname-ban`（起承転結の重複確認記録が無かった3テーマ）
は個別セッションで最初から最後まで通読、(4) 投票ボタン・文言統一・モバイルCSSは10テーマ横断で
機械チェック。

## 確認結果

### A. 高優先度 — 機能が消えている（読者に実害）

#### A-1. constitutional-amendment: 投票後の「Xでシェア」ボタンが存在しない

投票完了画面に、他9テーマ全部にある「Xでシェア」ボタンが無い。`share-x-btn.js`は
`<script>`で読み込まれているが、紐づく先の`id="share-x"`要素がページに1つも無い。

確認コマンド: `grep -c 'id="share-x"' docs/constitutional-amendment-reaction-map.html` → `0`
（他テーマは全て1以上）

#### A-2. 「一次資料照合」セクションが3テーマで中身ごと空

投稿の主張を条文・公的資料と照合する、このサイトの中核機能の一つが、3テーマで
**HTMLコメントのマーカーとCSSの飾りだけ残して本文（`<section>`・`<article>`要素）が消えている**。

| テーマ | マーカー名 | 消えたコミット | 内容 |
|---|---|---|---|
| constitutional-amendment | `CLAIM_AUDIT` | `67e586a`（2026-09-12、「憲法改正の山なみページ候補と原典照合を作成」） | 「原典にある数字・原典にない数字」8件のカードがこのコミットの差分で削除された（`git show 67e586a`で`-`行として確認済み） |
| bike-blue-ticket | `PROCESS_SECTIONS` | `00b693e`（2026-09-12、「自転車の青切符を『議論の山なみ』形式へ本番差し替え」） | 同型。`#process-collect`等4つのidを対象にしたCSSだけが残り、対応する要素はページ内のどこにも無い |
| elderly-license-revocation | `VERIFY_SECTION` | `6813bf1`（2026-09-11、「高齢者テーマを山なみ形式へ実際に差し替える」） | 同型。加えて他8/9テーマにある`ck-title`（「○○を分けて確かめる」という制度確認セクション）自体もこのテーマだけ丸ごと存在しない |

いずれも`verify_theme_page.py`等の機械検査はマーカーの存在有無しか見ないため、
1週間以上気づかれずに素通りしていた。

確認方法: 各テーマの`_START`〜`_END`間を抜き出し、`<style>`タグを除いた本体に
`<section>`・`<article>`・`<h2>`等の実要素があるか確認する。

#### A-3. 「議論の中心」（ヒーロー直下の最大論点要約）が3テーマに無い

`bike-blue-ticket`・`henoko-student-accident`・`school-nickname-ban`の3テーマだけ、
`class="thirty-summary"`（他7テーマにある要約カード）が無い。
（皇室典範で2026-09-18に一度見つかった同種の抜けが、実は他に3件潜んでいた）

確認コマンド: `grep -c "議論の中心" docs/{theme}-reaction-map.html` → 3テーマとも`0`

### B. 中優先度 — 数字・文言の食い違い

- **ai-copyright**: `meta description`・`og:description`・`twitter:description`・
  JSON-LDの`description`（4箇所）とヒーロー直下のリード文が「6つの論点」と書いているが、
  実データ・論点タブ・投票UIは全て7論点（学習データ・無断利用／利用者モラル・倫理／
  法制度・規制整備／クリエイター保護・権利／その他／AI生成物の権利・創作性／技術競争・推進）
- **elderly-license-revocation**: `article-trust`内「収集・分類で分かったこと」の数字
  （義務化賛成72.5%・地方の足18件・義務化そのものへの賛否126件）が、現行データ
  （収集506件・意見354件、`snapshot_id=elderly-license-revocation-20260904`）の
  どの集計とも一致しない。過去の収集回（2026年7月12日・26日比較）の観察文が
  更新されず取り残されている
- **school-nickname-ban**: `article-trust`内の分母が「420件を読み…87件」なのに、
  ヒーロー直下の注記(`id="caution"`)と詳細データ末尾(`id="detail-data"`)は
  「収集462件・意見87件」。462と420の差42件の説明がどこにも無い

### C. 低優先度 — 清掃対象（実害は小さい）

- **ai-copyright固有の死んだUI残骸**: 旧「問いの背骨」ウィジェットの跡が複数残る。
  `document.getElementById('strongest-arguments')`等、存在しない3要素を探す末尾スクリプト
  （空振りするだけで実害は軽微）、対応先の無いCSS約50行（`#arena-question-spine-pilot`・
  `#theme-atlas-pilot`）。課題73で扱う411KBの外部JS（`ai-copyright-arena-data.js`）も
  同じ旧UIの残骸で、まとめて整理できる
- **`ARGUMENTS_START`〜`END`が4テーマで空**: `ai-copyright`・`bike-blue-ticket`・
  `bukatsu-chiiki`・`elderly-license-revocation`に、内容が一字一句同じ「中身の無い
  飾りCSSブロック」（`.arguments-panel`等）が残存。対応するHTML要素はどのテーマにも無い
- **henoko-student-accident**: `INSIGHT_STATS_START`〜`END`が完全に空（CSSすら無い）
- **fukushuto・henoko-student-accident・koshitsu-tenpakai**: 「調査条件」の独立した
  説明ボックス（`<aside class="research-conditions">`）が無い。データ出典・取得期間の
  情報自体は山なみ本体内の注記（`.caution`）にあるため実害は小さいが、他7テーマより
  目立たない位置になっている
- **課題74の記録訂正**: `tasks/task-74.md`は「資料にしかない話を見る」ボックスの
  説明文について「henoko-student-accidentのみ個別対応済み、残り8テーマ未対応」と
  記録しているが、実際に10テーマを確認したところ対象は「henoko以外の9テーマ」
  （`consumption-tax-cut`が記録から漏れていた）。実害は無い（読みにくいだけ）ので
  優先度はそのままでよいが、`task-74.md`の対象テーマ数は訂正が必要

### D. 確認して問題が無かった項目（安心材料）

- 共通コードのCSSバグ2件（[[reference_planetpage_rollout]]記載の山の縁取り色
  `#0F1A3D`→`#2b3440`、`svg rect:first-of-type`のセレクタ修正）: 全10テーマで
  修正版を確認
- 投票欄の重複免責文言（課題74で3テーマ修正済みのもの）: 全10テーマで0件、再発なし
- モバイル用CSS（`@media(max-width:720px)`）・投票完了後ボタンの存在: 全テーマにあり
  （constitutional-amendmentのシェアボタンを除く。A-1参照）
- `verify_number_provenance.py`・`verify_theme_page.py`・再生成可能性検査:
  11テーマ全てNG0件（2026-09-20時点で実行して確認）
- モーダルのイベント委譲パターン（`closest('.explainer-card[data-img]')`）:
  henoko-student-accidentを除く9テーマで統一（henokoはこの機能自体が無いため対象外、実害なし）
- 皇室典範の論点画像の位置問題（旧メモ記録）: 既に解消済みと確認
  （`82b09dd`「論点図解5枚を差し替える」等で対応済み、メモリ更新済み）
- 「ではなく」「とどまる」の多用チェック: 誤検知。すべて正当な分析文（数値・制度の説明）で、
  課題74が問題視したのは別の特定フレーズ（「資料にしかない話」の説明文）だった

## 対応方針の案（次に着手するセッションへ）

優先度順に、専用の作業ツリーで1件（またはテーマ1つ）ずつ対応する。
すべて標準検査4種・実機確認・本番反映まで行うこと。

1. **A-1 constitutional-amendmentのXシェアボタン**: 他テーマ（例: fukushutoの
   投票結果HTML生成箇所）を手本に、投票完了時の`innerHTML`へ`id="share-x"`の
   リンクを追加する。このテーマは専用テンプレート（`constitutional-planet.template.html`）を
   使うため、共有雛形の一括修正では直らない点に注意
   （[[reference_shared_template_default_breaks_other_themes]]と同じ考え方で、
   theme_id分岐が必要になる可能性がある）
2. **A-2 一次資料照合の復元**: 3テーマとも「山なみ変換前のコミット」
   （`constitutional-amendment`は`67e586a`の親、`bike-blue-ticket`は`00b693e`の親、
   `elderly-license-revocation`は`6813bf1`の親）に元のカード本文が残っているため、
   そこから内容を救出し、現行データ・一次資料で内容を検証し直したうえで
   [[reference_planet_regen_wipes_hand_edits]]と同じ「後付けの補完処理」方式で
   再設置する。分量が大きいので3テーマ×1セッションを目安に分割するのが安全
3. **A-3 「議論の中心」の追加**: koshitsu-tenpakaiで確立済みの追加手順
   （`apply_koshitsu_conclusion()`相当）を3テーマに展開する
4. **B系（数字の食い違い）**: 該当箇所の文章をオーナー確認のうえ現行データに
   合わせて書き直す。[[feedback_verify_against_precedent]]のとおり、書き直す前に
   他テーマの「今の実物」の書き方を確認すること
5. **C系（清掃）**: 課題73の残タスクと合流できるものはまとめて対応する

## 判断待ち

なし（すべて技術的な復元・追加作業）。A-2の3テーマを1セッションでまとめて見るか
分けるかは着手時に判断してよい。
