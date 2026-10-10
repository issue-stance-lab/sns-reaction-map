# 憲法改正論議 リニューアル準備: 棚卸しと内容対応表（2026-10-11）

対象: constitutional-amendment。手順書23の手順1（棚卸し）と手順3（内容対応表・データ対応表）。HTML試作・スクリプト変更・検索調査は含まない。
重要な前提: **現行ページはすでに「連動表示（constitutional_connected）」に作り替え済み**（検索入口・制度4項目・論点選択の読書面あり）。今回は白紙からの新設ではなく、部活動型へ作り直すための差分整理になる。

## 1. 現状の要約

- 収集2,228件、意見1,963件（`docs/data/themes/constitutional-amendment.json` の `collected_count` / `opinion_count`。正典 `social-samples/constitutional_amendment_hermes_arena_classified.json` は2,228件で `classification.is_opinion=true` が1,963件、一致を確認）。
- 論点7（正典 `classification.main_issue` の意見のみ集計。公開JSON `issues[].count` と一致）: 改憲全般759／9条・自衛隊401／緊急事態条項306／国民投票・広告250／政党・発議手続き160／情報・議論の質75／その他12。
- 立場4（同 `stance`、意見のみ）: 慎重・反対1,337（68.1%）／改正推進331（16.9%）／中立220（11.2%）／手続き重視75（3.8%）。強さは high/medium/low（意見内の内訳はHTML詳細データ。全2,228件では782/1,019/427）。
- 取得期間 2026-06-20〜2026-10-04、最終更新 2026-10-04（公開JSON `collection_period` / `updated_on`、THEMES.yaml `updated_at`）。次回収集予定 2026-10-13。
- 再読（理由区分）データ: **あり**。`data/constitutional-amendment_issues-reread.json`（`read_at` 2026-10-10）の `items` 1,963件が全意見に `bucket` を持ち、論点別件数は意見数と同じ（759/401/306/250/160/75/12）。論点ごとに3〜4区分の `buckets`。10/10の追い読みで594件を追加（`catchup_2026_10_10`）。ただし立場別の理由内訳は無く、理由は「全立場」の値のみ。
- 作業記録に「追加659件の独立確認は継続中」とある。9/13記録: 1,369意見中の「他659意見」と皇室典範3件の論点修正は独立確認・修正が未完了のまま承認・公開（`themes/constitutional-amendment.md` 9/13節、`approval-20260913-002`）。その後の追い読みで本文確認と区分接続は全件済みだが、**独立確認が済んだ旨の記録はこのテーマ文書に無い**。
- 一次資料メモ `quality/research/constitutional-amendment-primary-sources.md` の確認日は 2026-08-30（8件）・08-31（11件）・09-07（2件）。最新は2026-09-07。背景・制度確認は `data/verification/constitutional-amendment-background.json` の `checked_on` 2026-09-13。主張照合 `claim_verification.checked_on` 2026-09-13、編集部整理 2026-09-12、語られていない争点 2026-10-04。

## 2. 棚卸し表（現行 docs/constitutional-amendment-reaction-map.html、上から順）

配置先の略: 冒頭／全体像（意見の全体像）／論点別／背景／不要。生成元の「手書き」はスクリプトが作らずHTMLにだけ存在するもの。

| # | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | head | title「憲法改正で何が変わる？9条・緊急事態条項をわかりやすく比較」、description、canonical、OGP、ld+json | 手書き＋SEO_META／ARTICLE_JSON_LD（`configs/constitutional-amendment-reaction-map.json` 由来） | 冒頭（維持） | - |
| 2 | 件数 | 読んだところ0（読了カウンタ）、SNSの意見1,963件 | THEME_COUNT_START（`build_constitutional_arena.py`） | 冒頭 | - |
| 3 | h1・導入 | h1、「現実の安全保障に合わせて改正するのか…」、説明1文 | 手書き | 冒頭 | - |
| 4 | 数値 | 「議論の中心 759件」（改憲全般）と一言 | build_constitutional_arena | 全体像 | - |
| 5 | 見出し | change-lens「知りたいところから条文の変化をのぞく」4経路（9条/緊急時/国民投票/SNS） | 手書き（SEARCH_ENTRY、`constitutional-search-entry.js/css`） | 冒頭 | - |
| 6 | 比較カード | 9条: いま／2018年条文イメージ／期待／懸念、SNS導線、自民党PDF | 手書き | 冒頭（短答）＋論点別（9条） | - |
| 7 | 比較カード | 緊急事態: 現行は法律対応／複数案／期待・懸念、衆議院討議記録 | 手書き | 冒頭＋論点別（緊急事態） | - |
| 8 | 図 | 国民投票: 国会3分の2→60〜180日→過半数、最低投票率なし、e-Gov | 手書き | 冒頭＋論点別（国民投票） | - |
| 9 | 図 | 「賛成・反対は一枚岩ではない」3立場の要約と調査条件へのリンク | 手書き | 全体像 | - |
| 10 | FAQ | 5問: 決まったか／何回改正か／誰が決めるか／最低投票率／国民投票法改正との違い。「2026年9月27日時点」の文言、e-Gov2点 | 手書き（スクリプトに該当なし） | 冒頭（短答） | - |
| 11 | 図表 | 立場別内訳: 「慎重・反対が7割近く」、331件(16.9%)、4立場バー、ボタン4つ | STANCE_GLANCE（build_constitutional_arena）。見出し「7割近く」は文章 | 全体像 | - |
| 12 | 注記 | 元データ2,228件中1,963件、取得期間、AI分類、世論調査ではない | RESEARCH_CONDITIONS（build_constitutional_arena） | 全体像（調査条件）＋背景 | - |
| 13 | 背景 | 「何が、どこまで進んでいるのか」導入、なぜ始まったか3段落、背景出典6件 | 手書き＋`constitutional-amendment-background.json`（`definition` `cause` `cause_sources`） | 背景 | - |
| 14 | 年表 | 11項目（1946〜2026年9月）、各項目に出典リンク | `constitutional-amendment-background.json` の `timeline` | 背景（開閉）。論点に結ぶ印は無し | - |
| 15 | 比較 | 「憲法の何をどう変える提案か」導入＋制度確認4項目（どの提案／どう改正／今の仕組みで対応／権利に何が起きるか）、出典 | `background.json` の `checklist.items`（`issue_ids` 付き） | 論点別（制度確認）＋背景 | - |
| 16 | 注記 | 「このページで未確認のこと」2点（世論調査でない、政党説明は党見解） | 手書き（背景ブロック内） | 全体像 | - |
| 17 | 図 | SNS反応マップ（山並み）: 幅=件数、高さ=強い表現割合、色=最多立場。操作ヒント、100マスの割合 | PLANET_SECTION（build_planet_data系）＋`constitutional-connected.js` | 全体像 | - |
| 18 | 表 | 図が使えないときの論点一覧（7論点、件数・割合） | PLANET_SECTION | 全体像（JSなし本文） | - |
| 19 | 論点7枚 | 各論点: 件数・割合・強い表現割合、立場別件数、全体比と立場内比、理由別件数（全立場）、「件数と割合は逆に動く」注 | PLANET_DATA＋issues-reread＋connected_content | 論点別 | - |
| 20 | 一次資料照合 | 9条2件（徴兵制18条＝資料どおり、自衛隊違憲解釈）、緊急事態1件（裏が取れない）、国民投票2件、政党手続き1件。改憲全般・情報議論・その他は照合なし | `claim_verification`（公開JSON）、`constitutional-amendment-claims.json`、`build_constitutional_process_sections.py` | 論点別 | - |
| 21 | 一次資料クイズ | 14投稿6主張の「その主張、資料に当たるとどうなる？」 | `constitutional-amendment_claim_posts.json`、`claims.json`、process_sections | 論点別（照合に統合） | クイズ形式は新構成では照合結果として表示し直す |
| 22 | 空白 | 語られていない争点4件（異議申立、緊急集会後措置、国会法68条の3、同日実施）。SNS側0件、母数1,963、検索条件、出典 | `sunk-continents.json`、`ocean_layer` | 論点別（国民投票・手続き）＋背景 | - |
| 23 | 共通の心配 | 「戦争を避けたい。」推進・反対各2件の代表 | `veins.json`（7件） | 論点別（改憲全般）＋全体像 | - |
| 24 | 編集部整理 | 共通する前提／本当の対立（2件）／まだ分からないこと（2件）。2026-09-12時点 | `editorial_summary`、`constitutional-amendment-editorial.json` | 全体像 | - |
| 25 | 見かた | このページの見かた（幅・高さ・色の読み方） | 手書き | 全体像（凡例） | - |
| 26 | 推移 | 立場の変化／論点の変化、9/26→10/4（188件→207件）、「慎重・反対3.8ポイント減」、再生ボタン | TIDE_CARD（`inject_tide_widget.py`、adapterの`_apply_tide`） | 全体像 | モデル差（kimi-k2.6→k2.7-code）の注記は残す |
| 27 | 投稿 | 論点ごとのX投稿 6論点×2件=12件（その他は無し）。要旨、@ID、論点へのリンク | FEATURED_POSTS（`data/constitutional-amendment-featured-posts.json`、build_constitutional_arena） | 論点別（最大2件） | - |
| 28 | 投稿URL | 12件のx.com/status URL（先頭に列挙） | 同上 | 論点別 | - |
| 29 | 投票 | 「どの論点を重く見る？」2問、24選択肢（論点7×立場4を基にした構成。投票キー`constitutional-amendment-issue-stance-v1`） | 手書き＋`vote-config.js`、`vote-store.js` | 全体像（維持必須） | - |
| 30 | 教育 | 授業・ディベート: 推進3理由、慎重3理由、確かめる一次資料3点、問いの例3、使い方 | CLASSROOM（`scripts/seo/apply_classroom_section.py`）＋手書き | 背景（開閉） | - |
| 31 | 信頼 | 公開日2026-06-24、更新日2026-10-04、収集方法、AI工程、分かったこと、訂正窓口 | ARTICLE_TRUST | 背景（開閉）。日付は生成元から | - |
| 32 | 回遊 | 次に見るテーマ3件（生成AIと著作権・自転車青切符・消費税減税） | related-topics（`related-theme-tracking`） | 背景 | - |
| 33 | 表 | 詳細データ折りたたみ: 論点別件数、立場、強さ、件数の出所、カテゴリ×検索クエリ、カテゴリ×スタンス（ヒートマップ2枚）、注意 | build_constitutional_arena（`build_constitutional_dashboard.py`系のヒートマップ） | 背景（開閉） | カテゴリ×検索クエリ／×スタンスは旧12カテゴリ体系で、論点7体系と別。残すか判断要（第5節） |
| 34 | 埋め込み | 論点別の読書面内「ここで投稿を表示」×2/論点、X widgets.js | constitutional_connected_content、`twitter.com/widgets.js` | 論点別（開いたときに読み込み） | - |
| 35 | 計測・広告 | GA4、AdSense、share-x-btn、related-theme-tracking | 共通 | 維持 | - |
| 36 | 別所 | 論点の一覧ブロック（押すと地図が切り替わる）、ページ内リンク #fallback-nav #ocean #planet-block #stance-glance #research-conditions #fb-* #issue-* | 生成（connected） | 内部リンクは維持（既存URLのアンカー保持を要確認） | - |
| 37 | 一次資料リンク | 背景・制度・論点の出典リンク（e-Gov憲法・国民投票法、国会会議録、自民党資料、衆議院、国立国会図書館、防衛省）。重複を除くと約25 URL | background.json／claim_verification／sunk-continents | 論点別と背景に再配置 | - |

## 3. データ対応表（正典→公開JSON→HTML）

流れ: 正典 → `scripts/build_constitutional_arena.py`（入力は THEMES.yaml の `sample_file`。`--input/--html-template/--output-html` で候補生成）→ `docs/constitutional-amendment-reaction-map.html` と `docs/data/themes/constitutional-amendment.json`。adapter は `scripts/refresh_adapters/constitutional.py`（`_run_builder` → build_constitutional_arena、続けて build_constitutional_process_sections、`_apply_tide`、`_apply_connected_display`）。

| 項目 | 正典・入力 | 公開JSON | HTMLを作る処理 | 手入力・重複 |
|---|---|---|---|---|
| 収集件数2,228 | 正典 全件 | `collected_count` | THEME_COUNT／RESEARCH_CONDITIONS（arena） | HTMLに「2228」「2,228」が計4か所（生成区間内）。`SEARCH_OPINIONS`で冒頭の1,963を同期 |
| 意見数1,963 | 正典 `is_opinion` | `opinion_count` / `issue_assigned_count` | arena（STANCE_GLANCE等）、connected | HTML内に「1963/1,963」が約38か所。**FAQ・change-lens本文・詳細データ説明は手書きで連動しない部分あり**（要確認） |
| 論点別件数 | 正典 `main_issue` | `issues[].count` | arena、`build_planet_data` 系（PLANET_DATAを埋め込み） | HTMLに論点件数が複数箇所（山・一覧・論点7枚・投稿カード・詳細表）。いずれも生成 |
| 立場 | 正典 `stance` | `issues[].stances[]` | arena、STANCE_GLANCE | 見出し「7割近く」「推進16.9%」文言は生成と手書きの混在（未確認）。投票の立場キーはJSリテラル |
| 理由（区分・件数） | `data/constitutional-amendment_issues-reread.json`（全1,963件） | 公開JSONには無し | `constitutional_connected_content.py`（読書面のtemplate）、検証は `constitutional_count_provenance.py` | 立場別の理由内訳が無い。件数の元記録照合あり |
| 推移 | `social-samples/updates/constitutional-amendment/` の更新回（2026-08-08〜10-04の8回） | HTMLのみ（TIDE_CARD） | `inject_tide_widget.py`（slug定義あり）＋adapter `_apply_tide`。前回回は更新回フォルダから選ぶ | 2026-07-26以前の潮目は手作業値（adapter内コメント）。モデル差の注記は承認記録 |
| 一次資料（主張照合） | `data/verification/constitutional-amendment-claims.json`、`claim_posts.json` | `claim_verification`（6件） | `build_constitutional_process_sections.py`（CLAIM_AUDITマーカー）、connected_content | 確認日2026-09-13が複数箇所。`verify_claim_verdicts.py`の鮮度警告対象 |
| 一次資料（背景・年表・制度確認） | `background.json` | 無し | connected系（年表・制度確認）。ただし背景本文自体は手書きで同内容を二重保持 | **背景の本文とbackground.jsonの重複**。出典リンクも両方 |
| 一次資料（語られていない争点・共通の心配・編集部整理） | `sunk-continents.json`、`veins.json`、`editorial.json` | `ocean_layer`、`editorial_summary` | arena／connected | 母数1,963を更新回ごとに手で更新（9/26・10/4記録）。検証は`verify_ocean_layer.py` |
| 投稿URL（代表12件） | `data/constitutional-amendment-featured-posts.json` | 無し | arena（FEATURED_POSTSマーカー7か所） | 読書面の「投稿2件」はHTML内FEATURED_POSTSから再利用（別コピー無し）。クイズ14投稿は別ファイル |
| 日付（公開日・更新日） | THEMES.yaml `published_at` `updated_at` | `updated_on` | ARTICLE_TRUST／ld+json | 公開JSON・THEMES.yaml・HTMLの3か所。FAQの「9月27日時点」は手書きで**10/4更新後も古いまま** |
| 検索入口（change-lens・FAQ） | なし | なし | **生成するスクリプト無し**（手書きHTML。`tests/test_constitutional_search_entry.py` が検査、件数のみ `apply_search_entry_counts`） | 全文が手入力。9条・緊急時・国民投票の説明が背景JSONと重複 |
| 投票 | `vote-config.js` | なし | adapter `vote_fingerprint` が選択肢の並びを検査（24個固定） | 論点・立場の順序変更は過去投票の意味を変える。リニューアルで順序を変えられない |
| 設定 | `configs/constitutional-amendment-reaction-map.json`、`-summary-ui.json`、`configs/topics/constitutional.yaml`（旧12カテゴリ分類設定） | - | SEO・投票導入文・分類 | 旧カテゴリ体系（12）と現行論点（7）が併存 |

注意: 全ビルダーが公開済みHTMLを `--html-template` に使う（手順書の「公開HTMLを次回生成の入力にしない」と食い違う）。

## 4. このテーマならではの疑問の候補（原稿からの推測。検索ツールは使っていない）

既存の search-entry 部品の内容: 4経路「9条は？自衛隊明記」「緊急時は？権限と期限」「いつ決まる？国民投票」「賛否は？SNS」と、FAQ5問（決まったか／改正回数／誰が決めるか／最低投票率／国民投票法改正との違い）。title は「何が変わる？」。以上を先に残した上で、原稿・論点からの推測は次のとおり。

1. 憲法改正で何が変わるのか（現行ページの主題）
2. 9条に自衛隊を書き加えると何が変わるのか（9条・自衛隊401件、2018年条文イメージ）
3. 緊急事態条項とは何か、何が心配されているのか（306件、うち慎重・反対274件）
4. 国民投票のやり方（過半数・最低投票率なし・60〜180日・広告規制）
5. 改正はもう決まったのか／日本は何回改正したか（FAQにある）
6. 国民投票法が改正されたが、憲法は変わったのか（2026年7月公布）
7. 賛成・反対の人はそれぞれ何を理由に挙げているか（理由区分の再読データ）
8. 「憲法改正に賛成でも今の政権の案には反対」は成り立つか（編集部整理の本当の対立）

注: 規模・時期・検索語は未確認。

## 5. 部活動と違う点・判断が必要な点

1. **すでに連動表示化済みで、完成形に近い。** 部活動型へ一から作るのか、現行の読書面・検索入口を磨くのかを先に決める。旧「不要」扱いの部品（#bukatsu-check、旧代表投稿、ocean）は `constitutional-connected-page.js` が非表示にしている。
2. **論点が7つ（その他を除くと6）で多い。** 部活動より山が多く、論点別の説明・照合・投稿を全部作ると長い。照合が付くのは4論点のみ（改憲全般・情報議論・その他は無し）。
3. **再読データの欠け方。** 論点別の理由は全件あるが、立場別の理由内訳が無い。さらに「他659意見の独立確認は未完了」の記録が残る。理由件数を公開表示する前に独立確認の扱いを決める。
4. **一次資料の鮮度とメモの欠陥。** 最新確認が2026-09-07、主張照合は9/13で、データ更新(10/4)の後。メモの冒頭に不要な1行（「以下に調査メモを標準出力に…」）が混入。国民投票法の2026年改正は成立済みで資料側は反映済みだが、緊急事態条項の主張は「裏が取れない」判定で、どの案を指すか未特定。
5. **投稿埋め込み。** 論点ごとの代表は2件固定で、「その他」には無し。投稿は開いたとき読み込み方式が既にある（`ca-embed`）。表示不可時のリンク残しは未確認。
6. **投票の順序固定。** 24選択肢は論点7×立場4の並びに依存。論点の追加・並べ替えができない。
7. **他テーマと共有するスクリプト。** `inject_tide_widget.py`、`apply_theme_design.py`、`build_planet_data.py`、`refresh_planet_section.py`、`verify_*`系、`seo/apply_classroom_section.py`が共通。憲法専用は arena / process_sections / connected(+content) / count_provenance / adapter。
8. **手書き部分が多い。** change-lens・FAQ・背景本文は生成元が無く、日付「9月27日時点」が古いまま。データ化するか手書きのまま検査を付けるか決める。
9. **旧12カテゴリ体系のヒートマップ**（カテゴリ×検索クエリ／スタンス）を残すか。現行論点7体系と別物。
10. **潮目のモデル差**（kimi-k2.6とk2.7-code）。オーナー判断で無視する運用だが、新ページで注記を残すか。

## 6. 読めなかったもの・確認していないもの

- 検索根拠（ラッコ、キーワードプランナー、Trends、Search Console）は未取得。疑問の規模・時期・検索語は未確認。
- 「追加659件の独立確認」が現時点で済んだかは、`quality/reviews/2026-10-10-constitutional-amendment-catchup.json` と各レビュー記録を開いていないため未確認。
- featured-posts・claim_posts の件数・内容の個別確認、X埋め込みの表示失敗時の挙動、スマホ表示・コンソールエラーは未確認。
- 手書き部分のうち、1,963が連動しない箇所の全数、「7割近く」文言の生成可否は未確認。
- `social-samples/updates/` の各回の件数と、`tests/` の検査内容全体は読んでいない（検索入口のテストの冒頭のみ）。
- `build_planet_data.py` / `refresh_planet_section.py` / `inject_tide_widget.py` が憲法ページで具体的に何を書き換えるかは確認していない。
- 一次資料メモ本文は先頭と確認日の抽出のみ。各資料のURL生存は未確認。
- `HTMLの実画面（ブラウザ描画）は見ていない`。構造はソースの解析のみ。
