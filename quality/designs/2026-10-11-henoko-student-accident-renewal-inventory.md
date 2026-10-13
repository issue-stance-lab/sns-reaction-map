# 辺野古高校生死亡事故 リニューアル準備：棚卸しと内容対応表（2026-10-11）

対象は `henoko-student-accident`。手順書「23_テーマ別リニューアル移植手順」の手順1（棚卸し）と手順3（内容対応表・データ対応表）まで。検索ツールの調査・HTML試作・スクリプト変更は含まない。作業ツリーは `task/renew-henoko-student-accident`。

## 1. 現状の要約

- 収集636件・意見495件。取得元は `docs/data/themes/henoko-student-accident.json` の `collected_count` / `opinion_count`。正典 `social-samples/henoko/henoko_hermes_arena_classified.json`（配列636件。`is_opinion=True` が495、関連だが非意見139、非関連2）と一致。
- 収集期間 2026-06-14〜2026-10-07（公開JSON `collection_period`）。収集回は9回（正典の `fetched_at` 日付：6/14, 6/20, 6/27, 7/26, 8/18, 8/24, 9/15, 9/23, 10/7）。最終更新 2026-10-08（公開JSON `updated_on`、`THEMES.yaml` `updated_at`）。次回収集 2026-10-22。
- 論点は6つ（公開JSON `issues[]`、正典 `classification.main_issue`）。安全管理・事故原因132／政治利用・基地問題127／報道・行政対応97／追悼・被害者の尊厳66／政治的中立性48／平和教育の萎縮25。「その他」は0件で、論点は名前付き6つ＋空の「その他」。
- 立場は4区分（`classification.stance`）。論点を切り分ける445／文科省判断を支持28／文科省判断に反発19／中立・情報共有3。切り分けが90%を占める。強度は high220／medium251／low24。
- 再読（理由区分）データは**あり**：`data/henoko-student-accident_issues-reread.json`。論点別の理由区分と件数（`buckets`）は、安全管理132（5区分）、政治利用・基地127（4区分）、報道・行政97（3区分）、追悼66（4区分）、政治的中立性48（5区分）、平和教育25（4区分）で、**495件すべてが区分済み**（`items`=495、`catchup_2026_10_10.added`=87）。再読者は `editorial_ai`（AI下読み）。
- 一次資料メモ `quality/research/henoko-student-accident-primary-sources.md`：全面取り直し2026-09-07（資料A〜P、各資料の確認日は多くが2026-09-07、資料C・Oのみ2026-08-31）。公開側の年表は `data/verification/henoko-student-accident-background.json` の `checked_on` が2026-09-13、主張照合 `claim_verification.checked_on` が2026-09-13、「資料にあるのにSNSにないこと」が2026-09-16/09-20。
- 取得できなかった値：Search Console等の閲覧数、公開後の流入。メモの「確認できなかったこと」に、運輸安全委員会の事故調査報告書は9/7時点で未公表と明記されている（その後の状況は未確認）。

## 2. 棚卸し表（現行ページ `docs/henoko-student-accident-reaction-map.html` 上から順）

出所の略号：【HTML】=HTMLに手書き／生成器が既存HTMLを雛形にして書き換える部分、【公開JSON】=`docs/data/themes/henoko-student-accident.json`、【検証】=`data/verification/henoko-student-accident-*.json`、【再読】=`data/henoko-student-accident_issues-reread.json`、【arena】=`docs/henoko-arena-data.js`（`build_henoko_arena.py`生成）、【seo】=`configs/theme-seo.json`。配置先：頭=冒頭、全=意見の全体像、論=論点別、背=背景。

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | 計測表示 | 「探ったところ 0」（操作済み19地点を端末内保存） | topic-modern.js の共通部品 | 不要または共通部品のまま | 全テーマ共通の進捗表示。新設計で扱いを決める（5節） |
| 2 | ヒーロー | H1「辺野古沖転覆事故とは？原因・報告書・安全管理の論点」、副題「何が確認され、何がまだ決まっていない？」 | 【HTML】＋SEO設定 | 頭 | |
| 3 | リード文 | 2026年3月・同志社国際高校の研修旅行中の船舶転覆、一次資料の事実／未決定／SNS意見を分ける、636件のうち495件を6論点に整理 | 【HTML】件数のみ build_henoko_arena.py が同期 | 頭 | |
| 4 | 数値カード | 「議論の中心 132件 何が事故を防げなかったのか」 | 件数は生成器、文は【HTML】 | 頭／全 | |
| 5 | 検索入口（3層） | 「事故を、3つの層に分けて読みます」。読み方の説明＋「気になる論点を選ぶ」6ボタン（件数付き）＋選択論点に応じて切替わる「確認済み／未決定／SNS上の意見（件数・割合）」。ボタンは `docs/henoko-search-entry.js` | 【HTML】＋ henoko-search-entry.js/css。件数は `apply_search_entry_counts` | 頭（短答）＋全（論点選び） | 既存の search-entry 部品。内容は4節で先に書き出し |
| 6 | 検索入口の確認済み事実 | 事故日・文科省が計画/引率/説明を検証・国交省が事業登録なしと公表（3文） | 【HTML】／search-entry.js の論点別文言 | 頭／論 | |
| 7 | 検索入口の未決定事項 | 事故原因の最終結論／個人の刑事・法的責任／全国の平和学習への影響。第三者委員会の指摘と最終認定を同じに扱わない | 【HTML】／search-entry.js | 頭 | |
| 8 | 検索入口のSNS意見 | 選択論点の件数と全意見に占める割合、代表の一文 | 件数は生成器（公開JSON由来）、文は search-entry.js | 全 | |
| 9 | ページ内リンク | 年表（#bukatsu-background）、確認項目（#bukatsu-check）、FAQ（#henoko-faq）、山なみ（#planet-block）、論点を開く「この論点の山を見る」 | 【HTML】 | 頭（導線） | idに「bukatsu」が残る（部活動からの流用名）。新ページで付け替え要否を決める |
| 10 | FAQ（6問） | 何があった／原因は確定したか／報告書の指摘／引率教員は同乗していたか／無登録運航の意味／ダンプカー・警備員の事故（2024年安和桟橋）との区別 | 【HTML】手書き。`tests/test_henoko_search_entry.py` がダンプカーの文言を検査 | 頭（短答） | 6問とも原稿の必須内容。別件事故の区別は残す |
| 11 | 立場の図（見出し） | 「『論点を切り分ける』が意見の90%」、支持28・反発19・切り分け445・中立3。立場ボタン4つと説明文 | 件数は生成器、文は【HTML】 | 全 | |
| 12 | 注記 | 立場別の操作は下調べ用で票に入らない（投票は後半） | 【HTML】 | 全（投票節の位置次第） | 投票節をどこに置くかで要否が変わる |
| 13 | 背景パネル | 「何が、どこまで進んでいるのか」。争点の説明2段落、「何が争点になっているのか」 | 【HTML】＋ `build_henoko_process_sections.py` 系 | 背 | |
| 14 | 年表（9件） | 3/16事故、4/7通知、5/22文科省判断・国交省告発、5/29知事会見、6/30登録確認の周知、7/14文科省答弁・文科相答弁・NHK副会長答弁、8/19県議会調査日程。各項に出典リンク（文科省・国交省・沖縄県・国会会議録） | 【検証】background.json の `timeline`（確認日2026-09-13）。HTMLへは生成 | 背（論点別に再掲あり） | |
| 15 | 一次資料リンク | 年表と確認項目に出てくる文科省・国交省・沖縄県・国会会議録・沖縄県議会のURL約11種 | 【検証】background.json / claims | 背／論 | |
| 16 | 確認項目（4項目） | 運送の手配（登録・保険）／中止できる準備（悪天候の代案）／生徒と保護者への説明／教育の内容（異なる見解）。各項に出典 | 【検証】background.json の `checklist` | 論（安全管理・政治的中立性）＋背 | |
| 17 | 未確認の注記 | 個人の刑事責任・事故原因の最終結論・全国の平和学習への影響は判断できない。発言主体を分ける | 【HTML】 | 頭（未決定）と重複 | 頭の「未決定」に統合 |
| 18 | 山なみ本体 | 「SNS反応マップ」。幅＝意見数、高さ＝強い表現の割合、色＝最多の立場。調査条件（期間・636/495・更新日）、「論点を切り分ける」の注記、凡例、ドット図、図が使えない時の論点一覧（6リンク） | 【arena】【公開JSON】。条件文は生成器 | 全 | |
| 19 | 論点着地パネル（6） | 各論点の件数・割合・強い表現の割合、立場の内訳（4立場別件数と、立場内での割合）、「件数と割合は逆に動くことがある」の注記 | 件数は公開JSON→生成器・`sync_issue_counts.py` | 論 | |
| 20 | 理由の内訳（6論点計22区分） | 安全管理5／政治利用・基地4／報道・行政3／追悼4／政治的中立性5／平和教育4。例：責任の所在56、批判する側にも説明を45 | 【再読】`buckets`。ページ内へは `henoko_connected` 系が生成 | 論 | |
| 21 | 一次資料と照らした結果（主張3＋α） | 引率教員不在／波浪警報か注意報か（少しずれる）／無登録運送、政治的中立性の2件（文科省の判断範囲、教育基本法は政治的教養を否定しない）、平和教育（危険な乗船だけが指摘ではない）。判定は資料どおり／少しずれる | 【検証】claims.json 14件＋【公開JSON】`claim_verification`（6件、確認日2026-09-13）。`henoko-student-accident_claim_posts.json`（該当投稿の選定） | 論 | |
| 22 | 一次資料クイズ | 「その主張、資料に当たるとどうなる？」 | 共通部品（build_planet_page_preview.py 系） | 論または背 | 配置は設計時に決める |
| 23 | 語られていない争点（4件） | 悪天候の代案／登録・安全情報の確認／引率不在時の体制／ライフジャケット着用指導。各「集めた投稿での件数：0件（意見495件のうち）」、確認日2026-09-16・09-20、出典リンク | 【検証】sunk-continents.json（`sns_base`=495） | 論（安全管理）＋背 | |
| 24 | 立場をこえて同じ心配 | 「学校行事で子供の安全を軽く扱ってはならない」、支持側・反発側の代表各2件、関わる論点 | 【検証】veins.json（確認日2026-09-13） | 全 | |
| 25 | 編集部の横断整理 | 共通する前提／本当の対立（検証の範囲）／まだ分からないこと（2026-09-12時点） | 【検証】editorial.json／【公開JSON】`editorial_summary` | 全 | |
| 26 | 論点一覧・見かた | 「このページの見かた」（幅・高さ・色の説明）、論点切替の一覧 | 共通部品＋【HTML】 | 全 | |
| 27 | 世論の潮目 | 「9月23日→10月8日」前回6件・今回7件の構成比（論点を切り分けるを除いて比較）。少数サンプル注記。「文科省判断を支持が0.0ポイント減少」 | `inject_tide_widget.py` の部品を `refresh_adapters/henoko.py::_apply_tide` が更新ごとに書く | 全（推移） | 母数が6と7件で情報が薄い。扱いを5節で決める |
| 28 | 投票 | 「あなたはどの論点を重く見る？」2問（論点／文科省判断への評価）。投票キー `henoko-student-accident-issue-stance-v1`（選択肢18）、24時間重複防止の説明、Xシェア、やり直し | 【HTML】共通部品（vote-store.js）。キーは adapter が互換性検査 | 全または末尾 | 投票の保存互換性を守る必要（保護対象） |
| 29 | 授業・ディベート | 「文科省判断を支持」側3理由、「反発」側3理由、確かめる一次資料3、問いの例3、使い方、印刷ボタン | 【HTML】手書き（`seo/apply_classroom_section.py` で入れた部品） | 背（学習用の開閉行） | |
| 30 | 信頼情報（このページの作り方） | 公開日2026-06-24、最終更新2026-10-08、編集 SNS反応まっぷ編集部 | `THEMES.yaml` の `published_at`/`updated_at`。信頼情報生成器 | 背 | |
| 31 | 収集方法・分類で分かったこと | Yahoo!リアルタイム検索の複数検索語、636件／495件、8/18に70件追加（重複2件除き68件、意見50件）、7/26は意見6件、「安全管理が98件で最多」ほか。データの読み方、訂正窓口 | 【seo】`configs/theme-seo.json`＋件数のみ生成器 | 背 | 「98件」「8/18追加」は旧回の文で現在の132件と食い違う（3節で重複・不整合として記載） |
| 32 | 関連テーマ | 次に読むテーマ3件（生成AIと著作権／あだ名禁止／部活動の地域移行） | 【HTML】 | 背（末尾） | |
| 33 | 詳細データ（折りたたみ5） | 論点別件数／立場別（評価28・保留・切り分け448・疑問19）／論点×立場／感情の強さ／注意（検索語の偏り） | `build_henoko_arena.py`（表の部分） | 背 | 「448」はページ上の立場図「445＋中立3」と見え方が違う（3節） |
| 34 | フッター | トップ・運営者情報・調査方法・問い合わせ（Googleフォーム）・プライバシー・免責・画像方針・寄付リンク | 【HTML】共通 | 背（共通） | |
| 35 | 論点別の拡大パネル（6） | 論点ごとに「この論点を語る理由」（上記の区分）、「資料と照合する」（確認項目・照合した経緯・主張と一次資料・資料にあるのに見当たらないこと・同じ心配・横断整理）。安全管理が最も厚く、政治利用・報道・追悼・平和教育は薄い | `henoko_connected_content.py` が生成。データは再読・検証 | 論 | 論点ごとの資料の厚みが不揃い（5節） |
| 36 | 投稿への導線 | 論点を選ぶと代表投稿へ。アリーナの495件に `u`（x.comのURL）あり。HTML上の直書きURLは0件、`twitter-tweet`の直書き1箇所（用途は未確認）。widgets.js を読み込み | 【arena】 | 論（最大2件） | 埋め込みの動作方式は未確認（5節・6節） |
| 37 | メタ・保護対象 | GA4（G-K10S4YCZFH）、AdSense（ca-pub-2542211932832864）、vote-store.js、OGP（`ogp/henoko-student-accident.png`）、canonical | 【HTML】＋ `configs/henoko-student-accident-reaction-map.json` | 保持 | 移植で落とさない（adapter の PROTECTED） |

## 3. データ対応表

| 項目 | 正典 → 公開JSON → HTML の経路 | 手入力の値の置き場所・重複 |
|---|---|---|
| 収集件数・意見件数 | 正典 `social-samples/henoko/henoko_hermes_arena_classified.json` → `docs/data/themes/henoko-student-accident.json`（`collected_count` `opinion_count`、`data/public/themes/` も同名で存在）→ HTML。HTML反映は `scripts/build_henoko_arena.py`（リード・調査条件・カード・ボタン・表）と `sync_issue_counts.py`。更新時は `refresh_adapters/henoko.py` が一括実行 | `configs/henoko-student-accident-reaction-map.json` の `vote_method` に「403件」と手入力が残る（現在値と違う。使用箇所は未確認）。`configs/theme-seo.json` に「98件」等の旧回の数字（不整合） |
| 論点別件数 | 正典 `main_issue` → 公開JSON `issues[].count` → 生成器 → 論点パネル・検索入口ボタン（`apply_search_entry_issue_counts`）・詳細表・arenaのセクター | 論点ラベルが場所で揺れる：「追悼・被害者の尊厳」（公開JSON）／「追悼と被害者の尊厳」「報道・行政の伝え方」（詳細表）。`configs/topics/henoko.yaml` の categories（10種、旧体系）とは別物 |
| 立場 | 正典 `stance` → 公開JSON `issues[].stances[]` → 生成器 | 詳細表が「判断を保留・切り分ける448」、立場図は「切り分け445＋中立3」。`build_henoko_arena.py` 内の固定文言に「判断を保留・切り分ける」（原因未確認）。立場名も「評価／疑問」と「支持／反発」が混在 |
| 強度（高さ） | 正典 `intensity` → 公開JSON → arena `e` → 山の高さ | 手入力なし |
| 理由（発言理由の区分） | 再読 `data/henoko-student-accident_issues-reread.json`（`buckets`+`items`）→ `henoko_connected.py` / `henoko_connected_content.py` → HTML、`henoko_count_provenance.py` が数字を照合 | 手入力なし（区分名・件数は再読ファイルが正典）。再読記録は `reread/` ではなく `data/` 直下（ガードの説明は `data/verification/reread/` と書いている点が実体と違う可能性。未確認） |
| 推移 | 正典の `fetched_at`（9回）→ `refresh_adapters/henoko.py::_apply_tide` → `inject_tide_widget.py` の部品がHTMLに書き込み（公開JSONには推移なし） | 潮目の期間・文言はHTMLに直接書かれる。前回/今回の比較は「論点を切り分ける」を除くため6件と7件 |
| 一次資料 | 調査メモ `quality/research/henoko-student-accident-primary-sources.md`（人が読む正）→ 手で転記 → `data/verification/*-background.json` `*-claims.json` `*-sunk-continents.json` `*-veins.json` `*-editorial.json` → 公開JSON（`claim_verification` `ocean_layer` `editorial_summary`）→ HTML | メモと検証JSONの二重管理（機械連携なし）。確認日が項目ごとに別（9/7・9/13・9/16・9/20）。メモの「論点2: 工事現場の安全管理」は旧名で、課題66に溜め置き。`configs/henoko-sources.json` `henoko-scorecards.json` `henoko-summary-ui.json` の役割は未確認（旧版の可能性） |
| 語られていない争点の母数 | 検証 sunk-continents の `sns_base`=495（更新のたびに手で更新、止まる検査あり） | 手入力。公開JSONは候補から作り直される |
| 投稿URL | 正典 `url` → arena `u`（495件） → 画面の導線 | 手入力なし。代表投稿の選定は `henoko-student-accident_claim_posts.json`（14件の `record_id_hash`＋主張） |
| 年表・確認項目 | `background.json` → HTML生成（`henoko_connected_content.py`ほか） | 年表がページ上で2種類出る（背景パネルの9件と、論点パネル内の「照合した経緯」）。同じ内容が複数箇所に出力される |
| 検索入口・FAQ | HTML内の手書き＋`henoko-search-entry.js`（論点別の文言6組：確認済み/未決定/導線ラベル）。件数だけ生成器が同期 | 文章は手入力でHTMLとJSに分散（FAQ6問、3層の文、論点別ボタン文言）。再生成の入力はHTML自体（`--html-template`） |
| 日付 | `THEMES.yaml` の `published_at`/`updated_at` → 信頼情報生成器 → HTML | `collection_period` は公開JSONとHTMLの条件文に重複 |

主なスクリプト（中身は修正しない）：収集は adapter `scripts/refresh_adapters/henoko.py`（設定 `configs/topics/henoko.yaml`、分類 `classify_henoko_arena_hermes.py`、旧 `classify_2d_henoko.py`）、候補検査 `henoko_planet_guard.py`、ページ生成 `build_henoko_arena.py`、山なみ `build_planet_data.py` / `build_planet_page_preview.py` / `refresh_planet_section.py`、連動読書面 `henoko_connected.py` / `henoko_connected_content.py`（テンプレ `scripts/templates/henoko_connected_bridge.js`）、数字照合 `henoko_count_provenance.py` / `verify_number_provenance.py`、公開集計 `build_public_registry.py`、潮目 `inject_tide_widget.py`、再読 `manage_reread_registry.py`。テスト `tests/test_henoko_*.py` 7本。

## 4. このテーマならではの疑問の候補（原稿からの推測。検索ツールは使っていない）

既存の search-entry（検索の入口）部品の内容を先に書き出す。
- 3層の見出し：「確認済み」「未決定」「SNS上の意見」。論点ボタンは6つ（安全管理・事故原因132／政治利用・基地問題127／報道・行政対応97／追悼・被害者の尊厳66／政治的中立性48／平和教育の萎縮25）。
- 既存FAQ6問：①何があった ②原因は確定したか ③報告書で何が指摘されたか ④引率教員は同乗していたか ⑤無登録運航とは ⑥ダンプカー・警備員の事故（2024年）とは別か。
- 現行のtitle/H1は「辺野古沖転覆事故とは？原因・報告書・安全管理の論点」（2026-10-02に課題105で変更。2026-11-01にSearch Consoleで30日判定の予定）。

疑問の候補（いずれも原稿・論点からの推測）：
1. 辺野古沖の転覆事故では何があったのか（日付・船・犠牲者・学校）。
2. 事故原因は分かったのか。報告書は出たのか（運輸安全委員会は9/7時点で未公表。以後は未確認）。
3. 引率の先生は船に乗っていたのか。学校の責任はどこまで問われているのか。
4. 無登録運航とは何か。どの船・誰の責任か。
5. 文科省は何を「教育基本法違反」と判断したのか（平和学習そのものか、安全管理か）。
6. 平和教育・修学旅行は今後できなくなるのか（萎縮の懸念）。
7. 2024年の安和桟橋のダンプカー事故とは別なのか。
8. SNSでは何が言われているのか。なぜ「論点を切り分ける」が9割なのか。

## 5. 部活動と違う点・判断が必要な点

1. **論点数と立場の偏り**：部活動より論点が少なくとも6つあり、立場は「論点を切り分ける」90%に偏る。論点ごとの立場割合の図は、安全管理が100%切り分けなど単調になる。ここでは立場別の割合より、理由区分（22区分）を主役にするか、立場図を縮めるか、設計時に決める。
2. **再読データの欠けは無い**が、論点ごとの資料の厚みが不揃い。照合した主張は安全管理・政治的中立性・平和教育に集中し、報道・行政対応、追悼・被害者の尊厳には「資料と照らした結果」が無い（HTML上は年表の抜粋のみ）。追悼は被害者の尊厳に関わるため、無理に資料を足すか「資料なし」と書くかの方針が必要。再読者がAI下読み（`editorial_ai`）である点の表示を継続するか。
3. **一次資料が薄い／更新が古い**：メモの確認日は2026-09-07が中心で、公開側は9/13〜9/20。運輸安全委員会の報告書、文科省の6/26フォローアップ調査結果、同志社の外部検証は未取得または未公表の可能性があり、「確認済み／未決定」の層が現時点の事実とずれる恐れ。リニューアル前に資料の再確認が要る（`primary-research` スキルの対象）。
4. **投稿の埋め込み可否**：正典の495件すべてに `x.com` URLがあり導線は作れるが、HTML内の埋め込み方式は今回未確認。被害者に触れる投稿や強い表現（強度high220件）が混ざるため、「最大2件を埋め込む」前に、表示する投稿の選定基準（過激表現・個人攻撃・遺族への言及の除外）を決める。削除済み投稿のリンク切れ時の挙動も要確認。
5. **他テーマと共有しているスクリプト**：`inject_tide_widget.py`、`apply_theme_design.py`、`build_public_registry.py`、`verify_*` 系、`build_planet_data.py` / `build_planet_page_preview.py`（辺野古分岐あり）は全テーマ共通。1テーマの都合で直すと他へ波及する（過去に `apply_theme_trust.py` が全10テーマを書き換えた事例が作業記録にある）。HTMLを雛形に書き換える方式（`--html-template`）なので、新デザインでは生成の入力を正典側へ移す設計が要る。
6. **重複・不整合の整理**：`configs/theme-seo.json` の旧回の数字（98件、8/18追加ほか）、`vote_method` の403件、詳細表の「448」、論点ラベルの表記揺れ、`bukatsu-` で始まるid（`#bukatsu-background` `#bukatsu-check`）。投票キー（`...-issue-stance-v1`、選択肢18）と論点の並び・番号は公開後に固定する運用のため、論点名・順序を変える場合は投票の互換性が条件（旧論点名「工事現場の安全管理」は課題66で溜め置き）。
7. **推移の薄さ**：潮目は直近2回の比較（6件と7件）で、少数サンプル注記が付く。9回分の件数推移（6/14〜10/7）を見せるか、潮目を省くか決める。話題は6月の発生後に減少し、収集1回あたり14〜158件。
8. **表現上の配慮（被害者が関わる事故）**：①死者は高校生1名と船長1名（メモ）。見出し・図柄でピクトグラムやイラストを使わず、遺族の発信や追悼をあおる表現を避ける。②「追悼・被害者の尊厳」の論点は、政治的対立と切り離して置き、投稿例は本人・遺族が特定できる内容を除く。③「死亡事故」の語を入れた現行のページ名（`title`）と、新しいH1「転覆事故」の整合を決める。④個人の刑事責任を確定する書き方（「船長が」「学校が責任」）をしない。現行の「個人の刑事責任を確定したものではありません」を引き継ぐ。⑤過激表現（陰謀論・殺害予告の話題。メモ資料O）は投稿例に使わない。⑥ダンプカー事故（2024年）は別件であることを残す。

## 6. 読めなかったもの・確認していないもの

- Search Console・Googleトレンド・キーワードプランナー・ラッコキーワードの数値（今回は範囲外。未確認）。
- 公開ページの実画面（PC/375px）、JavaScript動作、X埋め込みの実動作（HTMLの静的読み取りのみ）。`twitter-tweet` 1箇所の用途、投稿一覧の描画ロジック（`topic-modern.js`）の詳細。
- `themes/henoko-student-accident.md` は冒頭と2026-10-02以降を中心に確認。9/6〜9/24の節は見出しのみ。
- `quality/reviews/` の辺野古関連（9/12ページ設計、9/13監査、10/9標準経路、10/10追い読み証拠）の中身は読んでいない。
- `configs/henoko-sources.json` `henoko-scorecards.json` `henoko-summary-ui.json` の用途、`vote_method` の403件の使用箇所、「448」の生成元ロジック、`reread/` ディレクトリの有無。
- 各スクリプトの中身は入出力の把握のみ（`build_henoko_arena.py` / `refresh_adapters/henoko.py` の冒頭と呼び出し箇所）。`sync_issue_counts.py` / `build_planet_data.py` の辺野古分岐は未読。
- 一次資料メモの本文（資料A〜P）の個別確認と、9/7以降の新しい公表（運輸安全委員会報告書ほか）の有無。
- 公開JSON `data/public/themes/henoko-student-accident.json` の項目は先頭のみ確認（`docs/data/themes/` 側と同一かは未照合）。
- 件数の突き合わせは、正典（636/495）・公開JSON・HTML表示・arena（495件）が一致することまで。再読 `items` 495件が正典の意見495件と1対1かは未照合（件数一致のみ）。
