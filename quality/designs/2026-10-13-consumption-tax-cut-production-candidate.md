# 消費税減税（consumption-tax-cut）新デザインの公開候補と検査（手順7）

2026-10-13。ブランチ `task/renew-consumption-tax-cut`。手順書23の「7. 更新と公開を検査する」。
辺野古の [2026-10-11-henoko-student-accident-production-candidate.md](2026-10-11-henoko-student-accident-production-candidate.md)
（対話式の山なみを元HTMLから写す＋部活動型の圧縮）を踏襲し、推移は生成AIと著作権と同じく収集を重ねた「意見の推移」（10回分）を写した。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/consumption-tax-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/consumption-tax-cut-release/consumption-tax-cut-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-11）
確認画面: `quality/prototypes/consumption-tax-cut-release/evidence/`（PC・375px の全体、山なみ、立場モード切替、レシートの切替、山を押して読書面へ、
読書面、理由を開いた画面、背景を開いた画面、推移を開いた画面、X遮断時、JSなし）

## 0. 手順7の前に直したこと（コミット a5e32a2f）

| 項目 | 処理 |
|---|---|
| 1. よみやすの残り13件 | 公開JSON由来の文を、数字・出典・判定を変えずに区切った。重なる心配 `vein-1`・`vein-2` の `diverging_reason`、資料にしかない話 `sc-1`〜`sc-4` の `sns_note`・`life_impact`（`data/verification/consumption-tax-cut-{veins,sunk-continents}.json`）。`build_public_registry.py --topic consumption-tax-cut` で公開JSON・catalog を、`build_adoption_registry.py` で採用台帳の指紋を作り直した。現行ページ（当時の docs）の連動表示の同じ文も `build_consumption_tax_page.py --public-counts-only` で差し替えた（文の差し替えだけ）。`verify_number_provenance.py consumption-tax-cut` NG 0、`verify_ocean_layer.py` は直す前と出力が完全に同じ（他テーマの既存の指摘で終了1）。読書面の試作のよみやす `--strict` は完成を止める指摘 13件→0件。`veins.json` の `sample_total_opinions`（3,890）は作った時点の母数の記録で、公開JSONに出ないので変えていない |
| 2. 授業向けの設定 | `configs/classroom/consumption-tax-cut.json` の資料1を、大綱（sankou4、「法律はまだ成立していない」）から法律案の概要（sankou15）に差し替えた。説明は「2026年10月9日に閣議決定し、国会へ提出された法律案の概要。…成立したかどうかは、衆議院の議案の審議経過で確かめる。」で、段階が進んでも古くならない（一次資料メモ 資料W の範囲）。背景の「授業」の注記と「まだ確かめていないこと」の授業の行も直した。設定は旧ページと共有なので、現行ページの授業節も `apply_classroom_section` の関数で作り直した |
| 3. 再読データの立場のずれ102件 | 共有の再読データは変えず、更新経路（`refresh_adapters/consumption_tax.py` の `build_reread_stances`）で累積候補から立場の対応表を毎回作り直し、2回一致を確かめて公開対象に含める（自転車・辺野古の型）。現在の正典を累積候補とみなして作った表は、立場がいまの対応表と全件一致した |
| 4. 分類AIの切替 | `model_breaks` は `inject_tide_widget.py` ではなく `scripts/build_trend_section.py` の `TREND_THEMES` にある。消費税減税に `{"stance": ["2026-10-03"], "issue": ["2026-10-03"]}` を登録した（`social-samples/updates/consumption-tax-cut/*/report.json` で 9/24 まで kimi-k2.6、10/3 から kimi-k2.7-code。判定し直していないので両方の軸）。現行ページの推移の注意書きに「2026年10月3日の回から、分類に使うAIを切り替えました…」が出る。adapter に分類AIの変化の検査（`check_model_break`）を足した。推移の「ひと目」の注記にも出る（2節） |
| 5. 手入力の日付 | `build_consumption_tax_page.py` の `MODIFIED_AT="2026-09-27"` を外し、`configs/theme-seo.json` の `dateModified`（更新経路の `update_seo_date` が書く）を読む関数にした。照合日の `CHECKED_ON` は公開JSON `claim_verification.checked_on` の元（`public_registry_common.py` がこの定数を読む）で、すでに1か所なので残した |

### 申し送り（読書面の設計記録10節）の処理

| 申し送り | 処理 |
|---|---|
| 1. 山なみ | 元HTMLの `#planet-block` を写して論点タブの上に置いた（2節・3節）。入口 `window.ConsumptionTaxReading.select` |
| 2. 推移 | 10回分の推移のカード（TREND_CARD）を折りたたみ（「10回分の折れ線と表を開く」）に1文字も変えずに入れ、外部の埋め込みが指す `#consumption-tax-cut-trend-panel-stance`・`-issue` を残した。上に立場4本の小さな折れ線・前回から今回への1行・注記1行（小標本・古い投稿の混入・分類AIの切替）。各論点の「回ごとの動き」に小さな折れ線と最初・最新の回の割合2つ（「その他」は推移に無いので注記だけ）。潮目のカード（`consumption-tax-cut-tide-widget`）は 2026-10-05 にページから外れていたので、飛び先を推移の論点タブに変えた（設定 `trend.widget_id`） |
| 3. 手入力の日付 | 0節の5。新ページの更新日は Article JSON-LD（theme-seo の `dateModified`）・作り方（THEMES.yaml）・公開JSON から出る。制度の確認日は冒頭の設定 `checked_on`、照合日は公開JSON |
| 4. display_headline・FAQ | `configs/theme-seo.json` に `display_headline`（新しい H1）を足した（9節）。title・description は変えていない。FAQPage の構造化データを画面の6問（冒頭の短答3問＋背景の「よくある質問」3問）から作った（現行ページには無かった）。画面と構造化データの一致はテストで確認 |
| 5. 計算部品の二重管理 | 新デザインは冒頭の設定 `rates`・`calc` から作るレシートだけを使い、`docs/consumption-tax-search-entry.js/css`・連動表示（`consumption-tax-connected*`）・代表投稿の旧設定は読み込まない（テストで確認）。旧部品は元HTMLが読むので docs/ と元HTMLに残す。`build_consumption_tax_page.py` の直書きの初期値も元HTML側だけに残る |
| 6. よみやす13件 | 0節の1 |
| 7. 10/20 の定期更新 | DATA_REFRESH.md に書いた（9節）。立場の対応表は adapter が作り直す。新規0件相当の 10/20 を隔離コピーで模擬し、通ることを確かめた（9-4） |
| 8. 成立したら | 冒頭の設定 `law.enacted_on`・`promulgated_on`・`checked_on` と、一次資料メモの節・`memo_section` を直せば、冒頭・読書面・背景・制度の確認の文が切り替わる。仮の成立日と仮の節で、`--as-of` を成立後・引下げ中・終了にして生成が止まらず文が切り替わること、成立未確認のまま引下げ開始日を過ぎた基準日でも止まらないことをテストで確かめた（`test_phase_switch_after_enactment`。docs には入れていない） |
| 9. 授業向けの設定 | 0節の2 |
| 10. 既定で開く論点 | 件数1位の「選挙の約束は守られたのか」（理由は未公開）のまま。山なみの選択パネルも読み込み時に同じ論点を選ぶ（7節の判断待ち） |
| 11. 代表投稿の生存 | 2026-10-13 に cdn.syndication.twimg.com で14件とも `__typename: Tweet` |
| 12. 編集部の横断整理 | 新デザインには載せない（辺野古・高齢者・あだ名と同じ。日付が 2026-09-14 のままで、件数は差し込みでも本文の見立てが古い）。元HTMLの中では引き続き更新される |

## 1. 仕組み（辺野古と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_consumption_tax_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`consumption_tax_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview\|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/consumption_tax_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/consumption-tax-cut.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_consumption_tax_page.py` を引数なしで動かしたとき。元HTMLにページ生成・意見の推移・調査条件・公開JSONの集計と山なみ・テーマ共通の見た目を掛けてから新デザインを組む） |
| `configs/consumption-tax-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/consumption_tax_redesign/planet.js`（新規） | 山なみの橋渡し。山を押すと `ConsumptionTaxMap.selectIssue(id, {history:'none'})` で山なみ側を合わせ、読書面を選んで移る（URL は replaceState） |
| `scripts/consumption_tax_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（夜の藍・紙・橙）に合わせる |
| `scripts/consumption_tax_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細（入れ子・除いた明細つき）・立場の対応表・設定から数え直して照合（`consumption_tax_count_provenance.py` が新デザインのときだけ呼ぶ）。冒頭の件数欄、7論点の欄、推移の要約の注記 |

ページの並び：共通ヘッダー → 冒頭（パンくず・題名・段階の一言・レシート・短答3問・段階図・SNSの意見の件数・確かめた一次資料）→
論点ごとに読む（見出し → **対話式の山なみ**（調査条件・立場モード・山・論点ボタン・選択パネルと100マス・見かた）→ 論点タブ → 選んだ論点の欄）→
推移の要約（折りたたみに10回分のカード）→ 投票 → 背景の開閉行8行 → 集め方と分類、全部の集計表（折りたたみ1つ）→ 次に読むテーマ → フッター。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「消費税減税はいつから？食料品1％と給付・財源の現在地｜SNS反応まっぷ」 | 同じ | 継承（課題96の 10/27 判定のため文字どおり。テストで固定） |
| meta description・SEO_META（canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承。**description は「政府大綱が閣議決定済み」「法律成立前」のまま**（7節） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承（dateModified は theme-seo の値） |
| FAQ JSON-LD | 無し | 冒頭の短答3問＋背景「よくある質問」3問＝6問から作る | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間と `google-adsense-account` meta | 区間は release だけ、meta は両方 | 継承 |
| 共通CSS/JS | site-tokens（v=3）・topic-modern（css v=32・js v=14）・consumption-tax-connected（css/js/page.js）・consumption-tax-search-entry（css/js）・theme-design | site-tokens・topic-modern だけ（版は元HTMLから読む） | 検索入口・連動表示・テーマ共通の見た目は意図的に外した |
| 投票（Supabase） | topic `consumption-tax-cut-issue-stance-v1`、論点7×立場4＝28、`choiceIdx:CHOICES[issue.id][stance.id]`、保存キー `sns_vote_consumption-tax-cut-issue-stance-v1_my` | 投票節とスクリプトを複写。VOTE_ISSUES・STANCES・CHOICES は元と完全一致（並べ替えなし）。保存キーは本番ホストだけ既存キー、他は `…_my_preview`。前置きの文も元のまま | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（28通り）。**V2I という定義は現行ページに無い**（番号は CHOICES が持つ）。前置きの文は「2026年7月、…大詰めを迎えました」のまま（7節） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承 |
| 共通ヘッダー・パンくず | 静的ヘッダー無し（topic-modern.js が差し込む） | 辺野古と同じ静的な共通ヘッダー、冒頭のパンくず | JSなしでもトップへ戻れる |
| 意見の推移（TREND_CARD） | 10回分、立場・論点・反対慎重の理由の3タブ、画像4枚、埋め込みコード | 枠と CSS 区間を文字どおり複写し、要約の下の折りたたみ `#cap-trend-more` へ | 継承。外部の埋め込みが指す2つの id はそのまま（読み込み時に折りたたみを開いてそのタブへ） |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、詳細データと一緒に折りたたみ `#cap-method` へ | 継承 |
| 詳細データ（#detail-data） | 折りたたみ6つ（論点別・立場別・感情の強さ・投票の選択・収集クエリ・注意） | 文字どおり複写（論点別・立場別の件数は公開JSONと照合して違えば止まる）。折りたたみは最初どれも閉じる | 継承。中の「Hermes（kimi-k2.6）が…判定」は元HTMLの文のまま（7節） |
| 次に読むテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking` | 両方文字どおり複写 | 継承 |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間（元HTML） | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| 進み具合の帯「読んだところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先だけ隠して置く） | 内容対応表2 |
| 検索入口・立場の帯・背景パネル・確認項目・論点カード・主張の照合の一覧・編集部の整理・クイズ・予想・図解画像 | TAX_SEARCH_ENTRY・STANCE_GLANCE・`#bukatsu-background`・`#bukatsu-check`・ISSUE_CARDS・CLAIM_AUDIT・`#editorial`・`#quiz`・`#guesses` | 載せない（クイズと予想は受け皿だけ隠して残す） | 冒頭・読書面・背景に置き換え（旧アンカーは読み替え） |

政党名：読書面の文（論点タブから下）に政党名が無いことをテストで確かめた（0%案と各党の案は背景の行だけ）。

### 旧アンカーの到達確認

`grep -rn "consumption-tax-cut-reaction-map.html#" docs/ scripts/ configs/ company/` の結果は、作業文書 `configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md` の
`#modes`（新ページでも写した山なみの中にある）と、推移のカードの中の埋め込みコード（`#consumption-tax-cut-trend-panel-stance`・`-issue`。新ページにそのまま残る）だけ。
外から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開き、推移のタブならそのタブに切り替える）。

| 旧ID | 読み替え先 |
|---|---|
| `#progress`・`#tax-brief`・`#tax-brief-title` | 冒頭 `#tax-open` |
| `#tax-brief-stage` | 段階図 `#cto-steps` |
| `#tax-case-tabs`・`#tax-case-panel`・`#tax-tab-{food,takeout,eatin,alcohol}`・`#tax-before-*`・`#tax-after-*`・`#tax-price-delta`・`#tax-case-note` | レシート `#cto-calc` |
| `#tax-faq-title` | 背景「よくある質問」`#tax-faq`（旧FAQと同じid。開く） |
| `#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`）・立場の帯の `#consumption-tax-cut-{support,conditional,cautious,neutral}` | 冒頭の件数欄 `#cto-count` |
| `#bukatsu-background`・`#bg-title`・`#timeline-2026-07-30`・`-08-05`・`-09-15` | 背景「決まるまでの年表」`#bg-timeline`（開く） |
| `#bukatsu-check`・`#ck-title`・`#policy-finance` | 背景「『決まったこと』と『まだのこと』」`#bg-status`（開く） |
| `#policy-scope`・`#policy-rate-period` | 背景「1%の仕組みと、対象になる品目」`#bg-rate` |
| `#policy-benefit` | 背景「給付付き税額控除と、就業者負担軽減支援金」`#bg-benefit` |
| `#claim-audit`・`#fallback`・`#fallback-nav`・`#quiz`・`#ocean`・`#editorial`・`#issue-cards`・`#tax-connected-data` | 読書面 `#consumption-tax-cut-reading` |
| 主張の照合 `#rate10` | 「食料品だけか、全品目か」の欄 |
| `#register` | 「店や会社の手間と負担」の欄 |
| `#cost5cho`・`#welfare`・`#refund` | 「財源と社会保障はどうなる」の欄 |
| `#firstcut` | 「選挙の約束は守られたのか」の欄 |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#tax-reading-{論点ID}` | その論点の欄（選んだ状態になる） |
| 論点の素のID（旧ページの山なみの着地が URL に書いていた） | 読み込み時だけ、その論点の欄 |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |

そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`planet-block`・`modes`・`planet-data`・`consumption-tax-cut-trend`・
`consumption-tax-cut-trend-panel-stance`・`-issue`・`-reason`・`article-trust-title`・`tax-faq`・`issue-{論点ID}`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS・CSS の内部用ID（`tax-reason-count-…`・`tax-concern-count-…`・`tax-source-note-…`・
`explainer-modal…`・`pbar`・`vote-…` など）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_consumption_tax_redesign.py --mode release --output-dir quality/prototypes/consumption-tax-cut-release
```
成功すると `Built 1 file (release, as_of 2026-10-11); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文（`section.landing-panel`）・論点の目印（`span.issue-anchor`）・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。
  消費税の山なみには読み込み時の自動着地が無い（URL が素の論点IDのときだけ着地する）ので、その直後に「それ以外は URL の論点（`#issue-…`）か読書面の既定の論点を、
  ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」処理を足す（`AUTO_LAND_OFF`）。連動表示の本体を読み込まないので、橋渡し（TAX_CONNECTED_BRIDGE）は旧来の動き
- **山を押したとき**：なめらかなスクロールが山なみの描き直しと重なって途中で止まることが Chromium であったので、止まった位置で欄が画面の上の方に無ければ一度だけ寄せ直す（`planet.js`）
- **推移の要約**：推移のカードのスクリプトの `const panels` だけを読み、立場4本の10点の折れ線と、各論点の10点の折れ線・最初と最新の割合を描く。注記の数字（1回あたり450〜612件、±4ポイント、古い投稿は最大16%）と切替日は推移の注意書きから写す（手で書かない。カードの件数の幅が回ごとの件数と違えば止まる）
- **見出しの書き分け**：使い回し検査で、読書面の見出し（高齢者と0.72）・前置き（あだ名と0.74）・推移の要約の1文（部活動と0.70）が似ていたので書き直した（要約の1文はカードの最初の説明文ではなく「前回から今回にかけて」の1行にした）

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理 → 最後に `consumption_tax_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/consumption_tax.py` は `source_for_refresh` を入力にする。ページ生成器（山なみの件数・論点カード・主張の照合・検索入口・計算部品・連動表示）・意見の推移（`_apply_trend`）・推移の画像は元HTMLから作った候補に掛かる。
  **立場の対応表（`data/consumption-tax-cut_reread-stances.json`）は累積候補と再読データから作り直して公開対象に含める**（2回作って一致を確かめる）。新しい意見が再読データの明細に無いと「追い読みが要ります」で止まる（テストで確認）。分類AIが前回から変わった回は `model_breaks` の記録が無いと止まる。
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。
- `build_consumption_tax_page.py` は、公開後に引数なしで動かすと `rebuild`（`--check` で差分の有無だけ）。部分更新（`--conditions-only` など）や `--output-html` なしの全生成を新デザインのページに向けると止まる。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの件数・除いた明細 | `data/consumption-tax-cut_4issues-reread.json`（論点ごとの `buckets`・`items`・`excluded_items`） | **新しい意見の追い読み（人が読む）**。明細が正典の意見と合わないと生成が止まる |
| 区分ごとの立場・投稿の立場 | `data/consumption-tax-cut_reread-stances.json` | 更新経路では adapter が作り直す。経路の外では `consumption_tax_reread_stances.py --made-on` |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前 | `configs/consumption-tax-cut-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`（元は `build_consumption_tax_page.py` の CLAIM_AUDIT・`CHECKED_ON`）・`data/consumption-tax-cut_claim_posts.json` | 主張を足すとき |
| 資料にしかない話・重なる心配 | `data/verification/consumption-tax-cut-{sunk-continents,veins}.json` → 公開JSON `ocean_layer` | 文を直すときは1文80字以内・読点3つまで・同じ文末3連続なし |
| 冒頭（短答・レシート・段階図・件数欄）・確認日・法律の段階 | `configs/consumption-tax-cut-opening.json`（`checked_on`・`law`・`rates`・`calc`・`steps`） | 確かめ直したら `checked_on`。成立したら `law` と一次資料メモ |
| 背景（仕組み・支援金・決まったこと・年表・各党の案・FAQ・授業・未確認） | `configs/consumption-tax-cut-background.json`・`configs/classroom/consumption-tax-cut.json`・一次資料メモ | 一次資料の再確認時 |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION | 自動 |
| 意見の推移・論点ごとの「回ごとの動き」・要約の注記 | 元HTMLの TREND_CARD（adapter の `_apply_trend`、`build_trend_section.py`） | 自動。分類AIが変わったら `model_breaks` |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データ・次に読むテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成で辺野古の後に `finish` | 辺野古の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/consumption_tax.py` | 入力を `source_for_refresh(root)` に／`build_reread_stances`／`check_model_break` | 公開後も元HTMLから生成するため／追い読みの後の対応表の作り直し忘れ・分類AIの切替の記録漏れで止めるため |
| `scripts/build_consumption_tax_page.py` | 公開後の引数なしの実行で `rebuild`（`--check`）。新デザインのページを土台・書き出し先・部分更新の対象にしたら止める。`MODIFIED_AT` を theme-seo から読む | 単独実行で新ページを旧形式で上書きしないため／手入力の日付の一元化 |
| `scripts/build_consumption_tax_arena.py` | 変更なし | ページを書かない（アリーナの集計JSONだけ）。`--check` は既存の理由で NG（6節） |
| `scripts/consumption_tax_count_provenance.py` | 新デザインのページなら `consumption_tax_redesign_provenance` に渡す | 新デザインの件数を照合するため（旧ページの照合はそのまま） |
| `scripts/build_trend_section.py` | 消費税減税の `model_breaks`／`--apply` を新デザインのページ（`*-layout` の目印）に向けたら止める | 0節の4／新ページへ直接貼らないため（全テーマに効く守り） |
| `scripts/inject_tide_widget.py` | コメントのみ（消費税減税は adapter 側で生成、新デザインのページは既に SKIP） | — |
| `scripts/refresh_planet_section.py` | 消費税減税の新デザインも停止 | 他の新デザインと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 消費税減税の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐に消費税減税を追加。「どの区分にも当てはまらなかった」明細（`__excluded__`）は理由の一覧ではなく数え方の注記の件数（`data-excluded`）と照合 | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `configs/consumption-tax-cut-reading.json` | `trend.widget_id` を推移の論点タブへ、`compact` に手順7の見出しと文、読書面の見出しと前置きを書き直し | 2節・3節 |
| `configs/consumption-tax-cut-opening.json` | 件数欄の「理由は未公開」の注記から「3論点」を外した | ページの検査（論点数は1ページに1通り）が「3論点」と「6論点」を食い違いとして止めた |
| `configs/consumption-tax-cut-background.json` | 背景の前置きの文末、授業の注記、未確認事項から授業の行を外した | よみやす（同じ文末3連続）・0節の2 |
| 切替時の共有テスト | 9-3 | — |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に消費税減税の `finish` が走る。消費税減税の照合が合わないと、その回の
**公開候補生成全体が止まる**（他の新デザイン9テーマと同じ設計）。**10/20 の消費税減税の回で4論点に新しい意見があり追い読みしないと、adapter が止まる
（複数テーマをまとめて作る回なら全テーマが止まる）。** 消費税減税の adapter が立場の対応表も公開対象に含めるようになったので、消費税減税の回の公開物が1つ増える。
`build_trend_section.py --apply` は全テーマで新デザインのページへの直接書き込みを止めるようになった（部活動・生成AIも含む。更新経路では使っていない）。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・除いた明細・区分ごとの立場・資料・日付・推移の時点と件数の幅・詳細データの表） | 合格 | 合格 |
| `verify_theme_page.py consumption-tax-cut`（候補は `--html`） | NG 0（現行ページも NG 0） | NG 0、全10テーマ NG 0 |
| `verify_number_provenance.py` | 候補の照合関数で9領域（冒頭の件数欄・7論点・推移の注記）。現行ページ NG 0 | 消費税減税 542/542・10テーマ NG 0 |
| `verify_top_page.py` | 終了0 | 終了0 |
| `build_consumption_tax_page.py --check`（新設） | — | OK: 差分なし（公開後の経路＝元HTMLと新ページを作り直して比較。元HTMLはバイト不変） |
| `build_consumption_tax_arena.py --check` | **NG（would update）** | **NG（同じ）**。作業前の main でも同じ。Git管理の `social-samples/consumption-tax-cut_arena_data.json` は公開初日（667件）のまま更新されていない古い集計で、ページ生成器は使っていない（毎回一時ファイルに作る）。作り直すと全投稿の要約とURLがGitに入るので、今回は作り直していない（7節） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（他テーマの既存の指摘で終了1） | 同じ |
| `python3 -m unittest discover tests` | 2,278件 OK（skip 8） | 2,278件 OK（skip 4。ペルソナ設定を戻したため skip が減った。共有テストを直す前は失敗6・エラー4） |
| `run_public_checks.py` | 終了0 | 終了0 |
| `seo/validate_theme_seo.py` | OK（themes=10） | OK（themes=10。H1 が変わるので `display_headline` を足した） |
| `tests/test_consumption_tax_redesign.py` | 70件 OK（手順7分31件） | 同じ |
| 2回生成 | md5 一致（`PYTHONHASHSEED` 0・1・999・random） | md5 `a45004cd…`（4通りとも一致、docs のページとも一致） |
| よみやす（`--strict`） | 完成を止める指摘 0件・PASS（平均36.1字、最長80字）。最初は同じ文末の3連続が7件（論点の欄の注記・推移の要約・背景の前置き）→直した | 同じ |
| 使い回し（`verify_page_originality.py`） | — | 「10ページに、使い回された見出し・文はありません」（最初は3件→3節） |
| AI臭（`verify_ai_tone.py`） | — | 問題なし（公開ページ10本。ペルソナ検査も実施） |
| 採用台帳（`build_adoption_registry.py --check`）・`build_data_sheet.py --check` | — | 一致・最新 |
| 代表投稿の生存（cdn.syndication.twimg.com） | 14件とも本文あり（2026-10-13） | — |

操作（Playwright、`tests/test_consumption_tax_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（読書面の折りたたみ全開・背景8行・推移・詳細データを開いても0）、ページのコンソールエラー0。
- 読み込み時：URL にハッシュが付かず、読書面と山なみの選択パネルはどちらも件数1位の「公約と政治不信」（読書面の表示名「選挙の約束は守られたのか」）。
- 冒頭のレシート：「店内での飲食」に切り替えると税率と税込額が替わる。矢印キーで買い方を移れる。
- 山なみ：立場モード（3つ目＝減税反対・慎重）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`、山なみの選択パネルも同じ論点。
- 論点タブ7つで scrollY 不変、論点の切替と山の選択で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「この論点の別の理由」で次へ。理由が未公開の論点は「未公開」と出る。
- 推移：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「推移のグラフへ」で折りたたみが開き論点の変化になる（履歴は増えない）。
- 旧アンカー：2節の表の主な読み替えと、外部の埋め込みが指す推移の2タブをブラウザで確認。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン7つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：7論点すべて表示、レシートの代わりに全品目の表、図が使えないときの論点一覧・本文・推移の要約・作り方・詳細データ・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

細い山の注記（立場ごと）：すべて・減税推進・条件付き＝事業者の実務負担とその他、減税反対・慎重＝減税の対象範囲とその他、中立・情報＝事業者の実務負担
（「強い表現が0%の論点は、基準線上の点を押せます」も出る）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 18,518px | **12,190px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数 | 7,305字（body） | 4,387字（main） | — |
| うち冒頭 | — | 4,282px | — |
| 山なみ（選択パネル込み） | — | 2,134px | — |
| 推移の要約 | — | 545px | — |
| 1280px のページ全体 | 11,708px | 7,477px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 選挙の約束は守られたのか | 1,540px | 495字 | 846px |
| 食料品だけか、全品目か | 2,350px | 834字 | 1,337px |
| 暮らしは楽になるのか | 2,366px | 800字 | 1,337px |
| 財源と社会保障はどうなる | 1,870px | 647字 | 1,045px |
| 減税か、給付か | 2,489px | 872字 | 1,364px |
| 店や会社の手間と負担 | 2,488px | 869字 | 1,364px |
| その他 | 1,321px | 439字 | 795px |

7論点とも目標（2,500px以下）を満たす。最初は「回ごとの動き」の見出しと数字が折り返して 2,527px になったので、見出しを短くし日付を「7/28」の形にして1行に収めた。

## 7. 公開前の残作業・判断待ち

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. **meta description と Article JSON-LD の description が「政府大綱が閣議決定済み」「法律成立前」のまま**（法律案は 10/9 に国会提出済み。本文は法律案の段階）。
   課題96 の判定（10/27）まで変えない指示どおり保護対象として変えていない。判定後に直す。
3. **既定で開く論点**：件数1位の「選挙の約束は守られたのか」（理由は未公開）。山なみの自動選択と一致させるため変えていない。再読のある「食料品だけか、全品目か」を既定にするかは判断待ち。
4. 投票の前置きの文「2026年7月、…大詰めを迎えました」、詳細データの「Hermes（kimi-k2.6）が…判定」は元HTMLの文のまま（保護対象）。時点が古い。
5. `build_consumption_tax_arena.py --check` の NG（6節）。Git管理の集計JSONを作り直すか、`--check` の対象から外すかは判断待ち（ページの数字には影響しない）。
6. 山なみの色・論点ボタンの「／未再読」「／島N」・選択パネルの見出し（分類名）は元HTMLのまま（写した部品は変えない方針）。
7. title・H1：title は保護対象として変えていない。H1 は新デザインの見出し「消費税減税はいつから、何%？食料品1%・給付付き税額控除の中身と、SNSで割れる賛否」に変わる（`display_headline`）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。14件の投稿が残っていることは 10/13 に確認済み）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。
- 他サイトに貼られた推移の埋め込みコードの実在（id は残したので、貼られていても飛び先はある）。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は新規0件相当の模擬（9-4）と、明細不足で止まる単体テストだけ。
- 国会の審議日程。成立は 10/13 時点で未成立（一次資料メモ）。

## 9. 2026-10-13 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/consumption-tax-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | consumption-tax-cut に `display_headline`（新しい H1 の文字列そのまま） |
| `data/page-sources/consumption-tax-cut.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致。0節で直した文・授業節・推移の注意書きを含む） |
| `docs/consumption-tax-cut-reaction-map.html` | 新デザイン（`consumption_tax_layout.finish`、その後 `build_consumption_tax_page.py` の rebuild で作り直し。公開候補とバイト一致、md5 `a45004cd…`） |
| `scripts/consumption_tax_layout.py` | 単独実行の作り直し（`legacy_refresh`）の最後にテーマ共通の見た目（件数の札）を掛け直す（掛けないと元HTMLから件数の札が落ちた） |
| `configs/consumption-tax-cut-reading.json`・`scripts/build_consumption_tax_redesign.py` | 使い回し検査の3件を直した（3節） |
| `company/APPROVALS.yaml` | 末尾に `approval-20261013-consumption-tax-cut`（`status: pending`、`decided_at: null`）。既存の記録は動かしていない |
| `DATA_REFRESH.md` | 「消費税減税の定期更新（新デザインを維持する、2026-10-13〜）」の節と、推移の `--apply` の注記 |
| `themes/consumption-tax-cut.md` | 作業記録 |
| 共有テスト | 9-3 |

### 9-2. 切替後の検査（作業ツリー）

6節の「切替後」の列。切替後の docs/ のページは公開候補とバイト一致なので、Playwright の確認画面（`evidence/`）は切替後のページで撮った。
単独スクリプトは隔離コピーで確かめた：`refresh_planet_section.py --topic consumption-tax-cut --for-docs` は停止、`inject_tide_widget.py`（SKIP）・`apply_classroom_section.py`・
`apply_theme_trust.py --theme consumption-tax-cut`（skipped）・`apply_theme_design.finish`（対象外）・`sync_issue_counts.py consumption-tax-cut`（山なみ形式のため対象外）・
`build_trend_section.py --apply`（停止）・`build_consumption_tax_page.py --public-counts-only`（停止）・`--input` だけ（停止）を流しても、新デザインのページと元HTMLはバイト不変。

### 9-3. 切替に合わせて直した共有テスト

切替直後の全テストは失敗6・エラー4（2,278件中）。辺野古の切替と同じ直し方で、検査の基準は緩めていない。

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_consumption_tax_connected.py`・`test_consumption_tax_connected_refresh.py`・`test_consumption_tax_search_entry.py` | 読むページを「公開後は元HTML（`source_for_refresh`）」に | 旧形式の連動表示・部分更新・検索入口（課題96）・計算部品の検査。公開後も元HTMLに同じ構造で残る |
| `tests/test_cite_button.py` | 消費税減税の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 消費税減税の新デザインを飛ばす | 共通の見た目を掛けない設計 |
| `tests/test_page_originality.py`（直していない） | 見出し・前置き・推移の要約を書き直して通した | 3節 |

### 9-4. 10/20 の定期更新の模擬（切替後の作業ツリーの隔離コピー、完了記録の検査だけ外した）

実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む。ここでは、より多くの経路を通すため、前回（10/11）の回と同じ投稿を
10/20 の回として置き、正典をそのまま累積候補にして **adapter の `build`（元HTMLから候補ページ・推移・立場の対応表・推移の画像を2回作って一致）→
`prepare_public_candidate_bundle`（公開JSON・finalize・SEO・授業節・他テーマの新デザイン・`consumption_tax_layout.finish`）** を通した。**最後まで通った**。
- 候補の docs/ は新デザイン（最終更新日 2026-10-20、次の更新予定 10月27日）、元HTMLは旧形式、立場の対応表は立場の中身が同じで `made_on`・`public_updated_on` だけ 2026-10-20
- 公開対象（77ファイル）に元HTML・立場の対応表・推移の画像4枚が入る。他テーマの新デザイン9ページは変わらず（変わったのは消費税減税のページだけ）
- 候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0、`build_consumption_tax_page.py --check` OK、
  `verify_builder_rebuildability.py` 10テーマ NG 0、`validate_theme_seo.py` OK、よみやす PASS（完成を止める指摘0）、使い回し 0件
- 新しい意見がある回（明細が足りない回）で止まることは、`tests/test_consumption_tax_redesign.py` の `test_count_mismatch_stops_before_writing`（finish）と
  `test_adapter_rebuilds_stance_table_and_stops_without_reread`（adapter）で確かめた
- 模擬に使った隔離コピーは作業ツリーの外（セッションの作業用フォルダー）で、作業ツリーには何も書いていない
