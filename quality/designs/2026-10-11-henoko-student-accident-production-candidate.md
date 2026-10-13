# 辺野古高校生死亡事故（henoko-student-accident）新デザインの公開候補と検査（手順7）

2026-10-13。ブランチ `task/renew-henoko-student-accident`。手順書23の「7. 更新と公開を検査する」。
学校でのあだ名禁止の [2026-10-11-school-nickname-ban-production-candidate.md](2026-10-11-school-nickname-ban-production-candidate.md)
（対話式の山なみを元HTMLから写す＋部活動型の圧縮）をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/henoko-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/henoko-student-accident-release/henoko-student-accident-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-08）
確認画面: `quality/prototypes/henoko-student-accident-release/evidence/`（PC・375px の全体、山なみ、立場モード切替、山を押して読書面へ、
読書面、理由を開いた画面、短答から年表を開いた画面、背景を開いた画面、前の収集回との比較を開いた画面、X遮断時、JSなし）

人が亡くなった事故のテーマ。冒頭設計記録の「被害者への配慮で避けた表現」と手順5〜6の配慮の基準（氏名・性別・学校名・船名・遺族への言及・
生々しい描写・煽る表現・名指しの批判を使わない、船・波の図柄を使わない）を、手順7で書いた文・直した文・写した部品のすべてに当てた（2節の最後）。

## 0. 手順7の前に直したこと（コミット 4f5afa7d）

| 項目 | 処理 |
|---|---|
| 1. よみやすの残り5件 | 公開JSON由来の文を、数字・出典・判定を変えずに文体だけ直した。重なる心配 `vein-safety` の `diverging_reason`（「ます」3連続。2論点に出るので2件）、照合 `education-finding` の `finding`（81字・読点4。正本は `scripts/build_henoko_process_sections.py` の FACT_CHECKS `note`）、資料にしかない話 `lifejacket-training` の `sns_note`（114字）。`build_public_registry.py --topic henoko-student-accident` で公開JSON・catalog を、`build_adoption_registry.py` で採用台帳の指紋を作り直した。元HTML（当時の docs）の旧形式の部分も `build_henoko_arena.py` で作り直した（文の差し替えだけ）。`verify_number_provenance.py henoko-student-accident` NG 0、`verify_ocean_layer.py` は直す前と出力が完全に同じ（他テーマの既存の指摘で終了1）。読書面の試作のよみやす `--strict` は完成を止める指摘 5件→0件 |
| 照合文の船名（申し送り3の後半） | 照合 `unregistered-service` の正本の文から船名を外し「転覆した船のうち1隻の船長」にした。読書面の言い換え（`claim_finding_overrides`）は不要になったので空にした（言い換えを置いたときに公開JSONの文が変わると止まる検査は残した） |
| 2. 公開側 background.json の年表 | 新デザインは冒頭の設定の年表が正本。`data/verification/henoko-student-accident-background.json` の年表は元HTML（旧形式）が読むので残し、10/11の照合表の食い違いを冒頭の設定に合わせて直した：5/22（告発の対象＝転覆した船のうち1隻の船長。船名を外した）、7/14（抗議船での見学などを総合して第14条第2項に反すると判断した／移設工事を扱うこと自体を中立違反としたのではない）。あわせて3/16の文から学校名と府名を外した。checklist「教育の内容」の文末を直し、読書面の `check_overrides` を外した。確認日 `checked_on` を 2026-10-13 に |
| 背景パネル（元HTMLの `#bukatsu-background`） | 初回の切り替えで書かれた静的な部分で、どの生成器も作り直さない。`build_planet_page_preview.build_background` の出力が直す前の台帳から作った区間と1か所だけ一致することを確かめて、直した台帳の出力に差し替えた |
| `configs/theme-seo.json` | 「収集・分類で分かったこと」から旧回の件数（98件）を外し、`apply_theme_trust.py --theme henoko-student-accident` で元HTMLの作り方を作り直した |

### 申し送り（読書面の設計記録10節）の処理

| 申し送り | 処理 |
|---|---|
| 1. 山なみ | 元HTMLの `#planet-block` を写して論点タブの上に置いた（2節・3節）。planet 設定の論点アイコン（🛟 浮き輪・🕊️ など）は**山なみでも使わない**と決めた：PLANET_DATA（公開データの契約）は変えず、山なみのスクリプトが描く直前に表示用の値だけ空にする小さなスクリプトを挟んだ。JSなしの論点一覧の絵文字も外した |
| 2. 推移 | 潮目のカードを「2回の収集を比べたグラフを開く」の折りたたみに写し、各論点の「前の回との違い」に小さな折れ線と数字2つを入れた。潮目の論点は5つで「政治利用・基地問題」が無いので、その論点には「回ごとの比較の対象に入っていません」と書く（数字・折れ線は出さない）。比べる意見がごく少ない（6件と7件）ので、要約の1文はカードの見出し（「『文科省判断を支持』が0.0ポイント減少」）ではなく、何を比べているかの説明（設定 `compact.trend_lead`）にした |
| 3. よみやす・船名・check_overrides | 0節 |
| 4. 年表 | 0節。元HTML側の年表は残し、文言だけ冒頭の設定に合わせた（廃止は旧ページを生成し続ける間はしない）。`henoko_connected_content.py` の「照合した経緯」は台帳の年表を読むので、同じ直しが反映される |
| 5. FAQ | 構造化データは画面の7問（冒頭の短答3問「何があった？」「原因は分かった？」「何が争点？」の問いと1文の答え＋背景「よくある質問」4問）から作り直した。答えの文から出典リンクの名前（「文部科学省の見解（PDF）」）は外した。元HTMLの FAQ_JSON_LD（旧FAQ6問。1問目の答えに学校名があった）は使わない。`tests/test_henoko_search_entry.py` は元HTML側（旧ページ）を検査するので、そのまま通る |
| 6. 10/22 の追い読み | DATA_REFRESH.md に書いた（9節）。立場の対応表は更新経路の adapter が作り直すようにした（4節） |
| 7. 報告書の公表 | 冒頭の設定 `report.published_on` に日付を入れると、冒頭の短答・背景・構造化データの文が切り替わり、生成は止まらないことを隔離した root で確かめた（テスト `test_report_publication_switches_wording`。docs には入れていない） |
| 8. 代表投稿の生存 | 2026-10-13 に cdn.syndication.twimg.com で12件とも本文が返ることを確かめた（`__typename: Tweet`） |
| 9. 冒頭の試作単独のリンク | 公開ページでは「経緯を年表で見る」「まだ公表されていないものを見る」とも背景の行へ飛び、行が開く（ブラウザで確認） |
| 10. 授業向けの設定 | 「6月8日の抗議」は一次資料で確かめられた範囲（7/14総務委員会 #114 の議員の発言）に合わせ「7月14日の国会では、…抗議したことが、議員の質問で取り上げられた」に直した。「学校の第三者委員会が結論を出す前に…疑問の声」は確かめていないので外し、出典にある5/29の知事の発言（学校の自主的な対応を時間をかけて見守る必要があった）に置き換えた。設定は旧ページと共有なので、公開切替のときに元HTMLの授業節も作り直した（9節） |

## 1. 仕組み（あだ名禁止と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_henoko_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`henoko_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/henoko_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/henoko-student-accident.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_henoko_arena.py` を単独で動かしたとき。元HTMLに旧形式の生成（`build_page`：山なみの件数・調査条件・詳細データの表・連動表示。山なみの入力の版の守り `henoko_planet_guard.verify_inputs` もここで働く）とアリーナの点と公開JSONの集計を掛けてから新デザインを組む） |
| `configs/henoko-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/henoko_redesign/planet.js`（新規） | 山なみの橋渡し（あだ名と同じ。入口は `window.HenokoReading.select`） |
| `scripts/henoko_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（墨・灰青・砂色）に合わせる。立場は4つなので立場ボタンは5つ（スマートフォンでは「すべて」を1行、4立場を2列）。投票の論点ボタンの絵文字は CSS で隠す |
| `scripts/henoko_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・立場の対応表・設定から数え直して照合（`henoko_count_provenance.py` が新デザインのときだけ呼ぶ）。冒頭の件数欄、短答「何が争点？」、6論点の欄。論点の見出しと理由ごとの立場は帯ではなく1文なので、文の中身を数え直して比べる |

ページの並び：共通ヘッダー → 冒頭（パンくず・題名・短答3問・SNSの意見の件数）→
論点ごとに読む（見出し → **対話式の山なみ**（立場モード・山・論点ボタン・選択パネルと100マス・見かた・調査条件）→ 論点タブ → 選んだ論点の欄）→
2回の収集の比較（要約＋折りたたみ）→ 投票 → 背景の開閉行7行 → 集め方と分類、詳しい集計表（折りたたみ1つ）→ 次に読むテーマ → フッター。

時制：「◯月◯日時点」は冒頭の設定 `checked_on`（2026-10-13）1か所から出る。報告書は `report.published_on`／`content_checked_on` の3段階。
同じデータなら同じページになる。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「辺野古沖転覆事故とは？原因・報告書・安全管理の論点｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承（OGP画像も同じ）。**description に学校名がある**（7節・オーナー判断） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承（description に学校名。同上） |
| FAQ JSON-LD | 旧FAQ6問 | 冒頭の短答3問＋背景「よくある質問」4問＝7問から作り直し | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間と `google-adsense-account` meta | 区間は release だけ、meta は両方 | 継承 |
| 共通CSS/JS | site-tokens（v=3）・topic-modern（css v=32・js v=14）・henoko-connected（css/js/page.js）・henoko-search-entry（css/js）・theme-design・manga-viewer.js | site-tokens・topic-modern だけ（版は元HTMLから読む） | 検索入口・連動表示・テーマ共通の見た目は意図的に外した |
| 投票（Supabase） | topic `henoko-student-accident-issue-stance-v1`、論点6×立場3＝18、`choiceIdx:selected*STANCES.length+index`、保存キー `sns_vote_henoko_issue_arena_v1` | 投票節とスクリプトを複写。TOPIC・ISSUES・STANCES は元と完全一致。保存キーは本番ホストだけ既存キー、他は `…_preview`。前置きの文も元のまま | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（18通り）。元HTMLの V2I に当たる定義は辺野古には無い（論点は ISSUES の並び順が投票番号）。**論点ボタンの絵文字（🛟など）は定義を変えずに CSS で隠した**。投票後に出る論点の説明のうち「追悼、遺族への配慮と静かな検証」は定義の一部なので変えていない（7節） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承。PLANET_DATA の文字は変えない（論点の絵文字は表示の直前に空にする） |
| 共通ヘッダー・パンくず | 元HTMLは静的ヘッダーが無い（topic-modern.js が差し込む） | あだ名と同じ静的な共通ヘッダー、冒頭のパンくず「教育・事故 ／ 辺野古沖の船舶転覆事故」 | JSなしでもトップへ戻れる |
| 前の収集回との比較（TIDE_CARD） | 9/23→10/8、立場・論点の2タブ、再生ボタン | 枠と CSS 区間を文字どおり複写し、要約の下の折りたたみ `#cap-trend-more` へ | 継承。読書面の「回ごとの比較へ」の飛び先（設定 `trend.widget_id`＝`henoko-tide-widget`）は実際の id と一致（テストで確認） |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、詳細データと一緒に折りたたみ `#cap-method` へ | 継承（公開日・最終更新日の `<time>` も残る） |
| 詳細データ（#detail-data） | 表4つ（投票の3区分「評価・保留・疑問」、切り分け＋中立＝448）と「注意」 | 表は公開JSONの4立場・分類名で作り直し（件数の多い順）、「注意」は文字どおり複写。折りたたみは最初どれも閉じる | 内容対応表33の「448」の食い違いを解消 |
| 次に読むテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking` | 両方文字どおり複写 | 継承 |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間（元HTML） | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| アリーナの点（`docs/henoko-arena-data.js`） | 旧ページのアリーナが読む | 新ページは読み込まない | 更新経路（adapter・`build_henoko_arena.py`・`rebuild`）で引き続き生成され、公開対象に入る |
| 進み具合の帯「探ったところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先だけ隠して置く） | 内容対応表1 |
| 検索入口（3層）・立場の帯・背景パネル・確認項目・旧FAQ | HENOKO_SEARCH_ENTRY・`#stance-glance`・`#bukatsu-background`・`#bukatsu-check`・`#henoko-faq` | 載せない | 冒頭・読書面・背景に置き換え（旧アンカーは読み替え。`#henoko-faq` は背景の行が同じidを持つ） |
| 編集部の横断整理・一次資料クイズ・予想2問・論点の図解画像 | `#editorial`・`#quiz`・`#guesses`・landing-image | 整理と図解は外し、クイズと予想は受け皿だけ隠して残す | 内容対応表22・25 |
| llms.txt・sitemap | URL のみ | URL 不変 | 継承 |

**配慮の確認（本文を目で読んだ）**：写した山なみ（見出し・問い「辺野古の修学旅行中の事故を、学校はどう検証すべきか」・調査条件・切り分けの注記・100マスの説明・
JSなしの論点一覧・見かた）、潮目のカード（立場3つ・論点5つの名前と注記）、投票（前置き・問い・注記）、作り方（収集方法・分かったこと3つ・読み方）、
詳細データの注意3行、次に読むテーマ、フッターを読んだ。氏名・性別・学校名・船名・遺族への言及・生々しい描写・煽る表現・名指しの批判は無い。
外した・直したもの：論点の絵文字（山なみ・JSなしの一覧・投票ボタン。浮き輪は船・海の図柄）、作り方の旧い件数（0節）、授業向けの未確認の2文（申し送り10）。
山なみの「海面下の演出」（海・波の図柄）は CSS で隠している。
機械の確認：避けた語（`tests/test_henoko_redesign.py` の AVOID：学校名・船名2つ・「女子高」「女子生徒」「遺族」・🛟⚓🚢🌊）が、見えている文字に1つも無い
（テストとブラウザの両方。ブラウザでは山なみ・投票ボタンがスクリプトで描いた後の文字も見る）。HTML のソースに残るのは、文字どおり引き継いだ保護対象だけ：
SEO_META と Article JSON-LD の description の学校名、投票の定義（🛟 と「遺族への配慮」）、PLANET_DATA（理由区分の名前2つに「遺族」。選択パネルでは表示しない）。
**`scripts/henoko_planet_guard.py` は語のリストを持たない**（山なみの入力の版を確かめる守り。候補が正典を書き換えていないか・公開JSONと候補が同じ版か）。
新デザインでもこの守りは元HTMLへの旧形式の生成の途中で働く（更新経路の adapter・`rebuild` とも `build_page` → `refresh_verified_planet` → `verify_inputs`。テスト `test_rebuild_runs_planet_guard_on_source`）。
配慮の語の検査には、手順5〜6で決めた AVOID を使った。

### 旧アンカーの到達確認

`grep -rn "henoko-student-accident-reaction-map.html#" docs/ scripts/ configs/ company/` の結果は `company/CORRECTIONS.yaml` の
`#correction-20260906`（2026-09-06 の訂正の告知）の1件。この告知の枠は現行ページにも無く、既に飛び先が無かった。
新ページでは訂正窓口への案内がある「このページの作り方」へ読み替える（折りたたみを開く）。
外から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#progress`・`#henoko-entry`（`-title`・`-selection`・`-layers`） | 冒頭 `#henoko-open` |
| `#henoko-entry-facts`・`#henoko-entry-pending` | 背景「公的機関の公表と、まだ出ていないもの」`#bg-official`（開く） |
| `#henoko-entry-voices`・`#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`） | 冒頭の件数欄 `#hop-count` |
| `#henoko-entry-bridge-label`・`#henoko-entry-open-map` | 山なみ `#planet-block` |
| `#henoko-entry-tab-{safety など6つ}` | その論点の欄 `#issue-henoko-student-accident-…`（選んだ状態になる） |
| `#bukatsu-background`・`#bg-title` | 背景「経緯の年表」`#bg-timeline`（開く。旧検索入口が「年表」として指していた） |
| `#bukatsu-check`・`#ck-title` | 安全管理の欄（「学校の説明で確かめること」が最も多い論点） |
| `#fallback`・`#fallback-nav`・`#quiz`・`#ocean`・`#editorial`・`#henoko-connected-data` | 読書面 `#henoko-student-accident-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#henoko-student-accident-reading-{論点ID}`・`#henoko-reasons-{論点ID}`・`#henoko-evidence-{論点ID}` | その論点の欄（選んだ状態になる） |
| 論点の素のID（`#henoko-student-accident-safety` など。旧ページの山なみの着地が使っていた） | 読み込み時だけ、その論点の欄 |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |
| `#henoko-faq-title` | 背景「よくある質問」`#henoko-faq`（旧ページのFAQの節と同じid。開く） |
| `#correction-20260906` | 「このページの作り方」`#article-trust-title`（折りたたみを開く） |

そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`planet-block`・`planet-data`・`henoko-tide-widget`・
`article-trust-title`・`henoko-faq`・`issue-{論点ID}`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS・CSS の内部用ID（`henoko-reason-count-…`・`henoko-check-note-…`・
`henoko-source-…`・`pbar`・`vote-related-themes` など）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_henoko_redesign.py --mode release --output-dir quality/prototypes/henoko-student-accident-release
```
成功すると `Built 1 file (release, as_of 2026-10-08); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense の読み込みなし、noindex、投票は送らない）: `--mode preview --output-dir /tmp/henoko-preview`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文（`section.landing-panel`）・論点の目印（`span.issue-anchor`。新ページでは読書面の欄が `#issue-…` を持つ）・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。
  連動表示の橋渡し（`HENOKO_CONNECTED_BRIDGE` の `initialLand`）は、読み込み時（ハッシュが無いとき）に件数最多の論点へ着地して `location.hash` を書く。
  この4行を「読書面の既定の論点（`data-default-issue`）を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」処理に置き換える（`AUTO_LAND`／`AUTO_LAND_OFF`）。
  旧ページの論点テンプレート（`template#henoko-student-accident-reading-…`）は写さないので、選択パネルは山なみ本来の表示（件数・立場の帯・100マス）になる
- **論点の絵文字**：PLANET_DATA と山なみのスクリプトは文字どおりのまま、あいだに `NO_ICONS`（`issues[].icon` を空にする1行）を挟む
- **細い山の注記**：「論点を切り分ける」を選ぶと政治的中立性・平和教育の萎縮が細すぎて広げて描く注記、「中立・情報共有」では強い表現0%の点の案内が出る（Playwright で記録）
- **立場モードのボタン（375px）**：「すべて 495件」を1行、4立場を2列。「論点を切り分ける 445件 89.9%」も2列の中に収まる（`evidence/planet-mobile.png`・`planet-mode-mobile.png`）
- **2回の収集の比較**：潮目のカードの `const datasets` と比べた日付（9月23日→10月8日）だけを読み、要約に立場3本の2点の折れ線、読書面の各論点に2点の折れ線と
  「9月23日 0.0% → 10月8日 85.7%」の形の数字を入れる（件数は描かない）。比べる意見が6件と7件と少ないことは、要約の注記・各論点の注記・カードの注記の3か所に出る
- **詳細データの表**：公開JSONの4立場・分類名で作り直す（件数は手で書かない。合計が意見数と違えば止まる）
- **見出しの書き分け**：要約の見出し・注記・折りたたみの名前（`compact.trend_*`・`method_fold`）は、あだ名・高齢者と使い回しにならないよう書き分けた

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理 → 最後に `henoko_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/henoko.py` は `source_for_refresh` を入力にする。山なみの件数・連動表示・アリーナの点（`build_henoko_arena.py`）・潮目（`_apply_tide`）は
  元HTMLから作った候補に掛かる。山なみの入力の版の守り（`henoko_planet_guard`）も元HTMLへの生成の途中で働く。
  **立場の対応表（`data/henoko-student-accident_reread-stances.json`）は、あだ名禁止と同じく累積候補と再読データから作り直して公開対象に含める**
  （`build_reread_stances`。2回作って一致を確かめる）。新しい意見が再読データの明細に無いと「追い読みが要ります」で止まる（テストで確認）。
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。
- 10/22 の模擬は公開切替の後に行った（9-4）。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/henoko-student-accident.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの件数 | `data/henoko-student-accident_issues-reread.json`（`buckets` と明細 `items`） | **新しい意見の追い読み（人が読む）**。明細が正典の意見と合わないと生成が止まる |
| 区分ごとの立場・投稿の立場 | `data/henoko-student-accident_reread-stances.json`（post_key → 立場） | 更新経路では adapter が作り直す。経路の外では `henoko_reread_stances.py --made-on` |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前 | `configs/henoko-student-accident-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`（正本 `scripts/build_henoko_process_sections.py` の FACT_CHECKS）・`data/henoko-student-accident_claim_posts.json` | 主張を足すとき。船名・氏名を書かない |
| 資料にしかない話・重なる心配 | `data/verification/henoko-student-accident-sunk-continents.json`・`-veins.json` → 公開JSON `ocean_layer` | 文を直すときは1文80字以内・同じ文末3連続なし |
| 背景（年表・公表と未公表・FAQ・ことば・なぜ・授業・未確認） | `configs/henoko-student-accident-opening.json`（年表・未公表・FAQ・`report`）・`configs/henoko-student-accident-background.json`・`data/verification/henoko-student-accident-background.json`・`configs/classroom/henoko-student-accident.json` | 一次資料の再確認時。年表は冒頭の設定が正本（台帳の年表は旧ページ用で、直すなら両方） |
| 冒頭（短答・件数欄）・確認日・報告書の公表 | `configs/henoko-student-accident-opening.json`（`checked_on`・`report`） | 確かめ直したら `checked_on`。報告書が出たら `report.published_on`、読んだら `content_checked_on` |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION（`build_henoko_arena.py` の山なみと連動表示の橋渡し） | 自動 |
| 2回の収集の比較 | 元HTMLの TIDE_CARD（adapter の `_apply_tide`） | 自動 |
| 詳細データの表 | 公開JSON（`build_henoko_redesign.detail_tables`） | 自動 |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データの注意・次に読むテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件に辺野古／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成であだ名の後に `finish` | あだ名の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/henoko.py` | 入力を `source_for_refresh(root)` に／`build_reread_stances`（累積候補から立場の対応表を作り、2回一致を確かめ、公開対象に含める） | 公開後も元HTMLから生成するため／追い読みの後に対応表の作り直しを忘れて止まる事故をなくすため |
| `scripts/build_henoko_arena.py` | 公開ページが新デザインで、入出力の指定が無いとき `henoko_layout.rebuild`（`--check`・`--public-counts-only` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/henoko_count_provenance.py` | 新デザインのページなら `henoko_redesign_provenance` に渡す | 新デザインの理由区分などの件数を照合するため（旧ページの照合はそのまま） |
| `scripts/inject_tide_widget.py` | コメントのみ（新デザインのページは既に SKIP） | — |
| `scripts/refresh_planet_section.py` | 辺野古の新デザインも停止 | 他の新デザインと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 辺野古の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐を辺野古にも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `configs/henoko-student-accident-reading.json` | `compact` に手順7の見出しと文、`glance_missing` | 2節・3節 |
| `configs/classroom/henoko-student-accident.json` | 未確認の2文を直した | 申し送り10 |
| 切替時の共有テスト | 9-3 | — |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に辺野古の `finish` が走る。辺野古の照合が合わないと、その回の
**公開候補生成全体が止まる**（皇室・副首都・生成AI・憲法・自転車・高齢者・あだ名と同じ設計）。**10/22 の辺野古の回で新しい意見を追い読みしないと、adapter が止まる
（複数テーマをまとめて作る回なら全テーマが止まる）。** 辺野古の adapter が立場の対応表も公開対象に含めるようになったので、辺野古の回の公開物が1つ増える。
単独スクリプトは：`apply_classroom_section.py`・`apply_theme_trust.py`・`apply_theme_design.py`・`inject_tide_widget.py` は新ページを飛ばす、
`refresh_planet_section.py` は停止、`build_henoko_arena.py` は元HTMLから作り直す（`--check` で「OK: 差分なし」）。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付・潮目の日付・詳細データの表の合計） | 合格 | 合格 |
| `verify_theme_page.py henoko-student-accident`（候補は `--html`） | NG 0（現行ページも NG 0） | NG 0、全10テーマ NG 0 |
| `verify_number_provenance.py` | 候補 335/335・NG 0（`henoko_redesign_provenance` で冒頭の件数欄・短答・6論点の欄を照合）。現行ページ NG 0 | 辺野古 335/335・10テーマ NG 0 |
| `verify_top_page.py` | 終了0 | 終了0 |
| `build_henoko_arena.py --check` | unchanged（差分なし） | OK: 差分なし（公開後の経路＝元HTMLと新ページ・アリーナの点を作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（既存の指摘。終了1） | 同じ |
| `python3 -m unittest discover tests` | 2,208件 OK（skip 4） | 2,208件 OK（skip 4。共有テストを直す前は失敗14・エラー8） |
| `run_public_checks.py` | 終了0 | 終了0 |
| `seo/validate_theme_seo.py` | OK（themes=10） | OK（themes=10。H1 が変わるので `display_headline` を足した） |
| `tests/test_henoko_redesign.py` | 76件 OK（手順7分30件：同じ入力で同じ出力・docs出力と新ページ再入力の拒否・保護対象（共通CSS/JSの版を含む）・GA/AdSense・投票定義と保存キー・adapter の指紋・FAQ と画面の一致・継承部品・詳細データの4立場と注意・潮目の継承と折りたたみ・論点ごとの折れ線と飛び先・作り方の折りたたみ・初期状態・「その他」0件で出さない・授業節・配慮の語・旧アンカー（サイト内リンクを含む）・山なみの写し・元HTMLの更新への追随と自動着地／保存キーの変化で停止・旧部品なし・報告書の公表日で文面が切り替わる・出所検査の改ざん検知3種、レイアウト8件：無効時・状態の一貫・元HTML無し・往復・照合不一致で書かない・rebuild で planet_guard が働く・adapter の対応表の作り直しと追い読み不足で停止・更新経路の配線） | 同じ（76件 OK） |
| 2回生成 | md5 一致（`PYTHONHASHSEED` 0・1・999・random） | md5 `d2fd1592…`（4通りとも一致、docs のページとも一致） |
| よみやす（`--strict`） | 候補 90/100・完成を止める指摘 0件・PASS（平均34.4字、最長74字）。最初は要約の注記で「ます」3連続が1件→直した | 同じ |
| 使い回し（`verify_page_originality.py`） | — | 「10ページに、使い回された見出し・文はありません」（最初は読書面の前置きがあだ名と0.73で似ていた→書き直した） |
| AI臭（`verify_ai_tone.py`） | — | 問題なし（公開ページ10本） |
| 採用台帳（`build_adoption_registry.py --check`）・`build_data_sheet.py --check` | — | 一致・最新 |
| 代表投稿の生存（cdn.syndication.twimg.com） | 12件とも本文あり（2026-10-13） | — |

操作（Playwright、`tests/test_henoko_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（scrollWidth＝画面幅。読書面の折りたたみ全開・背景7行・比較・詳細データを開いても0）、ページのコンソールエラー0。
- 避けた語と船・波の絵文字が、見えている文字（スクリプトが描いた山なみの論点ボタン・選択パネル・投票ボタンを含む）に無い。
- 冒頭の「経緯を年表で見る」で背景の年表の行が開く。
- 山なみ：立場モード（3つ目＝文科省判断に反発）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`。
- 読み込み時：URL にハッシュが付かず、山なみの選択パネルと読書面はどちらも「安全管理・事故原因」（読書面の表示名「安全管理と、事故の責任」）。
- 論点タブ6つで scrollY 不変、論点の切替で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「ほかの理由も読む」で次へ。
- 前の収集回との比較：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「回ごとの比較へ」で折りたたみが開き論点の変化になる。
- 旧アンカー：2節の表の主な読み替えをブラウザで確認。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン6つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：6論点すべて表示、図が使えないときの論点一覧・本文・比較の要約・作り方・詳細データ・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 24,388px | **11,051px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数 | 9,848字（body） | 3,891字（main） | — |
| うち冒頭 | — | 2,652px | — |
| 山なみ（選択パネル込み） | — | 2,058px | — |
| 1280px のページ全体 | 14,916px | 7,127px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 安全管理と、事故の責任 | 2,438px | 855字 | 1,282px |
| 事故と、政治や基地問題の結びつけ | 2,156px | 801字 | 1,335px |
| 報道と行政の伝え方 | 2,098px | 792字 | 1,309px |
| 亡くなった方への配慮と追悼 | 2,025px | 755字 | 1,316px |
| 学校の学習と、政治的中立 | 2,299px | 797字 | 1,282px |
| 平和学習は萎縮するのか | 2,244px | 814字 | 1,316px |

論点の欄は6論点とも目標（2,500px以下）を満たす。手順6の試作より各欄が約100〜170px高いのは、「前の回との違い」に折れ線と数字が入ったため。

## 7. 公開前の残作業・判断待ち

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. **SEO_META と Article JSON-LD の description に学校名がある**（「2026年3月に同志社国際高校の研修旅行中に起きた…」。`configs/theme-seo.json` の description が正本）。
   本文と FAQ の構造化データからは外したが、検索結果の説明文・SNS共有のカードには出る。保護対象として変えていない（課題105の 11/1 Search Console 判定が title・description の変更を見ている）。
3. **投票の定義に浮き輪の絵文字と「遺族への配慮」がある**。絵文字は CSS で隠した。説明「追悼、遺族への配慮と静かな検証」は投票後に画面に出る。投票の定義は元と完全一致が条件なので変えていない。
4. 山なみの色は、元HTMLの山なみのスクリプトが決める色（「すべて」は青 `#075ef2`、「論点を切り分ける」は黄 `#D9A520`）のまま。冒頭の配色（墨・灰青・砂色、黄は使わない）と合わないが、写した部品の色は変えない方針なので変えていない。
5. 潮目のカードの中身（9/23→10/8 の比較で、立場は「中立・情報共有」が2回とも100%、見出し「『文科省判断を支持』が0.0ポイント減少」）は元HTMLのまま。比べる意見が6件と7件で情報が薄い（内容対応表27）。カードの数え方の確認は今回していない。
6. 山なみの選択パネルの見出しと論点ボタンは、元HTMLのとおり分類名（「安全管理・事故原因」）を出す（読書面の見出しは言い換えた表示名）。論点ボタンの「／島5」（理由区分の数）も元のまま。
7. title・H1：title は保護対象として変えていない。H1 は新デザインの見出し「辺野古の転覆事故、何が分かっていて何が争点か」に変わる（`display_headline`）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。12件の投稿が残っていることは 10/13 に確認済み）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は新規0件相当の模擬（9-4）と、明細不足で止まる単体テストだけ。

## 9. 2026-10-13 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/henoko-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | henoko-student-accident に `display_headline`（新しい H1 の文字列そのまま） |
| `configs/henoko-student-accident-reading.json` | 読書面の前置き（`section.lead`）を書き直した（使い回し検査であだ名の前置きと0.73で似ていた） |
| `data/page-sources/henoko-student-accident.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致。授業向けの設定を直した分だけ、切替の直前に元HTMLの授業節を `apply_classroom_section` の関数で作り直した） |
| `docs/henoko-student-accident-reaction-map.html` | 新デザイン（`henoko_layout.finish`。公開候補とバイト一致、md5 `d2fd1592…`） |
| `scripts/build_henoko_arena.py` | 公開後に `--input` などだけを渡したときの土台を元HTMLにし、`--output-html` が無ければ止める。`--public-counts-only` に新デザインのページを渡すと止める（新ページを旧形式で上書きしない） |
| `company/APPROVALS.yaml` | 末尾に `approval-20261013-henoko-student-accident`（`status: pending`、`decided_at: null`）。既存の記録は動かしていない |
| `DATA_REFRESH.md` | 「辺野古高校生死亡事故の定期更新（新デザインを維持する、2026-10-13〜）」の節と、旧「辺野古の定期更新」の節への注記 |
| `themes/henoko-student-accident.md` | 作業記録 |
| 共有テスト | 9-3 |

DATA_SHEET.md は `--check` で最新（全テーマで意見＝論点＝賛否＝マップの点）。

### 9-2. 切替後の検査（作業ツリー）

6節の「切替後」の列。切替後の docs/ のページは公開候補とバイト一致なので、Playwright の確認画面（`evidence/`）は切替後のページで撮り直した。
単独スクリプトは隔離コピーで確かめた：`refresh_planet_section.py --for-docs` は停止、`inject_tide_widget.py`（SKIP）・`apply_classroom_section.py`・
`apply_theme_trust.py --theme henoko-student-accident`（skipped）・`apply_theme_design.finish`（対象外）・`build_henoko_arena.py`（引数なし・`--public-counts-only` とも「OK: 差分なし」）・
`sync_issue_counts.py` を流しても、新デザインのページ・元HTML・アリーナの点はバイト不変。
（参考：`apply_theme_trust.py` を全テーマで流すと部活動のページで「missing SEO metadata block」と止まり、`apply_classroom_section.py --check` は部活動のページを
「would update」と出す。どちらも切替前の作業ツリー（変更を退避した状態）でも同じで、辺野古の変更とは関係ない既存の動き）

### 9-3. 切替に合わせて直した共有テスト

切替直後の全テストは失敗14・エラー8（2,194件中）。あだ名の切替（同じ記録の9-3）と同じ直し方で、検査の基準は緩めていない。

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_henoko_connected.py`・`test_henoko_planet.py`・`test_henoko_public_counts.py`・`test_henoko_search_entry.py`・`test_henoko_verified_refresh.py` | 読むページを「公開後は元HTML（`source_for_refresh`）」に | 旧形式の連動表示・山なみの件数・検索入口・公開集計・山なみの入力の版の検査。公開後も元HTMLに同じ構造で残る（あだ名と同じ扱い） |
| `tests/test_cite_button.py` | 辺野古の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 辺野古の新デザインを飛ばす | 共通の見た目を掛けない設計 |
| `tests/test_theme_hero_assets.py` | 辺野古の新デザインではヒーロー写真の出現回数を数えない（OGP・GA・AdSense の確認はそのまま） | 新デザインはヒーロー写真を載せない（部活動と同じ扱い） |
| `tests/test_page_originality.py`（直していない） | 前置きを書き直して通した | 9-1 |

### 9-4. 10/22 の定期更新の模擬（切替後の作業ツリーの隔離コピー、完了記録の検査だけ外した）

実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む。ここでは、より多くの経路を通すため、前回（10/8）の回と同じ投稿を
10/22 の回として置き、正典をそのまま累積候補にして **adapter の `build`（元HTMLから候補ページ・潮目・アリーナの点・立場の対応表を2回作って一致）→
`prepare_public_candidate_bundle`（公開JSON・finalize・SEO・授業節・他テーマの新デザイン・`henoko_layout.finish`）** を通した。**最後まで通った**。
- 候補の docs/ は新デザイン（最終更新日 2026-10-22、次の収集予定 11月5日）、元HTMLは旧形式（潮目は 10月8日 → 10月22日）、立場の対応表は立場の中身が同じで `made_on`・`public_updated_on` だけ 2026-10-22
- 公開対象（73ファイル）に元HTML・アリーナの点・立場の対応表が入る。他の新デザイン9ページ（部活動・皇室・副首都・生成AI・憲法・自転車・高齢者・あだ名・消費税）は変わらず
- 候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0、`build_henoko_arena.py --check` OK、
  `verify_builder_rebuildability.py` 10テーマ NG 0、`validate_theme_seo.py` OK、よみやす PASS（完成を止める指摘0）
- 新しい意見がある回（明細が足りない回）で止まることは、`tests/test_henoko_redesign.py` の `test_count_mismatch_stops_before_writing`（finish）と
  `test_adapter_rebuilds_stance_table_and_stops_without_reread`（adapter）で確かめた
- 模擬に使った隔離コピーは消した（作業ツリーには何も書いていない）
