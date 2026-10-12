# 憲法改正論議（constitutional-amendment）新デザインの公開候補と検査（手順7）

2026-10-12。ブランチ `task/renew-constitutional-amendment`。手順書23の「7. 更新と公開を検査する」。
生成AIと著作権の [2026-10-11-ai-copyright-production-candidate.md](2026-10-11-ai-copyright-production-candidate.md)（1〜9節の手順7、10節の対話式の山なみ、
11節の部活動型の圧縮）をそのまま踏襲した。山なみと圧縮は最初から組み込んでいるので、節を分けずに本文に含める。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/constitutional-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/constitutional-amendment-release/constitutional-amendment-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-04）
確認画面: `quality/prototypes/constitutional-amendment-release/evidence/`（PC・375px の全体、山なみ、立場モード切替、山を押して読書面へ、
理由を開いた画面、背景を開いた画面、前回の収集との比較を開いた画面、X遮断時、JSなし）

## 0. 手順7の前に直したこと（手順5・6の担当からの申し送り、設計記録 reading 8-6）

| 申し送り | 処理 |
|---|---|
| 1. 山なみ（`#planet-block` を論点タブの上に） | 済み（1・3節）。読書面の入口 `window.ConstitutionalReading.select(id)`、橋渡しは `planet.js` |
| 2. 推移（潮目のカードから小さな折れ線） | 済み。現行ページの推移は2回の比較（潮目、前回と今回の収集）なので、生成AIの「ひと目で見る推移」の型を2点の折れ線で作った（3節） |
| 3. よみやすの残り3件（`sns_note` 80字超） | `data/verification/constitutional-amendment-sunk-continents.json` の3文を区切った（「…あったが、いずれも…であり、…」→「…あった。いずれも…だった。…」）。数字・英数字の並びが前後で同じことをスクリプトで確かめた。`build_public_registry.py --topic constitutional-amendment`・`build_constitutional_arena.py` で公開JSON（data/public・docs/data）と現行ページの山なみを作り直した（差分は文の区切りだけ）。採用台帳の指紋も `build_adoption_registry.py` で合わせた。試作・候補のよみやす「完成を止める指摘 0件」 |
| 4. 冒頭の確認日（10-12）と背景台帳（09-13）のずれ | 背景台帳の `checked_on`・`source_scope_label` を 2026-10-12（一次資料メモ【2026-10-12追記】）に進め、年表の「9月13日時点では施行前」→「施行は公布から3か月後の10月31日です」、「直近の通常国会」→「前の第221回国会（特別会）」に直した。新デザインの年表は従来どおり設定の上書き文（臨時国会の召集を含む）を使う |
| 5. 10/31 の施行確認 | 手順を DATA_REFRESH.md に書いた（`law.enforcement_confirmed_on`）。施行は未来のことなので今回は未実施 |
| 6. 立場の対応表の作り直し | DATA_REFRESH.md に手順を追加（`constitutional_reread_stances.py --made-on`） |

既存データ由来のよみやす指摘は、上の3件以外は無かった（公開候補・切替後の docs とも「完成を止める指摘 0件」、info のみ）。
`verify_number_provenance.py constitutional-amendment` NG 0、`verify_ocean_layer.py` は憲法の指摘（sha256 の machine_hits・地下水脈1本・代表投稿 tweet_id 未設定）が
直す前と全く同じ（全体の終了コード1は既存。直す前後で出力が一致することを確かめた）。

## 1. 仕組み（生成AIと著作権と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_constitutional_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`constitutional_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/constitutional_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/constitutional-amendment.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_constitutional_arena.py` を単独で動かしたとき。元HTMLに公開JSONの集計・正典の山なみ・連動表示を掛けてから新デザインを組む） |
| `configs/constitutional-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/constitutional_redesign/planet.js`（新規） | 山なみの橋渡し（生成AIの planet.js と同じ。立場カード・論点ボタンの移動・viewBox・山→読書面・topic-modern.js の自動クリック止め） |
| `scripts/constitutional_redesign/production.css`（新規） | 引き継ぐ部品（共通ヘッダー・山なみ・前回の収集との比較・投票・作り方・詳細データ・次に見るテーマ）を条文の用紙・藍の配色に合わせる |
| `scripts/constitutional_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・立場の対応表・設定から数え直して照合（`constitutional_count_provenance.py` 経由で `verify_number_provenance.py` から呼ぶ）。見出しの立場の帯・立場別集計・理由区分・区分ごとの立場・主張・資料にしかない話（`sunk_issue_overrides` 込み）・共通する心配・条文の確認を論点の欄ごとに確かめる |

ページの並び：共通ヘッダー → 冒頭（決まり方の4段階・争点2つ・件数・よく聞かれること）→ 論点ごとに読む（見出し → **対話式の山なみ**（立場モード・山・論点ボタン・選択パネルと100マス・見かた・調査条件）→ 論点タブ → 選んだ論点の欄）→ 前回の収集との比較（要約＋折りたたみ）→ 投票 → 背景の開閉行8行 → 作り方と詳細データ（折りたたみ1つ）→ 次に見るテーマ → フッター。

時制：静的HTMLは公開JSONの更新日（`--as-of` で上書き）で国民投票法の改正の段階を決める（冒頭の流れ図の脚注・背景の国民投票法の行・年表・未確認の行）。
生成日に依存しないので、同じデータなら同じページになる。読む日による JavaScript の切り替えは入れていない（生成AIと同じ。8節）。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「憲法改正で何が変わる？9条・緊急事態条項をわかりやすく比較｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承（テストで一致確認） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 現行ページには無い（FAQ5問は画面だけ） | 冒頭「よく聞かれること」4問＋背景「よくある質問」4問＝8問から作り直し | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間 | release だけ複写 | 継承（`google-adsense-account` meta は現行ページに無い） |
| Webフォント | preconnect・Noto Sans/Serif JP | 同じ | 継承 |
| 共通CSS/JS | site-tokens・constitutional-search-entry・topic-modern・constitutional-connected（css/js/page.js）・theme-design・widgets.js | site-tokens・topic-modern（v=32、JS v=13）だけ | 検索入口・連動表示・テーマ共通の見た目・X一括読み込みは意図的に外した |
| 投票（Supabase） | topic `constitutional-amendment-issue-stance-v1`、論点6×立場4＝24、`choiceIdx:selected*stances.length+stanceIndex`、保存キー `sns_vote_constitutional_amendment_2step` | 投票節とスクリプトを複写。`issues`・`stances` の定義は元と完全一致。保存キーは本番ホストだけ既存キー、他は `sns_vote_preview_constitutional_amendment_2step` | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（24通り） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承 |
| 共通ヘッダー・パンくず | 元HTMLは静的ヘッダーが無い（topic-modern.js が後から差す。ヒーローの「トップ」リンクだけ） | 皇室・副首都と同じ静的な共通ヘッダー、冒頭のパンくず「政策・国会 ／ 憲法改正論議」 | JSなしでもトップへ戻れる |
| 前回の収集との比較（TIDE_CARD） | 9/26→10/4、立場・論点の2タブ、再生ボタン | `<section class="update-dashboard">…TIDE_CARD…</section>` と CSS 区間を文字どおり複写し、要約（2点の小さな折れ線・カードの見出しの1文）の下の折りたたみ `#cap-trend-more` へ | 継承。`#constitutional-tide-widget` で来たら折りたたみを開く。モデル差の注記は現行ページに無い（無いまま） |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、詳細データと一緒に折りたたみ `#cap-method` へ | 継承（公開日・最終更新日の `<time>` も残る） |
| 詳細データ | `#detail-data`（論点・立場・強さ・件数の出所） | 文字どおり複写 | 継承。旧12カテゴリのヒートマップ2表（main 直下の details）は詳細データの外にあり、新デザインには載せていない（7節） |
| 次に見るテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking`（GA4 `related_theme_click`） | 両方文字どおり複写 | 継承（生成AIは計測スクリプトを載せていなかった。憲法は内容対応表35で保護対象としたので載せた） |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間 | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| 読了カウンタ「読んだところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先だけ隠して置く） | 内容対応表2どおり |
| 検索入口（4つの切替・FAQ5問） | `#change-lens` | 載せない | 冒頭・背景に置き換え（内容対応表5・10） |
| 立場の帯「慎重・反対が7割近く」 | `#stance-glance` | 載せない | 冒頭の件数欄と論点の欄の帯（内容対応表11） |
| 編集部の整理（9/12時点） | `#editorial` | 載せない | 生成AIと同じ判断（内容対応表24） |
| 一次資料クイズ・予想2問 | `#quiz`・`#guesses` | 受け皿だけ隠して残す | 照合は論点の欄（内容対応表21） |
| 論点ごとのX投稿 | 12件 | 正典から選び直した13件（開いたときに読む） | 置き換え |
| llms.txt・sitemap | URL のみ | URL 不変 | 継承 |

### 旧アンカーの到達確認

`grep -rn "constitutional-amendment-reaction-map.html#" docs/ scripts/ configs/`（data・themes・quality・tests も）の結果は**0件**（サイト内からアンカー付きで指すリンクは無い）。
外部から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#top`・`#progress`・`#change-lens`（`-title`・`-tabs`） | 冒頭 `#ca-open` |
| `#constitutional-faq`・`#quick-faq-title` | 冒頭「よく聞かれること」`#ca-faq-title` |
| `#lens-tab-article9`・`#lens-panel-article9`・`#lens-tab-emergency`・`#lens-panel-emergency`・`#bukatsu-check`・`#ck-title` | 背景「9条と緊急事態条項は、何が論点になっているか」`#bg-issues-map`（開く） |
| `#lens-tab-referendum`・`#lens-panel-referendum` | 背景「国民投票法は、投票のやり方をどう決めているか」`#bg-referendum-law`（開く） |
| `#lens-tab-reasons`・`#lens-panel-reasons`・`#stance-glance`（`-title`・`-buttons`・`-result`）・`#fallback`・`#fallback-nav`・`#explainer-section`・`#editorial`・`#quiz`・`#ocean` | 読書面 `#constitutional-amendment-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#figure-{論点ID}`・`#constitutional-amendment-reading-{論点ID}` | その論点の欄 `#issue-{論点ID}`（選んだ状態になる） |
| `#bukatsu-background`・`#bg-title` | 背景 `#constitutional-amendment-background` |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |

`#issue-{論点ID}` は旧ページ（JSなし本文の前の目印）でも新ページ（読書面の欄）でも「その論点」。旧ページの目印 `span.issue-anchor` は山なみの写しから外した（同じidを2つ置かない。テストで重複id 0件を確認）。
そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`research-conditions`・`planet-block`・`planet-data`・`constitutional-tide-widget`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS の内部用ID（`ca-reason-count-…`・`ca-check-note-…`・`issue-count-…`・`explainer-modal`・`stance-glance-result-text` など、外から指す意味の無いもの）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_constitutional_redesign.py --mode release --output-dir quality/prototypes/constitutional-amendment-release
```
成功すると `Built 1 file (release, as_of 2026-10-04); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）: `--mode preview --output-dir /tmp/constitutional-preview`。

公開切替（9節で実施）: `configs/constitutional-layout.json` を `enabled: true`、`configs/theme-seo.json` に `display_headline`、
`python3 -c "import sys;sys.path.insert(0,'.');from pathlib import Path;from scripts import constitutional_layout as l;l.finish(Path('.'))"`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`（`<style>`・`#planet-block`）・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと `.fr-panels` のあいだ（論点タブの上）に置く。外すのは JSなし用の論点別本文（`section.landing-panel`）・`#ocean`・`#editorial`・`span.issue-anchor`。部品（`#modes`・`#section`・`#panel`・`#dotbox`・`#waffle`・`#fallback-nav`・`#list`・`#meta`・`#caution`・`#guesses`・`#quiz`・`#dive`）が1つずつ無ければ止まる。選択パネルの「この論点の図解とX投稿を見る →」（旧ページの図解への案内）と、中身を隠した理由一覧の見出しは CSS で出さない。
- **前回の収集との比較**：潮目のカードの `const datasets`（立場・論点の前回・今回の割合）と比べた日付だけを読み、要約に4立場の2点の折れ線、読書面の各論点に2点の折れ線と「9月26日 48.7% → 10月4日 31.9%」の形の数字を入れる（件数は描かない）。「その他」は潮目に無いので数字は出ない。比べた日が公開JSONの更新日より後なら止まる。読書面の「前回との比較を開く ↓」は折りたたみを開き「論点の変化」に切り替える。
- **圧縮**：読書面は手順5・6で最初から部活動型（上位4件・選んだ理由1つ・折りたたみ）。手順7で「前回の収集と比べると」（折れ線・数字・累計の表の折りたたみ）を論点の欄に足し、作り方と詳細データを1つの折りたたみにした。

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理（adapter・finalize・SEO・信頼情報・授業節・
  テーマ共通の見た目・皇室／副首都／生成AIの finish）→ 最後に `constitutional_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/constitutional.py` は `source_for_refresh` を入力にする。山なみ（finalize の `--public-counts-only`）・潮目（`_apply_tide`）・連動表示も元HTMLから作った候補に掛かる。
  潮目の汎用JS・CSSの原型（`inject_tide_widget._load_generic_js/_load_tide_css`）も元HTMLから読むようにした。
- 新デザインの照合（再読データの明細＝論点の件数、立場の対応表＝明細、明細の立場＝公開JSON、`sns_base`＝意見数など）が合わないと `finish` は ValueError で
  止まり、元HTMLも公開ページも書き換えない（テストで確認）。施行日（10/31）を過ぎても止まらない（テストで確認）。
- **次回 10/13 の模擬**（切替後の作業ツリーのスクラッチ複製で、新規0件の 10/13 回として `refresh_adapters/constitutional.build` → `refresh_topic.prepare_public_candidate_bundle`。
  完了記録の検査だけ外した。潮目の比較用に 10/04 回の classified.json・report.json を 10/13 回として置いた）：公開対象67件。候補の docs/ は新デザイン（基準日 2026-10-13、
  比較は「10月4日 → 10月13日」）、元HTMLは旧形式で潮目のカードも新しい日付。候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0
  （憲法 615/615）、`verify_builder_rebuildability.py` NG 0、よみやす「完成を止める指摘 0件」、使い回し0、皇室・副首都・生成AI・部活動の公開ページは変わらず。
  候補の `DATA_SHEET.md` に「副首都・部活動のマップの点がずれ」と出るが、これは隔離コピーで両テーマの元HTMLを戻した状態で数えるためで、憲法の変更とは関係しない（作業ツリーでは「ずれなし」）。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/constitutional-amendment.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分 | `data/constitutional-amendment_issues-reread.json`（7論点・全1,963件） | **新しい収集回の意見を追い読みして追記**（明細が論点の件数と合わないと生成が止まる） |
| 区分ごとの立場・投稿の立場 | `data/constitutional-amendment_reread-stances.json`（正典から `constitutional_reread_stances.py`） | **追い読み・判定し直しのたびに作り直す** |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前 | `configs/constitutional-amendment-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`（`build_constitutional_process_sections.py`）・`data/verification/constitutional-amendment-claims.json` | 主張を足すとき |
| 資料にしかない話・共通する心配 | `data/verification/constitutional-amendment-sunk-continents.json`・`-veins.json` → 公開JSON `ocean_layer` | 再検索の記録を追記（`sns_base` が意見数と違うと止まる。1文80字以内） |
| 条文の確認・確認日 | 一次資料メモ `quality/research/constitutional-amendment-primary-sources.md` の見出しと「確認日」 | 一次資料の再確認時 |
| 制度の確認（論点内）・背景の年表・なぜ議論されてきたか | `data/verification/constitutional-amendment-background.json`・`configs/constitutional-amendment-background.json` | 一次資料の再確認時（台帳の `checked_on` も） |
| 冒頭（決まり方・争点・短答・よく聞かれること）・確認日・施行の段階 | `configs/constitutional-amendment-opening.json`（`checked_on`・`law`） | 制度を確かめ直したら `checked_on`、施行後の条文を確かめたら `law.enforcement_confirmed_on` |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION（`build_constitutional_arena.py` の `apply_planet_counts`） | 自動 |
| 前回の収集との比較 | 元HTMLの TIDE_CARD（adapter の `_apply_tide`、前回の更新回と今回の更新回） | 自動 |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データ・次に見るテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件に憲法／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成で生成AIの後に `finish` | 生成AIの分岐と並べた最小の追加 |
| `scripts/refresh_adapters/constitutional.py` | 入力を `source_for_refresh(root)` に | 公開後も元HTMLから生成し、潮目・連動表示も元HTMLに掛けるため |
| `scripts/build_constitutional_arena.py` | 公開ページが新デザインで、入出力の指定が無いとき `constitutional_layout.rebuild`（`--check`・`--public-counts-only` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/inject_tide_widget.py` | 潮目の汎用JS・CSSの原型を `source_for_refresh` の元HTMLから読む／コメント | 原型が憲法のページにあるため（他テーマの潮目にも使われる） |
| `scripts/refresh_planet_section.py` | 憲法の新デザインも停止 | 皇室・副首都・生成AIと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 憲法の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐（副首都・生成AIと同じ `.fr-reason-n b`・`.fr-count b`）を憲法にも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/constitutional_count_provenance.py` | 新デザインなら `constitutional_redesign_provenance` を呼ぶ | 数字の出所検査 |
| `scripts/constitutional_reading.py` | 論点の欄の「収集ごとの割合と件数」を「前回の収集と比べると」（折れ線の受け皿・比較への案内・累計の表の折りたたみ）に | 推移の型 |
| `scripts/constitutional_redesign/reading.js` | `#fr-r-{論点ID}-{区分}` の区分IDにハイフンがあると理由が開かなかったのを直した（論点IDの前方一致で分ける） | 手順5・6からの不具合（全区分がハイフン入り） |
| 切替時の共有テスト | 9-3 | 公開後は旧形式の検査を元HTMLに向けるため |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に憲法の `finish` が走る。憲法の照合が合わないと、その回の
**公開候補生成全体が止まる**（皇室・副首都・生成AIと同じ設計）。憲法は全意見を追い読みしているが、新しい収集回の意見を同じ回に追い読みし、
立場の対応表を作り直さないと止まる。`inject_tide_widget.py` の原型の読み先が変わったが、`enabled: false` のときは従来どおり docs のページ。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付・潮目の日付） | 合格 | 合格 |
| `verify_theme_page.py constitutional-amendment`（候補は `--html`） | NG 0（OK 33） | NG 0（OK 33）、全10テーマ NG 0 |
| `verify_number_provenance.py` | 10テーマ NG 0（現行ページ 226/226） | 憲法 615/615・終了0（折りたたみの中の件数も読む）、10テーマ NG 0 |
| `verify_top_page.py` | 終了0 | 終了0 |
| `build_constitutional_arena.py --check` | OK | 「OK: 差分なし」（公開後の経路＝元HTMLと新ページを作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 憲法の指摘は直す前と同じ（既存。終了1） | 同じ |
| `python3 -m unittest discover tests` | 1,927件 OK（skip 4） | 1,927件 OK（skip 4。共有テストを直す前は失敗6・エラー4） |
| `run_public_checks.py` | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） | 終了0（同じ） |
| `tests/test_constitutional_redesign.py` | 61件 OK（手順7分25件：保護対象・重複id 0・投票定義・FAQ・潮目の継承と折りたたみ・論点ごとの折れ線・作り方の折りたたみ・初期状態・授業節・旧アンカー・山なみの写しと追随・旧部品なし・出所検査の改ざん検知2種・時制、レイアウト6件：無効時・状態の一貫・元HTML無し・往復・照合不一致で書かない・施行日後も止まらない） | 同じ |
| 2回生成 | md5 一致（`300aff1b…`、`PYTHONHASHSEED` 0・1・999・指定なし） | docs のページとも一致 |
| `--as-of 2026-11-01` | 止まらず、冒頭・背景が `after_unconfirmed`（「施行される予定でした。施行後の条文は編集部で確かめていません」） | 同じ |
| よみやす（`--strict`） | 候補 78/100・完成を止める指摘 0件・PASS | docs 同じ |
| 使い回し（`verify_page_originality.py`） | 最初は生成AI・副首都と同じ文が41件（理由の数え方・資料の検索件数・背景の案内と日付の文。論点ごとに数が違うだけの同じ文）→ 設定の5文を書き直して 0件 | 「10ページに、使い回された見出し・文はありません」 |
| AI臭（`verify_ai_tone.py`） | 問題なし | 問題なし |
| `seo/validate_theme_seo.py` | — | OK（themes=10） |

操作（Playwright、`tests/test_constitutional_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しに候補を置いて 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（scrollWidth＝画面幅。読書面の折りたたみ全開・背景8行・比較・詳細データを開いても0）、ページのコンソールエラー0。
- 山なみ：立場モード（3つ目）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`。
- 論点タブ7つで scrollY 不変、論点の切替で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「別の理由」で次へ。
- 前回の収集との比較：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「前回との比較を開く」で折りたたみが開き論点の変化になる。
- 旧アンカー：`#fb-…`・`#constitutional-amendment-reading-…` は論点、`#lens-panel-referendum`・`#bukatsu-check` は背景の行を開く、`#change-lens` は冒頭、`#stance-glance` は読書面、`#fr-r-…-em-control` で理由が開く、`#constitutional-tide-widget`・`#detail-data` は折りたたみを開いて表示。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン6つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：7論点すべて表示、図が使えないときの論点一覧・比較の要約・作り方・詳細データ・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 15,444px | **12,602px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数 | 5,824字 | 4,659字 | — |
| 山なみ（`#planet-block`、選択パネル込み） | 3,592px | 2,283px | — |
| 1280px のページ全体 | 10,134px | 7,535px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 改憲全般 | 2,453px | 796字 | 1,365px |
| 9条・自衛隊 | 2,562px | 870字 | 1,417px |
| 緊急事態条項 | 2,665px | 872字 | 1,393px |
| 国民投票・広告 | 2,718px | 933字 | 1,361px |
| 政党・発議手続き | 2,689px | 947字 | 1,389px |
| 情報・議論の質 | 2,051px | 691字 | 1,337px |
| その他 | 1,978px | 705字 | 1,341px |

論点の欄の目標（2,500px以下）は7論点中3論点で満たし、4論点（9条・緊急事態・国民投票・政党）が 62〜218px 超える。手順6の時点（2,248〜2,481px）より、
「前回の収集と比べると」（折れ線・数字・比較への案内・累計の表）を足した分（約200px）だけ伸びた。折れ線を横に並べ、案内を見出しの行へ寄せて 270px→200px に詰めた。
これ以上は内容を折りたたむか外す判断になるので、オーナーの判断に回す（7節）。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. 論点の欄が4論点で 2,500px を超える（6節）。私なら「前回の収集と比べると」を論点の欄から外し、ページ下の「前回の収集との比較」に任せる（各欄で約210px減る。計算上は国民投票・広告が 2,504px で僅かに超え、残り6論点は目標内。外した状態は未計測）。
3. 旧12カテゴリのヒートマップ2表（「カテゴリ×検索クエリ」「カテゴリ×スタンス」）は元HTMLの詳細データの外にあり、新デザインには載せていない（論点7体系と別の集計。内容対応表33の判断）。元HTMLには残る。
4. 論点の欄の「前回の収集と比べると」は2回の収集の比較（潮目）で、生成AIのような全収集回の推移ではない（現行ページに全回の推移が無いため）。
5. 内容対応表の「読了カウンタ」「編集部整理」は載せない判断のまま。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。13件の投稿が今も閲覧できるかは手順6で 10/12 に確認済み、表示そのものは未確認）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。
- 10/13 の模擬は新規0件の回。新規の意見があり、追い読みと立場の対応表の作り直しを同じ回に済ませない場合は、設計どおり止まる（実データでは未確認）。
- 静的な時制：10/31 をまたいで次の更新が無いと、施行後も「施行される予定です」の文が残る（副首都のような読む日による切り替えは入れていない）。

## 9. 2026-10-12 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/constitutional-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | constitutional-amendment に `display_headline`「憲法改正はどう決まり、何が争点か」（H1 が変わるため。生成AIと同じ） |
| `data/page-sources/constitutional-amendment.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致） |
| `docs/constitutional-amendment-reaction-map.html` | 新デザイン（`constitutional_layout.finish`。公開候補とバイト一致） |
| `DATA_REFRESH.md` | 「憲法改正論議の定期更新（新デザインを維持する、2026-10-12〜）」の節（申し送りの立場の対応表の節を吸収） |
| `company/APPROVALS.yaml` | `approval-20261012-constitutional-amendment`（`status: pending`、`decided_at: null`） |
| 共有テスト | 9-3 |

### 9-2. 切替後の検査（作業ツリー）

6節の「切替後」の列。全テスト・公開検査は 9-3 の共有テストを直したあとの結果。

### 9-3. 切替に合わせて直した共有テスト

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_constitutional_connected.py`・`_planet_refresh.py`・`_public_counts.py`・`_search_entry.py` | 読むページを「公開後は元HTML（`source_for_refresh`）」に | 旧形式の連動表示・山なみの再生成・公開集計・検索入口の検査。公開後も元HTMLに同じ構造で残る（生成AIと同じ扱い） |
| `tests/test_cite_button.py` | 憲法の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 憲法の新デザインを飛ばす | 共通の見た目を掛けない設計 |

直す前は失敗6・エラー4。直したあと `python3 -m unittest discover tests` 1,927件 OK（skip 4）、`run_public_checks.py` 終了0、`verify_builder_rebuildability.py` 10テーマ NG 0。
切替後の docs/ を 127.0.0.1 で配信して Playwright の検査をもう一度通した（全項目合格。docs のページは公開候補とバイト一致なので、確認画面は `evidence/` のものを使う）。
