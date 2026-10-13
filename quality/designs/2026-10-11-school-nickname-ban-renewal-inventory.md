# 学校でのあだ名禁止：リニューアル準備（棚卸しと内容対応表）

作成日 2026-10-11 / 作業ツリー `isa-wt-renew-school-nickname-ban` / 手順書 23 の手順1・3に相当。
HTML試作・スクリプト変更・検索ツール調査は含まない。数字は読んだファイルから取り、取れないものは「未確認」とした。

## 1. 現状の要約

| 項目 | 値 | 取得元 |
|---|---|---|
| 収集件数 | 483件 | `docs/data/themes/school-nickname-ban.json` の `collected_count`。正典配列の長さ483とも一致 |
| 意見件数 | 100件（意見でない383件。うち学校の呼称に関連180件） | `opinion_count`。正典 `classification.is_opinion` / `is_relevant` を集計 |
| 論点（6＋その他0） | 一律禁止の実効性36／いじめ・心理的安全29／親しさ・呼称文化13／学校運用・現場体験12／さん付け・ジェンダー配慮6／本人意思・柔軟運用4 | 公開JSON `issues[].count`（正典 `main_issue` の集計と一致） |
| 立場（4区分） | 一律禁止に反対50／中立・情報31／禁止支持10／条件付き・個別対応9 | 正典 `classification.stance`（意見のみ）。HTML「50%・59%」は反対＋条件付き |
| 収集期間・最終更新 | 2026-06-22〜2026-09-20／更新2026-09-20、公開2026-06-24。次回収集予定2026-10-18 | `THEMES.yaml` の `sample_period` `updated_at` `published_at` `collect_at` |
| 再読（理由区分）データ | あり。100件すべてに割当済み、13理由区分。除外1件（質問のみ） | `data/school-nickname-ban_issues-reread.json` の `items` `buckets` `excluded_items`。2026-10-10に未読13件を追い読み |
| 理由区分の論点別件数 | 実効性36＝禁止への違和感18＋実効性・理由の説明16＋人間関係への影響の推測2／いじめ29＝被害の記憶9＋嫌な呼び名を避ける禁止8＋いじめと呼び名の結びつき9＋被害への対処3／親しさ13＝残したい11＋愛称のよさと対応2／学校運用12＝昔と今4＋周知・指導の実際8／さん付け6＝1区分／本人意思4＝1区分 | 同ファイル `buckets[論点][group].count` |
| 一次資料メモ | 確認日2026-09-07（全面取り直し）。ページ側の制度確認日2026-09-12 | `quality/research/school-nickname-ban-primary-sources.md`、`data/verification/school-nickname-ban-background.json` の `checked_on` |
| 推移 | 2回分のみ（8/17回 意見24件、9/20回 意見13件）。「一律禁止に反対」37.5%→72.7%（+35.2pt） | `social-samples/updates/school-nickname-ban/{2026-08-17,2026-09-20}/classified.json`、作業記録 |
| 公開状態 | `published: done`、既に山なみ＋論点連動（課題77）の構成。理由・X埋め込み・制度確認・出典・主張照合が論点ごとに連動済み | 現行HTML、`scripts/school_nickname_connected*.py` |

## 2. 棚卸し表（現行 `docs/school-nickname-ban-reaction-map.html` を上から）

配置先の略：冒頭／全体像（意見の全体像）／論点別／背景／不要。

| # | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | メタ | title「学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否」、description、canonical、OGP（ogp/school-nickname-ban.png）、Article・FAQPage構造化データ | `configs/theme-seo.json`、`scripts/seo/apply_theme_trust.py`、`generate_seo_assets.py`。FAQ JSON-LDは `school_nickname_connected_content.py` | 維持（head） | - |
| 2 | 進捗表示 | 「探ったところ 0」（操作した地点数。スクロールでは増えない） | `theme-design.js` 等の汎用計測。文言は2026-09-29の検索入口作業で変更 | 維持 | - |
| 3 | 冒頭 | ヒーロー写真、パンくず（トップ/教育・日常論争）、「SNSの意見 100件」バッジ | 件数は `build_nickname_arena.py`。画像は `images/topics/school-nickname-ban/` | 冒頭 | - |
| 4 | 見出し | H1「学校のあだ名禁止はなぜ？…」、サブ「傷つく呼び方を防ぐルールか、関係性を縛る一律規制か」、リード1文 | `build_nickname_arena.py` ほか手書き文言 | 冒頭 | - |
| 5 | 結論ボックス | 「議論の中心：一律に禁止して、本当に効果があるのか」＋件数バッジ（36件） | `build_nickname_arena.py` の `CONCLUSION_ISSUE` / `apply_conclusion_count()` | 冒頭（件数の見せ方に統合） | - |
| 6 | 検索入口（search-entry） | 「学校のあだ名禁止はなぜ？先に3点」3タブ：①全国の決まり（全国一律の禁止ではない）②嫌な呼び名（いじめになりうる）③ルールの範囲（3つのルールは別）。各タブにSNS上の期待と懸念、「山並みマップで見る」ボタン | `scripts/school_nickname_connected_content.py` の `GUIDES`（手書き） | 冒頭（疑問と短答の起点） | - |
| 7 | 注意文 | 「論点の選択は投票ではなく表示の切り替え」 | 同上 | 冒頭〜全体像 | - |
| 8 | ページ内リンク | 「SNS 100意見を6論点で比べる」→#planet-block、「よくある質問を先に読む」→#school-nickname-faq | 同上（件数は生成） | 冒頭 | - |
| 9 | 日付注記 | 「国の資料の確認日 2026-09-12。個別校のルールや導入校の割合を示すものではありません」 | `background.json` の `checked_on` | 冒頭（短答の直下） | - |
| 10 | 立場の内訳 | 見出し「反対が意見の50%を占める」、条件付きを足すと59%、禁止賛成10件。100マス内訳（禁止支持10・条件付き9・反対50・中立31）、立場フィルタ4つ、「投票にはカウントされません」 | `build_nickname_arena.py`（正典から） | 全体像 | - |
| 11 | 母数注記 | 「元データ：Yahooリアルタイム検索の公開投稿483件、取得期間2026-06-22〜09-20、世論調査ではありません」 | 同上 | 全体像（注記）＋背景 | - |
| 12 | 背景パネル（bukatsu-background） | 一言定義、なぜ始まったか2段落、経緯3点（2013年いじめ防止対策推進法／2017年国の基本方針／2022年生徒指導提要）と各出典リンク、「意見の分布を先に見る」リンク | `data/verification/school-nickname-ban-background.json`（手書きの正典） | 背景（開閉）。定義1文は冒頭の短答に再利用可 | - |
| 13 | 「同じ禁止でも何をやめるルールか」 | 4観点（ルールの範囲／目的と理由／本人の経験／見直しの方法）＋各出典、「このページで未確認のこと」 | 同 `background.json` | 冒頭の比較表の候補。論点別の「制度の確認」にも再掲 | 出典リンクは重複するので1か所に集約 |
| 14 | 山なみマップ（planet-panel） | 見出し、問い「学校で『あだ名禁止』を指導すべきか」、期間・483件・意見100件・更新日、SVG山なみ（幅＝意見数、高さ＝強い表現の割合）、100マス、件数・割合 | `window.PLANET_DATA`（`build_planet_data.py` / `build_nickname_arena.py`）、`school-nickname-ban-arena-data.js` | 全体像 | - |
| 15 | フォールバック一覧 | JS非対応時の6論点リンク一覧（絵文字付き） | 同上 | 全体像（JSなし表示として維持） | - |
| 16 | 論点別パネル6つ | 各論点：立場チップ、理由区分、主な立場、一次資料との照合結果、「資料にあるのにSNSにないこと」へのリンク、「論点の一覧へ戻る」。絵文字は📏🛡️🤝🏫🏷️💬 | `school_nickname_connected_content.py`（HTML）と `school_nickname_connected.py`（接続） | 論点別 | - |
| 17 | 一次資料クイズ | 見出し「一次資料クイズ」のみ（本体は主張照合に統合済み） | 現行HTMLの見出し残り | 不要 | 本体が無い空見出し。主張照合4件（#19）に統合済み |
| 18 | 資料にしかない話（ocean） | 沈んだ大陸4件（校則見直しの手続き／柔軟対応でも組織へ共有／謝罪だけでは解消としない／具体内容は各校が決める＝法第13条）と、立場をこえた同じ心配1本（悪意ある呼び名で子供が傷つくのを防ぎたい） | `data/verification/school-nickname-ban-sunk-continents.json`、`-veins.json` | 論点別（紐づく論点の資料欄）＋背景 | - |
| 19 | 主張照合4件 | 「今の学校では禁止が普通」＝裏が取れない／「憲法違反なので従う必要がない」＝裏が取れない／「ルールは理由を理解できるよう指導」＝資料どおり／「嫌な呼び名はいじめにつながる」＝資料どおり。確認日2026-09-12 | `data/verification/school-nickname-ban-claims.json`、`scripts/build_nickname_process_sections.py` の `FACT_CHECKS`、`data/school-nickname-ban_claim_posts.json` | 論点別 | - |
| 20 | 編集部の横断整理 | 共通する前提／本当の対立（親しさ13件×いじめ29件、禁止と全員さん付けは別）／まだ分からないこと | `data/verification/school-nickname-ban-editorial.json` | 全体像（山なみの直下） | - |
| 21 | 「このページの見かた」 | 山の幅・高さ・色の読み方、小標本の注意 | `build_nickname_arena.py` ほか | 全体像（凡例）。重複説明は縮める | - |
| 22 | 論点一覧（押すと地図が切り替わる） | 見出しのみ。動的表示 | 汎用JS | 全体像 | - |
| 23 | 潮目ウィジェット | 立場の変化／論点の変化、「8月17日→9月20日、一律禁止に反対が35.2pt増加」、再生ボタン、比較対象と小標本の注意 | `scripts/inject_tide_widget.py`、`scripts/refresh_adapters/nickname.py` の `_apply_tide` | 全体像（推移） | - |
| 24 | 論点ごとのX投稿 | 6論点×代表2件（12件）と要約ラベル（例：あだ名がいじめの原因だったため禁止に賛成）、「地図へ戻る」 | `scripts/nickname_issue_media.py`（正典の `article_usable` かつ low risk から編集部選定）。埋め込みは `scripts/x_embed.py` | 論点別（最大2件） | 「地図へ戻る」リンクは新構成では不要 |
| 25 | 投票 | 「一番気になる論点は？」6論点＋立場3＝18択（`school-nickname-ban-issue-stance-v1`）、Xでシェア、選び直す | `vote-store.js`、`vote-config.js`。adapterが選択肢18を検査 | 維持（末尾付近。保護対象） | - |
| 26 | 授業・探究学習 | ディベート用：禁止支持側の理由3、反対側の理由3（論点へのリンク）、確かめる一次資料3、問いの例3、使い方、印刷ボタン | `scripts/seo/apply_classroom_section.py` | 背景（開閉）。授業用として残す | - |
| 27 | 編集・分析情報 | 公開日2026-06-24、最終更新2026-09-20、編集部リンク、収集方法、データの読み方、訂正窓口 | `scripts/seo/apply_theme_trust.py` | 背景（出典・確認日・限界）。公開日は維持 | - |
| 28 | FAQ（10問＋注意） | 法律か／文科省は求めているか／なぜ小学校で行うか／嫌なあだ名はいじめか／禁止とさん付けは同じか／メリット／デメリット／本人希望のあだ名／見直せるか／SNS比率は世論調査か。末尾「今つらい場合」の案内 | `school_nickname_connected_content.py` の `FAQS`（手書き） | 冒頭または背景（短答の根拠）。つらい場合の案内は冒頭近くに維持 | - |
| 29 | 関連テーマ | 次に読むテーマ（ai-copyright、bukatsu-chiiki、bike-blue-ticket ほか） | 共通部品 | 維持（末尾） | - |
| 30 | 調査上の注意（開閉） | 読み方、世論調査でない旨、偏り | 共通部品（`detail-data`） | 背景（限界の項に統合） | 他の注記と重複 |
| 31 | フッター | トップ、運営者情報、調査方法、お問い合わせ、プライバシー、免責、画像制作方針、応援 | 共通部品 | 維持 | - |
| 32 | 選んだ論点の詳細（論点ごと） | 〈理由区分ごとの開閉〉区分名・件数・要約・「この理由の投稿をXで読む」・X埋め込み／「実際の投稿を読む」代表2件／「この論点に関わる制度は？」（観点別の開閉と出典）／「同じ心配から違う結論へ」／「制度の経緯」（2013・2017・2022と出典）／「投稿の主張と一次資料」／「全体に関わる資料」 | `school_nickname_connected_content.py`、データは `data/school-nickname-ban_issues-reread.json`、`PLANET_DATA` | 論点別（中核）。主張・資料欄が複数論点で同じ文を繰り返すのは整理対象 | 「地図へ戻る」型の往復リンクは不要 |
| 33 | 一次資料リンク（出現順） | e-Gov いじめ防止対策推進法／文科省 いじめの防止等のための基本的な方針／文科省 生徒指導提要（改訂版）の3本（ページ内で計約20か所に再掲） | `background.json` ほか各生成元 | 論点別＋背景に集約 | 再掲は1リンク集に統合 |
| 34 | 確認日 | 2026-09-12（制度・主張照合）、2026-09-20（資料にしかない話・更新日） | `background.json`、`sunk-continents.json`、`claims.json`、公開JSON | 維持 | - |
| 35 | X投稿URL | ページ内の異なる投稿URL計36件（山なみ代表12＋理由区分別ほか）。アリーナの点100件（`NICKNAME_ARENA_DATA`）にも各URL | HTML、`docs/school-nickname-ban-arena-data.js` | 論点別（最大2件、開いたとき読み込み） | - |
| 36 | ページ内リンク | #planet-block、#school-nickname-faq、#ocean、#fallback-nav、#fb-…（論点6）、#issue-…（授業欄から） | 各生成元 | 新構成で再付与。既存アンカーは外部リンク・検索結果に残る可能性があるため維持を検討 | - |

出典の未取得分：#32の理由区分ごとの開閉（13区分）は上の6論点の中に入っており、区分名と件数は §1 に列挙済み。

## 3. データ対応表（正典 → 公開JSON → HTML）

| 項目 | 正典 | 公開JSON | HTMLを作る処理 | 手入力・重複 |
|---|---|---|---|---|
| 収集件数（483） | `social-samples/school-nickname-ban_hermes_arena_classified.json`（`THEMES.yaml` の `sample_file`） | `docs/data/themes/school-nickname-ban.json` `collected_count`（`scripts/build_public_registry.py`） | `scripts/build_nickname_arena.py`（`--public-counts-only` で公開JSONの数を貼る）。更新時は `scripts/refresh_adapters/nickname.py` が呼ぶ | 手入力なし。ただしFAQ・潮目の注意文に文言として数字が入る箇所は未確認 |
| 意見件数（100） | 同上 `is_opinion` | `opinion_count` `issue_assigned_count` | 同上。ヒーロー、リード、山なみ、投票STEP1、詳細表 | 作業記録（`themes/school-nickname-ban.md`）に過去の数字が残る（記録のみ） |
| 論点別件数 | 同上 `main_issue` | `issues[].count`、`issues[].stances[]` | `build_nickname_arena.py`（山なみ、フォールバック、論点ナビ、`conclusion-count`）。接続は `scripts/school_nickname_connected.py`（`PLANET_DATA`が件数の正本） | 論点ラベル・ID・絵文字は `build_nickname_arena.py` と `school_nickname_connected_content.py` と `inject_tide_widget.py` と `build_planet_data.py` に分散（他テーマと共有するのは後2者） |
| 立場（4区分、50%・59%） | 同上 `stance` | `issues[].stances[]` | `build_nickname_arena.py`（立場内訳・100マス・見出し文） | 見出し文「反対が50%」は生成と思われるが、書き換え箇所は未確認 |
| 理由区分（13） | `data/school-nickname-ban_issues-reread.json`（`buckets`、`items`） | 公開JSONには理由の項目なし（`issues`に `reasons` なし） | `build_nickname_arena.py` が再読検査（不一致なら停止）、`school_nickname_connected_content.py` が理由欄を作る | 区分名と件数は再読台帳が正。管理は `scripts/manage_reread_registry.py`、`reread_registry.py`。**区分名がHTML側に重複して持たれていないかは未確認** |
| 推移（8/17→9/20） | `social-samples/updates/school-nickname-ban/<日付>/classified.json`（2回分のみ） | なし | `scripts/inject_tide_widget.py`、adapterの `_apply_tide` | 小標本の注意文は手書き。**日付別の件数の推移JSONは存在しない** |
| 一次資料・制度背景 | `quality/research/school-nickname-ban-primary-sources.md`（確認日2026-09-07、人が読むメモ） | 公開JSON `ocean_layer` `claim_verification` の一部のみ | `data/verification/school-nickname-ban-background.json`（手書きの定義・経緯・4観点・出典）→ `school_nickname_connected_content.py` | メモと `background.json` は連動しない手書き二重管理。確認日が2026-09-07と2026-09-12で食い違う。出典URLは約20か所に再掲（出所は `background.json`、`FACT_CHECKS`、`claims.json`、授業欄、FAQ） |
| 主張照合 | `data/verification/school-nickname-ban-claims.json`、`data/school-nickname-ban_claim_posts.json`（匿名キー） | `claim_verification`（4件） | `scripts/build_nickname_process_sections.py` の `FACT_CHECKS` ほか | **`FACT_CHECKS` のPython直書きと `claims.json` の二重定義**（判定・文言）。日付「2026年9月12日」は文字列直書き |
| 資料にしかない話 | `data/verification/school-nickname-ban-sunk-continents.json`、`-veins.json` | `ocean_layer` | 連動スクリプト | `sns_base` は更新のたびに手で合わせる（9/20回に実作業あり） |
| 編集部整理 | `data/verification/school-nickname-ban-editorial.json` | `editorial_summary` | 同上 | 文中に「13件」「29件」を直書き（件数が変わると手直しが必要） |
| 投稿URL（代表） | `scripts/nickname_issue_media.py` が正典から選定（`article_usable`・low risk） | 公開JSONには入っていない | 同スクリプト（`--write-html`）＋ `scripts/x_embed.py` | 代表選定はスクリプト内の指定。理由区分別の投稿は再読台帳の `post_key` から |
| 点（アリーナ） | 正典 | なし | `docs/school-nickname-ban-arena-data.js`（100点、各URL付き）を `build_nickname_arena.py` が出力 | JS内に投稿の要約ラベルが直書きで出る（生成物） |
| FAQ・検索入口 | なし（手書きが正典） | なし | `school_nickname_connected_content.py` の `FAQS` `GUIDES` | 同じ答えが「検索入口」「FAQ」「背景」「授業欄」で重複 |
| 日付（公開・更新） | `THEMES.yaml` | `updated_on` | `apply_theme_trust.py`、`build_nickname_arena.py` | 作業記録・配信ページに複数 |

更新時の入口：`scripts/refresh_adapters/nickname.py`（`page_update_mode: adapter`。同じ入力で2回実行して差分ゼロを検査、投票互換18択と保護タグ（GA4・AdSense・vote-store）の個数を検査）。

## 4. このテーマならではの疑問の候補

既存の検索入口部品が先にある：「学校のあだ名禁止はなぜ？先に3点」（①全国の決まり ②嫌な呼び名 ③ルールの範囲）と、FAQ10問（§2 #6・#28）。下は**原稿からの推測**で、検索ツール（ラッコキーワード、キーワードプランナー、Trends、Search Console）は使っていない。検索規模・時期変動は未確認。

1. 学校のあだ名禁止は法律や文科省で決まっているのか（現行の短答1つめ。答え：確認した範囲では全国一律の定めなし）
2. あだ名禁止とさん付けは同じことか（呼び捨て・くん・ちゃんを含む範囲の違い）
3. 嫌なあだ名はいじめに当たるのか（受け手の苦痛で判断する定義）
4. なぜ小学校でさん付け・あだ名禁止になったのか（理由と経緯）
5. あだ名禁止のメリット・デメリットは何か（FAQにあり）
6. 本人が希望するあだ名、親しい愛称も禁止なのか
7. 学校のルールに納得できないとき、見直しを求められるか（子供や保護者の意見聴取）
8. 禁止して実際にいじめは減るのか（SNSでは最多論点。資料からは効果を言えない＝「未確認」と答える設計が必要）

## 5. 部活動と違う点・判断が必要な点

1. **既に論点連動の画面がある。** 部活動は初画面から作り直しだが、このテーマは2026-09-29に検索入口（3タブ）とFAQを追加済みで、論点ごとの理由・X・制度確認・主張照合も連動している。作り直す範囲は「検索入口と山なみの順序」「重複の整理」「冒頭の図柄」になる。どこまで壊して作り直すか（判断1）。
2. **論点が6つで、うち3つが小さい。** 6論点のうち3つは、理由区分が1つだけ（さん付け6件、本人意思4件）または2つ（親しさ13件）。件数が小さい論点に同じ型を当てるか、まとめる/短くするか（判断2）。部活動の論点数との比較は未確認。
3. **一次資料は3本で薄いが、結論の方向は強い。** 「全国一律の定めは確認できない」という否定の事実が核。主張照合は4件のみ（うち2件は「裏が取れない」）。「確認できなかったこと」（事務連絡の原文、判例名）が残る。冒頭の短答を断定にしない言い方の設計が要る（判断3）。
4. **再読データの欠けは無い（100件すべて割当）。** ただし公開JSONに理由が入っていないため、新ページで理由を表示するには再読台帳を直接読む経路を維持するか、公開JSONへ理由を足すか決める必要がある（`public_registry` 契約の変更になる）。
5. **投稿埋め込みの可否。** ページ内URLは36件で、ブラウザで埋め込み表示が通るか、削除済み投稿がないかは今回未確認。アリーナの点には `x.com/grok` 名義の2件（意見ではなく自動応答の可能性）が含まれ、代表投稿に選ばないか確認が要る。1362980759842091008 など2021〜22年の古い投稿も代表に入っている。
6. **共有スクリプト。** `build_planet_data.py`、`inject_tide_widget.py`、`apply_theme_design.py`、`verify_theme_page.py`、`seo/apply_theme_trust.py`、`seo/apply_classroom_section.py` は複数テーマ共通。このテーマ専用は `build_nickname_arena.py`（1321行）、`school_nickname_connected*.py`、`nickname_issue_media.py`、`build_nickname_process_sections.py`、`refresh_adapters/nickname.py`。部活動用に `scripts/bukatsu_redesign/` が既にあり、共通化するかテーマ別に作るかは未決（判断4）。
7. **二重管理の整理。** 一次資料メモ（9/07）と `background.json`（9/12）、`FACT_CHECKS` と `claims.json`、FAQ・検索入口・背景の文言重複（§3）。
8. **推移が2回分のみ。** 次回収集は2026-10-18。それまで推移は「8/17と9/20の比較」だけで、折れ線にできる点数がない。
9. **安全面。** 当事者のつらい経験を扱うため、「今つらい場合」の案内を冒頭近くに残す設計が要る。

判断の優先順位（私案）：①作り直す範囲（検索入口を軸に既存の連動を活かす案を推す）②小さい論点の扱い③推移の見せ方。

## 6. 読めなかったもの・確認していないもの

- ラッコキーワード、Googleキーワードプランナー、Google Trends、Search Console：検索ツールは使っていない。検索規模・時期変動・既存URLの表示/クリック/検索語はすべて未確認。
- ブラウザでの実画面（PC・375px）、X埋め込みの表示可否、JavaScript無しの表示：未確認。HTMLのテキストと構造のみ読んだ。
- `themes/school-nickname-ban.md` は冒頭と最近の節のみ。2026-09-06〜09-12の節（修復候補・独立監査）の中身は読んでいない。`quality/reviews/` 配下の各レビュー、`quality/research/` の資料D（問題行動調査の数値）の詳細は読んでいない。
- 公開HTML内のCSS/JS（`school-nickname-connected.css/.js/-page.js`、`topic-modern.*`）の挙動、`PLANET_DATA` 全体の中身。
- 各スクリプトの中身は入出力の把握のみ（`build_nickname_arena.py` 1321行は冒頭と呼び出し箇所だけ）。「立場見出しの50%」等が生成か手書きかは断定していない。
- `configs/school-nickname-ban-reaction-map.json`、`configs/page-originality.json`、`configs/theme-seo.json` の該当項目の内容。
- 一次資料の現時点での再確認（URLの生存、法令改正）はしていない。メモの確認日をそのまま引いた。
- 各テーマの論点数の比較（部活動など）は数えていない。
