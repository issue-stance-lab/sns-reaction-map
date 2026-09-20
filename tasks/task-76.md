# 課題76: 山なみ10テーマの構成監査 — 「議論の中心」欠落など

**登録日**: 2026-09-20
**状態**: 未着手（A-1・A-2は2026-09-20の実機検証で「対応不要」と判明。実質的に残るのはA-3のみ）
**優先度**: 中（A-3「議論の中心」の欠落は3テーマに残るが、事実誤りや機能欠落ではなく
見た目の統一感の話。B系の数字の食い違いのほうが読者への実害としては先に直す価値がある）
**関連**: 54（山なみ移行本体）/ 69（起承転結の再編、今回見つかった差分の多くがこの過程で発生）/
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

**2026-09-20追記**: 下記A-1・A-2は、登録直後に着手した実機検証・原文比較で
いずれも「実害なし・対応不要」と判明した。2件とも当初の判定は静的HTMLの
grepだけに基づいており、実際の描画結果・移設先を確認していなかったのが原因。
経緯は各項目に残す（[[feedback_verify_against_precedent]]と同種の教訓が
同じ課題内で2回連続で起きた記録として、あえて削除せず残す）。

### A. 機能・見た目の差分

#### A-1. 【2026-09-20 訂正・実害なしと判明】constitutional-amendmentの「Xでシェア」ボタン欠落は誤報だった

**結論**: 静的HTMLのgrepだけで判定したのが誤りで、実際にブラウザで投票を完了させると
問題なく「Xでシェア」ボタンが表示される。修正は不要。

**当初の誤診断**: 投票完了画面に、他9テーマ全部にある「Xでシェア」ボタンが無いと報告した
（`grep -c 'id="share-x"' docs/constitutional-amendment-reaction-map.html` → `0`）。

**実機検証で判明したこと**: `docs/topic-modern.js`（全10テーマ共通で読み込まれる）に
`normalizeVoteResult()`という関数があり、`#vote-result`が投票完了で可視化されるのを
`MutationObserver`で監視し、その場で「Xでシェア」ボタンが無ければ自動生成し、
「投票をやり直す」ボタンの文言も統一している。constitutional-amendmentの投票結果コード
（`<strong>あなたの選択</strong><p>「○○」を重視し、総合的には「○○」</p>`という形式）は、
この`normalizeVoteResult()`が検出する定型パターンにちょうど一致するため、静的HTMLに
`id="share-x"`が無くても、投票した瞬間にJSが補って正しく動く。

ローカルの簡易HTTPサーバーで実際に投票を完了させ（Supabaseへの投票保存はCORSでブロックされる
環境だったため、投票結果表示だけを直接再現）、ブラウザのJS実行で
`document.getElementById('share-x')`が実在し、正しいX投稿リンク（UTM付き）と
「𝕏 でシェア」の表示文言を持つことを確認した。**静的HTMLのgrepだけで「ボタンが無い」と
判定したのが誤りだった**（[[feedback_verify_against_precedent]]・
[[reference_repro_match_reported_env]]と同種の教訓——「コードを読んだだけ」ではなく
実際に動かして確認する必要があった）。

**対応**: 一度コードを追加してみたが、`topic-modern.js`側が独自にhrefを組み立て直すため
二重管理になるだけで意味が無いと判明し、変更は入れずに元のコードへ戻した
（作業ツリー`../isa-wt-task76-share-x`のstashを破棄）。

#### A-2. 【2026-09-20 訂正・実害なしと判明】「一次資料照合」セクションの消失は誤報だった

**結論**: マーカー直下の本文は確かに空だが、同じ内容は山なみ本体の各論点パネル内
「資料との照合」（`class="claims"`）へ移設済みで、実際には全テーマで読める。修正は不要。

**当初の誤診断**: 投稿の主張を条文・公的資料と照合する機能が、3テーマで
「HTMLコメントのマーカーとCSSの飾りだけ残して本文が消えている」と報告した。

| テーマ | マーカー名 | 消えたコミット |
|---|---|---|
| constitutional-amendment | `CLAIM_AUDIT` | `67e586a`（2026-09-12、「憲法改正の山なみページ候補と原典照合を作成」） |
| bike-blue-ticket | `PROCESS_SECTIONS` | `00b693e`（2026-09-12、「自転車の青切符を『議論の山なみ』形式へ本番差し替え」） |
| elderly-license-revocation | `VERIFY_SECTION` | `6813bf1`（2026-09-11、「高齢者テーマを山なみ形式へ実際に差し替える」） |

**実機検証で判明したこと**: `scripts/build_constitutional_process_sections.py`を読むと、
`PLANET_SECTION_START`がページにある場合（＝山なみ形式）は
「山なみ内の資料照合を使用（旧セクションは再挿入しません）」として早期returnし、
`CLAIM_AUDIT_START/END`の中身をそもそも書き換えない設計になっていた。つまり
「消えた」のではなく「もう使っていない」仕様変更だった。

3テーマとも、削除コミットの**直前**（山なみ変換前）の主張文をgitから取り出し
（例: bike-blue-ticketは「LUUPは免許不要で野放しなのに、自転車だけ青切符だ」
「対象になる違反は113種類もある」等7件）、現在の公開ページを全文検索したところ、
**全件が山なみ本体の該当論点パネル内「資料との照合」に見つかった**
（constitutional-amendmentの6主張、bike-blue-ticketの7主張、
elderly-license-revocationの7主張、いずれも一字一句同じ文面・出典URLで確認）。
この「資料との照合」（`class="claims"`）は10テーマ全部の山なみ本体に標準搭載されている
共通機能（`class="claims"`の出現数はai-copyright 5・bukatsu-chiiki 5・fukushuto 3・
koshitsu-tenpakai 3・consumption-tax-cut 4・school-nickname-ban 5・henoko 4・
constitutional-amendment 4・bike-blue-ticket 4・elderly-license-revocation 5、
全テーマに存在）で、山なみ変換の際に「1箇所にまとめた一覧」から
「各論点パネルに紐づけて表示」という、[[feedback_narrative_coherence_preference]]の
方向性に沿った意図的な再配置だったとみられる。

**残る唯一の実害**: トップレベルの`CLAIM_AUDIT`/`PROCESS_SECTIONS`/`VERIFY_SECTION`という
空のマーカー＋CSS約20〜30行が、読まれない飾りとして残っているだけ（`ARGUMENTS_START`等と
同種の残骸）。下記C系の清掃項目へ格下げした。

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
- **`CLAIM_AUDIT`/`PROCESS_SECTIONS`/`VERIFY_SECTION`が3テーマで空**（A-2参照、
  2026-09-20にC系へ格下げ）: constitutional-amendment・bike-blue-ticket・
  elderly-license-revocationに、山なみ変換で使わなくなったトップレベルの
  資料照合マーカー＋CSSが残存。内容は山なみ本体の各論点パネルへ移設済みで実害は無いが、
  読まれないCSS・マーカーが残っている
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
- constitutional-amendmentの「Xでシェア」ボタン: 静的HTMLには無いが、`topic-modern.js`の
  自動補完で実際には正しく表示される（A-1参照、2026-09-20訂正）
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

1. ~~A-1 constitutional-amendmentのXシェアボタン~~ 対応不要（2026-09-20、実機検証で
   誤報と判明。A-1参照）
2. ~~A-2 一次資料照合の復元~~ 対応不要（2026-09-20、山なみ本体へ移設済みと判明。A-2参照）
3. **A-3 「議論の中心」の追加**: koshitsu-tenpakaiで確立済みの追加手順
   （`apply_koshitsu_conclusion()`相当）を3テーマに展開する
4. **B系（数字の食い違い）**: 該当箇所の文章をオーナー確認のうえ現行データに
   合わせて書き直す。[[feedback_verify_against_precedent]]のとおり、書き直す前に
   他テーマの「今の実物」の書き方を確認すること
5. **C系（清掃）**: 課題73の残タスクと合流できるものはまとめて対応する
   （A-2で格下げした3件の空マーカーもここに含める）

## 判断待ち

なし。次に着手するならA-3（「議論の中心」の追加、3テーマ）かB系（数字の食い違い、
3件）のどちらでもよい。B系のほうが読者に見えている数字そのものの誤りなので、
先に直す価値がある。
