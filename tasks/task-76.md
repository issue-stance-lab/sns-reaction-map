# 課題76: 山なみ10テーマの構成監査 — 残るはC-5のみ（意図的に未着手）

**登録日**: 2026-09-20
**状態**: 進行中。A-1・A-2・B系のai-copyrightは実機検証で「対応不要」と判明、
A-3（3テーマ）・B系のelderly-license-revocation・school-nickname-ban・
C系（清掃、7テーマ分）はすべて対応・本番反映済み（2026-09-20）。
C-5（調査条件ボックスの新設、3テーマ）だけは「清掃」ではなく新規実装のため対象外とし、
未着手のまま残した
**優先度**: 低（新たな対応の予定なし。C-5は課題73または将来のUI改善と合流する形での
着手を推奨。詳細はC-5参照）
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

#### A-3. 【2026-09-20 対応済み】「議論の中心」（ヒーロー直下の最大論点要約）が3テーマに無かった

`bike-blue-ticket`・`henoko-student-accident`・`school-nickname-ban`の3テーマだけ、
`class="thirty-summary"`（他7テーマにある要約カード）が無かった。
（皇室典範で2026-09-18に一度見つかった同種の抜けが、実は他に3件潜んでいた）

A-1・A-2と違い、この3テーマは`build_planet_page_preview.py`の`build_generic()`が
山なみ変換時に旧「固定件数の要約」を意図的に`cut_block()`で除去しており
（コメント「旧固定件数の要約」）、henoko・school-nickname-banの`ARTICLE_TRUST`等
どこにも代替が無いことを確認したうえで実装した（bike-blue-ticketは`build_bike_process_sections.py`に
`#reread-basis`スコープの未使用の試作コードがあったが、置き場所が他テーマと違い、
最大論点が固定（取締り強化賛成のみ）だったため使わず、新規実装した）。

**実装**: `scripts/refresh_planet_section.py`に共通ヘルパー`_top_issue()`
（「その他」を除く最大論点を選ぶ。koshitsu-tenpakaiの`configs/koshitsu-tenpakai-reaction-map.json`の
`arena.issue_blocks`が「その他」を含んでいないのと同じ考え方）・`_thirty_summary_html()`・
`_apply_thirty_summary()`を追加し、`TOPIC_METHOD_TEXT`経由でテーマごとに呼ぶ形にした
（`_sync_bike_method_text`・`_sync_henoko_method_text`を拡張、`_sync_nickname_method_text`を新設）。
最大論点が入れ替わっても書き直しが要らないよう、「その他」を除く全論点ぶんの見出し・説明文
（`BIKE_CONCLUSION_BY_ISSUE_ID`・`HENOKO_CONCLUSION_BY_ISSUE_ID`・`NICKNAME_CONCLUSION_BY_ISSUE_ID`）を
用意した（bike 5件・henoko 6件・school-nickname-ban 6件）。文面は各論点パネルの内訳・一次資料照合
から作成し、他テーマの見出し文体（質問形式、例:「そもそも、憲法を変えるべきなのか」）に揃えた。

3テーマとも`refresh_planet_section.py --topic <テーマ> --for-docs`を2回実行し差分ゼロ（冪等性）を確認、
実機（ローカルサーバー）で表示を確認、標準検査4種＋`verify_page_originality.py`はNG0件。
`tests/test_bike_planet_refresh.py`の既存テストが「その他」しか論点を持たないダミーデータで
落ちたため、非その他の論点を1件加えて修正した。

確認コマンド: `grep -c "議論の中心" docs/{theme}-reaction-map.html` → 3テーマとも`0`

### B. 【2026-09-20 対応済み】数字・文言の食い違い

- **【訂正・対応不要】ai-copyright**: 当初「meta descriptionとヒーロー文が『6つの論点』と
  書いているが実データは7論点」と報告したが誤りだった。`consumption-tax-cut`・
  `fukushuto`・`constitutional-amendment`も同じく「その他」を除いた数（山なみ本体は
  その他を含め7パネルだが、meta description・ヒーロー文は「6つの論点」と書く）を
  採る多数派の慣習があり、ai-copyrightの「6つの論点」（学習データ・無断利用／
  利用者モラル・倫理／法制度・規制整備／クリエイター保護・権利／AI生成物の権利・創作性／
  技術競争・推進の6つ、その他を除く）はこの慣習と一致していた。`configs/theme-seo.json`を
  一度「7つの論点」に書き換えたが、この確認により元へ戻した。
  （`bukatsu-chiiki`だけ「その他」を含めた7で「7つの論点」と書いており、他テーマと
  慣習が逆だが、実害は無い表記ゆれなので今回は対応しない）
- **【対応済み】elderly-license-revocation**: `article-trust`内「収集・分類で分かったこと」の
  3つ目の箇条書きが「地方の足・移動権は18件、義務化そのものへの賛否は126件」としていたが、
  現行データでは29件・221件（義務化・事故防止）。`configs/theme-seo.json`の`observations`と
  `docs/`を実データに合わせて訂正した。1つ目の箇条書き（2026年7月12日・26日収集分の比較、
  義務化賛成72.5%）は実在する過去の収集回の記録（`social-samples/`に該当ファイルが実在）で、
  特定の過去2時点の比較として書かれているため対応不要と判断した
- **【対応済み】school-nickname-ban**: `article-trust`内の分母が「420件を読み…87件
  （約21%）…278件は無関係」だったが、`462件を読み…87件（約19%）…320件は無関係`が
  正しい内訳（320+55+87=462）。原因を特定: 2026年8月17日の追加収集（+46件・意見+24件、
  63件→87件）で意見の分子だけ更新され、分母（420件）と「無関係」の件数（278件）が
  古いまま取り残されていた（87÷420=21%という古い分母のままの計算値が、たまたま
  現在の表示と一致していたため気づかれにくかった）。`configs/theme-seo.json`の
  `observations`と`docs/`を訂正した

### C. 清掃対象（実害は小さい） — 2026-09-20 C-1〜C-4・課題74記録訂正 対応済み、C-5のみ未着手

作業ツリー`../isa-wt-task76-c-cleanup`（ブランチ`task/task76-c-cleanup`）で対応。
削除対象はいずれも「対応するHTML要素がどこにも無いCSS／常にnullを見て何もしない
スクリプト」であることを、削除前に生成元スクリプト（`build_reaction_map.py`・
`build_constitutional_process_sections.py`・`build_bike_process_sections.py`・
`build_elderly_process_sections.py`・`build_henoko_arena.py`）を読んで確認した。
いずれも山なみ形式（`PLANET_SECTION_START`あり）では早期returnしてこの区間へ
触れない設計だったため、マーカーごと削除しても次回の定例更新で復活しない
（[[reference_afterthought_block_ordering]]・[[reference_planet_regen_wipes_hand_edits]]の
逆パターン——後付け処理が「触らない」と確約している区間なので、まるごと削除してよい）。

- **【対応済み】C-1 ai-copyright固有の死んだUI残骸**: 旧「問いの背骨」ウィジェットの跡を全削除。
  `document.getElementById('strongest-arguments')`等、存在しない3要素を探すだけで
  何もしない末尾スクリプト、`#issue-arena-section`という実在しない祖先の子孫セレクタだけで
  構成されたCSS約50行（`#arena-question-spine-pilot`・`#theme-atlas-pilot`、`#sm-wrap`等
  2Dマップ本体のセレクタも含むが祖先ごと不在のため道連れで安全に削除できた）を削除した。
  課題73で扱う411KBの外部JS（`ai-copyright-arena-data.js`）自体は今回の対象外（別課題のまま）。
  **新たに気づいた点（今回は対応せず）**: 同ファイルの`showVote()`内に、投票後スクロール用の
  `document.getElementById('issue-arena-section')`参照が1箇所残っており、常にnullなので
  スクロールが黙って何もしない（実害はごく軽微）。生きている投票フローの内部なので、
  今回のC系（死骸削除）より慎重な確認が要ると判断し、あえて手を付けなかった
- **【対応済み】C-2 `ARGUMENTS_START`〜`END`が4テーマで空**: `ai-copyright`・`bike-blue-ticket`・
  `bukatsu-chiiki`・`elderly-license-revocation`の「中身の無い飾りCSSブロック」
  （`.arguments-panel`等）をマーカーごと削除した
- **【対応済み】C-3 `CLAIM_AUDIT`/`PROCESS_SECTIONS`/`VERIFY_SECTION`が3テーマで空**（A-2参照）:
  constitutional-amendment・bike-blue-ticket・elderly-license-revocationの
  トップレベル資料照合マーカー＋CSSをまるごと削除した（内容は山なみ本体の
  各論点パネルへ移設済みで実害は無かった）
- **【対応済み】C-4 henoko-student-accident**: 完全に空だった`INSIGHT_STATS_START`〜`END`を削除
- **【未着手・意図的に見送り】C-5 fukushuto・henoko-student-accident・koshitsu-tenpakai**:
  「調査条件」の独立した説明ボックス（`<aside class="research-conditions">`）が無い。
  データ出典・取得期間の情報自体は山なみ本体内の注記（`.caution`）にあるため実害は小さいが、
  他7テーマより目立たない位置になっている。**これは「死骸の削除」ではなく「無い要素の新規追加」
  であり、他のC系と性質が違う**（A-3の「議論の中心」追加に近い作業量）ため、今回のC系
  清掃パスには含めず、着手するなら別枠で判断してよい
- **【対応済み】課題74の記録訂正**: `tasks/task-74.md`は「資料にしかない話を見る」ボックスの
  説明文について「henoko-student-accidentのみ個別対応済み、残り8テーマ未対応」と
  記録していたが、実際に10テーマを確認したところ対象は「henoko以外の9テーマ」
  （`consumption-tax-cut`が記録から漏れていた）。この訂正はB系対応と同じセッションで
  2026-09-20に`task-74.md`・`TASK_BOARD.md`側へ反映済み（本ファイルの登録時点で対応済み）

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

## 対応方針の案（記録として残す。すべて対応済み）

優先度順に、専用の作業ツリーで1件（またはテーマ1つ）ずつ対応した。
すべて標準検査4種・実機確認・本番反映まで行った。

1. ~~A-1 constitutional-amendmentのXシェアボタン~~ 対応不要（2026-09-20、実機検証で
   誤報と判明。A-1参照）
2. ~~A-2 一次資料照合の復元~~ 対応不要（2026-09-20、山なみ本体へ移設済みと判明。A-2参照）
3. ~~A-3 「議論の中心」の追加~~ 対応済み（2026-09-20、3テーマとも実装・本番反映済み。A-3参照）
4. ~~B系（数字の食い違い）~~ ai-copright分は対応不要（誤報）、elderly-license-revocation・
   school-nickname-ban分は対応済み（2026-09-20、いずれも本番反映済み。B参照）
5. ~~C-1〜C-4（清掃）・課題74記録訂正~~ 対応済み（2026-09-20、7テーマ分のマーカー・CSS・
   スクリプトを削除し本番反映済み。C参照）
6. **C-5（調査条件ボックスの新設、3テーマ）**: 唯一の未着手項目。次に着手するとすれば、
   専用の作業ツリーで1テーマずつ、A-3と同じ手順（`refresh_planet_section.py`の
   `TOPIC_METHOD_TEXT`経由での挿入、標準検査4種、実機確認）で行う

## 判断待ち

なし。課題76はC-5以外すべて完了。C-5だけ「清掃」ではなく新規追加のため意図的に見送った
（優先度は低いまま。着手するかはオーナー判断）。
