# 皇室典範改正（koshitsu-tenpakai）リニューアル準備：棚卸しと内容対応表

作成日 2026-10-11。手順書 23_テーマ別リニューアル移植手順 の手順1（棚卸し）と手順3（内容対応表・データ対応表）に当たる。HTML試作・スクリプト変更・検索ツール調査は含まない。既存ファイルは変更していない。

## 1. 現状の要約

- 収集 2,565件／意見 2,016件。出所: `docs/data/themes/koshitsu-tenpakai.json` の `collected_count` `opinion_count`。正典 `social-samples/koshitsu-tenpakai_release_20260913.json`（配列2,565件、`classification.is_opinion` が真で2,016件）と一致。
- 論点（6、`issues[].count`、正典の `main_issue` で意見のみ集計も一致）: 男系vs女系 570／旧宮家養子縁組 347／その他 299／立法手続き・民主主義 281／愛子さま・皇族の地位 260／女性天皇・女系天皇 259。
- 立場（今回案全体への評価、5区分、意見2,016件、正典の `classification.stance` を `is_opinion` で絞って集計）: 支持 46／反対 404／条件付き 26／未表明 1,511／読み取れない 29。画面の内訳の合計と一致。全2,565件で数えると未表明は2,060で、画面の1,511とは対象が違う。
- 最終更新 2026-10-05（公開JSON `updated_on`、THEMES.yaml `updated_at`）。収集期間 2026-07-26〜2026-10-05。次回更新予定 2026-10-15（`refresh_at`）。
- 再読（理由区分）データあり: `data/koshitsu-tenpakai_issues-reread.json`（`items` 2,016件、`review_kind` はすべて `editorial_body_reread`）。意見2,016件すべてが理由区分に接続済み（2026-10-10追い読みで667件を追加、`catchup_2026_10_10.added`）。論点別の件数は意見数と同じ（男系570、養子347、その他299、立法281、愛子260、女性天皇259）。理由区分の種類数は男系8、女性天皇9、養子8、愛子9、立法6、その他9。
- 一次資料メモ `quality/research/koshitsu-tenpakai-primary-sources.md`（222行）の確認日は 2026-08-30（10箇所）／08-31／09-07（5箇所）／09-13（背景部分のみの再確認）。最新は 2026-09-13。ページ側の資料照合6件の確認日も 2026-09-13。
- 背景台帳 `data/verification/koshitsu-tenpakai-background.json`（checked_on 2026-09-13）、主張照合 `...-claims.json`（21件の該当投稿）、語られていない争点 `...-sunk-continents.json`（4件、10-05更新）、共通の心配 `...-veins.json`（1件）、編集部整理 `...-editorial.json`（4件）。
- 現行ページは既に「連動版」（`koshitsu_connected*`）で、論点を選ぶと読書面（理由・投稿例・資料照合・制度確認）が出る。旧セクション（claim-audit・issue-cards・ocean・bukatsu-check）は `docs/koshitsu-connected-page.js` で非表示にして再配置している。
- 投票は `koshitsu-tenpakai-issue-stance-v2`（6論点×4立場=24選択肢）。

## 2. 棚卸し表（現行ページ docs/koshitsu-tenpakai-reaction-map.html、上から順）

出所の略称: ARENA = `scripts/build_koshitsu_arena.py`／AUDIT = `scripts/build_koshitsu_process_sections.py`／CONN = `scripts/koshitsu_connected.py`＋`koshitsu_connected_content.py`／TRUST = `configs/theme-seo.json`＋`scripts/seo/apply_theme_trust.py`／手書き = 生成元スクリプトが見つからないHTML直書き。配置先の「全体」は意見の全体像。

| 番号 | 種類 | 内容の要約 | 出所 | 新ページでの配置先 | 不要の理由 |
|---|---|---|---|---|---|
| 1 | メタ | title「皇室典範改正で何が変わる？女性皇族・旧宮家養子の論点｜SNS反応まっぷ」、description、canonical、OG画像 koshitsu-hero.webp、Article JSON-LD（公開2026-07-18／更新2026-10-05） | `scripts/seo/apply_meta_tags.py`（SEO_META）／JSON-LD生成元は未確認 | 冒頭（維持） | - |
| 2 | 進捗バー | 「読んだところ」質問・山・クイズで増える | 共通 theme-design.js 系 | 冒頭（共通部品） | - |
| 3 | ヘッダー | トップへの戻り、バッジ「皇室・憲法」 | 手書き＋共通 | 冒頭 | - |
| 4 | 件数 | 「SNSの意見 2,016件」帯（THEME_COUNT） | `scripts/apply_theme_design.py` | 冒頭 | - |
| 5 | 見出し | h1「皇室典範改正で何が変わる？…」、リード「皇族の人数と、皇位を継ぐ資格。二つを分けて読む。」 | 手書き（ARENA がhero lead件数を更新） | 冒頭 | - |
| 6 | 注記 | 「世論調査ではありません。2,565件から意見2,016件」 | ARENA（件数のみ生成、文は固定） | 冒頭 | - |
| 7 | 結論カード | 「議論の中心：継承資格の線引き 570件」 | ARENA（`conclusion-count`） | 冒頭または全体 | - |
| 8 | 先に答える | 「3分でわかる」見出しと「2026年9月30日時点で成立・公布済み、主な規定は施行前」 | 手書き（生成元なし、テストのみ `tests/test_koshitsu_quick_guide.py`） | 冒頭 | 日付表現は更新時に古くなる（要見直し） |
| 9 | 日付チップ | 成立7月17日／公布7月24日／主な施行10月24日 | 手書き | 冒頭 | - |
| 10 | 切替カード3枚 | 変わること1「女性皇族は結婚後も皇族に」、変わること2「旧11宮家の男系男子を養子に」、変わらないこと「天皇になれる資格は現行のまま」 | 手書き | 冒頭 | - |
| 11 | 結果欄 | カード選択で説明と「山なみで『愛子さま・皇族の地位』を見る」ボタン（3枚とも論点へ接続） | 手書き＋`docs/koshitsu-connected*.js` | 冒頭→論点別への導線 | - |
| 12 | 一次資料リンク | e-Gov 皇室典範、2026-10-24施行版条文。「具体的な養子候補や本人の意向は未確認」 | 手書き | 冒頭 | - |
| 13 | FAQ（6問）＋FAQ JSON-LD | 成立・施行時期／変わる二点／愛子さまは決まったか／配偶者と子は皇族か／養子本人の継承資格／養子候補は決まったか | 手書き（表示文とJSON-LDを一致させるテストあり） | 冒頭（短答） | - |
| 14 | 立場の内訳 | 「なぜ賛否を示さない投稿が多いのか」。2,016件を5立場に（支持46・反対404・条件付き26・未表明1,511・読み取れない29）、バーと5ボタン（押しても投票にならない旨） | ARENA（STANCE_GLANCE）＋CONN（ボタン⇄山の立場フィルター連動） | 意見の全体像 | - |
| 15 | 調査条件 | Yahooリアルタイム検索の公開投稿2,565件、取得期間2026-07-26〜2026-10-05、世論調査ではない | ARENA（RESEARCH_CONDITIONS、`scripts/research_conditions.py`） | 意見の全体像（脚注）または背景 | - |
| 16 | 背景：定義 | 「何が、どこまで進んでいるのか」2段落（改正の中身、施行日、皇族と継承資格は別） | `data/verification/koshitsu-tenpakai-background.json`（definition）、文面は `scripts/koshitsu_background_detail.py` にも重複 | 背景 | - |
| 17 | 背景項目1 | 人数が減ると、どの役割に影響するのか（2017年退位特例法の決議、2021年有識者会議、臨時代行・皇室会議・摂政、慰問等）。出典：報告書1・6〜9頁 | `koshitsu_background_detail.py`（SECTIONS） | 背景 | - |
| 18 | 背景項目2 | 検討された3案と今回選んだ範囲（①婚姻後の身分保持②男系男子の養子③直接皇族化。今回は①②、第一条は不変）。出典：報告書9〜13頁、改正後条文 | 同上 | 背景 | - |
| 19 | 背景項目3 | 女性皇族が残ることと家族の身分（配偶者・子は皇族としない、第十五条、当事者への配慮）。出典：報告書10〜11頁 | 同上 | 背景（論点「愛子さま・皇族の地位」へも接続） | - |
| 20 | 背景項目4 | 養子制度は誰でも皇族になれる仕組みではない（第三十八条、15歳以上・配偶者と子なし・皇室会議、本人と子孫の扱い） | 同上 | 背景（論点「旧宮家養子縁組」へも接続） | - |
| 21 | 背景項目5 | 資料が挙げる期待と、なお残る課題（男子出産の重圧緩和の可能性、血縁の遠さ、理解と共感）。出典：報告書11〜12頁 | 同上 | 背景 | - |
| 22 | 年表 | 2021年12月 有識者会議報告／2026年7月24日 改正法公布／2026年10月24日 主要部分の施行予定。各出典付き。連動版で日付タブ化。成立7月17日は年表に無い | background.json（timeline 3件）。論点IDは無タグ | 背景（年表）。7月17日成立の追加は判断が必要 | - |
| 23 | 山なみへの導線 | 「意見の分布のほうを先に見る →」 | 手書き | 不要（新構成で冒頭から全体へ続くため） | 新構成で順序が変わる |
| 24 | 制度確認3項目 | 「皇族」と「天皇」を分けて読む：結婚後の身分／養子本人と子孫／女性天皇と女系天皇。各出典付き。連動版で論点別の読書面に分配 | background.json（checklist、論点IDはcheckerで付与）＋CONN | 論点別（愛子さま／養子／男系・女性天皇） | - |
| 25 | 未確認の明記 | 「養子候補の意向、施行後の運用実績は確かめていない」 | 手書き（bukatsu-check内） | 背景（未確認事項の枠） | - |
| 26 | 山なみ（PLANET） | 「SNS反応マップ」見出し・質問「今回の皇室典範改正をどう評価するか」・注意書き（収集期間、収集2,565／意見2,016、更新2026-10-05）・色の説明・予想2問（guesses）・立場フィルター（modes）・SVG（幅＝意見数、高さ＝強い表現の割合）・潜る操作 | ARENA（PLANET_DATA、`build_planet_page_preview.py` 系共通部品） | 意見の全体像 | - |
| 27 | 山なみ脚注 | 「山を押すと…」、「このページの見かた」説明、水面下の注意 | 共通部品 | 意見の全体像 | - |
| 28 | 100マス図 | 立場を絞ると件数は減るが割合は増える仕組み（waffle、件数・割合の前後表示） | 共通部品 | 意見の全体像 | - |
| 29 | 論点の一覧（図なし用） | 6論点へのリンク（件数・割合：28.3／17.2／14.8／13.9／12.9／12.8%）、JS無効時用 | ARENA（fallback-nav） | 意見の全体像（JSなしの本文） | - |
| 30 | 論点パネル×6 | 各論点：図解1枚、件数と割合、山の高さ、立場の内訳バー、「立場ごとにその立場の中での占有率」、理由の内訳（再読）、一次資料との照合、資料との照合、投稿例 | ARENA＋再読JSON＋CONN | 論点別 | - |
| 30a | 図解（6枚） | 男系 keisho-v5、養子 yoshi-v3、その他 sonota-v2、立法 shingi-v2、愛子 aiko-v3、女性天皇 josei-tenno-v3（webp、代替文あり、画像直下に注記） | `images/topics/koshitsu-tenpakai/*` を ARENA の画像設定と `koshitsu_issue_media.py` で参照 | 論点別 | 旧版の画像ファイルはディレクトリに残存（掃除は別判断） |
| 30b | 理由の内訳 | 男系：継承資格の選び方176／歴史・比較・実現性100／今回案全体への評価91／主張・説明への評価72／個別の制度への評価60／制度の説明・背景50／審議・説明・採決16／皇族と家族の暮らし5 ほか5論点も同様（件数は再読JSON `buckets`） | 再読JSON→ARENA・CONN | 論点別 | - |
| 31 | 一次資料クイズ | 「その主張、資料に当たるとどうなる？」見出し（中身は旧セクション内） | 共通クイズ部品（上位ページでは非表示/再配置） | 論点別（資料照合へ統合） | 連動版で読書面に統合済み。独立見出しは不要 |
| 32 | 資料にしかない話（語られていない争点）4件 | 養子の年齢条件（6件）／複数宮家と男子出生の重圧（3件）／附則第六条30年ごとの見直し（0件）／参院修正案が成立法に反映されず（0件）。各に件数・近い論点・再検索の記録・出典 | `data/verification/koshitsu-tenpakai-sunk-continents.json` | 論点別（養子2件、立法2件） | - |
| 33 | 立場をこえて同じ心配 | 「皇位継承を安定させたい」心配は支持・反対の双方にある。支持代表2・反対代表2。関わる論点：男系vs女系・旧宮家養子縁組 | `...-veins.json` | 論点別（男系・養子）または全体 | - |
| 34 | 編集部の横断整理 | 共通する前提／本当の対立／まだ分からないこと（未表明は中立ではない、山なみは全国比率でない） | `...-editorial.json` | 意見の全体像（読み方） | - |
| 35 | 論点の一覧（押すと切替） | 山なみの論点ボタン | 共通部品 | 意見の全体像 | - |
| 36 | 世論の潮目 | 9月27日→10月5日、支持が1.4ポイント減。前回251件／今回240件の構成比。立場の変化／論点の変化、再生ボタン、「世論全体の変化ではない」注記 | `scripts/inject_tide_widget.py` 系（`refresh_adapters/koshitsu.py` の `_apply_tide`）、入力は `social-samples/updates/koshitsu-tenpakai/` の収集回 | 意見の全体像（推移） | - |
| 37 | 資料照合（6件） | 主張6件：第一条（資料どおり・5件）／旧11宮家と施行日（資料どおり・5件）／養子本人の継承資格（資料どおり・3件）／有識者会議11人・7人（原典に届かず・1件）／継承資格者3名（原典に届かず・3件）／「直系優先かつ男子優先」（原典とズレ・4件）。計21件。照合日2026-09-13。数え方の注記あり | AUDIT、入力 `data/koshitsu-tenpakai_claim_posts.json` と `data/verification/koshitsu-tenpakai-claims.json` | 論点別（claim_1・5・6＝男系／愛子、2・3＝養子、4＝女性天皇） | - |
| 38 | 論点ごとのX投稿 | 6論点×2件=12件（論点見出しと件数、投稿の要約ラベル、「Xで見る」リンク）。ID：benjymin84/…262600、a_aok04352/…615144、5VcfqTGE08SrXGE/…762、ayumuchan3/…923、kazuhi2024/…492037、fi44504/…792025764197、so_far_away0712/…631、Aruhuvrv0/…432、oaVVaHIYjJ2s8Y6/…089、dainankosan/…488、77tMf5niwphliBQ/…904、fRdpHzPfSK70519/…571 | `scripts/koshitsu_issue_media.py` の MEDIA（投稿IDと要約ラベルを手入力）。埋め込みは Twitter widgets.js、失敗時はリンク | 論点別（最大2件） | - |
| 39 | 投票 | 「あなたはどの論点を重く見る？」2問（論点→総合評価）、topic `koshitsu-tenpakai-issue-stance-v2`、24選択肢、保存方法の注記、Xでシェア、やり直し | ARENA（VOTE_ISSUES／STANCES）＋共通 vote-store.js・Supabase Edge Function | 論点別の後または末尾（維持。24選択肢は変更不可） | - |
| 40 | 授業・ディベート | 支持側理由3・反対側理由3、確かめる一次資料3（e-Gov／内閣官房報告書／国会会議録）、問い3、使い方、印刷ボタン。理由文から論点へのリンク付き | 手書き（theme-seo.json か `scripts/seo/` の可能性あり、未確認） | 背景（開閉行） | - |
| 41 | このページの作り方 | 公開日2026年7月18日、最終更新日2026年10月5日、編集・分析：編集部、収集方法、「収集・分類で分かったこと」（8月10日の回、325件、女性天皇・女系天皇論点（140件）） | TRUST（`configs/theme-seo.json` 140行付近）。日付はADD生成だが固定文の部分あり | 背景（方法と限界） | 8月10日の回の記述と「140件」は現行値（259件）と食い違う。移植せず書き直す |
| 42 | 詳細データ表 | 論点×5立場（支持・反対・条件付き・未表明・読み取れない）の件数表。注記「未表明は中立ではない」「表現強度は従来のAI分類のまま」 | ARENA（詳細データ） | 背景（開閉行）または全体 | - |
| 43 | 次に読むテーマ | 憲法改正論議、副首都法案 | 共通（関連テーマ生成） | 末尾（維持） | - |
| 44 | フッター | トップ・運営者情報・調査方法・お問い合わせ（Googleフォーム）・プライバシー・免責・画像制作方針・Buy Me a Coffee | 共通 | 末尾（維持） | - |
| 45 | 計測・広告 | GA4、AdSense、vote-config、Edge Function | 共通 | 維持（保護対象） | - |
| 46 | ページ内リンク | `#planet-block` `#bukatsu-background` `#bukatsu-check` `#koshitsu-quick-guide` `#koshitsu-audit` `#issue-cards` `#vote-section` `#detail-data` `#related-topics`、`#fb-koshitsu-tenpakai-…`、`#issue-koshitsu-tenpakai-…`、`#aic-search-entry` は無し | 各生成元 | 既存URLのアンカーは維持が望ましい（外部から参照されているかは未確認） | - |

外部リンク（ページ全体の重複を除く）: e-Gov現行条文／e-Gov 10-24施行版API／内閣官房報告書PDF（令和3年12月22日）／内閣官房 第11回資料1／国会会議録 令和8年7月15日 発言093／国会会議録 令和8年7月16日（参院特別委 第3号）。確認日として画面に出る日付: 2026-09-13（資料照合・制度確認）、2026-10-05（件数・潮目・資料にしかない話）、2026-09-27（資料にしかない話の再検索記録）、2026-09-18（同）。

## 3. データ対応表

| 項目 | 正典 | 公開JSON | HTML（生成元スクリプト） | 手入力・重複 |
|---|---|---|---|---|
| 収集件数／意見件数 | `social-samples/koshitsu-tenpakai_release_20260913.json`（THEMES.yaml `sample_file`） | `data/public/themes/koshitsu-tenpakai.json` → `docs/data/themes/koshitsu-tenpakai.json`（`build_public_registry.py --topic koshitsu-tenpakai`） | ARENA `--public-counts-only`（`refresh_adapters/koshitsu.py` の `finalize`）。PLANET_DATA の `totals`、ヒーロー件数帯、調査条件、図の注意書き | 「2,565」「2,016」が HTML 本文の複数箇所（結論カード、立場の内訳、このページの作り方）に出る。多くは生成だが、手書きの文章内の数字は要確認 |
| 論点別件数 | 同上（`main_issue`、`is_opinion`） | `issues[].count` | ARENA（fallback-nav、論点パネル、詳細データ表）、`sync_issue_counts.py` | `configs/koshitsu-tenpakai-reaction-map.json` の `issue_counts.basis=public_json` でJSON参照。カード用 `cards` に旧タイトル5件（「男系維持 vs 女系容認」など）が残る |
| 立場 | `classification.stance` | `issues[].stances[]`（5区分、強度別も） | ARENA（STANCE_GLANCE、PLANET_DATA の `stances`、色コード）。CONN がバーと山を連動 | 色コード（#2F8F83 他）は PLANET_DATA と立場バーに重複（どちらも生成） |
| 理由（再読） | `data/koshitsu-tenpakai_issues-reread.json`（`buckets` `items`）。`data/verification/koshitsu-tenpakai-issues-reread.json` は別形式の配列（2,016件、構造は未確認） | 公開JSONには理由区分なし（未確認：`issues` に理由キーは無い） | CONN（`koshitsu_connected_content.py` が読書面を生成）。`scripts/koshitsu_count_provenance.py` が件数を照合 | ラベル名は再読JSONの `buckets` が唯一のはず。ARENA 内に重複があるかは未確認 |
| 推移（潮目） | `social-samples/updates/koshitsu-tenpakai/`（2026-08-10, 08-17, 08-24, 09-18, 09-27, 10-05 の収集回） | 無し | `inject_tide_widget.py`（`_apply_tide`、前回=直前の収集回、今回=今回の分類済み収集回） | `configs/koshitsu-tenpakai-reaction-map.json` の `number_provenance.sources` が旧ファイル `..._hermes_prev_synthetic.json`／`..._hermes_cur_20260726.json` を指したまま（現状の潮目とは別物の可能性、未確認） |
| 一次資料（背景・制度確認） | `quality/research/koshitsu-tenpakai-primary-sources.md`（人が読むメモ）→ `data/verification/koshitsu-tenpakai-background.json` | 無し | CONN（`koshitsu_connected.py` がbackground.jsonを読む）。背景本文は `koshitsu_background_detail.py` の SECTIONS にも保持 | 背景の本文が background.json と `koshitsu_background_detail.py` の両方にある（二重管理の疑い）。出典URLは手入力 |
| 資料照合（主張6件） | `data/koshitsu-tenpakai_claim_posts.json`（投稿ID）＋`data/verification/koshitsu-tenpakai-claims.json`（判定・出典） | `claim_verification`（6件） | AUDIT。`CANONICAL_JSON` が古い `social-samples/koshitsu-tenpakai_hermes_cur_20260726.json` を指している点に注意（現在の `sample_file` と別） | 照合日 2026-09-13 は JSON 内。「合わせて21件」は生成 |
| 資料にしかない話・共通の心配・編集部整理 | `data/verification/koshitsu-tenpakai-sunk-continents.json`／`-veins.json`／`-editorial.json` | `ocean_layer` `editorial_summary` | CONN 経由でページへ | `sns_base`（意見数）が各項目に入っており、更新のたび再検索記録を手で追記している |
| 投稿URL | 正典の `url`（2,565件） | 無し（`ocean_layer`/veins に一部） | `koshitsu_issue_media.py` の MEDIA（12件の投稿IDと要約ラベルを手入力）。`restore_issue_media` がHTMLへ戻す | 投稿IDと要約ラベルは手入力。要約ラベルは正典の `summary` とは別 |
| 図解画像 | `images/topics/koshitsu-tenpakai/` | 無し | ARENA の画像設定、`koshitsu_issue_media.py` の MEDIA | 論点→ファイル名の対応が2箇所（ARENAとMEDIA）。画像に件数・％を焼き込まないルール（`creative/manga-prompts/koshitsu-tenpakai-infographic-prompts.md`） |
| 3分でわかる／FAQ | 無し（正典なし） | 無し | **生成元なし（HTML直書き）**。検査は `tests/test_koshitsu_quick_guide.py`（FAQの表示文とJSON-LDの一致） | 手入力。日付（成立・公布・施行）が本文に直接入る。更新時に手で直す必要がある |
| ページの作り方（収集方法・分かったこと） | 無し | 無し | `configs/theme-seo.json` → `scripts/seo/apply_theme_trust.py` | 固定文に「8月10日の回・325件」「論点（140件）」が残り、現行値と不一致 |
| 投票 | `refresh_adapters/koshitsu.py`（VOTE_TOPIC `koshitsu-tenpakai-issue-stance-v2`、VOTE_CHOICES=24） | 無し | ARENA（VOTE_ISSUES、STANCES）。保護対象 | `supabase/functions/cast-vote/index.ts` に `-v2: 24` を手書き（v1:28 も残存）。選択肢数を変えると投票側の再デプロイが必要 |
| 日付・期間 | `THEMES.yaml`（`sample_period` `updated_at` `refresh_at`） | `collection_period` `updated_on` | ARENA、`sync_portal_stats.py`、`verify_sample_periods.py` | Article JSON-LD の `dateModified`、バッジ類にも重複 |

## 4. このテーマならではの疑問の候補（原稿からの推測）

検索ツール（ラッコキーワード、キーワードプランナー、Trends、Search Console）は今回使っていない。以下は現行原稿・論点からの推測。ただし課題103（`tasks/task-103.md`、2026-09-27調査）に過去の検索調査の要約が記録されている：「皇室典範 改正」月間1万〜10万、「女性天皇 女系天皇 違い」月間1,000〜1万、Yahoo!知恵袋119件で「なぜ」41・「女性天皇・女系天皇の違い」38・「旧宮家・養子」31、2026年7月に急騰し9月末は低下。これは記録の引用で、今回再確認していない。

既にある入口: 検索入口専用部品（`*-search-entry`）は無いが、「3分でわかる、今回の皇室典範改正」（切替カード3枚）と FAQ 6問が同じ役割を持つ。先に書き出すと:
1. 改正法はいつ成立し、いつ施行されるか（7月17日成立／7月24日公布／10月24日）。
2. 今回何が二つ変わるか（女性皇族の婚姻後の身分保持、旧11宮家の男系男子の養子）。
3. 愛子さまが天皇になることは決まったか（決まっていない。第一条は不変）。
4. 女性皇族の配偶者と子は皇族になるか（自動的にはならない）。
5. 養子になった本人に皇位継承資格はあるか（本人は無し、子孫は実方の系統で適用）。
6. 具体的な養子候補は決まっているか（確認できない）。

新たに考えられる疑問（推測）:
- 女性天皇と女系天皇は何が違うのか（原稿でも分類が割れた混同点、「女性天皇・女系天皇」論点）。
- 今回の改正で女性天皇は認められるのか（認められない、が短答）。
- 旧宮家とは何か、なぜ養子なのか（昭和22年に離脱した11宮家、第九条の禁止との関係）。
- 賛成派・反対派はそれぞれ何を理由にしているのか（賛否を示さない投稿が多いことも含む）。
- 皇位継承資格者は今何人で、改正後はどうなるのか（資格者3名の主張は「原典に届かず」）。
- 国会の決め方に問題はなかったのか（修正案、附帯決議、立法手続き論点）。
- 次の見直しはいつか（附則第六条の三十年ごとの見直し）。

## 5. 部活動と違う点・判断が必要な点

1. **論点が6つで、うち「その他」が299件（14.8%）。** 部活動より多く、「その他」を山として独立させるか、補助扱いにするか決める。図解は「その他」だけ補助図（sonota）で性格が違う。
2. **「疑問を確かめる」の置き場所。** 既存の「3分でわかる」＋FAQ（9月30日追加）が先頭にあり、日付が手書きで古くなる（「2026年9月30日時点」）。新構成でこれを冒頭の短答にするか、生成元（正典）を作って日付を自動更新にするかを決める。10月24日の施行を過ぎると本文の時制がすべて変わる。
3. **立場軸が「今回案全体への評価」で、未表明が75%。** 部活動の賛否軸のようには読めない。見せ方（色、バー、文言）を専用に設計する必要がある。「未表明は中立ではない」の注記は維持が必要。
4. **再読データの欠けは無い**（2,016件すべて接続）。ただし理由区分が論点ごとに6〜9種類で、同じ名前でも論点で件数の意味が違う。立場別の理由内訳は無く、全立場の値のみ（`koshitsu_connected_content.py` の説明どおり）。部活動の「立場を絞ると理由の件数が変わる」操作は、再読データに立場別の理由が無いため、そのままでは移せない（要確認）。
5. **一次資料は厚いが、確認日が古い部分がある。** メモ 8/30・9/7、ページの資料照合 9/13。施行日（10月24日）を過ぎたら e-Gov の現行版が切り替わるため、メモ自身が再確認を求めている（`review_days: 30`）。衆議院側審議、宮内庁の人数、施行後の実績は未取得。
6. **投稿埋め込みは可能。** 12件すべて x.com の個別投稿で、widgets.js 埋め込みとリンクの両方がある。埋め込みを開いたときに読み込む形に変えるかは別判断。論点ごとの2件（最大2件）は手順書の仕様と一致。
7. **他テーマと共有しているスクリプト／部品。** `build_planet_page_preview.py` 系（山なみ）、`inject_tide_widget.py`、`apply_theme_design.py`、`seo/apply_theme_trust.py`、`research_conditions.py`、`topic-modern.css/js`、`theme-design.css/js`、`vote-store.js`、`sync_issue_counts.py`。皇室専用は `build_koshitsu_arena.py`（1,269行）、`koshitsu_connected*.py`、`koshitsu_issue_media.py`、`koshitsu_background_detail.py`、`build_koshitsu_process_sections.py`、`refresh_adapters/koshitsu.py`、`docs/koshitsu-connected*.js/css`、`scripts/templates/koshitsu_connected_bridge.js`。更新はアダプター（`page_update_mode: adapter`）が2回生成して差分ゼロを確認する方式なので、新構成は「同じ入力で2回生成して同じ」でなければ公開できない。
8. **すでに部活動型の連動版が入っている。** 部活動の後追いというより、構成の再配置（冒頭の疑問→全体→論点→背景）と旧セクションの完全撤去、手書き部分（3分でわかる・FAQ・授業・ページの作り方）の生成元化が主な作業になる。
9. **古い・食い違う値が残っている（移植時に解消対象）。** 「論点（140件）」と「8月10日の回・325件」（`configs/theme-seo.json`）。`configs/koshitsu-tenpakai-reaction-map.json` の旧カード名と `number_provenance` の旧ファイル参照。`build_koshitsu_process_sections.py` の `CANONICAL_JSON` が `sample_file` と別。`supabase` の v1 定義が残る。
10. **画像。** 現在の図解は6論点分あるが、旧版ファイルが同じディレクトリに複数残る。ページ構成を変えると画像の横長比率が合わない可能性がある。

## 6. 読めなかったもの・確認していないもの

- ブラウザーでの実表示（PC・375px・操作時の見え方）。HTMLのテキスト抽出と構造だけで棚卸しした。
- `docs/koshitsu-connected.js`／`koshitsu-connected-page.js`／`koshitsu-connected.css`／`scripts/templates/koshitsu_connected_bridge.js` の中身（旧セクションを隠す対象は docstring から把握しただけ）。
- 各論点の「一次資料との照合」「資料との照合」「制度確認」の本文の全文、各論点パネルの立場別の数値（論点1つ目の一部だけ確認）。
- `data/verification/koshitsu-tenpakai-issues-reread.json`（配列形式）の構造、`data/public/themes/koshitsu-tenpakai.json` に理由区分が入っているか。
- Article JSON-LD・FAQ JSON-LD・授業/ページの作り方の正確な生成元（`configs/theme-seo.json` か `scripts/seo/`）。
- `refresh_adapters/koshitsu.py` が実際に呼ぶ全工程と `DATA_REFRESH.md` の皇室の項、`social-samples/updates/koshitsu-tenpakai/` の各ファイルの中身。
- 一次資料メモの各資料の本文、e-Gov・国会会議録・内閣官房の現時点の最新状態（オンライン再確認はしていない）。
- 検索需要（ラッコキーワード、キーワードプランナー、Google Trends、Search Console）。課題103の記録の引用に留まり、今回の取得はなし。
- 既存URLのアンカーが外部（X、note、検索結果）から参照されているか。
- 画像（webp）の実物、X投稿12件が現在も閲覧可能か。
- 作業ツリーが main と同一かの突き合わせ（git status は着手時点で確認していない）。
