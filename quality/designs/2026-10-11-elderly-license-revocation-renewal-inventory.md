# 高齢者免許返納：リニューアル準備の棚卸しと内容対応表（2026-10-11）

手順書23の手順1（棚卸し）と手順3（置き場所の割当）の成果物。検索ツールは使っていない。HTMLの試作・スクリプトの変更はしていない。
作業ツリー: `isa-wt-renew-elderly-license-revocation`（ブランチ task/renew-elderly-license-revocation）。

## 1. 現状の要約

- 件数: 収集662件・意見455件（`docs/data/themes/elderly-license-revocation.json` の `collected_count` / `opinion_count`。正典 `social-samples/elderly-license_2d_classified.json` は662件、`is_opinion` が True の211件はここでは使わず、意見455件は公開JSONの値。正典側の意見455件の再集計は未確認）
- 論点（同JSON `issues[].count`）: 義務化・事故防止283 / 適性検査強化57 / 地方の足・移動権39 / 自主返納支援26 / 代替交通整備25 / その他25（合計455）
- 立場（同JSON 論点別 `stances` の合算）: 義務化賛成241 / 条件付き賛成93 / 義務化反対49 / 中立・情報72（合計455）。詳細データ節の強度別は high160 / medium234 / low61
- 期間・更新日: 2026-06-27〜2026-09-30（`collection_period`）、`updated_on` 2026-09-30、次回収集・更新予定 2026-10-14（THEMES.yaml `refresh_at`）、公開日 2026-06-28、X投稿日 2026-10-07
- 再読（理由区分）データ: あり。`data/elderly-license_issues-reread.json`（`buckets` / `items`322件）。対象は義務化・事故防止283件（8区分）と地方の足・移動権39件（7区分）のみ。適性検査強化・自主返納支援・代替交通整備・その他の4論点（計133件）は再読なし。2026-10-10の追い読みで72件を接続済み（`catchup_2026_10_10.added`）
- 別の再読台帳 `data/verification/reread/elderly-license-revocation.json` は records 578件、snapshot 2026-09-06（移行時の指紋で読了時点ではないと注記あり）。論点別件数は未集計
- 一次資料メモ `quality/research/elderly-license-revocation-primary-sources.md`: 確認日は資料により 2026-08-30 / 08-31、追記は 2026-09-07（運転免許統計）。半年後の再確認目安 2027-02-18（作業記録より）
- 主張の照合7件（`data/verification/elderly-license-revocation-claims.json` / 公開JSON `claim_verification`）: 確認日 2026-09-30（ページ内表記は「照合確認日 2026-08-18」と併存）。「資料にしかない話」4件、編集部の横断整理は 2026-09-11 時点
- 推移（世論の潮目）: 9月20日→9月30日、前回67件・今回16件

## 2. 棚卸し表（現行ページを上から）

出所の略記: 【手】=HTMLへの手書き（生成元なし）、【生】=スクリプトが生成。配置先: 冒頭／全体像／論点別／背景／不要。

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | メタ・構造化データ | title・description・canonical・OGP・Article JSON-LD（SEO_META / ARTICLE_JSON_LD） | 【生】seo/apply_meta_tags.py ほか、設定は configs/elderly-license-revocation-reaction-map.json | 冒頭（head、維持） | 不要ではない。URL・GA4・AdSense・OGPは保護対象 |
| 2 | ヘッダー部 | 「探ったところ 0」の進行表示、トップ・カテゴリへの導線 | 共通テンプレート | 冒頭 | 共通部品 |
| 3 | ヒーロー見出し | h1「免許返納は何歳から？年齢・メリットとデメリット・義務化の賛否」、副題「事故を防ぐための年齢線引きか…」 | 【手】ページ直書き（テストが検査） | 冒頭 | |
| 4 | 件数表示 | 「SNSの意見 455件」（THEME_COUNT） | 【生】apply_theme_design.py | 冒頭 | |
| 5 | リード文 | 取得662件のうち意見455件。世論調査ではない旨 | 【生】build_elderly_arena.py（旧マップ時のみ。山なみ化後は手書き残り） | 冒頭 | 重複（調査条件と同文） |
| 6 | 議論の中心 | 「283件 事故を防ぐため、年齢で線を引くべきか」 | 【生】build_elderly_arena.py（conclusion-count） | 全体像 | |
| 7 | 検索の入口: 短答 | 「返納する年齢に、全国一律の答えはありません」。自主返納は本人申請、70歳・75歳は更新時の節目 | 【手】HTML直書き（SEARCH_ENTRY、生成元なし） | 冒頭 | |
| 8 | 年齢別3段 | 年齢を問わず相談・自主返納／70歳以上高齢者講習／75歳以上認知機能検査（違反歴で運転技能検査） | 【手】 | 冒頭 | |
| 9 | 家族で話す前の確認 | 「年齢より先に4つを並べる」運転の変化・健康と検査・返納後の足・続ける条件とやめる条件 | 【手】 | 背景（または冒頭下） | |
| 10 | メリット・デメリット | 返納する側／暮らしからの各3項目 | 【手】 | 背景 | |
| 11 | 家族の話し方 | 説得より先に移動手段を用意する。医療判断は医師・警察へ | 【手】 | 背景 | |
| 12 | FAQ 6問 | 何歳から義務か／70・75歳で何が変わる／親が拒むとき／どこでできるか／運転経歴証明書は身分証か／割引・給付金は全国共通か | 【手】details | 冒頭（疑問と短答） | |
| 13 | 一次資料リンク（入口） | 警察庁「運転免許証の自主返納」「認知機能検査」、「義務化をめぐる455件の立場を見る」（ページ内） | 【手】 | 冒頭／背景 | |
| 14 | 立場の全体像 | 見出し「賛成は反対の4.9倍」「肯定的な投稿は73%」、4立場241/93/49/72と割合53/20/11/16%、立場選択UI | 【生】apply_elderly_stance_glance（build_elderly_arena.py）。見出しの倍率・73%の言い回しは同スクリプト内 | 全体像 | |
| 15 | 調査条件 | 元データ・取得期間・AI分類・世論調査ではない注意 | 【生】build_elderly_arena.py（取得期間はTHEMES.yaml） | 背景（方法） | |
| 16 | 背景パネル（定義と現状） | 「何が、どこまで進んでいるのか」。義務化の定義、現行制度、なぜ始まったか（統計：85歳以上約3.4倍、踏み間違い80〜84歳約20倍）、賛否の論拠、国会答弁 | 【手】HTML（根拠 data/verification/elderly-license-revocation-background.json、確認日 2026-09-11）。id名 `bukatsu-background` は部活動からの流用 | 背景 | |
| 17 | 年表 | 2016〜17年閣僚会議／2020年3月報告書／2022年5月運転技能検査／2026年4月国会／2026年6月追跡調査と検討会（8月目途の報告書） | 【手】同上 | 背景 | |
| 18 | 「意見の分布を先に見る」リンク | ページ内 | 【手】 | 不要 | 新構成では順序が逆転するため |
| 19 | 山並み（planet）図 | 6論点の円、色は最多の立場、操作UI、論点選択、図が使えないときの一覧 | 【生】build_elderly_arena.py → refresh_planet_section.py、データ configs/planet/elderly-license-revocation.yaml・build_planet_data.py | 全体像 | |
| 20 | 論点パネル×6 | 各論点: 件数・割合・山の高さ（強い表現%）、立場内訳、立場ごとの占有率、図解画像（v2 webp 6枚） | 【生】同上、画像割当は refresh_planet_section.py ほか | 論点別 | |
| 21 | 理由の分類（義務化・事故防止8区分、地方の足7区分） | 例: 具体的な危険運転への怒り107、年齢一律43、趣旨不明39…。各区分から投稿例 | 【生】elderly_connected.py / elderly_connected_content.py、入力 data/elderly-license_issues-reread.json と configs/elderly-license-reason-posts.json | 論点別 | 他4論点は再読なし→「未公開」明記 |
| 22 | 論点別代表投稿（X）12件 | 6論点×2件、編集部選定 | 【手】？生成元未確認（configs/elderly-license-revocation-reaction-map.json の可能性、未確認） | 論点別 | |
| 23 | 論点ごとのX投稿の節 | 同12件の埋め込み節（件数付き、地図へ戻るリンク） | 同上 | 論点別（重複を統合） | 22と重複 |
| 24 | 一次資料との照合カード7件 | 少しずれる3／資料どおり／確認できず等。出典リンク | 【生】build_elderly_process_sections.py（VERIFY_SECTION）、入力 data/verification/elderly-license-revocation-claims.json と data/elderly-license-revocation_claim_posts.json | 論点別（連動表示と一本化） | 同じ内容が3か所（クイズ節・論点パネル・連動コンテンツ） |
| 25 | 一次資料クイズ | 見出しのみで本文は上記を再利用 | 【手】/【生】 | 不要または論点別へ吸収 | 重複 |
| 26 | 資料にあるのに、SNSにないこと | 4件（サポートカー限定免許／クロスセクター効果／運転技能検査の成立理由／＃8080）、各「集めた投稿での件数」と再確認履歴、確認日 2026-09-30 | 【生】elderly_connected_content.py ほか、入力 data/verification/elderly-license-revocation-sunk-continents.json | 論点別（連動）＋背景 | |
| 27 | 編集部の横断整理 | 共通する前提／本当の対立／まだ分からないこと（2026-09-11時点） | 【生】入力 data/verification/elderly-license-revocation-editorial.json | 全体像（意見の全体像の直下） | |
| 28 | 論点一覧（押すと切替） | 山並みの操作見出し | 【生】 | 全体像 | |
| 29 | 「このページの見かた」 | 凡例 | 【手】 | 全体像 | |
| 30 | 論点カード（ISSUE_MEDIA） | 図解付き論点カード、件数バッジ | 【生】scripts/elderly_issue_media.py | 論点別 | 山並みパネルと重複気味 |
| 31 | 世論の潮目 | 9/20→9/30 立場・論点の構成比、変化再生（前回67件・今回16件） | 【生】inject_tide_widget.py（prev/cur 登録は同スクリプト内の表）、adapter が `_apply_tide` | 背景（推移） | 今回16件は少数。論点側「自主返納支援33.3%」は母数が小さい |
| 32 | 投票 | 論点（2問）・立場（18選択肢）、vote-store連携 | 【手】HTML内 `VOTE_ISSUES`/`STANCES`（アダプタが指紋検査） | 論点別の後（投票欄） | 不要ではない。保護対象 |
| 33 | 授業・ディベート節 | 賛成側3理由・反対側3理由、確かめる一次資料3、問いの例3、使い方、印刷 | 【生】scripts/seo/apply_classroom_section.py、設定は configs/classroom/elderly-license-revocation.json | 背景 | |
| 34 | このページの作り方 | 公開日2026-06-28・最終更新、収集方法、AI工程、収集・分類で分かったこと、データの読み方、訂正窓口 | 【生】seo/apply_theme_trust.py、文言は configs/theme-seo.json | 背景（方法） | 「分かったこと」の7/12→7/26比較は古い。要見直し |
| 35 | 次に見るテーマ | 自転車の青切符・部活動・憲法改正論議 | 【生】 | 背景（末尾） | |
| 36 | 詳細データ（開閉） | 論点別・スタンス別・強度別件数、カテゴリ×検索クエリ、カテゴリ×スタンスのヒートマップ | 【生】build_elderly_arena.py（build_details） | 背景（または不要） | ヒートマップ2枚は旧マップ時代の表。山並みと重複 |
| 37 | 注意 | 世論調査ではない、2026-07-01の再分類の履歴 | 【手】 | 背景 | 7/1の履歴は古く削除候補 |
| 38 | 連動コンテンツ（elc-claim / elc-source-only） | 論点別に「投稿の主張と一次資料」「資料にあり収集投稿で見つからなかったこと」を開閉で表示。JS: elderly-connected.js, elderly-connected-page.js | 【生】elderly_connected.py / elderly_connected_content.py | 論点別 | 24と同一素材 |
| 39 | フッター・共有 | share-xボタン、運営者情報、調査・編集方法、訂正窓口、プライバシー、免責 | 共通 | 背景（末尾） | |
| 40 | 外部資料リンク（ページ内に出る出典） | 警察庁（検討会報告書、追跡調査、R07分析、自主返納、認知機能検査）、内閣府（R06・R07白書、高齢社会白書）、国交省（近畿運輸局PDF、MLIT PDF）、e-Gov、国会会議録 | 【生】/【手】混在 | 論点別・背景 | |
| 41 | X投稿URL | href 29件のユニークURL（論点別代表12件＋理由別の例）。`twitter-tweet` 引用24個 | 上記22・21 | 論点別 | 引用24個と href 29件の差の内訳は未確認 |
| 42 | 画像 | ヒーロー1、論点図解6（v2）と旧版、マンガ（charsheet・page）3+2、投票画像4、OGP | docs/images/topics/elderly-license-revocation/ | 冒頭（ヒーロー）／論点別（図解）／不要（マンガ・投票画像、使用状況は未確認） | |

## 3. データ対応表

流れ: 正典 `social-samples/elderly-license_2d_classified.json`（THEMES.yaml `sample_file`）→ `data/public/themes/elderly-license-revocation.json`（公開データ。`docs/data/themes/` の同名ファイルとサイズ31,889バイトで同一と見られるが、内容の完全一致照合は未実施）→ HTML。

| 項目 | 正典 | 公開JSON | HTML生成 | 手入力・重複 |
|---|---|---|---|---|
| 収集件数662 | 正典の件数 | `collected_count` | build_elderly_arena.py（リード・調査条件）、refresh_planet_section.py の `_sync_elderly_method_text`（本文「取得した公開投稿N件」2か所）、apply_theme_trust.py（作り方の節） | 本文に直書きされる箇所が複数。設定 configs/elderly-license-revocation-reaction-map.json の `issue_counts.sync` で同期 |
| 意見件数455 | `is_opinion` 判定済み | `opinion_count` | 同上＋apply_theme_design.py（THEME_COUNT） | 検索入口の「義務化をめぐる455件」ボタン、h1付近の文言は【手】で重複 |
| 論点別件数 | `classification.main_issue`（正典側の集計は未確認） | `issues[].count` | build_elderly_arena.py（apply_public_counts）、山並み（build_planet_data.py）、`ELDERLY_ISSUE_MEDIA`、投稿節の件数バッジ | configs/theme-seo.json の論点比較文は2026-10-07に差し込み式に修正済み。以後べた書き禁止 |
| 立場 | 正典 | `issues[].stances[]`（強度付き） | apply_elderly_stance_glance（STANCE_GLANCE_META） | 「4.9倍」「73%」の見出しは同スクリプト内のため手入力ではないが、再計算されるかは未確認 |
| 理由区分 | data/elderly-license_issues-reread.json | なし（公開JSONに理由は含まれない） | elderly_connected.py、検査 elderly_license_count_provenance.py | 区分の件数は再読ファイルが原本。投稿例は configs/elderly-license-reason-posts.json（各区分3件候補、要旨とURLのみ） |
| 推移 | social-samples/updates/…/classified.json（前回・今回） | `updates/` は含まれない（未確認） | inject_tide_widget.py ／ refresh_adapters/elderly.py `_apply_tide` | 前回ファイル名が inject_tide_widget.py の表にべた書き（elderly-license-revocation_hermes_prev_20260712.json）。adapter側は更新日で自動選択するため二重 |
| 一次資料（背景） | data/verification/elderly-license-revocation-background.json | 含まれない | HTML直書き（背景パネル・年表）。生成スクリプトは未特定 | 背景パネル・年表は手書き。メモ quality/research/…primary-sources.md と二重 |
| 一次資料（主張の照合） | …-claims.json、claim_posts.json | `claim_verification` | build_elderly_process_sections.py、elderly_connected_content.py | ページ内の確認日が08-18と09-30で併存 |
| 一次資料（資料にしかない話） | …-sunk-continents.json | `ocean_layer.sunk_continents` | elderly_connected_content.py | 件数は意見総数455に依存 |
| 編集部の整理 | …-editorial.json | `editorial_summary` | 同上 | 文中の％（61.4%、80.9%、66.7%）が文章に埋まる |
| 投稿URL | 正典 `url` | 含まれない | 代表投稿は設定 configs/…reaction-map.json ほか、理由別例は reason-posts.json | 代表投稿12件の選定元は未特定 |
| 公開日・更新日 | THEMES.yaml | `updated_on` | apply_theme_trust.py | 作り方の節と投稿節の日付 |
| 投票定義 | なし | なし | HTML直書き（VOTE_ISSUES/STANCES）。adapterが指紋で検査 | 18選択肢をアダプタ内にも定数 VOTE_CHOICES=18 で保持 |

## 4. このテーマならではの疑問の候補（原稿からの推測。検索ツールは未使用）

既存の search-entry はあり（上記表の7〜13）。先に書き出す内容は、現行FAQ6問（何歳から義務か／70・75歳で何が変わる／親が拒むとき／どこでできるか／運転経歴証明書は身分証か／割引・給付金は全国共通か）。テストが「何歳から」を見出し・title・descriptionで検査している。

追加候補（原稿・論点からの推測、検索数は未確認）:
1. 免許返納は義務になるのか（国会・検討会の状況）
2. 返納のメリット・デメリットは何か
3. 返納しないとどうなる（技能検査・講習の仕組み）
4. 地方で車がなくなったら通院や買い物はどうするのか
5. 高齢ドライバーの事故は本当に増えているのか（資料では件数は減少、割合は上昇）
6. サポートカー限定免許とは何か
7. 運転が心配なとき、どこに相談できるか（＃8080）
8. 賛成・反対はそれぞれ何割か（意見455件の内訳）

## 5. 部活動と違う点・判断が必要な点

1. 論点が6つ（部活動より多く、うち「その他」25件は意味の薄い論点）。山並みに「その他」を入れるか、地方の足・移動権・代替交通整備（隣接）を寄せるかを決める。
2. 再読データの欠け: 理由区分があるのは2論点（322件）だけで、他4論点（計133件）は「未公開」表示になる。追い読みを先に行うか、未公開のまま出すかを決める。理由の投稿例は各区分3件候補のみ。
3. 検索入口（FAQ・年齢別・メリット/デメリット）が既にあり、生成元がなくHTMLにのみ存在する。手順1は「公開HTMLを入力に使わない」が、現行アダプタは既存HTMLを雛形として更新する。新構成へ移す際、この手書き部分の正典化（設定ファイル化）が必要。
4. 一次資料は厚いが、主張の照合が7件、資料にしかない話が4件。「その他」には一次資料が無い（メモの節は5論点のみ）。2026-09-07追記の運転免許統計（自主返納件数）がページに反映されているかは未確認。
5. 投稿埋め込み: 現状は引用24個＋リンク。「開いたときに読み込み」は手順5の要件で、x_embed.py が4テーマ共有。現行の可否・失敗時のリンク残しは未確認。
6. 他テーマと共有するスクリプトが多い: apply_theme_design.py・apply_theme_trust.py・inject_tide_widget.py・refresh_planet_section.py・build_planet_data.py・build_public_registry.py・x_embed.py。elderly 専用は build_elderly_arena.py・elderly_connected*.py・elderly_issue_media.py・build_elderly_process_sections.py・refresh_adapters/elderly.py。共有側の変更は他テーマに波及する。
7. 内部の重複: 一次資料の照合が3か所、代表投稿が2か所、論点カードが山並みと二重。新構成で一本化するときに数字の検査（verify_number_provenance 等）を合わせる必要がある。
8. 古い記述の整理: 「収集・分類で分かったこと」の7/12→7/26比較、注意欄の7/1再分類、背景パネルの id 名（bukatsu-background）。
9. 潮目の今回16件（母数小）を前面に出さない判断。
10. 次回更新は2026-10-14。公開済みページはオーナー承認待ちの追い読み結果（2026-10-10）を作業ツリーでのみ再生成済み。構成変更はこの更新と衝突させない。

## 6. 読めなかったもの・確認していないもの

- ラッコキーワード、キーワードプランナー、Google Trends、Search Console（手順2）は未実施。検索数・期間・取得日は未確認。
- 正典の意見455件・立場別の再集計（公開JSONの値を使用）。`is_opinion` の True が211件で455と一致しない理由は未確認。
- `data/verification/reread/elderly-license-revocation.json`（records 578件）の論点別件数。
- 代表投稿12件の選定元・生成元、引用24個とhref29件の内訳。
- docs/data/themes と data/public/themes の内容の完全一致、公開JSONに推移・投稿URLが含まれるか。
- 背景パネル・年表を書き換えるスクリプトの有無。
- 一次資料メモ全文（約28KB）は見出し・確認日・一部のみ。リンク切れの確認はしていない。
- 作業記録は見出しと最近の節のみ。quality/reviews 配下の過去の監査記録、theme-seo.json の中身は未読。
- 部活動の参照ページ・設計書は節構成のみ確認し、全文は未読。
- ブラウザでの表示確認（PC・375px）、X埋め込みの動作、JavaScriptなし表示は未確認。
