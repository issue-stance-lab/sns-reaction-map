# 自転車の青切符導入（bike-blue-ticket）リニューアル準備 棚卸しと内容対応表

作成日 2026-10-11 / 対象ブランチ task/renew-bike-blue-ticket / 手順書 `23_テーマ別リニューアル移植手順_2026-10-10.md` の手順1・3に当たる。
範囲外：HTML試作、スクリプト変更、検索ツールの調査（検索語の数字は既存の課題97の記録を引用するだけで、今回は取り直していない）。

## 1. 現状の要約

- 収集 585件、意見 415件（意見でない170件は母数から除外）。出所：`social-samples/bike-blue-ticket_2d_classified.json`（全585件、`is_opinion` が true=415）。公開JSON `docs/data/themes/bike-blue-ticket.json` の `collected_count` 585・`opinion_count` 415 と一致。
- 論点は6つ（`issues[]` の `label` と `count`、正典の `classification.main_issue` で数え直して一致）：取締り強化賛成85／インフラ整備優先67／ルール曖昧・不信66／免許制要求33／車道走行への不安21／その他143。主要5論点の合計は272。
- 立場は3区分（正典 `classification.stance`）：賛成（取締り強化支持）94／反対（インフラ・制度優先）205／どちらでもない116。
- 強さ（intensity）は low/medium/high の3段階（公開JSON `issues[].intensities`）。
- 最終更新日 2026-09-28（公開JSON `updated_on`、THEMES.yaml `updated_at`）。収集期間 2026-06-27〜2026-09-28。次回収集予定 2026-10-12（THEMES.yaml `collect_at`）。公開日 2026-06-28。
- 再読（理由区分）データ：あり、6論点すべてに全件。`data/bike-blue-ticket_issues-reread.json` の論点別 `buckets` 合計が 85/67/21/33/66/143 で意見415件と完全に一致。理由区分の数は論点ごとに 16/7/9/9/5/24。反対側だけの旧5区分もあり（`data/bike-blue-ticket_opposition_reread.json`、青切符では足りない15／対象と順番に異議48／走る場所がない35／警察の運用への不信39／制度そのものに反対68、計205）。
- 再読の質：`data/verification/reread/bike-blue-ticket.json` は585記録のうち379件が `evidence_quality=verified`（読了日あり）、206件が `legacy`（読了日なし。旧記録の日付は全件の再読日を保証しない、と `date_caveat` に明記）。
- 一次資料メモ：`quality/research/bike-blue-ticket-primary-sources.md`、資料22件、確認日は 2026-08-30（13件）・2026-08-31（8件）、2026-09-07に政令別表第六で反則金額を追加確認（`quality/research/status.yaml` の `last_verified` 2026-09-07）。ページ側の制度確認は2026-09-06、資料照合（7主張）は2026-09-29。
- 推移（潮目）：9月12日（19件）→9月28日（35件）の賛否構成比。「賛成が16.8ポイント減少」と表示。

## 2. 棚卸し表（現行ページ `docs/bike-blue-ticket-reaction-map.html` 3,517行、上から順）

配置先の凡例：冒頭／全体像（意見の全体像）／論点別／背景／不要。出所の「手書き」はテンプレートまたはHTML内の直書き。

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | メタ・SEO | title/OGP「自転車の青切符で何が変わる？対象と賛否」、canonical、OGP画像 ogp/bike-blue-ticket.png | `scripts/seo/apply_meta_tags.py`（SEO_META）＋`configs/bike-blue-ticket-reaction-map.json` | 冒頭（維持） | - |
| 2 | 構造化データ | Article JSON-LD | `scripts/seo/apply_theme_trust.py`（ARTICLE_JSON_LD） | 維持 | - |
| 3 | 計測・広告 | GA4（G-K10S4YCZFH）、AdSense（ca-pub-2542211932832864）、vote-store.js | 手書き（保護対象） | 維持（adapterが個数を検査） | - |
| 4 | 進み具合の帯 | 「探ったところ N」（質問・山・クイズ操作数） | `scripts/bike_blue_ticket_connected.py` ほか | 全体像（要否を設計時に判断） | 操作数の意味が新構成と合うか未確認 |
| 5 | ヘッダー | トップ、分類「交通ルール・日常論争」 | 共通部品 | 冒頭 | - |
| 6 | 件数表示 | 「SNSの意見 415件」 | `scripts/apply_theme_design.py`（THEME_COUNT） | 冒頭 | - |
| 7 | H1・副題 | 「自転車の青切符で何が変わる？対象と賛否」「危険運転を減らす青切符か、道路整備が追いつかないままの罰則強化か？」 | 手書き（configのsubtitleと別に直書き） | 冒頭 | - |
| 8 | リード文 | 585件のうち意見415件を主要5論点272件に分類、残り143件はその他。世論調査ではない | `scripts/sync_issue_counts.py`（数字部分） | 冒頭 | - |
| 9 | 議論の中心 | 取締り強化賛成 85件「危険運転を減らすには、取締りを強めるべきか」 | `scripts/sync_issue_counts.py` | 全体像 | - |
| 10 | ヒーロー画像 | images/topics/bike-blue-ticket/bike-blue-ticket-hero.webp | 手書き（画像資産） | 冒頭 | - |
| 11 | 検索入口の見出し | 「まず、対象年齢と反則金を確認」、山なみへの導線リンク（#section）2か所 | `scripts/templates/bike_blue_ticket_search_entry.html` | 冒頭 | - |
| 12 | 年齢チェック | 13歳未満／13〜15歳／16歳以上の3択で短答が切り替わる。警察庁「自転車の新しい制度」リンク | 同テンプレート＋`docs/bike-blue-ticket-search-entry.js`（`ageAnswers` 直書き） | 冒頭 | - |
| 13 | 反則金検索 | 違反名・金額で主な10例を絞り込み（3,000/5,000/6,000/7,000/12,000円）。各行に警察庁・東京都・e-Govリンク（3機関） | 同テンプレート（手書き表） | 冒頭 | - |
| 14 | 注記 | 「主な例であり全件ではなく、違反があれば必ず即交付ではない」 | 同テンプレート | 冒頭 | - |
| 15 | FAQ 4問 | 大人は歩道を走れる？／手信号は新ルール？／反則金はどこで支払う？／現場で現金を求められたら？（警察庁リンク各1） | 同テンプレート | 冒頭（短答） | - |
| 16 | 立場の内訳 | 見出し「最多は取り締まりより整備を求める声」、賛成94(22.7%)・反対205(49.4%)・どちらでもない116の帯、近い考えを押すと立場別の説明、元データ585件・期間・世論調査ではない注記 | `scripts/build_bike_arena.py`（STANCE_GLANCE） | 全体像 | - |
| 17 | 背景「何が、どこまで進んでいるのか」 | 制度の概要、なぜ始まったか（警察庁：死亡・重傷事故の約4分の3で自転車側にも違反）、第3次自転車活用推進計画（9,841km→12,000km） | 手書き（id が `bukatsu-background` のまま。部活動ページからの流用名） | 背景 | - |
| 18 | 年表 | 2023年8月〜2026年5月29日の6項目（法改正、施行、国会質疑、1か月運用状況、閣議決定） | 手書き。`data/verification/bike-blue-ticket-background.json`（timeline 6件、確認日2026-09-06）に同内容 | 背景 | - |
| 19 | 制度の確認 4項目＋未確認 | 対象／運用の実際／走る場所／運転免許との関係、および「113種類・65項目」は未確認 | 手書き（id `bukatsu-check`）。論点別の読書面にも同文が重複 | 背景＋論点別（重複解消） | - |
| 20 | 山なみマップ | 幅＝意見数、高さ＝強い表現の割合、色＝最多の立場。論点6つ、立場フィルター4モード、マス目100個の割合表示 | `scripts/refresh_planet_section.py`（PLANET_SECTION、`#planet-data`） | 全体像 | - |
| 21 | 論点パネル×6 | 各論点の件数・割合・強い表現の割合、立場内訳、立場別シェア、中身（理由区分の件数一覧）、図解画像1枚（infographic-wide-*） | `refresh_planet_section.py`＋`scripts/bike_blue_ticket_connected_content.py`（論点別読書面） | 論点別 | - |
| 22 | 一次資料との照合 | 7主張の判定（資料どおり／少しずれる／裏が取れない等）。取締り強化2、インフラ0、ルール曖昧5（LUUP・6,000円・16歳・歩道・113種類）、免許制1、車道不安1（重複掲載あり） | `scripts/build_bike_verification.py` と `data/verification/bike-blue-ticket-claims.json`（64件の該当投稿）→公開JSON `claim_verification` | 論点別 | - |
| 23 | 資料にあるのにSNSにないこと | 4件（運用ルール、導入1か月実績2,147件対13万5,855件、側方通過、インフラ整備計画） | `data/verification/bike-blue-ticket-sunk-continents.json`←`refresh_adapters/bike.py` | 論点別（1件は全体共通） | - |
| 24 | 編集部の横断整理 | 共通する前提／本当の対立／まだ分からないこと（5所見） | `data/verification/bike-blue-ticket-editorial.json`→公開JSON `editorial_summary` | 全体像 | - |
| 25 | 論点一覧（図が使えない時の表示） | 6論点の件数・割合のリンク一覧、論点ごとの静的パネル | `refresh_planet_section.py` | 全体像（JSなし本文として維持） | - |
| 26 | 一次資料クイズ | 主張を資料に当てるクイズ | `#planet-data` の claims | 論点別 | 要否を設計時に判断 |
| 27 | 論点の一覧（押すと切り替え）＋ページの見かた | 山の読み方説明 | `refresh_planet_section.py` | 全体像 | - |
| 28 | 推移（世論の潮目） | 9/12→9/28、賛成16.8ポイント減、前回19件・今回35件、立場／論点の2表示、再生ボタン、注記 | `scripts/inject_tide_widget.py`（共通）＋`refresh_adapters/bike.py` の `_apply_tide` | 全体像 | - |
| 29 | 論点ごとのX投稿 | 6論点×2件=12投稿の埋め込み＋出典リンク（x-embed-fallback） | `scripts/bike_issue_media.py`（正典の `article_usable` かつ `risk=low` から選定） | 論点別 | - |
| 30 | 投票 | 「一番気になる論点は？」（論点6つ×立場3つ=18選択肢）。TOPIC `bike-blue-ticket-issue-stance-v1` | 手書き＋adapterが指紋を検査（変更不可） | 全体像 or 末尾（維持） | - |
| 31 | 投票の導入文 | 「2024年に…青切符が導入されます」（未来形のまま。2026年4月施行済みと食い違い） | 手書き | 修正して維持 | 現状は事実と合わない |
| 32 | 授業・探究学習 | 賛成側3・反対側3の理由（論点へのリンク）、一次資料3件、問い3つ、使い方、印刷ボタン | `scripts/seo/apply_classroom_section.py`（CLASSROOM）。文面は手書き | 背景（開閉） | - |
| 33 | 調査条件（再読の根拠） | 区分の根拠、全件表の説明、署名定型文の件数など | `scripts/build_bike_process_sections.py`（REREAD_BASIS） | 背景 | - |
| 34 | このページの作り方 | 公開日2026-06-28／更新2026-09-28／収集方法／分かったこと4段落／データの読み方／訂正窓口 | `scripts/seo/apply_theme_trust.py`（ARTICLE_TRUST）＋手書き段落 | 背景 | 一部不要：「7/26と8/17の比較（31件と82件）」の段落は古い（現在の潮目は9/12→9/28）。更新または削除 |
| 35 | 次はこのテーマ | 憲法改正・部活動・高齢者免許返納の3リンク | `scripts/build_planet_page_preview.py` 系の共通部品 | 末尾 | - |
| 36 | 詳細データ 分類別件数 | 6旧カテゴリ合計177件（34/31/14/41/12/45） | `scripts/build_reaction_map.py`（旧生成器）で生成された古い値 | 不要 | 585/415件・現行の論点と一致しない旧体系。残すと件数が2種類表示される |
| 37 | 詳細データ カテゴリ×検索クエリ | 旧カテゴリ×10検索語の表 | 同上 | 不要または背景に再生成 | 同上。検索語は「収集のしかた」として別途示せる |
| 38 | 詳細データ カテゴリ×スタンス | 旧カテゴリ×旧6スタンスの表 | 同上 | 不要 | 同上 |
| 39 | 注意 | 世論調査ではない、検索語に偏りの可能性 | `configs/bike-blue-ticket-reaction-map.json` の `notes` | 背景 | - |
| 40 | フッター | 運営者情報、調査・編集方法、問い合わせフォーム、プライバシー、免責 | 共通部品 | 維持 | - |
| 41 | アリーナ点群 | `#bike-arena-points`（415点）とSM_RAW | `scripts/build_bike_arena_points.py` | 全体像の部品（数字の出所検査から除外されている） | - |
| 42 | 漫画・投票画像 | manga-page-1〜3、charsheet2、vote-1〜4 画像が `docs/images/topics/bike-blue-ticket/` にある。現行ページ本文では参照を確認できず | `configs/bike-blue-ticket-reaction-map.json` の `manga` | 未確認（使われているか未確認） | - |

ページ内リンク（#section、#planet-block、#fallback-nav、#ocean、#issue-<論点ID>、#fb-<論点ID>）と、X投稿URL12件（論点ごとに2件、`bike_issue_media.py` 生成）は上の行に含めた。ページ全体のX投稿URLは475箇所に現れるが、実体は意見の元投稿（アリーナ点群・全件表）で、表示対象は12件。

## 3. データ対応表

流れ：正典 `social-samples/bike-blue-ticket_2d_classified.json`（585件、Git管理外の非公開）→ 検証データ `data/verification/*.json` → 公開JSON `data/public/themes/bike-blue-ticket.json`（`docs/data/themes/` に同一内容、24,918バイト）→ HTML。定期更新は `scripts/refresh_topic.py` → `scripts/refresh_adapters/bike.py` が候補を2回作って差分0を確認してから昇格（`page_update_mode: adapter`）。

| 項目 | 生成スクリプト | 入力 | 出力 | 手入力・重複の有無 |
|---|---|---|---|---|
| 収集・意見件数 | `scripts/build_bike_verification.py`（検証データ）、公開JSON生成（`public_registry_common.py` 系）、`sync_issue_counts.py`、`apply_theme_design.py` | 正典 | 公開JSON `collected_count` `opinion_count`、ヒーロー件数、リード文、`#planet-data`、THEMES.yaml `collect_delta` | 重複：HTMLに複数箇所（ヒーロー、リード、立場内訳、山なみ、このページの作り方）。生成だが最終は貼り直し。THEMES.yaml の `collect_delta`（83）は手入力 |
| 論点別件数 | `refresh_planet_section.py`（`--for-docs`）、`build_bike_arena.py`、`bike_blue_ticket_connected.py` | 正典の `main_issue` | `#planet-data`、論点ブロック、帯、論点一覧、公開JSON `issues[]` | `docs/` 内の旧分類語（「カテゴリ×〜」の表）は別系統で未更新（行36〜38） |
| 立場 | `build_bike_arena.py`（STANCE_GLANCE、論点別の立場内訳） | 正典の `stance` | 立場内訳、山なみ、公開JSON `issues[].stances` | 立場名は`configs/topics/bike-blue-ticket.yaml`の旧6区分と現行3区分が併存（旧は分類器用） |
| 理由（再読） | `build_bike_editorial_reread.py`、`build_bike_refresh_candidate.py`（反対側の追記） | 正典＋`data/bike-blue-ticket_opposition_reread.json`＋`..._editorial-supplement.json`＋`..._editorial-reread-20260906.json`＋`..._editorial-updates/{日付}.json` | `data/bike-blue-ticket_issues-reread.json`、`data/verification/reread/bike-blue-ticket.json`、論点の「中身」 | **読む工程だけ手作業**。新しい反対投稿が未再読ならadapterが意図的に失敗する。論点別の理由区分名は再読ファイルの `bucket_label` を手で決めている |
| 推移 | `inject_tide_widget.py`、`refresh_adapters/bike.py` の `_apply_tide`、`_write_config` | 更新回の分類結果（`social-samples/updates/.../`） | 潮目カード、`configs/bike-blue-ticket-reaction-map.json` の数字出所 | 前回・今回の更新回は自動。注記文（署名定型文の件数）は生成。「このページの作り方」の7/26→8/17の段落は手書きで古い |
| 一次資料・照合 | `build_bike_verification.py`、`build_bike_process_sections.py`（`claims.json`）、`verify_claim_verdicts.py`（検査） | `quality/research/bike-blue-ticket-primary-sources.md`（人が書く）→ 公開JSON `claim_verification` | 照合カード、資料にあるのにSNSにない、制度の確認 | 判定文・URL・確認日は手入力（JSONとHTML読書面に二重）。`data/verification/bike-blue-ticket-background.json`（年表・チェックリスト）と、HTMLの背景・制度確認が同文の重複 |
| 検索入口の値（年齢・反則金10例・FAQ） | なし（生成なし） | - | `bike_blue_ticket_search_entry.html` と `bike-blue-ticket-search-entry.js` | **全て手入力**。金額は政令別表第六（確認日2026-09-07）と手で合わせる。年齢の短答はJSとHTMLに同じ文が二重 |
| 投稿URL | `bike_issue_media.py` | 正典（`article_usable` かつ `risk=low`、論点ごと2件） | 論点ごとのX投稿12件 | 選定は自動、並べ替えは固定。表示件数12は手入力の仕様 |
| アリーナ点・注目ポイント | `build_bike_arena_points.py`、`build_bike_arena.py` | 正典 | `#bike-arena-points`、insight-stats、本当の対立点の件数 | 自動 |
| OGP・画像 | なし | - | `ogp/bike-blue-ticket.png`、論点別図解6枚 | 手作成の資産。数字を焼き込んでいるかは**未確認** |
| 投票 | なし（adapterが指紋検査のみ） | - | 18選択肢 | 手入力。変更するとadapterが失敗 |

## 4. このテーマならではの疑問の候補

**検索データの扱い**：今回は検索ツールを使っていない。下の1〜4は、既に作業ツリーにある課題97（`tasks/task-97.md`、2026-09-27調査、Googleサジェスト・Trends・キーワードプランナー・知恵袋107件）の結論と、2026-09-28公開済みの検索入口（`scripts/templates/bike_blue_ticket_search_entry.html`）の内容の書き出し。5〜8は**原稿と論点からの推測**で、検索量の根拠はない。調査資料の元フォルダ `/Volumes/M2-WorkSpace/Projects/副業/ニーズ調査/2026-09-27_bike-blue-ticket/` は存在せず読めなかったため、検索数値の原本は未確認。

既存の検索入口（課題97の結論）：「自転車 青切符」は月間1万〜10万だが直近3か月は-90%でTrendsは2026年3月末が頂点。対象一覧は1万〜10万、何歳から・反則金一覧・ハンドサインは1,000〜1万、小学生・歩道・支払い・詐欺は100〜1,000。既存ページは過去90日で表示2・クリック0。公開後30日の評価は2026-10-28（Search Console）。

1. 何歳から青切符の対象か（入口に既存：年齢3択）
2. 反則金はいくらか、違反名で調べたい（入口に既存：10例の検索）
3. 歩道は走れるか、すぐ切符を切られるか（入口に既存：FAQ。論点「車道走行への不安」とも対応）
4. 反則金はどこで払うか、現場で現金を求められたら（入口に既存：支払い・詐欺のFAQ）
5. （推測）違反しても必ず切符を切られるのか、指導警告との違いは。原稿の根拠：運用の実際、導入1か月の実績2,147件対13万5,855件
6. （推測）前科は付くのか、運転免許の点数に響くのか。原稿の根拠：制度の確認「運転免許との関係」、論点「免許制要求」
7. （推測）自転車に免許は必要になるのか。原稿の根拠：論点「免許制要求」33件
8. （推測）自転車道・レーンは足りているのか、整備の予定は。原稿の根拠：論点「インフラ整備優先」67件、第3次自転車活用推進計画

## 5. 部活動と違う点・判断が必要な点

1. **すでに検索入口がある。** 部活動は初画面を一から作るが、自転車は課題97で年齢チェック・反則金検索・FAQを公開済み（2026-09-28）。作り直すか、位置づけだけ変えるかを決める。評価日は2026-10-28で、その前に構成を大きく変えると30日のKPI計測と比較できなくなる。
2. **論点が6つでうち「その他」が143件（34.5%）で最大。** 部活動より論点の説明力が弱く、「その他」の中身（制度そのものに反対59件など24区分）をどう見せるか、「その他」を山として並べるかを決める必要がある。反対側の旧5区分（205件）と論点別理由区分の2系統が併存している点も整理が要る。
3. **立場が賛成/反対/どちらでもないの3区分で、反対が205件（49.4%）。** 論点が立場とほぼ1対1（取締り強化賛成は賛成、インフラ・車道は反対）に重なるため、論点を選ぶ画面で立場の見せ方が冗長になりやすい。署名定型文が反対に多く混じる（5.の旧区分で68件が「制度そのものに反対」。具体の署名件数は`data/verification/bike-blue-ticket-reread.json`の列で数え直すこと）。
4. **再読データの欠けは小さいが、読了日が弱い。** 意見415件は全件いずれかの理由区分に入っているが、585記録のうち206件は `legacy`（読了日・確認者なし）。「再読済み」と表示するときの限定表現を決める。
5. **一次資料は厚いが偏りと未照合がある。** 資料22件・確認日は2026-08-30〜09-07。「違反113種類」「65項目」の数え方は未照合で、訴求に使えない。インフラ側の資料は計画の目標値のみで予算額が無い。
6. **古い箇所が現行ページに残っている。** 詳細データの3表（旧177件・旧分類）、「このページの作り方」の7/26→8/17比較、投票導入文の未来形、背景と制度確認が部活動の流用idのまま。移植時に整合の検査が落ちる可能性がある。
7. **X投稿の埋め込み。** 論点ごと2件・12件が可能で、blockquote＋出典リンクの代替も実装済み。開いたとき読み込み方式へ変えられるかは`bike_issue_media.py`と`widgets.js`の関係を調べていない。
8. **共有スクリプトが多い。** 自転車専用：`build_bike_*.py`、`bike_blue_ticket_*.py`、`bike_issue_media.py`、`refresh_adapters/bike.py`。共有：`apply_theme_design.py`、`inject_tide_widget.py`、`refresh_planet_section.py`、`sync_issue_counts.py`、`seo/apply_*.py`、`refresh_topic.py`、`verify_theme_page.py`、`verify_number_provenance.py`。専用側を触っても共有側の検査（全テーマ）が通るか確認が必要。テスト `tests/test_bike_adapter.py` などが現行構造を固定している。
9. **ページ本体が大きい。** 現行HTML 442KB・3,517行で、論点別の読書面はテンプレート（`BIKE_CONNECTED_CONTENT`）として本文末尾に置かれている。部活動のように共通部品へ寄せるか、現行の連動表示を残すかを決める。

## 6. 読めなかったもの・確認していないもの

- Search Console、Googleキーワードプランナー、Trends、ラッコキーワードの数値（今回は取得せず、課題97の記載を引用）。課題97の調査原本フォルダ `/Volumes/M2-WorkSpace/Projects/副業/ニーズ調査/2026-09-27_bike-blue-ticket/` は存在せず読めなかった。
- 参照仕様 `quality/designs/2026-10-10-bukatsu-production-candidate.md` と `docs/bukatsu-chiiki-reaction-map.html` の中身（今回は手順書の抜粋と本テーマの資料のみ読んだ）。
- 手順書の後半（手順4〜7と依頼文の節）は先頭部分だけ読み、細部は未読。
- 表示の実機確認（PC/375px、JS無効、コンソールエラー）はしていない。HTMLはテキスト抽出のみ。
- 画像（ヒーロー、図解6枚、OGP）に数字が焼き込まれているか。漫画・投票画像がどこで使われているか。
- 詳細データ3表と`bukatsu-background`系idを生成するスクリプトの確定（`build_reaction_map.py`が旧表の生成元と推定。背景・制度確認の生成元は手書きか`seo/apply_background_sources.py`か未確認）。
- 署名定型文の正確な件数、`data/bike-blue-ticket_editorial-updates/` の全ファイルの内容、`social-samples/updates/` 配下の更新回データ。
- 手書き値（反則金の額10例）と政令別表第六の突き合わせ。
- 全テストの通過状況（実行していない）。
