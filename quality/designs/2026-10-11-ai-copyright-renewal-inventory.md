# 生成AIと著作権（ai-copyright）リニューアル準備：棚卸しと内容対応表

作成日 2026-10-11。手順書 `23_テーマ別リニューアル移植手順_2026-10-10.md` の手順1（棚卸し）と手順3（内容対応表・データ対応表）に当たる。
HTMLの試作、スクリプト変更、検索ツール（ラッコキーワード等）の調査はしていない。「新ページでの配置先」は提案であり、決定ではない。
読んだ現行ページは作業ツリーの `docs/ai-copyright-reaction-map.html`（456KB、2026-10-06時点の数字。作業ツリーの再生成分を含む）。

## 1. 現状の要約

- 件数：収集5,175件、意見3,353件（`docs/data/themes/ai-copyright.json` の `collected_count` / `opinion_count`。正典 `social-samples/ai-copyright_hermes_classified.json` は5,175行、`classification.is_opinion` が真で3,353行で一致）。
- 論点（`issues[].count`、同JSON）：学習データ・無断利用841／利用者モラル・倫理818／法制度・規制整備643／クリエイター保護・権利409／その他260／AI生成物の権利・創作性243／技術競争・推進139。名前付き6論点＋「その他」で合計3,353。
- 立場（`issues[].stances[]` の合計、ページの「立場ごとの内訳」と一致）：規制・制限強化支持1,878（56%）／中立・情報712（21%）／推進・活用支持763（23%）。
- 取得期間 2026-06-22〜2026-10-06（`collection_period`）。最終更新 2026-10-06（`updated_on`、`THEMES.yaml` の `updated_at`）。次回収集予定 2026-10-16（`THEMES.yaml` の `collect_at`）。公開日 2026-06-24。
- 再読（理由区分）データあり：`data/ai-copyright_issues-reread.json`（旧形式。`data/verification/reread/ai-copyright.json` は無い）。5論点が対象で、学習データ841（区分12）／クリエイター保護409（10）／その他260（7）／AI生成物243（7）／技術競争・推進139（6）＝計1,892件、未読0（ページ内 `PLANET_DATA.reread_summary` も1,892一致）。**法制度・規制整備643と利用者モラル・倫理818（計1,461件）は再読データなし。**
- 再読の経緯（`themes/ai-copyright.md`）：2026-09-13に1,465件を読了、10/07に91件を外し、10/10の追い読みで518件を追加。10/10分は作業ツリーで再生成済みで、本番反映はオーナー承認待ちと記録されている。本番に出ているかは未確認。
- 一次資料メモ `quality/research/ai-copyright-primary-sources.md`（288行、資料A〜L）の確認日：2026-08-30（8件）／08-31（12件）／09-07（3件、資料J・K・L）。最新は2026-09-07。ページ内の別の確認日：資料照合6件 2026-09-19、背景年表・制度確認 2026-09-19、検索入口 2026-09-28、沈んだ大陸4件 2026-10-07。
- 意見の推移：8/3〜10/6の9回分あり（立場3×論点6、画像4枚 `docs/images/trend/ai-copyright-*.png`）。
- 分類の注意：9/5の回458件は2026-10-07に現行AIで判定し直して置換済み（`data/verification/rejudge/ai-copyright-wave-20260905-rejudge-20261007.json`）。

## 2. 棚卸し表（現行ページを上から順に）

出所の略称：「JSON」＝`docs/data/themes/ai-copyright.json`（正典 `social-samples/ai-copyright_hermes_classified.json` から `scripts/build_public_registry.py` 系が生成。生成元の細部は未確認）、「PLANET」＝ページ内 `PLANET_DATA`（`scripts/refresh_planet_section.py` が公開JSONから再生成）、「背景JSON」＝`data/verification/ai-copyright-background.json`（手書き・編集部AI作成）。

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | head/メタ | title「生成AIと著作権は何が問題？規制賛成・反対の論点」、description（「6つの論点」と記載）、OGP（`docs/ogp/ai-copyright.png`）、canonical | `configs/theme-seo.json`（`configs/ai-copyright-reaction-map.json` にも旧版の題名あり。どちらが現行かは未確認） | 冒頭（URL・計測タグ・OGPは維持） | - |
| 2 | ヘッダー/ナビ | サイト共通ヘッダー、パンくず（トップ＞テック・著作権） | 共通テンプレート | 冒頭 | - |
| 3 | ヒーロー | h1、副題「創作の権利を守るため、生成AIにはどこまでルールが必要か？」、意見3,353件、「議論の中心 841件」（学習データの無断利用を、どこまで認めるのか） | JSON + `scripts/issue_card_counts.py` / `refresh_planet_section.py` の同期。副題は手書き | 冒頭 | - |
| 4 | 検索入口 `#aic-search-entry` | 3論点（学習データ／AI生成物／クリエイター）の切替と、3つの疑問ボタン（無断学習は違法？／30条の4とは？／学習データは開示される？）。短答と文化庁リンク、確認日「2026年9月28日」 | `scripts/templates/ai_copyright_search_entry.html`＋`scripts/ai_copyright_search_entry.py`＋`docs/ai-copyright-connected-page.js`（手書きテンプレート。確認日は直書き） | 冒頭（疑問と短答。3論点のみで他4論点が無い点は要設計） | - |
| 5 | 立場の内訳 `#stance-glance` | 「規制派は推進派の2.5倍」、規制1,878／中立712／推進763、割合56/21/23%、立場ボタン（山と連動） | `scripts/build_ai_copyright_arena.py`（公開JSONから貼り直し）。見出しの「2.5倍」は文字として生成されるか手書きか未確認 | 意見の全体像 | - |
| 6 | 調査条件 `.research-conditions` | 元データ=Yahooリアルタイム検索5,175件、取得期間、世論調査ではない旨 | `build_ai_copyright_arena.py --public-counts-only` | 意見の全体像（集計の限界） | - |
| 7 | 背景 `#bukatsu-background` | 定義（30条の4・法改正はされていない）、なぜ始まったか2段落、年表6件（2024-03-15 文化庁考え方／2024-05 内閣府中間とりまとめ／2025-06-04 AI法／2025-12-12 プリンシプル・コード案／2026-04-21・23 パブコメ結果とヒアリング／2026-06 知財推進計画2026）。確認日2026-09-19。idは部活動と共通のまま | 背景JSON（手書き。一次資料メモの資料B-2・C-2・C-4〜C-6・C-8・D・J・K・Lから起こした） | 背景（年表は開閉行）。定義の一文は冒頭の短答にも使える | - |
| 8 | 制度確認 `#bukatsu-check` | 「法律」と「任意のルール」を分けて確かめる。4項目：AI学習と著作権侵害／学習データの情報開示／2026年の著作権法改正／声・作風の保護。各に問い・答え・出典・分かっていないこと・注意 | 背景JSON `checklist`（手書き。論点idタグ無し） | 冒頭の短答候補＋背景。4項目とも疑問形で、冒頭の問い答えに最も近い | - |
| 9 | 反応マップ（山並み）`.planet-panel` | 7論点の山、面積=強い表現の数、件数と割合、立場フィルタ、マス目100個の割合表示、論点クリックで図解・立場・サブ分類・資料照合を表示 | PLANET（`scripts/build_planet_data.py`、`configs/planet/ai-copyright.yaml`、`refresh_planet_section.py`） | 意見の全体像（部活動と同じ山並み） | - |
| 10 | 山の中のサブ分類 | 論点ごとの内訳（学習データは12区分：無断学習は著作権侵害（一般）420／個人の作品保護・肖像権162／経済的搾取46／学習は合法出力が問題44／規制・法整備39／創作環境33／二重基準批判30／その他23／補償・opt-out19／透明性・開示13／人間の模倣と同等8／技術的対策4、ほか論点にも区分あり） | 再読 `data/ai-copyright_issues-reread.json` の `buckets`（5論点のみ）。法制度・モラルは無し | 論点別（理由）。法制度・モラルの2論点は「理由別は未公開」と明記 | - |
| 11 | 論点別の図解画像 | 7論点それぞれの図解（`gakushu-v2` ほか、`refresh_planet_section.py` の対応表に定義） | 画像は既存、紐付けは `refresh_planet_section.py` 597行付近 | 論点別 | - |
| 12 | 論点別の連動読書面（`<template>` 7個） | 論点を選ぶと理由・投稿例・資料照合・制度確認を差し替え表示 | `scripts/ai_copyright_connected_content.py` 生成 + `scripts/templates/ai_copyright_connected_bridge.js` | 論点別（新設計の中核） | - |
| 13 | JS無し用の論点別本文 `.landing-panel`（7、`#fb-ai-copyright-*`）＋ `nav#fallback-nav` | 各論点の説明、投稿例、資料照合（JS無しでも読める本文） | `refresh_planet_section.py` が生成 | 論点別（JSなしの本文として維持） | - |
| 14 | 一次資料クイズ | 「その主張、資料に当たるとどうなる？」6問 | `data/ai-copyright_claim_posts.json` + 公開JSON `claim_verification` | 論点別（資料照合） | - |
| 15 | 資料にあるのにSNSにない `#ocean` | 語られていない争点4件（廃棄・除去請求／パブリシティ権／電子透かし・来歴／robots.txt・オプトアウト）。件数はすべて0。意見3,353件が母数 | `data/verification/ai-copyright-sunk-continents.json`（手書き。母数 `sample_total_opinions` は2593のままの可能性あり、公開JSON側は3353。要確認） | 背景または論点別（資料にしかない話） | - |
| 16 | 地下水脈（2本） | 「政策対応が遅い」という共通の不満から立場が分かれる（公開JSON `veins`、`data/verification/ai-copyright-veins.json`）。ページ上の位置は山並み内で、独立の見出しは見つからなかった | 手書き（編集部AI） | 論点別（立場を超えた共通の心配） | - |
| 17 | 編集部の横断整理 `#editorial` | 5件：共通する前提／本当の対立（2件）／まだ分からないこと（2件）、論点の一覧、このページの見かた | `data/verification/ai-copyright-editorial.json`（手書き。2026-09-14） | 意見の全体像（読み方）。数字（37.4%、75.5%等）は手入力で重複 | - |
| 18 | 意見の推移 `#ai-copyright-trend`（`.update-dashboard`） | 立場と論点の9回分の推移、ひと目版・詳細版、画像ダウンロード、埋め込みコード、Xで投稿 | `scripts/build_trend_section.py`、`scripts/refresh_adapters/trend_support.py`、画像 `docs/images/trend/`（4枚） | 意見の全体像（推移） | - |
| 19 | 一次資料との照合 `#ai-copyright-audit` | 6つの言い分（無断学習は常に侵害／学習データ開示が必要／補償が必要／クリエイター保護が不十分／AI生成物に著作権／規制より技術革新）と原典の文言、判定（ズレ・事実など）、照合日2026年9月19日、出典リンク（cas.go.jp、bunka.go.jp、e-Gov） | 公開JSON `claim_verification`（正典は `data/ai-copyright_claim_posts.json` 手書き） | 論点別（資料照合） | - |
| 20 | 論点ごとのX投稿 `#issue-cards` | 7論点×2投稿＝14件の埋め込み。ID付き見出し（@名と一言）と件数バッジ、「↑地図へ戻る」 | `scripts/ai_copyright_issue_media.py` ＋ `scripts/x_embed.py`。投稿URLの選定は手書き。件数バッジは `scripts/sync_issue_counts.py` 等で更新 | 論点別（最大2件。開いたときに読み込み） | - |
| 21 | 授業・ディベート `.classroom-section` | 推進側・規制側の理由（各3程度、論点リンク付き）、確かめる一次資料、問いの例、使い方 | `configs/classroom/ai-copyright.json`（手書き） | 背景（授業で使う開閉行） | - |
| 22 | 編集・分析情報 `.article-trust` | 公開日、更新日、収集方法、検索語13語、意見率約64%、2026年7月の分類変動（78%→60%等）、モデル差の注意 | `configs/theme-seo.json` ほか。件数は同期、文章は手書き | 背景（方法と限界） | - |
| 23 | 判断の入口 `.copyright-entry` | 学習／生成／公開・販売の3場面の考え方と断り書き、根拠リンク2件（文化庁・内閣府） | `scripts/build_ai_copyright_arena.py`（手書き文面。他テーマに無い独自節） | 冒頭の短答の下、または背景。3場面は「疑問に答える」入口に使える | - |
| 24 | 投票 `#vote-section` | 論点投票（全2問：最も気になる論点21通りの組＝論点7×立場3と、賛否）、シェア、やり直し | ページ内スクリプト（`VOTE_TOPIC='ai-copyright-issue-stance-v1'` `VOTE_ISSUES` `STANCES`）。`refresh_adapters/ai_copyright.py` が定義不変を検査 | 配置は自由だが定義と保存先は変更不可 | - |
| 25 | 関連テーマ `#related-topics` | 憲法改正論議・自転車の青切符・部活動の地域移行 | 手書き/共通 | 末尾 | - |
| 26 | 詳細データ `#detail-data` | 分類別件数7、カテゴリ×検索クエリ表、カテゴリ×スタンス表（旧2D分類の語：著作権厳格保護…などの表。合計は168+34+13+27+9+88+136=475で、現行の3,353とは別の旧集計とみられる。未確認） | `build_ai_copyright_arena.py`。旧表は更新されていない可能性 | 背景（折りたたみ）。**旧表の整合は要確認。不要の可能性あり** | 旧集計の残りで現行件数と合わない疑い（要確認のため確定はしない） |
| 27 | 進捗表示 `#progress` | 「探ったところ 0/21」（予想2＋論点7＋争点4＋主張6＋共通の心配2）。ブラウザー保存のみ | `ai_copyright_connected.py` + 共通JS | 不要の可能性（部活動新デザインの扱いに合わせる） | 部活動の完成形に同機能があるかは今回未確認 |
| 28 | フッター | トップへ、運営者情報、調査・編集方法、お問い合わせ、プライバシー、免責、画像制作方針、応援 | 共通 | 末尾 | - |
| 29 | 計測・広告 | GA4（G-K10S4YCZFH）、AdSense（ca-pub-2542211932832864）、vote-store.js、X widgets.js | 共通 | 維持（個数を変えない） | - |
| 30 | ページ内リンク | `#fallback-nav`、`#fb-ai-copyright-*`（7）、`#issue-ai-copyright-*`（6、論点ごとのX投稿の見出しID）、`#ocean`、`#planet-block`、`#ai-copyright-trend-panel-stance`（推移の埋め込みコードが外部から参照） | 手書き/生成 | 既存URLのアンカーは残す | - |
| 31 | 外部リンク | cas.go.jp 22／bunka.go.jp 16／laws.e-gov.go.jp 11／kokkai.ndl.go.jp 2／x.com 14／docs.google.com 1（お問い合わせ）／buymeacoffee 1 | 背景JSON・照合・メモ | 論点別・背景 | - |
| 32 | 確認日（ページ内に出るもの） | 2026-09-19（照合・背景）／2026-09-28（検索入口）／2026-10-07（沈んだ大陸）／2026-10-06（更新） | 上記各JSON | 各所に維持 | - |

注：「不要」と書いた行は、新ページで置き場が見つからない場合の候補で、決定ではない。原稿の記述（行2〜32）は、h1/h2/h3、主要ブロック、リンク先ドメイン別件数まで確認した。本文の全文字は転記しておらず、各ブロックの細かな文言（検索入口の短答全文、資料照合6件の全文、授業節の全文など）は新ページ作成時に現行HTMLから再抽出が必要。

## 3. データ対応表

流れ：正典 `social-samples/ai-copyright_hermes_classified.json` → 公開JSON（`data/public/themes/ai-copyright.json`、`docs/data/themes/ai-copyright.json`） → HTML。生成の司令は `scripts/refresh_adapters/ai_copyright.py`（`build` が `build_ai_copyright_arena.py` を2回走らせて差分ゼロを確認、`finalize` が `build_ai_copyright_arena.py --public-counts-only`→`refresh_planet_section.py --topic ai-copyright --for-docs`→`build_ai_copyright_arena.py --skip-issue-counts` の順）。`scripts/ai_copyright_connected.py` が連動表示を貼り、`trend_support.render_trend` が推移を貼る。

| 項目 | 正典（手入力の場所） | 公開JSONのキー | HTMLへの生成スクリプト | 手入力の重複・注意 |
|---|---|---|---|---|
| 件数（収集・意見） | 正典の `is_opinion` | `collected_count` `opinion_count` | `build_ai_copyright_arena.py --public-counts-only`、`refresh_planet_section.py` | 「3,353」が22回、「5175」「5,175」が複数。「約64%」「13語」「公開中の10テーマ」は `configs/theme-seo.json` 側の手書き。64.8%は「約64%」より約65%が近い |
| 論点別件数 | `main_issue` | `issues[].count` | `refresh_planet_section.py`、`sync_issue_counts.py`/`issue_card_counts.py`（論点ごとのX投稿の件数バッジ） | 検索入口、詳細データ、授業節にも件数が出る。過去に更新漏れ（2026-09-20）あり |
| 立場 | `stance` | `issues[].stances[]` | `build_ai_copyright_arena.py`（立場の内訳）、`refresh_planet_section.py` | 「2.5倍」「56/21/23%」が文字になっている。ズレ検査は `verify_number_provenance.py` が担当 |
| 強い表現の割合 | `intensity` | `issues[].intensities` | `build_planet_data.py` | - |
| 理由区分（再読） | `data/ai-copyright_issues-reread.json`（手読みの記録。5論点のみ） | 公開JSONには無し。PLANET側へ接続 | `build_planet_data.py`（旧形式の読み込み） | 他テーマは `data/verification/reread/{テーマ}.json` の新形式。本テーマだけ旧形式。`configs/planet/ai-copyright.yaml` の `reread_registry: false` |
| 推移 | 累積正典＋収集回ごとの保存（`social-samples/updates/ai-copyright/{日付}/`） | 公開JSONには無し | `build_trend_section.py`、`refresh_adapters/trend_support.py`（ページと画像4枚を同時生成）、`build_trend_images.py` | 文章は生成。補足の注意書き（モデル差）は手書きの可能性（`check_model_break` が止める） |
| 一次資料（論点別） | `quality/research/ai-copyright-primary-sources.md`（人が確認） | `claim_verification.claims[].sources[]` | `data/ai-copyright_claim_posts.json`（手書き）→公開JSON | メモ本文、claim_posts、背景JSON、授業設定の4か所に似た出典が散る。メモの確認日と照合日（9/19）が別管理 |
| 資料照合6件 | `data/ai-copyright_claim_posts.json`（curated 2026-09-13） | `claim_verification` | `build_planet_data.py` ほか | 照合日はJSON `checked_on` 2026-09-19 |
| 背景・年表・制度確認 | `data/verification/ai-copyright-background.json` | 公開JSONには無し | `ai_copyright_connected.py` / `ai_copyright_connected_content.py` | 手書き一箇所。注意：内容はメモ資料J・K・Lと重複 |
| 語られていない争点 | `data/verification/ai-copyright-sunk-continents.json` | `ocean_layer.sunk_continents` | `refresh_planet_section.py` | `sample_total_opinions` がファイル内は2593、公開JSONの `sns_base` は3353。要確認 |
| 編集部の横断整理 | `data/verification/ai-copyright-editorial.json` | `editorial_summary` | `refresh_planet_section.py` | 37.4%・75.5%などの数字が文章内に手入力で、件数更新で自動では動かない可能性が高い（9/14作成のまま） |
| 投稿URL（論点ごとのX） | 手選定（14件） | 公開JSONには無し。ページに直書き | `ai_copyright_issue_media.py`、`x_embed.py` | `tests/test_ai_copyright_issue_media.py` が判定し直しで論点違いになる事故を検出 |
| 投票定義 | ページ内 | - | `refresh_adapters/ai_copyright.py` が不変を検査 | 21通りの組。変更不可 |
| 日付（更新日） | `THEMES.yaml` の `updated_at` | `updated_on` | `refresh_topic.py` 系 | ページ内に20回以上（「2026年10月6日」等） |

## 4. このテーマならではの疑問の候補（原稿からの推測。検索ツールは未使用で、検索量の裏付けは無い）

1. 無断でAIに学習させるのは違法か（原稿の検索入口・制度確認・資料照合1が答える）。
2. 著作権法30条の4とは何か、どこまで許されるか（検索入口に既出）。
3. AIで作った画像・文章に著作権はあるか（論点「AI生成物の権利・創作性」、資料照合5）。
4. AI事業者は学習に使ったデータを公開する義務があるのか（検索入口・制度確認2）。
5. 自分の絵・声・作風が真似されたとき、どんな手段があるか（沈んだ大陸4件、制度確認4、メモ資料K・L）。
6. 日本は規制を強めるのか、緩めるのか。いま法改正はあるのか（背景の定義「法改正はされていない」、制度確認3、年表）。
7. 学習は合法でも、似た作品を出力すると侵害になるのか（判断の入口の3場面、論点「学習は合法、出力が問題」44件）。
8. 賛成派・反対派はそれぞれ何を理由にしているのか（山並み、授業節の両側の理由）。

## 5. 部活動と違う点・判断が必要な点

1. **論点が7つ（名前付き6＋その他）で、しかも大きさが偏る**（最大841、最小139）。部活動の論点数との差は未確認。山並みに「その他」260件（7.8%）を残すか、疑問の入口をどの論点に紐づけるかを決める必要がある。検索入口は現在3論点のみ。
2. **再読（理由別）データの欠けが2論点・1,461件（43.6%）**。法制度・規制整備と利用者モラル・倫理が最大級の論点なのに理由区分が無く、「未公開」と書く運用では目立つ。追い読みするか、未公開と明記するか。さらに再読の形式が旧形式（`data/ai-copyright_issues-reread.json`）で、他テーマの `data/verification/reread/` と違うため、共通部品の新ページへ載せるには変換が要る。
3. **一次資料の最終確認が2026-09-07で、約1か月前**。資料は法制度中心（文化庁・内閣府・e-Gov・国会会議録）で、論点別では学習データに14件（資料A〜C-11）、クリエイター2件、法制度1件、技術競争1件、利用者モラル1件、AI生成物1件と偏る（メモ見出しの数。ほかに全体向けの資料J・K・L）。利用者モラルや技術競争は薄い。`primary-research` スキルでの再調査を、新ページ公開の前にするか。
4. 投稿埋め込み：現行は論点ごとに2件×7＝14件でX埋め込み（`platform.twitter.com/widgets.js`）。新手順の「開いたときに読み込み、失敗時もリンクを残す」へ変える場合、`ai_copyright_issue_media.py` と `x_embed.py` の修正が必要。X投稿の著作権・引用の扱いは変更しない前提。
5. **共有スクリプト**：`refresh_planet_section.py`、`build_planet_data.py`、`build_trend_section.py`、`trend_support.py`、`x_embed.py`、`sync_issue_counts.py` は他テーマと共有。ai-copyright専用なのは `ai_copyright_*.py`、`build_ai_copyright_arena.py`、`refresh_adapters/ai_copyright.py`。共有部品を直すと他9テーマの再生成に影響するため、部活動の完成形で共通化された部品の範囲と、今回専用に分ける範囲を決める。
6. 「連動表示」（課題77）で既に再配置済みのため、HTMLの再編は既存の貼り付け方式（`AI_COPYRIGHT_CONNECTED_START/END` の目印）との整合が要る。`ai_copyright_connected.py` の説明文は「理由別X投稿は理由別の投稿データが無いため対象外」とあるが、現在は5論点で理由データがある（説明が古い）。
7. 判定し直し（9/5分）の後も、分類モデルの違いによる傾向差がある。推移の注意書きの扱い、意見率約64%（公開10テーマで低い部類）をどう見せるか。
8. 「投票」は定義変更不可（21通り）で、新ページでも同じ集計に載せる必要がある。
9. 古い値の残り：詳細データの旧表、沈んだ大陸4件の母数、編集部の横断整理の数字。新ページで再利用する前に正典と照合が必要。

## 6. 読めなかったもの・確認していないもの

- 検索根拠（ラッコキーワード、Googleキーワードプランナー、Google Trends、Search Console）は手順書の対象外のため未取得。疑問候補に検索量の裏付けは無い。
- 現行ページの全文転記はしていない。見出し、リンクのドメイン別件数、各ブロックの冒頭〜1,400字程度を読んだ。資料照合6件・授業節・沈んだ大陸4件・検索入口の全文は未読。
- 本番（main）のページとの差は未確認。作業ツリーのページだけを読んだ。10/10の追い読み（518件）が本番に反映済みかも未確認。
- `scripts/` の中身は、`refresh_adapters/ai_copyright.py` と `ai_copyright_connected.py` の冒頭以外は読んでいない。表の「生成スクリプト」の一部（立場の内訳「2.5倍」の出所、論点ごとのX投稿の選定箇所、公開JSONの生成スクリプトの正式名）は文字列検索による推定で、断定していない。
- `configs/theme-seo.json` と `configs/ai-copyright-reaction-map.json` のどちらが現行の題名・説明か、`data/public/themes/ai-copyright.json` を作る具体的なスクリプト名は未確認。
- `quality/reviews/` と `quality/designs/` の過去記録（課題77の内容確定書など）は冒頭のみ。部活動の完成形（`docs/bukatsu-chiiki-reaction-map.html`、`quality/designs/2026-10-10-bukatsu-production-candidate.md`）は今回読んでいない。部活動との比較は手順書の記述とパイプライン構造からの推定で、論点数などの部活動側の値は未確認。
- X投稿14件の表示可否（削除・非公開になっていないか）は未確認。出典リンクの生死も未確認。
- 一次資料メモの全文（資料A〜L）は見出しと確認日のみ確認。
