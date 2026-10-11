# 副首都（fukushuto）リニューアル準備：棚卸しと内容対応表（2026-10-11）

対象は `docs/fukushuto-reaction-map.html`（手順書23の手順1と手順3）。HTMLの試作・スクリプト変更・検索ツールの調査は含まない。
数字は作業ツリー `isa-wt-renew-fukushuto`（ブランチ task/renew-fukushuto）のファイルから直接数えた。取れなかった値は「未確認」と書く。

## 1. 現状の要約

1. 件数：収集2,860件、意見2,356件、意見外504件（`social-samples/fukushuto_hermes_classified.json` の配列長と `classification.is_opinion`。公開JSON `docs/data/themes/fukushuto.json` の `collected_count` `opinion_count` と一致）。期間は2026-07-14〜2026-10-10（同JSON `collection_period`）。
2. 論点は7つ（意見の件数）：都構想・維新677、候補地538、防災・災害350、定義・中身332、優先順位203、その他147、費用・財源109（正典 `classification.main_issue` を意見で数えた値。公開JSON `issues[].count` と一致）。
3. 立場は3区分：法案反対1,449、法案賛成・推進504、中立・情報403（正典 `classification.stance`。意見に占める割合は反対62%・賛成21%・中立17%）。強さ（intensity）は high 785／medium 1,171／low 400。
4. 最終更新日：2026-10-10（`THEMES.yaml` の `updated_at`、公開JSON `dateModified` 相当）。公開日2026-07-15。次回収集予定2026-10-19（`collect_at`）。10/10の更新回は新規282件、意見218件、累積は前回2,578投稿・意見2,138件から増加。
5. 再読（理由区分）データ：**5論点だけにある**（`data/fukushuto_5issues-reread.json`）。候補地538（7区分）、防災・災害350（3区分）、優先順位203（4区分）、その他147（5区分）、費用・財源109（4区分）。合計1,347件で、各論点の意見件数と一致（未再読0件）。
6. 再読データが**無い論点**：都構想・維新677、定義・中身332（合計1,009件。ページ内 `reread_summary.not_connected_opinion_count` と一致）。新形式の再読登録簿 `data/verification/reread/fukushuto.json` も無い（`configs/planet/fukushuto.yaml` 1行目 `reread_registry: false` にその旨の注記）。
7. 一次資料メモ：`quality/research/fukushuto-primary-sources.md`（263行、資料A〜Nの見出し19個）。確認日は 2026-08-31（資料A〜J）、2026-09-07（資料K）、2026-10-03（資料L〜N）。**最新の確認日は10月3日で、10月10日の更新回では資料メモは更新されていない**（git最終更新も2026-10-03）。
8. 公開ページ側の確認日：事実確認5主張と「資料にしかない話」4件は2026-10-10、現在地・候補地8件・FAQは2026-10-03、背景（制度の確認）は2026-09-12、編集部の横断整理は2026-10-03。
9. 事実確認5主張（`data/verification/fukushuto-claims.json`、判定は資料どおり2・少しずれる2・裏が取れない1）。該当投稿は延べ26件（ページ表示：12・8・3・2・1）。「資料にしかない話」4件（`data/verification/fukushuto-sunk-continents.json`）、地下水脈（veins）は0件。
10. 検索入口の部品はすでにある（`scripts/fukushuto_search_entry.py` ＋ `docs/fukushuto-search-entry.css/js`）。FAQ6問、4つの問いタブ、候補地8地域、現在地3段階を持つ（詳細は4節）。

## 2. 棚卸し表（現行ページを上から順に）

配置先の略号：冒頭＝先に答える内容／全体像＝意見の全体像／論点＝論点別／背景＝開いて読む背景／不要。
出所の「手書き」は `docs/fukushuto-reaction-map.html` に直接書かれているか、生成器が現行HTMLを雛形として引き継いでいる文言。

### 2-1 ページ頭（head・上部）

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| H1 | メタ | title「副首都はいつ・どこに決まる？大阪の指定状況と法案の問題点｜SNS反応まっぷ」、meta description、canonical | 手書き（HTML雛形） | 冒頭（題名として維持） | - |
| H2 | 構造化データ | JSON-LD Article（datePublished 2026-07-15、dateModified 2026-10-10、画像 fukushuto-hero.webp） | 手書き＋日付は更新時に書換え | 冒頭（維持） | - |
| H3 | 構造化データ | JSON-LD FAQPage（FAQ6問） | `fukushuto_search_entry.py` の `FAQS` から生成 | 冒頭（FAQ本文と同期して維持） | - |
| H4 | 共通部品 | GA4・AdSense・OGP・site-tokens/topic-modern/theme-design の CSS/JS、vote-config/vote-store | 共通テンプレート | 維持（保護対象） | - |
| T1 | 進捗表示 | 「探ったところ 0／18」（予想2問・論点7・資料にしかない話4・クイズ5の計18地点。localStorage `isa-seen-fukushuto`） | `fukushuto_connected.py` の `PROGRESS_LABEL` 等 | 論点（別途判断。5節） | 新ページで地点数が変われば数え直す必要あり |
| T2 | ナビ | 「トップ／統治機構・地方」パンくず | 共通 | 冒頭 | - |
| T3 | 件数 | 「SNSの意見2,356件」（収集した投稿のうち意見を含むもの） | `build_fukushuto_arena.py`（正典の意見件数） | 冒頭（件数。データで変わる文字） | - |
| T4 | 見出し | H1＋問い「副首都、本当に必要？ 場所は大阪でいい？」 | 手書き | 冒頭 | - |
| T5 | リード | 「2860件のうち意見2356件を**6つの論点**に整理。世論調査ではない」 | `build_fukushuto_arena.py`（件数）＋手書き文言 | 冒頭 | 「6つ」は実際の論点7つ（その他を含む）と食い違う。直す対象 |
| T6 | 結論カード | 「議論の中心677件：『大阪ありき』への不信が最も集まった」＋SVG | `build_fukushuto_arena.py` | 全体像 | - |

### 2-2 先に答える部分（指定状況・FAQ・制度の問い）

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| A1 | 現在地 | 「副首都法は2026年7月成立。大阪はまだ指定されていません」。3段階（7月成立・公布／10月3日要件案公表、10月16日まで意見募集／時期未定・指定前） | `fukushuto_search_entry.py` の `render()` に文言を直書き | 冒頭 | - |
| A2 | 外部リンク | 意見募集の資料（e-Govパブコメ）へのリンク | 同上（直書き） | 冒頭 | - |
| A3 | 候補地一覧 | 「各地は今どの段階？」国の指定0道府県、法律の施行は10月30日予定、e-Gov法令へのリンク | 同上 | 冒頭 | - |
| A4 | 候補地8件 | 大阪府・市（2/12構想公表）、福岡県（8/7）、愛知県・名古屋市（8/10）、北海道・札幌市（8/27）、群馬県（7/30意思表明）、広島県（8/25検討）、宮城県・仙台市（8/26要件待ち）、京都府（7/31単独準備なし）。各行に自治体の一次資料リンク8本 | `fukushuto_search_entry.py` の `CANDIDATE_REGIONS`（手入力） | 冒頭（「各地の動き」） | - |
| A5 | 絞り込み | すべて8／指定を目指す5／検討2／準備なし1の切替 | 同上（件数は `CANDIDATE_REGIONS` から計算） | 冒頭 | - |
| A6 | 注記 | 「全国の網羅的な一覧や国の認定候補地一覧ではない。次は意見募集の結果と10月末の政令を確認」 | 同上 | 冒頭 | - |
| A7 | 問いタブ4つ | 何が変わる？／候補地は？／都構想との関係は？／費用はいくら？。各タブに短答＋3点＋該当する山への導線 | 同上 `ENTRY_TOPICS` | 冒頭（短答）＋論点（導線） | - |
| A8 | 入口2 | 「副首都法案の問題点は何？」3カード（防災：東京と同時に被災しないか／決め方：大阪ありきで決まらないか／費用：いくらかかり何を優先するか）＋条文・過去の移転費用試算・SNS内訳へのリンク3本＋注記 | 手書き（`fukushuto_connected` 系または HTML直書き。生成元の特定は未確認） | 冒頭（問題点の入口）→論点へ | - |
| A9 | FAQ6問 | 成立済みか／大阪に決まったか／いつ決まるか／代替地域と副首都の違い／都構想との違い／4兆〜7.5兆円か。出典リンク2本（e-Gov、衆院審議経過） | `FAQS` | 冒頭 | - |

### 2-3 意見の全体像

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| B1 | 立場の内訳 | 「賛成・推進は意見の21%にとどまる」。反対1,449（62%）、中立・情報403（17%）、賛成504（21%）の積み上げ棒。立場3ボタンで説明表示。「投票済みにはならない」注記 | `build_fukushuto_arena.py`（スタンス集計） | 全体像 | - |
| B2 | 調査条件 | 「元データ：Yahooリアルタイム検索2860件、取得期間2026-07-14〜10-10、世論調査ではない」 | `research_conditions.py`／`build_fukushuto_arena.py` | 全体像（集計の限界） | - |
| B3 | 山なみ（SNS反応マップ） | 幅＝意見の数、高さ＝強い表現の割合、色＝最多の立場。山の選択、立場モード4（すべて／賛成／反対／中立）、100マスのワッフル（件数と割合）、図が使えない時の一覧 | `build_planet_data.py`＋`refresh_planet_section.py`（`PLANET_DATA` を埋め込み、設定は `configs/planet/fukushuto.yaml`） | 全体像 | - |
| B4 | 論点一覧（フォールバック） | 7論点それぞれの件数・割合・山の高さ・立場内訳、「立場ごとにその論点が占める割合」（例：賛成504件のうち候補地189件37.5%） | 同上 | 論点（件数は山なみと同じデータ） | フォールバックのため新ページは山なみ側と統合 |
| B5 | 横断整理 | 編集部の整理（共通する前提1／本当の対立2／まだ分からないこと3）。2026-10-03時点 | `data/verification/fukushuto-editorial.json`（手書き文章）。**文中の％と件数が手入力**（下記3節） | 全体像 | - |
| B6 | 見かた | 「このページの見かた」山・幅・高さ・色の説明 | 手書き（雛形） | 全体像（凡例） | - |
| B7 | 推移（潮目） | 「10月3日→10月10日：法案賛成・推進が3.8ポイント増加」。立場の変化／論点の変化／変化を再生。比較対象は各回の意見投稿。中立を除く母数の注記あり | `inject_tide_widget.py`（`refresh_adapters/fukushuto.py` の `_apply_tide`）。入力は `social-samples/updates/fukushuto/` の回ごとのclassified.json | 全体像 | - |

### 2-4 論点別（理由・投稿・資料）

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| C1 | 論点カード7 | 論点ごとの件数・立場別件数・理由区分・資料照合・図解（「図解をひらく」）。図解画像は6枚（論点画像、`refresh_planet_section.py` の対応表） | `build_fukushuto_arena.py`／`refresh_planet_section.py` | 論点 | - |
| C2 | 理由区分 | 候補地7、防災3、優先順位4、その他5、費用4の各件数（1節5） | `data/fukushuto_5issues-reread.json` → `configs/planet/fukushuto.yaml` の `sub_issues` | 論点（5論点のみ） | - |
| C3 | 理由区分なし | 都構想・維新、定義・中身は理由区分の表示なし | - | 論点（「未公開」と明記） | 再読データが無い |
| C4 | 連動パネル | 山を押すと下に出る「選んだ論点」：件数、理由、実際の投稿2件（X埋め込みは開閉式、元投稿リンク付き）、制度の確認、投稿の主張と一次資料、資料にあり収集投稿で見つからなかったこと | `fukushuto_connected.py`／`fukushuto_connected_content.py`／`docs/fukushuto-connected*.js/css` | 論点（新ページの核） | - |
| C5 | 制度の確認 | 4項目（担う機能／指定の手続き／費用と負担／進めた後の確認）。「確認 2026-09-12」。論点ごとに該当項目を紐づけ（候補地→指定手続き、防災・定義→担う機能など） | `data/verification/fukushuto-background.json` の `checklist` | 論点＋背景 | - |
| C6 | 論点ごとのX投稿 | 7論点×2件＝14件の代表投稿（要約1行＋X埋め込み） | `scripts/fukushuto_issue_media.py` の `MEDIA` 定数（手入力）。連動パネルでも同じ投稿を再利用 | 論点（最大2件） | 同じ14件が2か所に出ている。1か所へ |
| C7 | 投稿の主張と一次資料 | 論点ごとの「資料どおり／少しずれる」バッジと出典（都構想・維新に2主張、定義・中身に1、費用・財源に2） | `data/verification/fukushuto-claims.json`・`data/fukushuto_claim_posts.json` | 論点 | - |
| C8 | 資料にしかない話 | 4件：①東成区の2015→2020年の逆転（0件）、②副首都と首都中枢機能代替地域の区別（2件）、③副首都推進局予算314億円の大半は大学関連（0件）、④2016年の馬場伸幸氏の質問（0件）。各件に調べた範囲と出典リンク | `data/verification/fukushuto-sunk-continents.json`。**「集めた投稿での件数」と調べた範囲の注記が手入力** | 論点（関連する山の下）＋背景 | - |
| C9 | クイズ | 「一次資料クイズ 5問」（主張が資料に当たるとどうなる？） | `claims` から描画（`topic-modern.js`） | 論点（または不要。5節） | 新ページの主役でなければ削除可 |

### 2-5 事実確認・投稿・投票・授業・作り方

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| D1 | 事実確認5主張 | ①住民投票二度否決（資料どおり・12件）②123対121で成立（資料どおり・8件）③附帯決議が同日実施を禁止（少しずれる・3件）④整備費用4〜7.5兆円（少しずれる・2件）⑤AI試算2兆円（裏が取れない・1件）。各主張に一次資料の説明、判定、X投稿例1件。件数の数え方の注記 | `build_fukushuto_process_sections.py`（`FACT_CHECK_START/END`）←`data/fukushuto_claim_posts.json` | 論点（C7と同データ）＋背景 | 判定表示の重複は1か所へ |
| D2 | Xリンク | 事実確認の投稿例4件（kiriyaikuo は2主張で共用） | 同上 | 論点 | - |
| D3 | 投票 | 「一番気になる設計の論点は？」論点7×立場3＝21通り。やり直しボタン、Xでシェア | 共通 `vote-store.js`＋Supabase `cast-vote`（`fukushuto-issue-stance-v1`） | 全体像の後（保護対象） | 削除不可（既存の票） |
| D4 | 授業 | 「授業・ディベートで使うとき」賛成理由3・反対理由3、確かめる一次資料3本、問いの例3つ、使い方、印刷ボタン | `configs/classroom/fukushuto.json` | 背景 | - |
| D5 | 作り方 | 編集・分析情報：公開日2026年7月15日、最終更新日2026年10月10日、収集方法（9検索語）、分類で分かったこと、データの読み方、訂正窓口 | 手書き＋日付・件数は生成器 | 背景 | - |
| D6 | 詳細データ | 論点別件数表、立場別、強さ別（high785／medium1,171／low400）、投票の選択とマーカー、収集クエリ9個（副首都法案／副首都構想／副首都 大阪／維新／反対／防災／費用／どこ／南海トラフ）、注意2点（世論調査でない／初回収集が衆院通過直前のため国会審議への反応が多く出やすい） | `build_fukushuto_arena.py` | 背景（折りたたみ） | - |
| D7 | 次に読む | 憲法改正論議、消費税減税 | 手書き（雛形） | 背景 | - |
| D8 | フッター | トップ、運営者情報、調査・編集方法、お問い合わせ・訂正（Googleフォーム）、プライバシー、免責、画像制作方針、応援リンク | 共通（`unify_site_chrome`） | 維持 | - |
| D9 | 背景（制度） | 「何が、どこまで進んでいるのか」：定義、いま、なぜ始まったか、経緯3件（2020年11月住民投票／2026年7月成立／2026年9月確認）、必要性・制度・場所を分けて確かめる4項目（担う機能／指定の手続き／費用と負担／進めた後の確認）、未確認のこと、各項目の出典リンク（大阪市選管、参議院、e-Gov） | `data/verification/fukushuto-background.json`（確認日2026-09-12相当） | 背景 | - |
| D10 | 外部リンク類 | e-Gov法令、衆院審議経過、参議院投票結果・附帯決議PDF、大阪市選管、国交省移転費用、国会会議録、大阪府予算PDFなど。ページ中のリンク総数は未集計 | 各データの出典欄 | 論点／背景 | - |

## 3. データ対応表

流れは「非公開正典 → 検証データ・設定 → 生成器 → HTML（＋公開JSON）」。**重要な性質：`build_fukushuto_arena.py` は現行の公開HTMLを雛形（`--html-template`）として読み、決まった区間だけを差し替える。**手順書の「公開HTMLを入力に使わない」とは異なる作りになっている（5節）。

| 項目 | 正典・元データ | 公開JSON／中間 | HTMLを作る生成器 | 手入力の値の場所・重複 |
|---|---|---|---|---|
| 収集・意見件数 | `social-samples/fukushuto_hermes_classified.json`（`is_opinion`） | `data/public/themes/fukushuto.json` ＝ `docs/data/themes/fukushuto.json`（`build_public_registry.py`。2つは同一バイト列を確認） | `build_fukushuto_arena.py`（`--input` は候補、`--public-counts-only` は仕上げ）、`research_conditions.py`、`refresh_planet_section.py`（調査条件の同期） | HTMLの題名・リード・調査条件・詳細データ・作り方・FAQ周辺に2,356/2,860が複数回登場（生成器が差し替え。手で直す場所は無いが、**同じ数字が10か所以上ある**）。`THEMES.yaml` の `sample_period` も別に手入力 |
| 論点別件数 | 同上（`main_issue`） | 公開JSON `issues[].count` | `build_fukushuto_arena.py`（ISSUES、ナビ、詳細表）、`build_planet_data.py`（`PLANET_DATA`）、`fukushuto_taxonomy.py`（唯一の論点定義） | 論点定義は4か所で一致が必要：HTMLの `ISSUES`／`VOTE_ISSUES`、`supabase/functions/cast-vote/index.ts`、`configs/fukushuto-reaction-map.json` の `issue_counts.cards`（`tests/test_fukushuto_taxonomy.py` が検査） |
| 立場 | 同上（`stance`） | 公開JSON `issues[].stances[]` | `build_fukushuto_arena.py`（スタンス集計・積み上げ棒）、`PLANET_DATA` | 見出し「賛成・推進は意見の21%」の％は生成。**立場名・色は `configs/planet/fukushuto.yaml` と `fukushuto_taxonomy.py` の2か所** |
| 強さ | 同上（`intensity`） | 公開JSON `issues[].intensities[]` | 同上 | 山の高さは「強い表現（調整後）」。高さの式は `PLANET_DATA.elevation_formula` |
| 理由（再読） | `data/fukushuto_5issues-reread.json`（5論点、区分と投稿ごとの bucket） | `PLANET_DATA.issues[].sub` | `refresh_planet_section.py`、`fukushuto_connected_content.py`、`fukushuto_count_provenance.py`（件数照合） | **同ファイルの `population`（1681/951）と `method` 文が古いまま**（現在は意見2,356・5論点1,347）。区分名は `configs/planet/fukushuto.yaml` ではなく再読ファイル側 |
| 理由なし論点 | （無い） | `reread_summary.not_connected_opinion_count`＝1,009 | - | 新形式の再読登録簿が未作成 |
| 推移 | `social-samples/updates/fukushuto/2026-10-03,10-10/classified.json` | （公開JSONには無い） | `inject_tide_widget.py`（`refresh_adapters/fukushuto.py` が呼ぶ）。`inject_tide_widget.py` 内に旧ファイル名（`fukushuto_hermes_prev_20260714_v2.json` 等）の設定も残る | 比較対象の日付は回ごとの自動。論点は `fukushuto_taxonomy` から「その他」を除く |
| 事実確認（主張） | `data/fukushuto_claim_posts.json`（投稿ID）、`data/verification/fukushuto-claims.json` | 公開JSON `claim_verification`、`PLANET_DATA.claims` | `build_fukushuto_process_sections.py`（`FACT_CHECK_START/END`） | 判定文・出典の文章は検証データに手書き。**件数は投稿IDから毎回数え直し**（重複なし） |
| 一次資料（本文用） | `quality/research/fukushuto-primary-sources.md`（人が読むメモ。機械は読まない） | 公開JSON `ocean_layer`、各検証JSONの出典欄 | 上記の各生成器 | **メモ本文と、検証JSON・`PLANET_DATA`・`configs/classroom/fukushuto.json` 内のURL・文言が別々に手入力**。確認日（8/31, 9/7, 10/3）はメモ側。`fukushuto-background.json` の出典は別管理 |
| 資料にしかない話 | `data/verification/fukushuto-sunk-continents.json` | 公開JSON `ocean_layer.sunk_continents[]` | `verify_ocean_layer.py` で検査、HTMLは `refresh_planet_section.py`／連動で描画 | 「集めた投稿での件数」「調べた範囲」の文が手書きで、母数（2,356）や正規表現の結果が**文中に手入力**。再照合は更新のたびに手作業 |
| 背景・制度 | `data/verification/fukushuto-background.json` | `fukushuto_connected.py` の `background_data()` が読む | `fukushuto_connected.py`、HTML内 `#bukatsu-background`（雛形側にも本文あり。**どちらが正かは未確認**） | 確認日2026-09-12。経緯に「2020年11月」「2026年9月確認」とあり、更新時に手で直す |
| 横断整理 | `data/verification/fukushuto-editorial.json` | 公開JSON `editorial_summary` | `refresh_planet_section.py` | 文中の％・件数（賛成27.7%、反対59.7%、75.5%、83.3%、41.1%、189件、109件、4.6%、2,356件）が**手入力**。2026-10-03時点のまま。10/10の件数で再計算していない可能性（**未確認**） |
| 現在地・候補地・FAQ・問いタブ | 無し（一次資料のURLと文言をコードに直書き） | - | `fukushuto_search_entry.py`（`FAQS`、`ENTRY_TOPICS`、`CANDIDATE_REGIONS`、`render()`）。件数だけ引数 `opinions` | **更新の仕組みが無い**。「2026年10月3日確認」「10月16日まで意見募集」「10月30日施行予定」「国の指定0」が直書き。FAQのJSON-LDにも同文 |
| 投稿URL | 正典の `url`／`tweet_id` | - | 論点別14件：`fukushuto_issue_media.py` の `MEDIA`（手入力）。事実確認の例：`fukushuto_claim_posts.json`。視認できる異なるXリンクは18件（14＋4） | 同じ14件が論点別セクションと連動パネルの両方に出る（出所は1つ）。MEDIA は更新回で自動更新されない |
| 授業内容 | `configs/classroom/fukushuto.json` | - | 共通の授業節生成 | 手書き。1〜3の理由に論点リンクが付く |
| 投票の定義 | `fukushuto_taxonomy.py`、`supabase/functions/cast-vote/index.ts` | - | HTML内 `VOTE_ISSUES`／`V2I`／`STANCES` | **変更不可**（既存の票の意味が変わる）。リフォーム中も順序を維持 |
| 出所の登録 | `configs/fukushuto-reaction-map.json` の `number_provenance`／`issue_counts` | - | `verify_number_provenance.py` が照合 | 旧2D時代の `vote_labels` `category_order` 等が残る（現在のページでは未使用の可能性。**未確認**） |

生成の通し順（`scripts/refresh_adapters/fukushuto.py`）：候補JSON → `build_fukushuto_arena.py` → `build_fukushuto_process_sections.py` → `_apply_tide`（`inject_tide_widget.py`）を2回実行し、2回目に差分が出ないことを検査。投票互換性（21通り）と保護タグの個数も検査する。仕上げは `build_fukushuto_arena.py --public-counts-only`。

## 4. このテーマならではの疑問の候補

**検索ツール（ラッコキーワード・キーワードプランナー・Trends・Search Console）は使っていない。以下はすべて原稿と論点からの推測で、検索需要の裏付けは無い。**

### 4-1 既存の検索入口部品に入っているもの（先に記載）

`fukushuto_search_entry.py` のFAQ6問：①副首都法はもう成立している？ ②副首都は大阪に決まった？ ③副首都はいつ決まる？ ④首都中枢機能代替地域と副首都は同じ？ ⑤大阪都構想と副首都法は同じ制度？ ⑥副首都の整備費は4兆〜7.5兆円？
問いタブ4つ：何が変わる？／候補地は？／都構想との関係は？／費用はいくら？
ページのtitleは「副首都はいつ・どこに決まる？大阪の指定状況と法案の問題点」。

### 4-2 追加で挙がる候補（推測）

| 番号 | 疑問 | 推測の根拠（原稿のどこ） | 答えの置き場所 |
|---|---|---|---|
| Q1 | 副首都とは何か（首都との違い、何をする制度か） | 背景「何が、どこまで進んでいるのか」の定義、論点「定義・中身」332件 | 冒頭の短答（既存の「何が変わる？」と近い） |
| Q2 | 副首都に手を挙げている都道府県はどこか（福岡・愛知・北海道など） | 候補地8件、論点「候補地」538件 | 冒頭（既存の候補地一覧を前に出す） |
| Q3 | なぜ大阪が有力と言われるのか、「大阪ありき」とは | 議論の中心677件、資料にしかない話の2016年質問 | 論点「都構想・維新」 |
| Q4 | 副首都が必要な理由と、反対の理由は何か | 立場の内訳、授業節の賛否理由3つずつ | 全体像→論点 |
| Q5 | 法案はどんな問題点が指摘されているか | 既存の入口2「問題点は何？」3カード | 冒頭→論点 |
| Q6 | 南海トラフの地震で大阪は大丈夫か | 防災の理由区分で最大（158件）、候補地の「大阪は南海トラフで不適」123件 | 論点「防災・災害」「候補地」 |
| Q7 | 副首都の費用はいくら、誰が負担するのか | 費用4〜7.5兆円の事実確認、予算314億円の資料 | 論点「費用・財源」（FAQにあり） |
| Q8 | 副首都法はどういう採決で成立したか（賛成123・反対121、附帯決議） | 事実確認②③ | 論点「定義・中身」・事実確認 |

## 5. 部活動と違う点・判断が必要な点

| 番号 | 論点 | 内容 | 私ならこうする |
|---|---|---|---|
| J1 | 論点が7つで、再読データが5論点だけ | 部活動の論点数との比較は未確認。都構想・維新（677件、最大の山）と定義・中身（332件）に理由区分が無く、最大の山で「理由」を見せられない。新形式の再読登録簿も無い（`reread_registry: false`） | まず新ページは「理由は5論点のみ公開、2論点は未公開と明記」で設計し、都構想・維新の再読を別工程に切り出す |
| J2 | 雛形が現行HTMLそのもの | 生成器が公開HTMLを雛形にして区間だけ差し替える。手順書は「公開HTMLを入力にしない」前提。新デザインでは雛形ごと作り替えるため、手書き文言（H1, T5, A8, B6, D5, D7）の置き場所を決める必要あり | 手書き文言を設定ファイルに出し、新テンプレートから全生成する形にする。工数は大きい |
| J3 | 検索入口部品の更新の仕組みが無い | 現在地・候補地8件・FAQ・問いタブが `fukushuto_search_entry.py` に直書き（日付は10月3日のまま）。10月19日の次回更新でも自動では変わらない | 候補地と現在地を検証データ（JSON）へ移し、確認日つきで更新できるようにする |
| J4 | 投稿の埋め込み | 14件（7論点×2）が固定の `MEDIA` 定数。埋め込みはクリックで読み込み、元リンク付きで既に実装済み。表示不可時の代替表示は実機未確認。10/10に`article_usable: false`が10件あり、代表投稿の選び直しルールが必要 | 埋め込みは現行方式を踏襲し、選定を正典の `article_usable` と連動させる |
| J5 | 他テーマと共有しているスクリプト | `refresh_planet_section.py`、`inject_tide_widget.py`、`apply_theme_design.py`、`build_planet_data.py`、`research_conditions.py`、`build_public_registry.py`、多数の `verify_*.py`、`topic-modern.css/js`、`theme-design.css/js` は複数テーマ共通。fukushuto専用は `fukushuto_*.py` と `build_fukushuto_*.py` | 共通部品は触らず、専用側で完結させる。共通に手を入れる場合は他テーマの再生成差分を確認する |
| J6 | 文言と数字の食い違い | 「6つの論点」（実際は7）。横断整理の％が10/3時点のまま。再読ファイルの`population`が1681のまま。資料メモの確認日が10/3で止まっている | 新ページ作成と同時に直す。数字は生成側から出す |
| J7 | 事実確認・資料の薄さ | 事実確認5主張のうち1主張（AI試算2兆円）は一次資料を特定できず「裏が取れない」のまま。附帯決議の主張は、決議の逐語全文の確認が会議録の公開待ちだった（themes/fukushuto.md 2026-08-25の記述。現在の公開状況は未確認）。一次資料は法令・国会・自治体が中心で、費用・防災の資料は薄い（資料メモ「確認できなかったこと」節あり、中身は未精査） | 資料メモの再確認（primary-researchスキル）を新ページ作成前に行うか判断が必要 |
| J8 | 進捗表示（探ったところ0/18）・クイズ・投票の扱い | 新ページで地点数が変わる。投票の21通りは変更不可 | 投票は維持。進捗表示とクイズは新構成で主役でなければ縮小 |
| J9 | 日付の重なり | 次回収集は2026-10-19。リニューアルと更新が重なると、どちらかが上書きする恐れ | リニューアル公開は10/19の更新前か後かを先に決める |

上位3つ：**J1（最大の山に理由データが無い）**、**J2（雛形が現行HTML）**、**J3（検索入口が手入力で更新されない）**。

## 6. 読めなかったもの・確認していないもの

- 検索根拠（ラッコキーワード、キーワードプランナー、Google Trends、Search Console）：**今回は範囲外のため未実施。4節は推測**。
- `docs/topic-modern.js/css`、`docs/theme-design.js/css`、`docs/fukushuto-connected*.js/css`、`docs/fukushuto-search-entry.js/css` の中身：ファイル名と役割だけ把握。クイズ・進捗表示の描画元は未確認（`topic-modern.js` と推測）。
- `scripts/build_fukushuto_arena.py`（1,093行）と `fukushuto_connected*.py` の全文：docstring・定数・呼び出し関係のみ。入口2（A8）と「背景」節（D9）の本文の生成元はコード上で未特定。
- `themes/fukushuto.md`：各段落の冒頭400字までと末尾6段落のみ。途中の記述に抜けがあり得る。
- `supabase/functions/cast-vote/index.ts`、`tests/` の内容、`quality/reviews/` の個別ファイル（監査記録・9月の20例比較など）：未読。
- `quality/research/fukushuto-primary-sources.md`：見出し、確認日、冒頭のみ。資料ごとの内容は未精査。「確認できなかったこと」の中身は未読。
- 各外部リンクの現在の到達性（HTTP応答）は未確認。リンク総数も未集計。
- 事実確認の該当投稿26件の内訳（`fukushuto-claims.json` の26）と、検証JSON内の件数の完全照合は未実施（ページ表示の12・8・3・2・1を採用）。
- 検査スクリプト（`verify_*`、unittest）は実行していない。数字は正典と公開JSONを自分で数えた値で、両者の一致のみ確認した。
- 横断整理の％（B5）が10/10の件数と合うかの再計算は未実施。
- 375px・PCでの実機表示は確認していない（ファイルの読み取りのみ）。
- 部活動の完成形（`docs/bukatsu-chiiki-reaction-map.html`、`quality/designs/2026-10-10-bukatsu-production-candidate.md`）は今回開いていない。したがって部活動との件数・論点数の比較は未確認。
