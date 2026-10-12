# 自転車の青切符（bike-blue-ticket）新デザインの公開候補と検査（手順7）

2026-10-12。ブランチ `task/renew-bike-blue-ticket`。手順書23の「7. 更新と公開を検査する」。
憲法改正論議の [2026-10-11-constitutional-amendment-production-candidate.md](2026-10-11-constitutional-amendment-production-candidate.md)
（対話式の山なみを元HTMLから写す＋部活動型の圧縮）をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/bike-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/bike-blue-ticket-release/bike-blue-ticket-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-11）
確認画面: `quality/prototypes/bike-blue-ticket-release/evidence/`（PC・375px の全体、山なみ、立場モード切替、山を押して読書面へ、
読書面、理由を開いた画面、背景を開いた画面、前回の収集との比較を開いた画面、X遮断時、JSなし）

## 0. 手順7の前に直したこと（コミット 73917c15）

| 項目 | 処理 |
|---|---|
| 1. 反則金の誤り | `scripts/templates/bike_blue_ticket_search_entry.html` の「並進禁止・乗車積載方法違反 3,000円」を、政令別表第六（原付等の欄）どおりの3行（並進禁止違反 3,000円／乗車積載方法違反 5,000円／軽車両乗車積載制限違反（二人乗りなど）3,000円、出典 e-Gov 道路交通法施行令）に直し、件数表示を「主な例 12件」に。元HTML（当時の docs）の検索入口を作り直した |
| 2. 背景台帳の誤り | `data/verification/bike-blue-ticket-background.json` の checklist「走る場所」を警察庁FAQどおり（例外は標識・13歳未満・70歳以上・身体の不自由な人・車道が危険な具体的状況。子乗せ自転車は歩道を通っただけでは取り締まらない扱い）に直し、caveat（「半年に満たない」）を更新、`checked_on` を 2026-10-12 に。読書面の言い換え `check_rewrites.basho` は不要になったので外した。元HTMLの連動表示（4か所）と、手書きの静的な「制度の確認」節（`#bukatsu-check`）の文も同じ文にした |
| 3. よみやすの残り | `data/verification/bike-blue-ticket-sunk-continents.json` の `life_impact` 3件（sc-1 112字・読点4、sc-2「土台」、sc-4 123字）を区切った。英数字の並び（数字・記号）が前後で同じことをスクリプトで確かめた。`build_public_registry.py --topic bike-blue-ticket` で公開JSONを作り直し、採用台帳の指紋（`build_adoption_registry.py`）も合わせた。`verify_number_provenance.py bike-blue-ticket` NG 0（318/318）、`verify_ocean_layer.py` は直す前と出力が完全に同じ（既存の sc-1 の machine_hits の指摘。全体の終了コード1は既存） |
| 4. 他の既存データ由来の指摘 | 公開候補のよみやす（`--strict`）で、既存データ由来の完成を止める指摘は上の3件だけだった |

## 1. 仕組み（憲法改正論議と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_bike_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`bike_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/bike_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/bike-blue-ticket.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_bike_arena.py` を単独で動かしたとき。元HTMLに公開JSONの集計・論点ごとのX投稿・アリーナ・山なみと連動表示を adapter の finalize と同じ順で掛けてから新デザインを組む） |
| `configs/bike-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/bike_redesign/planet.js`（新規） | 山なみの橋渡し（憲法の planet.js と同じ。入口は `window.BikeReading.select`） |
| `scripts/bike_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（標識の青・路面の墨色・注意の黄）に合わせる。冒頭の出典の行（`<footer>`）に共通のフッターの紺の地が掛かるのを戻す、見出しをゴシックに、スマートフォンでは山なみの「このページの見かた」を出さない |
| `scripts/bike_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・立場の対応表・設定から数え直して照合（`bike_blue_ticket_count_provenance.py` 経由で `verify_number_provenance.py` から呼ぶ）。冒頭の件数欄（「その他」の中身を含む）と6論点の欄 |

ページの並び：共通ヘッダー → 冒頭（題名・青切符の図・短答4つ・歩道と支払いの短答・SNSの意見の件数・出典）→ 論点ごとに読む（見出し →
**対話式の山なみ**（立場モード・山・論点ボタン・選択パネルと100マス・見かた・調査条件）→ 論点タブ → 選んだ論点の欄）→ 前回の収集との比較（要約＋折りたたみ）→
投票 → 背景の開閉行6行 → 作り方と詳細データ（折りたたみ1つ）→ 次はこのテーマ → フッター。

時制：施行済み（2026-04-01）なので段階の切り替えは無い。「◯月◯日時点」は冒頭の設定 `checked_on` 1か所から出る。同じデータなら同じページになる。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「自転車の青切符で何が変わる？対象と賛否｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承（テストで一致確認。OGP画像も同じ） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 現行ページには無い | 冒頭「歩道・手信号・支払いの短答」4問＋背景「よくある質問」4問＝8問から作り直し | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間 | release だけ複写 | 継承（`google-adsense-account` meta は現行ページに無い） |
| 共通CSS/JS | site-tokens・topic-modern・bike-blue-ticket-connected（css/js/page.js）・search-entry（css/js）・theme-design・widgets.js | site-tokens・topic-modern（v=32、JS v=13）だけ | 検索入口・連動表示・テーマ共通の見た目・X一括読み込みは意図的に外した |
| 投票（Supabase） | topic `bike-blue-ticket-issue-stance-v1`、論点6×立場3＝18、`choiceIdx:selIssue*STANCES.length+stanceIdx`、保存キー `sns_vote_bike_blue_ticket_2step` | 投票節とスクリプトを複写。`VOTE_ISSUES`・`V2I`・`STANCES` は元と完全一致。保存キーは本番ホストだけ既存キー、他は `sns_vote_preview_bike_blue_ticket_2step` | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（18通り）。**投票の前置きの1文だけ**、元の「2024年に…導入されます」（未来形、棚卸し31）を設定 `compact.vote_lead`（「2026年4月から…使われています」）に差し替えた |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承 |
| 共通ヘッダー・パンくず | 元HTMLは静的ヘッダーが無い（ヒーローの「トップ」リンクだけ） | 皇室・副首都・憲法と同じ静的な共通ヘッダー、冒頭のパンくず「交通ルール・日常論争 ／ 自転車の青切符」 | JSなしでもトップへ戻れる |
| 前回の収集との比較（TIDE_CARD） | 9/28→10/11、立場・論点の2タブ、再生ボタン | `<section class="update-dashboard">…TIDE_CARD…</section>` と CSS 区間を文字どおり複写し、要約（立場2本の小さな折れ線・カードの見出しの1文・注記）の下の折りたたみ `#cap-trend-more` へ | 継承。`#bike-blue-ticket-tide-widget` で来たら折りたたみを開く |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、詳細データと一緒に折りたたみ `#cap-method` へ | 継承（公開日・最終更新日の `<time>` も残る）。古い段落「7/26と8/17の比較」は `configs/theme-seo.json` の observations を直して元HTMLから消した（内容対応表34） |
| 詳細データ | `#detail-data`（分類別件数・カテゴリ×検索クエリ・カテゴリ×スタンス・注意） | `#detail-data` のうち「注意」だけ文字どおり複写 | **旧体系の3表（旧177件）は載せない**（内容対応表36〜38。残すと件数が2種類になる）。元HTMLには残る |
| 次はこのテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking` | 両方文字どおり複写 | 継承 |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間（元HTML） | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| 進み具合の帯「探ったところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先 `#pbar`・`#pseg`・`#pnum` だけ隠して置く） | 内容対応表4 |
| 検索入口（年齢・反則金・FAQ） | `#bike-search-entry` | 載せない | 冒頭に置き換え（内容対応表11〜15。反則金は正しい12例） |
| 立場の帯 | `#stance-glance` | 載せない | 冒頭の件数欄と論点の欄の帯（内容対応表16） |
| 背景・制度の確認 | `#bukatsu-background`・`#bukatsu-check`（部活動の流用id） | 載せない | 背景の開閉行・論点ごとの制度の確認（内容対応表17〜19） |
| 編集部の横断整理・一次資料クイズ・予想2問 | `#editorial`・`#quiz`・`#guesses` | 整理は外し、クイズと予想は受け皿だけ隠して残す | 内容対応表24・26 |
| 論点ごとのX投稿・アリーナの点 | 12件・`#bike-arena-points`（SM_RAW） | 正典から選び直した12件（開いたときに読む）。アリーナの点は載せない | 置き換え（内容対応表29・41） |
| llms.txt・sitemap | URL のみ | URL 不変 | 継承 |

### 旧アンカーの到達確認

`grep -rn "bike-blue-ticket-reaction-map.html#" docs/ scripts/ configs/`（data・themes・quality・tests も）の結果は**0件**（サイト内からアンカー付きで指すリンクは無い）。
外部から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行・冒頭の短答なら開く。折りたたみの中なら外側を開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#top`・`#progress`・`#bike-search-entry`（`-title`） | 冒頭 `#bike-open` |
| `#bike-age-title`・`#bike-age-answer-title`・`#bike-age-answer-body` | 冒頭「何歳から？」`#bop-age` |
| `#bike-fine-title`・`#bike-fine-search`・`#bike-fine-count`・`#bike-fine-list`・`#bike-fine-empty` | 冒頭「いくら？」`#bop-fines` |
| `#bike-faq-title` ／ `#bike-faq-sidewalk`・`-signal`・`-payment`・`-fraud` | 冒頭の短答 `#bop-faq` ／ 同じ問い `#bop-faq-…`（開く） |
| `#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`） | 冒頭の件数欄 `#bop-count` |
| `#bukatsu-background`・`#bg-title` | 背景「なぜ自転車に青切符が導入されたのか」`#bg-why`（開く） |
| `#bukatsu-check`・`#ck-title` | 背景「青切符を切られると、どんな手続きになるのか」`#bg-system`（開く） |
| `#fallback`・`#fallback-nav`・`#quiz`・`#ocean`・`#editorial`・`#issue-cards`・`#bike-arena-points` | 読書面 `#bike-blue-ticket-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#bike-blue-ticket-reading-{論点ID}` | その論点の欄 `#issue-{論点ID}`（選んだ状態になる） |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |

`#issue-{論点ID}` は旧ページ（論点ごとのX投稿）でも新ページ（読書面の欄）でも「その論点」。
そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`planet-block`・`planet-data`・`bike-blue-ticket-tide-widget`・`article-trust-title`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS・CSS の内部用ID（`bike-reason-count-…`・`bike-check-note-…`・`bike-source-…`・`explainer-modal`・
`bike-connected-data`・`pseg`・`reread-basis-css` など、外から指す意味の無いもの）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_bike_redesign.py --mode release --output-dir quality/prototypes/bike-blue-ticket-release
```
成功すると `Built 1 file (release, as_of 2026-10-11); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）: `--mode preview --output-dir /tmp/bike-preview`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文（`section.landing-panel`）・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。
  **自転車だけの変更**：山なみのスクリプトの中の連動表示の橋渡し（`BIKE_CONNECTED_BRIDGE`）は、読み込み時に件数最多の論点（「その他」）へ
  自動で着地して `location.hash` を書く（履歴が1つ増えて「戻る」で前のページへ戻れず、読書面も「その他」に切り替わる）。この4行だけを
  「読書面の既定の論点（`data-default-issue`）を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」処理に置き換える（`AUTO_LAND`／`AUTO_LAND_OFF`。
  元HTMLの該当箇所が変わると止まる）。ハッシュ付きで来たときの着地はそのまま
- **前回の収集との比較**：潮目のカードの `const datasets` と比べた日付だけを読み、要約に立場2本の2点の折れ線、読書面の各論点に2点の折れ線と
  「9月28日 22.9% → 10月11日 59.0%」の形の数字を入れる（件数は描かない）。「その他」は潮目に無いので数字は出ない。読書面の「収集回ごとの比較へ」は
  折りたたみを開き「論点の変化」に切り替える。要約の注記に「1回分の件数は数十件なので、数件の違いでも割合は大きく動く」と書いた（9/28回は35件・10/11回は39件）
- **圧縮**：読書面は手順5・6で最初から部活動型。手順7で作り方と詳細データを1つの折りたたみにした
- 冒頭の件数欄の「5つの論点に入らない意見」と読書面の見出し「6つの論点で」は、`verify_theme_page.py` の「同じ数字は1回だけ」
  （意見数・論点数が2通りに読める）で止まったので、「5つの論点のどれにも入らないもの」「5つの論点と「その他」で」に直した（検査は緩めていない）

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理 → 最後に `bike_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/bike.py` は `source_for_refresh` を入力にする。アリーナ・潮目（`_apply_tide`）・連動表示・検索入口も元HTMLから作った候補に掛かる。
  **adapter が累積候補から立場の対応表（`data/bike-blue-ticket_reread-stances.json`）も作り直し、昇格対象に含める**（`build_reread_stances`。
  正典はまだ古いので、立場は累積候補の分類から写し、論点×立場も累積候補で数えて照合する）。新しい意見が入る回でも、人が読む工程
  （本文確認記録・再読）を済ませれば新デザインの照合が通る。
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。
- **模擬（切替後の作業ツリーのスクラッチ複製、完了記録の検査だけ外した）**:
  - **10/11 回の再生**（新規54件を採用した直近の回を adapter に通す）: `refresh_adapters/bike.build` → `refresh_topic.prepare_public_candidate_bundle`。
    adapter の生成物は、再読データの `input_sha256`・対応表の `made_on` などの記録欄を除き作業ツリーと同じ（立場の対応表の中身は469件とも一致）。
    候補の docs/ は新デザインで、**作業ツリーの公開ページとバイト一致**。皇室・副首都・生成AI・憲法・部活動の公開ページは変わらず。
  - **10/21 の新規0件の回**: 実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む（`refresh_topic.py`）。他テーマの回で自転車の finish が走る場合と同じ
    条件として、adapter の生成物なしで `prepare_public_candidate_bundle`（finalize と finish）を通した。候補の docs/ は新デザイン（最終更新日 2026-10-21、
    次回の収集予定 10月31日）、元HTMLは旧形式。候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0、
    `verify_builder_rebuildability.py` NG 0、よみやす PASS、使い回し0。候補の `DATA_SHEET.md` の「副首都・部活動のマップの点がずれ」は憲法の記録と同じ既知の表示（隔離コピーの事情）。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/bike-blue-ticket.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分 | `data/bike-blue-ticket_issues-reread.json`（adapter が累積候補と本文確認記録から作る） | **本文確認記録（`data/bike-blue-ticket_editorial-updates/`）を人が書く**（明細が論点の件数と合わないと生成が止まる） |
| 区分ごとの立場・投稿の立場 | `data/bike-blue-ticket_reread-stances.json` | 定期更新では adapter が作る。それ以外で再読データを直したら `bike_reread_stances.py --made-on` |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前・投票の前置き | `configs/bike-blue-ticket-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`・`data/verification/bike-blue-ticket-claims.json` | 主張を足すとき |
| 資料にしかない話 | `data/verification/bike-blue-ticket-sunk-continents.json` → 公開JSON `ocean_layer` | adapter が `sns_note` を更新。文を直すときは1文80字以内 |
| 制度の確認・背景の年表・なぜ導入されたか | `data/verification/bike-blue-ticket-background.json`・`configs/bike-blue-ticket-background.json` | 一次資料の再確認時（台帳の `checked_on` も） |
| 冒頭（短答・反則金12例・FAQ・切られた後・運用の実際）・確認日 | `configs/bike-blue-ticket-opening.json`（`checked_on`） | 制度を確かめ直したら `checked_on` |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION（`refresh_planet_section.py --for-docs`・連動表示の橋渡し） | 自動 |
| 前回の収集との比較 | 元HTMLの TIDE_CARD（adapter の `_apply_tide`） | 自動 |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データの注意・次はこのテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件に自転車／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成で憲法の後に `finish` | 憲法の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/bike.py` | 入力を `source_for_refresh(root)` に／立場の対応表を累積候補から作る `build_reread_stances` と昇格対象 `REREAD_STANCES` | 公開後も元HTMLから生成するため／新しい意見が入る回に照合が止まらないため |
| `scripts/bike_reread_stances.py` | 表を作る処理を `table()` に分けた（CLI の動きは同じ。作業ツリーで「変更なし」） | adapter から同じ表を作るため |
| `scripts/build_bike_arena.py` | 公開ページが新デザインで、入出力の指定が無いとき `bike_layout.rebuild`（`--check`・`--public-counts-only` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/bike_issue_media.py` | `--write-html` で新デザインのページには書かない（停止） | 投票節の前に旧形式の節を差し込む事故を防ぐ |
| `scripts/bike_blue_ticket_count_provenance.py` | 新デザインなら `bike_redesign_provenance` を呼ぶ | 数字の出所検査 |
| `scripts/inject_tide_widget.py` | コメントのみ（新デザインのページは既に SKIP） | — |
| `scripts/refresh_planet_section.py` | 自転車の新デザインも停止 | 他の新デザインと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 自転車の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐を自転車にも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| 切替時の共有テスト | 9-3 | 公開後は旧形式の検査を元HTMLに向けるため |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に自転車の `finish` が走る。自転車の照合が合わないと、その回の
**公開候補生成全体が止まる**（皇室・副首都・生成AI・憲法と同じ設計）。単独スクリプトは複製で確かめた：`bike_issue_media.py --write-html` は停止、
`build_bike_process_sections.py`・`build_bike_arena_points.py`・`sync_issue_counts.py`・`apply_background_sources.py`・`inject_tide_widget.py`・
`apply_classroom_section.py`・`apply_theme_design.py`・`build_bike_arena.py`（`--public-counts-only` を含む）を流しても新デザインのページはバイト不変。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付・潮目の日付） | 合格 | 合格 |
| `verify_theme_page.py bike-blue-ticket`（候補は `--html`） | NG 0（OK 33） | NG 0（OK 33）、全10テーマ NG 0 |
| `verify_number_provenance.py` | 10テーマ NG 0（現行ページ 318/318） | 自転車 579/579・終了0、10テーマ NG 0 |
| `verify_top_page.py` | 終了0 | 終了0 |
| `build_bike_arena.py --check` | OK: 差分なし | OK: 差分なし（公開後の経路＝元HTMLと新ページを作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（既存の指摘。終了1） | 同じ |
| `python3 -m unittest discover tests` | 1,990件 OK（skip 4） | 1,990件 OK（skip 4。共有テストを直す前は失敗5・エラー3） |
| `run_public_checks.py` | 終了0 | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） |
| `tests/test_bike_redesign.py` | 63件 OK（手順7分25件：同じ入力で同じ出力・docs出力と新ページ再入力の拒否・保護対象・GA/AdSense・投票定義と前置き・adapter の指紋・FAQ と画面の一致・継承部品・詳細データ・潮目の継承と折りたたみ・論点ごとの折れ線・作り方の折りたたみ・初期状態・授業節・旧アンカー・山なみの写し・元HTMLの更新への追随・旧部品なし・出所検査の改ざん検知2種、レイアウト6件：無効時・状態の一貫・元HTML無し・往復・照合不一致で書かない・更新経路の配線） | 同じ |
| 2回生成 | md5 一致（`f496557d…`、`PYTHONHASHSEED` 0・1・999・指定なし） | docs のページとも一致 |
| よみやす（`--strict`） | 候補 66/100・完成を止める指摘 0件・PASS | docs 同じ |
| 使い回し（`verify_page_originality.py`） | 最初は64件（理由の数え方の文が生成AI・憲法と、冒頭の件数欄の説明が副首都と、背景の案内・資料照合の前置き・読書面の案内が他テーマと似すぎ）→ 設定の6文を書き直して 0件 | 「10ページに、使い回された見出し・文はありません」 |
| AI臭（`verify_ai_tone.py`） | 問題なし | 問題なし |
| `seo/validate_theme_seo.py` | — | OK（themes=10） |

操作（Playwright、`tests/test_bike_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（scrollWidth＝画面幅。読書面の折りたたみ全開・背景6行・比較・詳細データを開いても0）、ページのコンソールエラー0。
- 山なみ：立場モード（3つ目）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`。
- 読み込み時：URL にハッシュが付かず、`history.length` は増えない。山なみの選択パネルと読書面はどちらも「取締りを強めてほしい」。
- 論点タブ6つで scrollY 不変、論点の切替で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「別の理由」で次へ。
- 前回の収集との比較：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「収集回ごとの比較へ」で折りたたみが開き論点の変化になる。
- 旧アンカー：2節の表の主な読み替え（`#fb-…`・`#bike-blue-ticket-reading-…`・`#bukatsu-check`・`#bukatsu-background`・`#bike-search-entry`・`#bike-faq-payment`・
  `#stance-glance`・`#classroom-title`・`#fr-r-…`・`#bike-blue-ticket-tide-widget`・`#detail-data`）をブラウザで確認。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン6つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：6論点すべて表示、図が使えないときの論点一覧・比較の要約・作り方・詳細データ・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 15,285px | **13,983px** | 13,000px以下 ✗（983px超） |
| ページ全体の表示中の文字数 | 5,529字 | 4,718字（main の中） | — |
| うち冒頭 | — | 5,733px | — |
| 山なみ（`#planet-block`、選択パネル込み） | — | 1,940px | — |
| 1280px のページ全体 | 10,300px | 8,486px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 取締りを強めてほしい | 2,567px | 859字 | 1,377px |
| 先に走る場所を整えて | 2,324px | 799字 | 1,401px |
| ルールが分かりにくい・運用が不安 | 2,598px | 848字 | 1,349px |
| 自転車にも免許制を | 2,317px | 788字 | 1,377px |
| 車道を走るのが怖い | 2,317px | 753字 | 1,377px |
| その他 | 2,180px | 749字 | 1,414px |

論点の欄の目標（2,500px以下）は6論点中4論点で満たし、2論点（取締り・ルール曖昧）が 67〜98px 超える。手順6の時点（2,445・2,455px）から、
「前の収集回との違い」（折れ線・数字・比較への案内）を足した分だけ伸びた。ページ全体は、冒頭（短答4つ・反則金12例・件数欄。手順4で決めた中身）が
5,733px あり、スマートフォンで山なみの「このページの見かた」を隠しても 13,983px。これ以上は内容を折りたたむか外す判断になるので、オーナーの判断に回す（7節）。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. ページ全体が 375px で 13,983px（目標より約1,000px長い）。私なら冒頭の「切られたら、どうする？」「違反したら、必ず切られる？」の2枚を、スマートフォンだけ
   問いと短い答えを見せる折りたたみにする（約1,000px 減る見込み。未計測）。ただし冒頭は検索評価日 10/28 まで中身を変えない方針なので、評価日の後に行う。
3. 論点の欄が2論点で 2,500px を超える（67〜98px）。私なら「前の収集回との違い」の累計の表の折りたたみを外す（見出しの件数と同じ数字。各欄約50px）。
4. 旧体系の3表（詳細データ）・アリーナの点・論点ごとのX投稿12件は元HTMLに残り、新デザインには載せていない（内容対応表36〜38・41・29）。
5. 「前の収集回との違い」は2回の収集の比較（潮目）で、全収集回の推移ではない（現行ページに全回の推移が無いため）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。12件の投稿が閲覧できることは手順6で 10/12 に確認済み）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は 10/11 回の再生（新規54件）と 10/21 の新規0件の模擬だけ。
- `scripts/seo/apply_theme_trust.py` を引数なしで流すと部活動のページで止まる（`missing SEO metadata block`。既存の動き。自転車のページは止まる前に更新される）。

## 9. 2026-10-12 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/bike-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | bike-blue-ticket に `display_headline`「自転車の青切符、何歳から・いくら？切られた後の払い方と、SNSで意見が分かれる理由」（H1 が変わるため） |
| `data/page-sources/bike-blue-ticket.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致） |
| `docs/bike-blue-ticket-reaction-map.html` | 新デザイン（`bike_layout.finish`。公開候補とバイト一致） |
| `DATA_SHEET.md` | 自転車の「マップの点」が「—」に（新デザインにアリーナの点が無いため。副首都・憲法と同じ） |
| `company/APPROVALS.yaml` | `approval-20261012-bike-blue-ticket`（`status: pending`、`decided_at: null`） |
| 共有テスト | 9-3 |

（`DATA_REFRESH.md` の「自転車の青切符の定期更新（新デザインを維持する、2026-10-12〜）」の節は公開候補のコミットで足した。）

### 9-2. 切替後の検査（作業ツリー）

6節の「切替後」の列。全テスト・公開検査は 9-3 の共有テストを直したあとの結果。切替後の docs/ を 127.0.0.1 で配信して Playwright の検査をもう一度通した（全項目合格）。

### 9-3. 切替に合わせて直した共有テスト

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_bike_adapter.py`・`_bike_planet_refresh.py`・`_bike_blue_ticket_connected.py` | 読むページを「公開後は元HTML（`source_for_refresh`）」に | 旧形式のアリーナ・山なみの再生成・連動表示・投票定義の検査。公開後も元HTMLに同じ構造で残る（憲法と同じ扱い） |
| `tests/test_cite_button.py` | 自転車の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 自転車の新デザインを飛ばす | 共通の見た目を掛けない設計 |
| （`tests/test_data_sheet.py`） | テストは変えず、`DATA_SHEET.md` を作り直した | 「マップの点」の列 |
