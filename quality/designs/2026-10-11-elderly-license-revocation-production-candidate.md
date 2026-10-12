# 高齢者免許返納（elderly-license-revocation）新デザインの公開候補と検査（手順7）

2026-10-12。ブランチ `task/renew-elderly-license-revocation`。手順書23の「7. 更新と公開を検査する」。
自転車の青切符の [2026-10-11-bike-blue-ticket-production-candidate.md](2026-10-11-bike-blue-ticket-production-candidate.md)
（対話式の山なみを元HTMLから写す＋部活動型の圧縮）をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/elderly-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/elderly-license-revocation-release/elderly-license-revocation-reaction-map.html`（基準日＝公開JSONの更新日 2026-09-30）
確認画面: `quality/prototypes/elderly-license-revocation-release/evidence/`（PC・375px の全体、冒頭、山なみ、立場モード切替、山を押して読書面へ、
読書面、理由を開いた画面、理由が未公開の論点、背景を開いた画面、前の収集回との比較を開いた画面、X遮断時、JSなし）

## 0. 手順7の前に直したこと（コミット 15fb2dab）

| 項目 | 処理 |
|---|---|
| 1. よみやすの残り5件 | `data/verification/elderly-license-revocation-sunk-continents.json` の `life_impact` 3件（sc-1 83字・「装置」、sc-2 109字、sc-4 82字）と、照合 skilltest の `finding`（104字。正本は `scripts/build_elderly_process_sections.py` の FACT_CHECKS `note`。`elderly-license-revocation-claims.json` は投稿と主張の対応表で文を持たない）を、数字・出典・判定を変えずに区切った。「装置」は「機能」に（バックグラウンドの行と同じ言い方）。`--original` 付きのよみやす検査で数字・URLの増減なし、5件→0件。`build_public_registry.py --topic elderly-license-revocation` で公開JSON・catalog を、`build_adoption_registry.py` で採用台帳の指紋を作り直した。元HTML（当時の docs）の旧形式の部分（山なみの資料にしかない話・連動表示）も `refresh_planet_section.py --for-docs` で作り直した（文の差し替えだけ。10行）。`verify_number_provenance.py elderly-license-revocation` NG 0（275/275）、`verify_ocean_layer.py` は直す前と出力が完全に同じ（他テーマの既存の指摘で終了1） |
| 2. 家族で話す前の確認 | 背景に開閉行「家族で話す前に、年齢より先に並べる4つ」（`#bg-family`、新しい種類 `checklist`）を足した。中身は現行ページの4項目（見る・確かめる・組み立てる・比べる）。編集部の整理なので確認日は付けない。メリット・デメリット（棚卸し10）は載せない（司令塔の決定） |
| 3. 照合「事故は増えている」 | 判定は変えず、注記 `claim_notes.increase` を維持。10/14 の定期更新でやり直す旨を一次資料メモ（資料W）と DATA_REFRESH.md に書いた |
| 4. 再読データの `population` | 値は変えず、DATA_REFRESH.md に注意として書いた |

## 1. 仕組み（自転車の青切符と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_elderly_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`elderly_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/elderly_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/elderly-license-revocation.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_elderly_arena.py` を単独で動かしたとき。元HTMLに公開JSONの集計・旧形式の生成・山なみと連動表示を掛けてから新デザインを組む） |
| `configs/elderly-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/elderly_redesign/planet.js`（新規） | 山なみの橋渡し（自転車と同じ。入口は `window.ElderlyReading.select`） |
| `scripts/elderly_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（標識の青・柿色・路面の墨）に合わせる。立場は4つなので立場ボタンは5つ（スマートフォンでは「すべて」を1行、4立場を2列）。スマートフォンでは山なみの「このページの見かた」を出さない。論点の欄の小さな折れ線は自転車より小さく（数字2つを1行に） |
| `scripts/elderly_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細（立場を持つ）・設定から数え直して照合（`elderly_license_count_provenance.py` 経由で `verify_number_provenance.py` から呼ぶ）。冒頭の件数欄、冒頭の統計（運転免許統計の2つの数）、6論点の欄 |

ページの並び：共通ヘッダー → 冒頭（題名・短答3つ・年齢のものさし・返納したあとの流れ・よく検索される疑問6問・SNSの意見の件数・出典）→ 論点ごとに読む（見出し →
**対話式の山なみ**（立場モード・山・論点ボタン・選択パネルと100マス・見かた・調査条件）→ 論点タブ → 選んだ論点の欄）→ 前の収集回との比較（要約＋折りたたみ）→
投票 → 背景の開閉行9行 → 作り方と詳細データ（折りたたみ1つ）→ 次に見るテーマ → フッター。

時制：期限付きの制度イベントは無いので段階の切り替えは無い。「◯月◯日時点」は冒頭の設定 `checked_on` 1か所から出る。同じデータなら同じページになる。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「免許返納は何歳から？年齢・メリットとデメリット・義務化の賛否｜SNS反応まっぷ」 | 同じ | 継承（メリット・デメリットの節は新ページに無い。7節の判断事項） |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承（テストで一致確認。OGP画像も同じ） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 現行ページには無い | 冒頭「よく検索される疑問」6問＋背景「よくある質問」3問＝9問から作り直し。背景の答えの末尾の「（一次資料メモの確認日 …）」は答えに入れない | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間 | release だけ複写 | 継承（`google-adsense-account` meta は現行ページに無い） |
| 共通CSS/JS | site-tokens・topic-modern・elderly-connected（css/js/page.js）・elderly-search-entry（css/js）・theme-design・widgets.js | site-tokens・topic-modern（v=32、JS v=13）だけ | 検索入口・連動表示・テーマ共通の見た目・X一括読み込みは意図的に外した |
| 投票（Supabase） | topic `elderly-license-revocation-issue-stance-v1`、論点6×立場3＝18、`choiceIdx:selIssue*STANCES.length+stanceIdx`、保存キー `sns_vote_elderly_license_revocation_2step` | 投票節とスクリプトを複写。`VOTE_ISSUES`・`V2I`・`STANCES` は元と完全一致。保存キーは本番ホストだけ既存キー、他は `sns_vote_preview_elderly_license_revocation_2step`。前置きの文も元のまま | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（18通り） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承 |
| 共通ヘッダー・パンくず | 元HTMLは静的ヘッダーが無い（topic-modern.js が差し込む） | 自転車と同じ静的な共通ヘッダー、冒頭のパンくず「交通ルール・日常論争 ／ 高齢者の運転免許返納」 | JSなしでもトップへ戻れる |
| 前の収集回との比較（TIDE_CARD） | 9/20→9/30、立場・論点の2タブ、再生ボタン | `<section class="update-dashboard">…TIDE_CARD…</section>` と CSS 区間を文字どおり複写し、要約（立場3本の小さな折れ線・カードの見出しの1文・注記）の下の折りたたみ `#cap-trend-more` へ | 継承。読書面の「回ごとの比較へ」の飛び先（設定 `trend.widget_id`）は実際の id `elderly-license-revocation-tide-widget` と一致（テストで確認） |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、詳細データと一緒に折りたたみ `#cap-method` へ | 継承（公開日・最終更新日の `<time>` も残る）。古い段落「7/12と7/26の比較」は `configs/theme-seo.json` の observations を直して元HTMLから消した（内容対応表34） |
| 詳細データ | `#detail-data`（論点別・スタンス別・表現強度別の3表） | 3表とも文字どおり複写 | 継承。3表とも公開JSONと同じ455件の集計で、ヒートマップ（旧マップの表）は現行ページに既に無い（内容対応表36） |
| 次に見るテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking` | 両方文字どおり複写 | 継承 |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間（元HTML） | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| 進み具合の帯「探ったところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先 `#pbar`・`#pseg`・`#pnum` だけ隠して置く） | 内容対応表2 |
| 検索入口（短答・年齢別・家族の確認・メリデメ・家族の話し方・FAQ） | SEARCH_ENTRY | 載せない | 冒頭と背景に置き換え（内容対応表7〜13。家族の確認は `#bg-family`、メリデメは載せない） |
| 立場の帯 | `#stance-glance` | 載せない | 冒頭の件数欄と論点の欄の帯（内容対応表14） |
| 背景パネル | `#bukatsu-background`（部活動の流用id） | 載せない | 背景の開閉行（内容対応表16・17） |
| 編集部の横断整理・一次資料クイズ・予想2問 | `#editorial`・`#quiz`・`#guesses` | 整理は外し、クイズと予想は受け皿だけ隠して残す | 内容対応表25・27 |
| 論点カード（ELDERLY_ISSUE_MEDIA）・アリーナの点 | `#issue-cards`・SM_RAW | 載せない | 読書面の投稿の例（12件）に置き換え（内容対応表22・23・30） |
| llms.txt・sitemap | URL のみ | URL 不変 | 継承 |

### 旧アンカーの到達確認

`grep -rn "elderly-license-revocation-reaction-map.html#" docs/ scripts/ configs/`（data・themes・tests・quality/designs も）の結果は**0件**（サイト内からアンカー付きで指すリンクは無い）。
ページ内のリンク（`#fb-…`・`#issue-…`・`#stance-glance`・`#ocean`・`#planet-block`・`#fallback-nav`）は新ページで飛び先があるか読み替えられる。
外部から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#progress`・`#return-age-guide` | 冒頭 `#elderly-open` |
| `#return-age-title` | 冒頭の年齢のものさし `#elo-ages` |
| `#elderly-license-faq`・`#return-faq-title` | 冒頭のよく検索される疑問 `#elo-faq` |
| `#decision-check-title`・`#family-talk-title` | 背景「家族で話す前に、年齢より先に並べる4つ」`#bg-family`（開く） |
| `#return-merit-title`・`#return-demerit-title` | 背景「返納の手続き、サポカー限定、相談の窓口」`#bg-options`（開く。メリデメの節は無い） |
| `#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`） | 冒頭の件数欄 `#elo-count` |
| `#bukatsu-background`・`#bg-title` | 背景「なぜ、年齢で返納させるべきかが議論になるのか」`#bg-why`（開く） |
| `#fallback`・`#fallback-nav`・`#quiz`・`#ocean`・`#editorial`・`#issue-cards` | 読書面 `#elderly-license-revocation-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#elderly-license-revocation-reading-{論点ID}` | その論点の欄 `#issue-{論点ID}`（選んだ状態になる） |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |

`#issue-{論点ID}` は旧ページ（論点カード）でも新ページ（読書面の欄）でも「その論点」。
そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`planet-block`・`planet-data`・`elderly-license-revocation-tide-widget`・`article-trust-title`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS・CSS の内部用ID（`elc-reason-count-…`・`elc-claim-finding-…`・`explainer-modal`・
`elderly-connected-data`・`pbar` など、外から指す意味の無いもの）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_elderly_redesign.py --mode release --output-dir quality/prototypes/elderly-license-revocation-release
```
成功すると `Built 1 file (release, as_of 2026-09-30); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）: `--mode preview --output-dir /tmp/elderly-preview`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文（`section.landing-panel`）・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。
  **高齢者だけの変更**：山なみのスクリプトの中の連動表示の橋渡し（`ELDERLY_CONNECTED_BRIDGE` の `initialLand`）は、読み込み時に件数最多の論点へ
  自動で着地して `location.hash` を書く（履歴が1つ増える）。さらに読書面の template が無いと同じ論点へもう一度着地する。この6行だけを
  「読書面の既定の論点（`data-default-issue`）を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」処理に置き換える（`AUTO_LAND`／`AUTO_LAND_OFF`。
  元HTMLの該当箇所が変わると止まる。テストで確認）。ハッシュ付きで来たときの着地はそのまま
- **前の収集回との比較**：潮目のカードの `const datasets` と比べた日付だけを読み、要約に立場3本の2点の折れ線、読書面の各論点に2点の折れ線と
  「9月20日 80.0% → 9月30日 41.7%」の形の数字を入れる（件数は描かない）。潮目の論点は4つ（`inject_tide_widget.py` の `issue_labels`）なので、
  「バスや乗合の足を整える」と「その他」には数字が出ない。論点の割合の母数はこの4論点の意見（中立・情報を含む）なので、読書面の注記（`compact.glance_note`）を
  手順6の「中立・情報と「その他」を除いた」から「「バスや乗合の足を整える」と「その他」を除いた論点の意見を100%として」に直した。
  今回の回が16件と少ないことは前面に出さず、要約の注記に「1回分の件数は少ないので、数件の違いでも割合は大きく動きます」とだけ書いた（申し送り2）
- **圧縮**：読書面は手順5・6で最初から部活動型。手順7で作り方と詳細データを1つの折りたたみにした
- `verify_theme_page.py` の「同じ数字は1回だけ」で止まった3か所を、検査を緩めずに文で直した：読書面の題「6つの論点に分けると」→「5つの論点と「その他」に分けると」、
  論点の順位の文「6つの論点の中で」→「論点の中で」、理由区分の名前「…を求める意見 22件」「…分析的意見 16件」（ページ全体の意見数と読める）→
  設定の `label_override` で「…を求める声」「統計・データに基づく分析」。見出し「前の収集回と比べて、立場の割合はどう変わった？」は自転車の見出しと
  使い回し検査で 0.91 だったので「立場ごとの割合は、前の収集の回からどれだけ動いた？」に直した
- 読書面の設定 `trend.note` に「手順7で…つなぎます」という作業の言葉が画面に出ていたので、「このページの下の「収集の回どうしの比較」で見られます」に直した

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理 → 最後に `elderly_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/elderly.py` は `source_for_refresh` を入力にする。アリーナ（`build_elderly_arena.py`）・潮目（`_apply_tide`）は元HTMLから作った候補に掛かり、
  山なみ・連動表示（`refresh_planet_section.py` → `elderly_connected.apply`）も元HTMLに掛かる。再読データの明細が立場を持つので立場の対応表は作らない。
  代わりに adapter の最初で `check_reread_stances` が、明細に立場（stance）が無い・planet 設定に無い立場がある場合に止める（追い読みで足した明細の書き漏れ）。
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。**新しい意見が入った回で2論点の追い読みをしないと、
  明細の件数が論点の件数と合わず、どのテーマの公開候補生成も止まる**（DATA_REFRESH.md に書いた）。
- **模擬（切替後の作業ツリーのスクラッチ複製、完了記録の検査だけ外した）**:
  - **10/14 の新規0件の回**: 実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む。他テーマの回で高齢者の finish が走る場合と同じ条件として、
    正典をそのまま累積候補にし、adapter の生成物なしで `prepare_public_candidate_bundle`（finalize と finish）を通した。
    最初は `verify_sample_periods.py --generate` が「取得期間の終わりが最終更新日と違う」で止まった（高齢者は `sample_period_source: owner_confirmed` で、
    取得期間を手で伸ばす運用。新デザイン以前からの動き）。THEMES.yaml の `sample_period` を 10/14 まで伸ばして再実行すると**最後まで通った**。
    候補の docs/ は新デザイン（最終更新日 2026-10-14、次回の収集予定 10月24日）、元HTMLは旧形式。自転車・皇室・副首都・生成AI・憲法・部活動の公開ページは変わらず。
    候補の中で `verify_number_provenance.py` 10テーマ NG 0、`verify_builder_rebuildability.py` NG 0、よみやす PASS、使い回し0。
    `verify_theme_page.py` は高齢者で「調査条件（取得元・期間・件数）」の1件だけ NG（伸ばした取得期間が、adapter を通していない元HTMLの調査条件にまだ入っていないため。
    旧形式のページでも同じ形で止まる模擬の事情で、実際の回では adapter が元HTMLの取得期間を書き直す）。
  - 新しい意見がある回（明細が足りない回）で止まることは、`tests/test_elderly_redesign.py` の `test_count_mismatch_stops_before_writing` で確かめた。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/elderly-license-revocation.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの立場・投稿の立場 | `data/elderly-license_issues-reread.json`（`buckets` と明細 `items`。明細に `stance`） | **新しい意見の追い読み（人が読む）**。明細が論点の件数と合わないと生成が止まる |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前 | `configs/elderly-license-revocation-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`（正本 `scripts/build_elderly_process_sections.py` の FACT_CHECKS）・`data/elderly-license-revocation_claim_posts.json` | 主張を足すとき・10/14 の「事故は増えている」の見直し |
| 資料にしかない話 | `data/verification/elderly-license-revocation-sunk-continents.json` → 公開JSON `ocean_layer` | 文を直すときは1文80字以内 |
| 背景（更新時の講習と検査・返納の手続き・家族で話す前・なぜ議論になるか・件数の推移・年表・FAQ・未確認事項） | `configs/elderly-license-revocation-background.json`・`data/verification/elderly-license-revocation-background.json`・一次資料メモ | 一次資料の再確認時 |
| 冒頭（短答・年齢のものさし・返納の流れと統計・FAQ・件数欄）・確認日 | `configs/elderly-license-revocation-opening.json`（`checked_on`） | 制度を確かめ直したら `checked_on` |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION（`refresh_planet_section.py`・連動表示の橋渡し） | 自動 |
| 前の収集回との比較 | 元HTMLの TIDE_CARD（adapter の `_apply_tide`） | 自動 |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データ・次に見るテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件に高齢者／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成で自転車の後に `finish` | 自転車の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/elderly.py` | 入力を `source_for_refresh(root)` に／`check_reread_stances`（明細の立場の書き漏れで止める） | 公開後も元HTMLから生成するため／新しい意見の追い読みで立場が無い明細が増えたとき、何を直すか分かる形で止めるため |
| `scripts/build_elderly_arena.py` | 公開ページが新デザインで、入出力の指定が無いとき `elderly_layout.rebuild`（`--check`・`--public-counts-only` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/elderly_issue_media.py` | `--write-html` で新デザインのページには書かない（停止） | 投票節の前に旧形式の節を差し込む事故を防ぐ |
| `scripts/elderly_license_count_provenance.py` | 新デザインなら `elderly_redesign_provenance` を呼ぶ | 数字の出所検査 |
| `scripts/inject_tide_widget.py` | コメントのみ（新デザインのページは既に SKIP） | — |
| `scripts/refresh_planet_section.py` | 高齢者の新デザインも停止 | 他の新デザインと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 高齢者の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐を高齢者にも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/elderly_background.py` | 開閉行の種類 `checklist`（家族で話す前の確認） | 0節2 |
| 切替時の共有テスト | 9-3 | 公開後は旧形式の検査を元HTMLに向けるため |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に高齢者の `finish` が走る。高齢者の照合が合わないと、その回の
**公開候補生成全体が止まる**（皇室・副首都・生成AI・憲法・自転車と同じ設計）。**10/14 の高齢者の回で新しい意見を追い読みしないと、その後の他テーマの回も止まる。**
単独スクリプトは：`elderly_issue_media.py --write-html` は停止、`apply_classroom_section.py`・`apply_theme_trust.py`・`apply_theme_design.py`・`inject_tide_widget.py` は新ページを飛ばす、
`refresh_planet_section.py` は停止、`build_elderly_arena.py` は元HTMLから作り直す（`--check` で「OK: 差分なし」）。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付・潮目の日付） | 合格 | 合格 |
| `verify_theme_page.py elderly-license-revocation`（候補は `--html`） | NG 0（OK 29） | 9-2 |
| `verify_number_provenance.py` | 10テーマ NG 0（現行ページ 275/275。候補は複製で NG 0） | 9-2 |
| `verify_top_page.py` | 終了0 | 9-2 |
| `build_elderly_arena.py --check` | OK: 差分なし | 9-2 |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 9-2 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（他テーマの既存の指摘。終了1） | 同じ |
| `python3 -m unittest discover tests` | 2,062件 OK（skip 4） | 9-2 |
| `run_public_checks.py` | 終了0 | 9-2 |
| `tests/test_elderly_redesign.py` | 72件 OK（手順7分28件：同じ入力で同じ出力・docs出力と新ページ再入力の拒否・保護対象・GA/AdSense・投票定義・adapter の指紋・FAQ と画面の一致・継承部品・詳細データ・潮目の継承と折りたたみ・論点ごとの折れ線と飛び先・作り方の折りたたみ・初期状態・理由は未公開の表示・授業節・家族の確認とメリデメなし・旧アンカー・山なみの写し・元HTMLの更新への追随と自動着地の変化で停止・旧部品なし・出所検査の改ざん検知3種、レイアウト7件：無効時・状態の一貫・元HTML無し・往復・照合不一致で書かない・立場の無い明細で adapter が止まる・更新経路の配線） | 同じ |
| 2回生成 | md5 一致（`546db31e…`、`PYTHONHASHSEED` 0・1・999・指定なし） | docs のページとも一致 |
| よみやす（`--strict`） | 候補 58/100・完成を止める指摘 0件・PASS（平均35.9字） | 同じ |
| 使い回し（`verify_page_originality.py`、切替後の複製で） | 最初は1件（前の収集回との比較の見出しが自転車と 0.91）→ 見出しを書き直して 0件 | 9-2 |
| AI臭（`verify_ai_tone.py`） | 問題なし | 9-2 |
| `seo/validate_theme_seo.py` | — | 9-2（H1 が変わるので `display_headline` を足す） |

操作（Playwright、`tests/test_elderly_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（scrollWidth＝画面幅。読書面の折りたたみ全開・背景9行・比較・詳細データを開いても0）、ページのコンソールエラー0。
- 山なみ：立場モード（3つ目）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`。
- 読み込み時：URL にハッシュが付かず、山なみの選択パネルと読書面はどちらも「事故防止と年齢の線引き」（分類名「義務化・事故防止」）。
- 論点タブ6つで scrollY 不変、論点の切替で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「次の理由へ」で次へ。
- 前の収集回との比較：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「回ごとの比較へ」で折りたたみが開き論点の変化になる。
- 旧アンカー：2節の表の主な読み替えをブラウザで確認（`#fb-…`・`#elderly-license-revocation-reading-…`・`#bukatsu-background`・`#decision-check-title`・`#return-merit-title`・
  `#return-age-guide`・`#elderly-license-faq`・`#stance-glance`・`#classroom-title`・`#issue-…`・`#fr-r-…`・潮目のカード・`#detail-data`）。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン6つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：6論点すべて表示、図が使えないときの論点一覧・「理由は未公開」の1行・比較の要約・作り方・詳細データ・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 16,662px | **12,782px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数（main） | 5,949字 | 4,741字 | — |
| うち冒頭 | — | 3,908px | — |
| 山なみ（選択パネル込み） | 3,980px | 2,033px | — |
| 1280px のページ全体 | 10,530px | 7,850px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 事故防止と年齢の線引き | 2,496px | 862字 | 1,301px |
| 検査で運転を見極める | 1,419px | 476字 | 861px |
| 車がないと暮らせない地域 | 2,034px | 700字 | 1,325px |
| 自分から返納しやすくする | 1,627px | 534字 | 901px |
| バスや乗合の足を整える | 1,320px | 428字 | 804px |
| その他 | 1,113px | 330字 | 804px |

論点の欄は6論点とも目標（2,500px以下）を満たす。最初は「前の収集回との違い」を足して事故防止の欄が 2,540px になったので、
見出しと飛び先の文を短くし（「前の回との違い」「回ごとの比較へ ↓」）、スマートフォンだけ小さな折れ線を 52px にして数字2つを1行に収めた。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. title・description・Article の見出しに「メリットとデメリット」が残る（`configs/theme-seo.json` の `headline`・`description`）が、新ページにはメリット・デメリットの節が無い。
   私なら、検索の評価を見てから（変えると検索結果の題が変わるため）`headline` を「免許返納は何歳から？年齢の節目と返納後の手続き、義務化の賛否」のように直す。今回は保護対象として変えていない。
3. 申し送り5（背景台帳の年表「令和8年8月を目途に報告書」・`cause` の80字超）：背景台帳は旧ページの連動表示と共有しているので直さず、新ページは設定の言い換え（`timeline.overrides`・`extra`・`cause_rewrites`）で正しく表示している。
   台帳を直すのは 10/14 以降の一次資料の再確認のとき（直したら言い換えを外す）。
4. 申し送り6の後半（照合「運転技能検査はザル」の finding が「8月を目途に報告書」のまま）：判定は変えず注記 `claim_notes.skilltest`（報告書の公表）を維持。10/14 の照合の見直しで一緒に直す。
5. 申し送り7（編集部の横断整理）：文中に％が埋まっているので新ページには載せていない（山なみから `#editorial` を外した）。差し込み式にするのは別作業。
6. 申し送り10（冒頭の「その他」の扱い）は案Aのまま。
7. 山なみの選択パネルの見出しと論点ボタンは、元HTMLのとおり分類名（「義務化・事故防止」）を出す（読書面の見出しは言い換えた表示名）。写した部品の文言は変えない方針のため。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。12件の投稿が閲覧できることは手順6で 10/12 に確認済み）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は新規0件の模擬と、明細不足で止まる単体テストだけ。

## 9. 2026-10-12 公開切替

9節は公開切替のコミットで書き足す。
