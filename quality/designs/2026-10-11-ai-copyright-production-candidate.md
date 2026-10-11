# 生成AIと著作権（ai-copyright）新デザインの公開候補と検査（手順7）

2026-10-11。ブランチ `task/renew-ai-copyright`。手順書23の「7. 更新と公開を検査する」。副首都の
[2026-10-11-fukushuto-production-candidate.md](2026-10-11-fukushuto-production-candidate.md)（皇室典範改正と同じ型）をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 手順7の公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/ai-copyright-layout.json` を `enabled: true` にして docs/ に適用した。

公開候補: `quality/prototypes/ai-copyright-release/ai-copyright-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-06）
確認画面: `quality/prototypes/ai-copyright-release/evidence/`（PC・375px・論点選択・背景を開いた画面・意見の推移・X遮断時・JSなし）

## 0. 手順7の前に直したこと（手順5・6の担当からの申し送り）

| 申し送り | 直したこと | 確かめ方 |
|---|---|---|
| 読書面の生成が非公開の正典（`social-samples/`）に依存 | 再読データ `data/ai-copyright_issues-reread.json` の明細の立場（`stance`）を、2026-10-07 の判定し直し後の正典の立場に**11件**合わせた（学習データ6・クリエイター1・AI生成物3・技術競争1。理由区分と要約は変えていない）。直した投稿IDと前後の立場は同じファイルの `stance_resync_2026_10_11` に記録。**共通台帳 `data/verification/reread/ai-copyright.json` はこのテーマには無い**（`configs/planet/ai-copyright.yaml` の `reread_registry: false`）ため `manage_reread_registry.py resync-source` は対象外。代わりに、明細の各投稿が正典でも同じ論点の意見であることを確かめてから立場だけを写した。`data/verification/ai-copyright-issues-reread.json`（皇室にある明細の写し）は副首都と同じく作っていない（数字の出所検査は再読データを直接数え直すため、読む所が無い）。`build_public_registry.py --topic ai-copyright` を再実行し、公開JSONの差分が無いことを確かめた | `scripts/ai_copyright_reading.py` から正典の読み込み（`load_canon`・`canonical_json`）を外し、区分ごとの立場と代表投稿の立場を明細から数える形（副首都と同じ）にした。明細の立場の合計が公開JSONの論点×立場と違うと止まる。直す前後で試作の HTML がバイト単位で同じ。正典を退けた環境でもテスト34件が通る（代表投稿の選定基準を正典で確かめる1件だけスキップ） |
| 授業の設定の「違法になるとは限らない」 | `configs/classroom/ai-copyright.json` 推進側の理由1：「学習という行為自体が直ちに違法になるとは限らない」→「学習という行為自体が直ちに許されないとは限らない」 | 旧ページの授業節も `apply_classroom_section.py` で同じ文に。テストを「背景の行（授業も含む）に違法・合法を使わない」に強めた |
| 既存データ由来のよみやす指摘19件 | 数字・出典・判定を変えずに文を区切った。資料にしかない話（`ai-copyright-sunk-continents.json`）7文で8件、共通する心配（`ai-copyright-veins.json`）2文で6件（2論点に同じ文が出る）、主張照合（`build_ai_copyright_process_sections.py` の tech_innovation_over_regulation の note）1文で2件、背景台帳（`ai-copyright-background.json` の gakushu・kaiji の found）2文で3件 | 直す前のファイルと、数字の並び・英数字の語（robots.txt・C2PA など）の並びが完全に同じことをスクリプトで確かめた。`git diff` で、変わったのが句読点・接続の言葉（「ただし」「しかし」「出発点は」）・語順だけであることを目視。`verify_number_provenance.py ai-copyright` 445/445（数字の出所検査は文中の件数を「記録の文と画面の文が完全一致のときだけ」認めるので、件数を変えていれば NG になる）、`verify_ocean_layer.py` で生成AIの指摘なし、試作のよみやす「完成を止める指摘 0件」 |

## 1. 仕組み（副首都 `fukushuto_layout.py` と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_ai_copyright_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`ai_copyright_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力は拒否。新デザインのページを入力に渡すと拒否 |
| `scripts/ai_copyright_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/ai-copyright.html`）/ `materialize`（隔離コピーで元HTMLを docs/ に戻す）/ `finish`（全生成の最後に元HTMLを保存し、新デザインを docs/ に書く）/ `rebuild`（公開後に `build_ai_copyright_arena.py` を単独で動かしたとき用。元HTMLに公開JSONの集計と旧形式の生成を掛け、公開ページとアリーナデータも作り直す） |
| `configs/ai-copyright-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/ai_copyright_redesign/production.css`（新規） | 意見の推移・投票・作り方・詳細データ・次に読むテーマを、紙色の地・藍の配色に合わせる追加分（冒頭・読書面の CSS は変えない） |
| `scripts/ai_copyright_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・設定から数え直して照合（`ai_copyright_count_provenance.py` 経由で `verify_number_provenance.py` から呼ぶ）。副首都の照合に「立場が違っても共通する心配」の読んだ投稿の数を足した |

時制：静的HTMLは公開JSONの更新日（`--as-of` で上書き）で届出の段階を決める。冒頭には段階の表示が無いので、副首都のような
読む日による JavaScript の切り替えは入れていない（背景の段階は次の更新で切り替わる。背景の末尾に「届出の段階は◯月◯日時点で
表示しています」と出る）。生成日に依存しないので、同じデータなら同じページになる。

## 2. 保護対象の一覧と継承結果

棚卸し記録（`2026-10-11-ai-copyright-renewal-inventory.md`）と内容対応表で「手順7」とした部品。

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「生成AIと著作権は何が問題？規制賛成・反対の論点｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 区間を文字どおり複写 | 継承（テストで一致確認） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 現行ページには無い（検索入口の問いは画面だけ） | 背景「よくある質問（4問）」から作り直し | 画面と構造化データの一致をテストで確認。検索入口の問いは使わない |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ文字どおり複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間 | release だけ複写 | 継承。`google-adsense-account` meta は現行ページに無いので、新ページにも無い（あれば複写する作り） |
| Webフォント | preconnect・Noto Sans/Serif JP | 同じ | 継承 |
| 共通CSS/JS | site-tokens・topic-modern・ai-copyright-connected・theme-design・connected.js・connected-page.js・arena-data.js・widgets.js | site-tokens・topic-modern（v=3/32、JS v=13）だけ | 連動表示・テーマ共通の見た目・検索入口・アリーナ・X一括読み込みは意図的に外した（独自の見た目。Xは開いたときに読む） |
| 投票（Supabase） | topic `ai-copyright-issue-stance-v1`、論点7×立場3＝21、`V2I=[0,2,4,1,3,5,6]`、`choiceIdx:selIssue*STANCES.length+stanceIdx`、保存キー `sns_vote_ai_copyright_2step` | 投票節とスクリプトを複写。VOTE_ISSUES・V2I・STANCES は元と完全一致。保存キーは本番ホストだけ既存キー、他は `sns_vote_preview_ai_copyright_2step` | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（21通り）。VOTE_ISSUES の説明文に「合法性」の語が残るが、投票定義は変えない約束なので触っていない |
| 投票の参加者数・やり直し・シェア | 投票スクリプト | 同じ | 継承（アリーナのマーカー `setArenaVoteMarker` は描く先が無いので呼ばれない。関数の有無を確かめてから呼ぶ元のコードのまま） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの注記の下に #caution（RESEARCH_CONDITIONS で囲む）、末尾に PLANET_DATA | 継承（公開検査が読む契約） |
| 共通ヘッダー・パンくず | 静的ヘッダー（ロゴ画像 `images/brand/mark.svg`）、`トップ＞テック・著作権` | 静的ヘッダーを文字どおり複写、冒頭の crumb | 継承（JSなしでもトップへ戻れる） |
| 意見の推移（TREND_CARD） | 立場・論点の9回分、画像4枚 `images/trend/ai-copyright-{stance,issue}-trend-{summary,detail}.png`、説明・埋め込みコード・Xで投稿 | `<section class="update-dashboard">…</section>` と CSS 区間を文字どおり複写。読書面の後・投票の前 | 継承。埋め込みコードが外部から指す `#ai-copyright-trend-panel-stance`・`-issue` も残る。読書面の「収集ごとの割合と件数」の注記を「この推移の節で見られる」に直した |
| アリーナデータ `docs/ai-copyright-arena-data.js` | ページが読み込む | 新デザインは読まない | adapter が引き続き作り、公開物に含める（10/16 の模擬で確認）。単独の作り直し（`rebuild`）でも更新する |
| 作り方（ARTICLE_TRUST） | 区間 | 背景の後に区間を文字どおり複写 | 継承（公開日・最終更新日の `<time>` も残る）。観察の文「AIの学習が合法かどうか」を「著作権法上認められるかどうか」に直した（`configs/theme-seo.json`。冒頭設計の免責方針） |
| 詳細データ | `#detail-data` | 文字どおり複写（枠の class だけ足す） | 継承（「カテゴリ×検索クエリ」「カテゴリ×スタンス」は旧2D分類の表で合計475件。7節） |
| 次に読むテーマ | `#related-topics` | 文字どおり複写 | 継承 |
| フッター（運営者情報・訂正窓口・プライバシー・免責） | footer | 文字どおり複写 | 継承 |
| 授業節（印刷ボタン・GA4計測） | CLASSROOM 区間 | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| 進捗表示「探ったところ 0／21」 | `#progress` | 載せない | 継承しない（内容対応表どおり） |
| 編集部の横断整理 | `#editorial`（9/14時点の手入力の％） | 載せない | 継承しない（文中の数字が9/14時点のまま。旧アンカーは読書面へ） |
| 立場の内訳（全体の帯「規制派は推進派の2.5倍」） | `#stance-glance` | 載せない | 継承しない（「2.5倍」は手入力の重複。立場は論点ごとの欄に出る。旧アンカーは読書面へ） |
| 検索入口（3論点×7問、確認日9/28） | `#aic-search-entry` | 載せない | 冒頭の2問・背景の FAQ・条文の行に置き換え（内容対応表4） |
| 論点ごとのX投稿14件 | `#issue-cards` | 正典から選び直した14件を論点の欄に（開いたときに読む） | 置き換え |
| 判断の入口（3場面） | `#copyright-entry` | 背景「文化庁の『考え方』」と FAQ に吸収 | 置き換え（旧アンカーは背景の行を開く） |
| noscript 本文 | noscript なし | JSなしで7論点・背景・推移・作り方・詳細データがすべて読める | 確認済み |
| llms.txt・sitemap | URL のみ参照 | URL 不変 | 継承 |

### 旧アンカーの到達確認

`grep -rn "ai-copyright-reaction-map.html#" docs/ scripts/ configs/`（data・tests・themes・quality/research も）の飛び先は
**`#ai-copyright-trend-panel-stance`（2件）・`#ai-copyright-trend-panel-issue`（2件）の4件だけ**で、どれも推移の節の埋め込みコードの中。
推移の節を文字どおり継承したので、新ページでも同じIDで到達できる（Playwright で `#ai-copyright-trend-panel-issue` から開くと「論点の変化」が表示されることを確認）。

外部から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#top`・`#progress`・`#aic-search-entry`・`#aic-search-heading`・`#aic-search-panel`・`#aic-search-answer` | 冒頭 `#ai-copyright-opening` |
| `#stance-glance`・`#stance-glance-title`・`#planet-block`・`#fallback`・`#fallback-nav`・`#issue-cards`・`#editorial`・`#quiz`・`#ocean`・`#ai-copyright-audit` | 読書面 `#ai-copyright-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#ai-copyright-reading-{論点ID}` | その論点の欄 `#issue-{論点ID}`（選んだ状態になる） |
| `#bukatsu-background`・`#bg-title` | 背景 `#ai-copyright-background` |
| `#bukatsu-check`・`#ck-title` | 背景「法律・解釈・任意のルールの違い」`#bg-rules`（開く） |
| `#copyright-entry`・`#copyright-entry-title` | 背景「文化庁の『考え方』」`#bg-kangaekata`（開く） |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |

**`#issue-ai-copyright-*` は旧ページでも新ページでも「その論点の欄」**（旧：論点ごとのX投稿の見出し、新：投稿を含む読書面）で、
同じ意味のまま残る（7論点とも。テストで旧ページにも新ページにもあることを確認）。そのまま残るID：`vote-section`・`detail-data`・
`related-topics`・`article-trust-title`・`caution`・`planet-data`・`ai-copyright-trend` と推移の節の各ID。
**到達できなくなった旧アンカーは無い**（読み替え先が無いのは、JSの内部用ID〔`vote-step1`・`pbar`・`aic-reason-count-…` など、
外から指す意味の無いもの〕だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される）。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_ai_copyright_redesign.py --mode release --output-dir quality/prototypes/ai-copyright-release
```
成功すると `Built 1 file (release, as_of 2026-10-06); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）:
```sh
python3 scripts/build_ai_copyright_redesign.py --mode preview --output-dir /tmp/ai-copyright-preview
```

公開切替（9節で実施）:
1. `configs/ai-copyright-layout.json` を `enabled: true` にする。
2. 同じコミットで `configs/theme-seo.json` の ai-copyright に `display_headline` を足す（H1 が変わるため）。
3. `python3 -c "import sys;sys.path.insert(0,'.');from pathlib import Path;from scripts import ai_copyright_layout as l;l.finish(Path('.'))"`
   で元HTMLを `data/page-sources/` に保存し、docs/ のページを新デザインにする。

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理（adapter・意見の推移・finalize・SEO・
  信頼情報・授業節・テーマ共通の見た目・皇室と副首都の finish）→ 最後に `ai_copyright_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/ai_copyright.py` は `source_for_refresh` を入力にする。連動表示（`ai_copyright_connected.apply`）と意見の推移の貼り直し
  （`trend_support.render_trend`）も元HTMLから作った候補に掛かり、推移の画像4枚（`trend_support.build_images`）とアリーナデータも同じ累積候補から作る。
- 新デザインの照合（再読データの明細＝論点の件数、明細の立場＝公開JSON、`sns_base`＝意見数など）が合わないと `finish` は ValueError で
  止まり、元HTMLも公開ページも書き換えない（テストで確認）。届出開始日を過ぎても止まらない（テストで確認）。
- 推移の節の「◯月◯日時点」は保存した収集回の最新日で、新規0件の回は公開JSONの更新日より前のまま残る。一致までは求めず、更新日より
  後の日付のときだけ止める（最初は一致を求めたが、10/16 の模擬で止まったため直した）。
- **次回 10/16 の模擬**：切替後のスクラッチ複製で、新規0件の 10/16 回として `refresh_adapters/ai_copyright.build` →
  `refresh_topic.prepare_public_candidate_bundle` を実行した（完了記録の検査だけ外した。保存回の report は 10/06 の分を代用）。
  公開対象71件が作られ、候補の docs/ は新デザイン（基準日 2026-10-16・届出は「開始前」）、元HTMLには推移の節が入ったまま。
  候補の中で `verify_theme_page.py` 全テーマ NG 0、`verify_number_provenance.py ai-copyright` 609/609、よみやす「完成を止める指摘 0件」、
  皇室・副首都の公開ページは変わらず。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/ai-copyright.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの立場 | `data/ai-copyright_issues-reread.json`（5論点） | **新しい収集回の意見を再読して追記**（件数が論点の件数と合わないと生成が止まる）。判定し直しで正典の立場が変わったら明細の `stance` も合わせる |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件の選定 | `configs/ai-copyright-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | `build_ai_copyright_process_sections.py` の FACT_CHECKS → 公開JSON `claim_verification`（投稿数は `data/verification/ai-copyright-claims.json` から数え直し） | 主張を足すとき |
| 資料にしかない話・共通する心配 | `data/verification/ai-copyright-sunk-continents.json`・`ai-copyright-veins.json` → 公開JSON `ocean_layer` | 再検索の記録を追記（`sns_base` が意見数と違うと止まる） |
| 制度の確認（論点内）・背景の年表 | `data/verification/ai-copyright-background.json`、一次資料メモ | 一次資料の再確認時 |
| 冒頭の2問・件数のものさし・確認日・届出の日付 | `configs/ai-copyright-opening.json` | 制度を確かめ直したら `checked_on`、届出開始を確かめたら `principle_code.filing_confirmed_on` |
| 背景の行・FAQ・授業 | `configs/ai-copyright-background.json`、`configs/classroom/ai-copyright.json` | 段階の文を直すとき |
| 意見の推移（画像4枚と説明） | 元HTML の TREND_CARD（`trend_support.render_trend`）、画像は adapter の `trend_support.build_images` | 自動（分類AIが変わった回は `TREND_THEMES` の `model_breaks`） |
| 公開日・次回更新予定・収集元 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・JSON-LD（Article）・GA・AdSense・投票・作り方・詳細データ・次に読む | 元HTML（`data/page-sources/`、公開前は docs/） | 変更しない（継承するだけ。数字は元HTML側の生成器で直る） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の新デザイン停止条件に生成AI／`_copy_candidate_tree` で生成AIの `materialize`／単一・複数の公開候補生成で、副首都の後に生成AIの `finish` | 副首都の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/ai_copyright.py` | 入力を `source_for_refresh(root)` に | 公開後も元HTMLから生成し、連動表示・推移も元HTMLに掛けるため |
| `scripts/build_ai_copyright_arena.py` | 公開ページが新デザインで、入出力の指定が無いとき `ai_copyright_layout.rebuild`（`--check`・`--public-counts-only`・`--skip-issue-counts` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/refresh_planet_section.py` | 生成AIの新デザインも停止 | 皇室・副首都と同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped と表示） | 単独実行で授業節・作り方を旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/inject_tide_widget.py` | コメントだけ（`-layout` の meta を持つページを飛ばす処理は既に全テーマ共通） | — |
| `scripts/verify_builder_rebuildability.py` | 生成AIの `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐（副首都と同じ `.fr-reason-n b`・`.fr-count b`）を生成AIにも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/ai_copyright_count_provenance.py` | 新デザインなら `ai_copyright_redesign_provenance` を呼ぶ（推移の節の照合 `private_verified_selectors` はそのまま両方に効く） | 数字の出所検査 |
| `scripts/ai_copyright_reading.py` | 正典を読まない（0節）／論点欄の順位の文「7つの論点で」→「7つの分類で」 | 公開入力だけで生成するため／1ページの論点数の表記を「その他を除く6」に統一（副首都と同じ。`verify_theme_page.py` の論点数検査） |
| 切替時（9節）の共有テスト | 9-4 を参照 | 公開後は旧形式の検査を元HTMLに向けるため |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に生成AIの `finish` が走る。生成AIの照合
（再読データの件数・明細の立場・`sns_base` 等）が合わないと、その回の**公開候補生成全体が止まる**（皇室・副首都と同じ設計）。
生成AIは5論点の再読を毎回の収集で追う必要がある（旧ページは「まだ読み直していない分」を残せたが、新デザインは残せない）。

## 6. 検査結果（公開前＝作業ツリー、enabled=false）

| 検査 | 結果 |
|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付） | 合格 |
| `verify_theme_page.py`（候補は `--html`） | 候補 NG 0、全10テーマ NG 0 |
| `verify_number_provenance.py` | 10テーマ NG 0（現行ページ 445/445。新ページは切替後 609/609） |
| `verify_top_page.py` | 終了0 |
| `build_ai_copyright_arena.py --check` | OK |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 生成AIは指摘なし（全体の終了コードは school-nickname-ban・koshitsu-tenpakai の既存の指摘で1。変更前の HEAD でも同じ） |
| 全テスト `python3 -m unittest discover -s tests` | 1,831件 OK（skip 4、失敗0・エラー0）。0節を直した直後は1,811件 OK |
| `run_public_checks.py` | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） |
| `tests/test_ai_copyright_redesign.py` | 54件合格（手順7分20件：保護対象・投票定義・FAQ・推移の継承・docs出力拒否・新デザイン再入力拒否・materialize/finish の往復・2回生成の一致・照合不一致で書かない・届出開始後も止まらない・数字の照合の改ざん検知・旧アンカーの読み替え先 ほか） |
| 2回生成 | md5 一致（`PYTHONHASHSEED` を 0・1・999・指定なしで4回とも同じ） |
| `--as-of 2026-10-27` | 生成は止まらず、背景が「開始後・未確認」（`data-filing-phase="after_unconfirmed"`、年表「始まったかどうかは、まだ確かめていません」）に切り替わる |
| よみやす（試作・候補） | 「完成を止める指摘 0件」判定 PASS |

操作（Playwright、`tests/test_ai_copyright_redesign_browser.cjs`、x.com・platform.twitter.com・twimg を遮断、docs/ の写しに候補を置いて 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0、コンソールエラー0。論点7つと山を押しても scrollY 不変。背景7行の開閉、推移の「論点の変化」タブ、詳細データを開いても横はみ出し0。
- 戻る：論点を7回切り替えても history.length 不変、「戻る」で前のページ（index.html）へ。
- 旧アンカー：`#fb-ai-copyright-creator-rights`・`#ai-copyright-reading-ai-copyright-tech-promotion` は論点、`#copyright-entry`・`#bukatsu-check` は背景の行を開く、`#bukatsu-background` は背景、`#aic-search-entry` は冒頭、`#stance-glance` は読書面、`#ai-copyright-trend-panel-issue`（別ページから）で推移の「論点の変化」が開く。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン7つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：7論点すべて表示、推移・作り方・詳細データ・背景も読める。
- 投票ボタンは押していない（POST していない）。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. 「詳細データ」の「カテゴリ×検索クエリ」「カテゴリ×スタンス」は旧2D分類の表（合計475件）で、現行の3,353件と別の集計。
   元HTMLの生成器が書く表なので今回は継承のまま残した（私なら、次の更新までに新デザインでは2表を外す）。
3. 再読データの無い2論点（利用者モラル・倫理 818件、法制度・規制整備 643件）は「理由ごとに読み分けた結果をまだ載せていません」表示のまま。
4. 編集部の横断整理・進捗表示・全体の立場の帯は外した。
5. `data/ai-copyright_issues-reread.json` の `scope`・`population`・`method` の文が古い（表示には使っていない）。
6. 単独の `apply_theme_trust.py` は部活動の新デザインのページで止まる（`bukatsu-chiiki: missing SEO metadata block`。今回の変更前からの既存の挙動で、更新経路では部活動は元HTMLに戻してから掛かるので影響しない）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。14件の投稿が今も閲覧できるかは未確認）。
- 印刷ボタンの実際の印刷結果。
- 推移の節の画像（ダウンロード用の4枚）と次に読むテーマの画像は、全画面撮影で空白に写った（遅延読み込みの撮影上の問題とみられる。副首都と同じ。目視は未確認）。
- 10/16 の模擬は新規0件の回。新規の意見があり5論点の再読データを追記しない場合は、設計どおり止まる（実データでは未確認）。

## 9. 2026-10-11 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/ai-copyright-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | ai-copyright に `display_headline`「生成AIと著作権、何が侵害になる？」 |
| `data/page-sources/ai-copyright.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致） |
| `docs/ai-copyright-reaction-map.html` | 新デザイン（`ai_copyright_layout.finish`。`--mode release --output-dir` の公開候補とバイト一致） |
| `DATA_REFRESH.md` | 「生成AIと著作権の定期更新（新デザインを維持する、2026-10-11〜）」の節 |
| `company/APPROVALS.yaml` | 生成AIページの新デザイン公開の承認記録（`approval-20261011-ai-copyright`、承認待ち。並行して他テーマの承認記録が増えても番号がぶつからないよう、連番でなくテーマ名の id にした） |
| `configs/ai-copyright-background.json` | 9-2 の使い回しの書き直し（背景末尾の日付の文） |
| `quality/prototypes/ai-copyright-release/`・`ai-copyright-reading/` | 公開候補と確認画面を最終版で作り直し |
| 共有テスト | 9-4 |

### 9-2. 切替で初めて見つかったことと対応

- **ページ間の言い回しの使い回し**（`verify_page_originality.py`）：手順7の候補の段階で、副首都の新デザインと同じ文が16件
  （読書面の説明・注記・投稿の案内・背景の案内など）あった。`configs/ai-copyright-reading.json` の11文と
  `configs/ai-copyright-background.json` の3文を、意味を変えずに生成AI向けの言い方へ書き直した（例：「山の幅は一定より細くしていません」→
  「山の幅には最小値を決めています」）。切替後に背景末尾の日付の文（「制度の記述は◯月◯日時点の確認です（背景台帳の確認日…）」）が
  副首都と似すぎる（0.76）と出たため、「SNSの集計は◯月◯日まで。制度は◯月◯日時点の内容で、…」の順に直した。
  よみやす「完成を止める指摘 0件」、`verify_page_originality.py`「10ページに、使い回された見出し・文はありません」。
- **H1 の不一致**（`validate_theme_seo.py`）：新デザインの H1 が台帳の headline と違うため、副首都と同じく `display_headline` を足した。
- **DATA_SHEET.md**：生成AIの行は変わらなかった（`build_data_sheet.py` で「ずれなし」）。
- 承認台帳は **`status: pending`（承認待ち）** で足した。オーナーの公開承認は受けていない。

### 9-3. 切替後の検査（作業ツリー）

| 検査 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests` | 1,831件 OK（skip 4、失敗0・エラー0）。共有テストを直す前は失敗8・エラー5（9-4） |
| `verify_theme_page.py ai-copyright` / 全テーマ | NG 0 / 10テーマ NG 0 |
| `verify_number_provenance.py ai-copyright` / 全テーマ | 609/609 説明済み・終了0 / 10テーマ NG 0 |
| `verify_top_page.py` | 終了0 |
| `run_public_checks.py` | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） |
| `build_ai_copyright_arena.py --check` | OK: 差分なし（公開後の経路＝元HTML・新ページ・アリーナデータを作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 生成AIは指摘なし（終了1は既存の他テーマの指摘） |
| `seo/validate_theme_seo.py` | OK（themes=10、sitemap URLs=16） |
| `verify_ai_tone.py` | 問題なし（公開ページ10本） |
| `verify_page_originality.py` | OK |
| よみやす（docs の新ページ） | 完成を止める指摘 0件・PASS |
| 2回生成 | md5 一致（`ff06d8d5…`、`PYTHONHASHSEED` 0・7・4242、docs のページとも一致） |
| `--as-of 2026-10-27` | 止まらず、背景が `after_unconfirmed` |
| Playwright（docs/ を 127.0.0.1 で配信） | 6節と同じ項目すべて合格。画像は `evidence/`（10枚、切替後に撮り直し） |
| 10/16 の模擬（4節） | 最終版で再実行して合格（候補の新ページは基準日 2026-10-16・届出「開始前」、公開対象71件、アリーナデータも候補に含まれる） |

### 9-4. 切替に合わせて直した共有テスト

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_ai_copyright_adapter.py`・`_connected.py`・`_connected_refresh.py`・`_issue_media.py`・`tests/test_theme_hero_assets.py`（生成AIのページ） | 読むページを「公開後は元HTML（data/page-sources）」に | 旧形式の連動表示・論点ごとのX投稿・図解画像・ヒーロー画像の検査。公開後も元HTMLに同じ構造で残る（副首都と同じ扱い） |
| `tests/test_cite_button.py` | 生成AIの新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 生成AIの新デザインを飛ばす | 共通の見た目を掛けない設計 |

## 10. 山なみを対話式に戻す（2026-10-11）

ブランチ `task/planet-ai-copyright`。オーナーの依頼で、「意見の全体像」の山なみだけを、新デザインの静的SVG（`ai_copyright_reading.mountains_svg`
と論点名リスト `.fr-chip`）から、旧ページの対話式の山なみに戻した。冒頭・論点ごとの読書面・背景の開閉行・保護対象の継承は変えていない。
content-map 9番（「立場フィルタと100マス図は移さない」）の判断を、生成AIについてだけ取り消したことになる。

### 10-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `scripts/build_ai_copyright_redesign.py` | `_planet()` を追加。元HTMLの `<!-- PLANET_SECTION_START/END -->` から `section.planet-panel`（中の `<style>`・`planet-live` 判定・`#planet-block`）・`#planet-data`・山なみのスクリプトを写し、読書面の `.fr-map` の静的SVG（`.fr-map-shell`）と `nav.fr-chips` の位置に置く。PLANET_DATA は山なみの直後の1つだけ（末尾の写しはやめた）。部品（`#modes`・`#section`・`#panel`・`#dotbox`・`#waffle`・`#fallback-nav`・`#list`・`#meta`・`#caution`・`#guesses`・`#quiz`・`#dive`）が1つずつ無ければ止まる。旧アンカー `planet-block` の読み替えを外し、隠した受け皿（`fallback`・`fallback-nav`・`quiz`・`progress`）は「表示されていなければ読み替える」形にした |
| `scripts/ai_copyright_redesign/planet.js`（新規） | 山なみの橋渡し（10-3） |
| `scripts/ai_copyright_redesign/reading.js` | `window.AiCopyrightReading.select(id)` を公開（planet.js から論点を選ぶ入口）。動きは変えていない |
| `scripts/ai_copyright_redesign/production.css` | 山なみの配色と並べ方（10-2） |
| `tests/test_ai_copyright_redesign.py` | `test_planet_is_copied_from_source`・`test_planet_follows_source_updates` を追加。旧アンカーの検査を受け皿に対応、旧ページ用スクリプトの検査を「読み込み（`="…`）が無い」に（山なみのスクリプトの説明文にファイル名が出るため） |
| `docs/ai-copyright-reaction-map.html`・`quality/prototypes/ai-copyright-release/`・`quality/prototypes/ai-copyright-reading/reading.js` | 作り直し |
| `DATA_REFRESH.md` | 生成AIの節に、山なみは元HTMLから写す旨を1行 |

元HTML（`data/page-sources/ai-copyright.html`）は変えていない。

### 10-2. 写したもの・外したもの・載せた CSS/JS

- **そのまま写した**：山なみ本体（`#section`、山の幅＝意見の数・高さ＝強い表現の割合、細い山の最小幅と注記）・立場モード4つ（すべて／規制／中立／推進）・
  100マス（`#dotbox`、件数と割合の前後、「なぜ動くのか」の文）・選択パネル（`#panel`、件数・立場の内訳の棒・「論点の一覧へ戻る（Esc）」）・
  論点ボタンの一覧（`#list`、順位・件数・割合）・図が使えないときの一覧（`#fallback-nav`）・見かた（`#meta`）・調査条件（`#caution`）・PLANET_DATA・山なみのスクリプト
  （立場切替の480msの変化・山の選択色・初期表示の自動着地・`hashchange` の処理・GA4 の `issue_view`・`localStorage` の `isa-seen-ai-copyright`）。スクリプトは1文字も変えない。
- **外した**（新デザインに同じ役目があるか、採用しないと決めたもの）：JSなし用の論点別本文 `section.landing-panel`（読書面がJSなしでも全論点並ぶ。中に一次資料と突き合わせていない図解画像がある＝content-map 11）・
  「資料にあるのに、SNSにないこと」`#ocean`（論点ごとの読書面にある。旧ページでも連動表示の CSS で隠していた）・編集部の横断整理 `#editorial`（％が手入力で古い＝content-map 17）。
- **受け皿だけ残して隠した**（スクリプトが書き込むため）：予想2問 `#guesses`・一次資料クイズ `#quiz`（見出しは削除）・進捗表示 `#progress`（`hidden`＋CSS）。
- **JSなしの論点一覧** `#fallback-nav` のリンクは `#fb-…`（外した本文）から `#issue-…`（読書面）へ書き換えた。
- **CSS**：旧ページでは `theme-design.css`（明るい配色）と `ai-copyright-connected.css`（立場カード・論点ボタンの格子・海面下の演出を隠す）が山なみの見た目を作っていた。
  両方とも `body.site-renewal`／`.ai-copyright-connected` 付きで、印刷・背景・検索入口など新ページに無い部品の規則も多いため**読み込まず**、山なみの分だけを
  `production.css` に `.acp-planet #planet-block …` として写し、紙色・藍に合わせた。選択パネルの論点タブ（上の論点ボタンと重なる）・図解画像・旧い理由区分の名前（読書面で言い換えた）は CSS で出さない。
  100マスの横に件数と割合を並べた（旧ページは右側に山なみを薄く敷いていたが、新ページでは山なみを上に残すため）。
- **JS**：`topic-modern.js`（v=13）と `topic-modern.css`（v=32）は前から読み込んでいる。`ai-copyright-connected.js`・`ai-copyright-connected-page.js` は
  読書面のテンプレート・検索入口・連動パネルが前提で、新ページでは何もしない（先頭で止まる）か壊れるため**読み込まない**。代わりに必要な分を `planet.js` で行う。

### 10-3. 山を押したときの飛び先（planet.js）

| 操作 | 動き |
|---|---|
| 山を押す（クリック・Enter・Space） | 山なみのスクリプトの処理（選択パネルへのスクロール）を止め、①URLを素の論点ID（`#ai-copyright-…`）にして山なみ自身の `hashchange` で画面を動かさずに着地（山の選択色・100マス・選択パネル・論点ボタンが合う）、②読書面のその論点を選ぶ、③URLを `#issue-{論点ID}` に書き換え、④読書面の欄へスクロールし見出し（`#fr-h-…`）にフォーカス |
| 立場モードのボタン | 前のとおり（山の幅と高さが変わり、選んだ論点の100マス・件数・割合が変わる）。375px では選択パネルへ運ぶ（前のとおり） |
| 論点ボタン（`#list`）・選択パネルの「戻る」・Esc | 前のとおり（地図の中で切り替え）。URLが素の論点IDになり、読書面もその論点に切り替わる（読書面は素のIDも受ける） |
| 冒頭・背景の `#issue-…` リンク、`#issue-…` 付きで来た人 | 読書面へ（今までどおり）。`topic-modern.js` が `#btn-…` を押させて地図へ戻そうとするので、スクリプトが押したクリック（`isTrusted=false`）だけ止めた。URLは山なみの処理で素の論点IDに書き換わる |
| 初めて開いたとき | 山なみが件数1位の論点（学習データ・無断利用）に自動で着地し、100マスが出る（前のとおり）。URLに `#ai-copyright-learning-data` が付く（前のとおり） |

論点IDの対応は PLANET_DATA の `issues[].id` ＝ 公開JSONの論点ID ＝ 読書面の `data-issue-panel`（`scripts/ai_copyright_taxonomy.py` の7つ）で、変換表は要らない。

### 10-4. 検査結果（作業ツリー、2026-10-11）

| 検査 | 結果 |
|---|---|
| `build_ai_copyright_arena.py` → `--check` | 「UPDATE: HTMLを更新しました」→「OK: 差分なし」。元HTMLは変わらない |
| 2回生成 | md5 一致（`8a031c87…`、`PYTHONHASHSEED=7` でも同じ、docs のページとも一致） |
| `verify_theme_page.py ai-copyright` | NG 0（OK 33） |
| `verify_number_provenance.py ai-copyright` | 605/605 説明済み・終了0 |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `run_public_checks.py` | 終了0 |
| `python3 -m unittest discover tests` | 1,833件 OK（skip 8） |
| よみやす（docs の新ページ、`--strict`） | 完成を止める指摘 0件・PASS（info 17件は変更前と同数） |
| 10/16 の模擬（新規0件、4節と同じ手順をスクラッチ複製で） | 公開対象71件。候補の新ページは基準日 2026-10-16 で山なみ・PLANET_DATA（1つ）・planet.js 入り。候補の中で `verify_theme_page.py` 全テーマ NG 0、`verify_number_provenance.py ai-copyright` NG 0、よみやす 0件、皇室・副首都の公開ページは変わらず |
| Playwright（docs と模擬候補、1280/375px、x.com・platform.twitter.com・twimg.com 遮断） | コンソールエラー0、scrollWidth 一致。立場「規制」で100マス34個・件数635件。山（AI生成物）を押すと読書面がその論点に切り替わり、欄の上端が画面上104px・見出しにフォーカス・URL `#issue-ai-copyright-generated-work-rights`・地図側もその論点。背景の論点リンク・`#issue-…` 付きの読み込みも読書面へ。画像は `quality/prototypes/ai-copyright-release/evidence/planet-restore/` |

### 10-5. 他テーマ（部活動・皇室・副首都）に広げるとき

1. 元HTML（`data/page-sources/{テーマ}.html`）に `PLANET_SECTION` と同じ部品があるか確かめる（`#modes`・`#dotbox`・`#list` など。旧ページの連動表示の有無で中身が違う）。
2. そのテーマの `build_*_redesign.py` に `_planet()` と同じ写し方を入れ、静的SVGと論点名リストの位置に置く。外す部分（本文・資料にしかない話・編集部整理・予想・クイズ・進捗）は同じ。
3. `planet.js` を共通化するか写す（読書面の入口 `window.…Reading.select`、読書面の欄のID）。`topic-modern.js` の `#btn-…` の問題はどのテーマでも同じ。
4. 明るい配色は `production.css` の `.acp-planet` の節をテーマの色に合わせて写す。
5. テスト2件を写し、旧アンカーの読み替え（`planet-block` を外す・受け皿は表示されていなければ読み替え）を同じにする。

テーマごとの違い（未確認）：部活動は旧ページで `bukatsu-connected.js`、副首都・皇室は別の連動表示を持っていた。山なみのスクリプトにテーマ固有の橋渡し
（生成AIの `AI_COPYRIGHT_CONNECTED_BRIDGE`、読書面テンプレートが無いと旧描画に戻る作り）が入っているかで、選択パネルの中身が変わる。

### 10-6. 確認していないこと

- 実機（iPhone Safari など）。Playwright の Chromium だけ。
- スクリーンリーダーでの読み上げ（初期表示で山なみが選択パネルの見出しへフォーカスを移すのは旧ページと同じ）。
- 新規の意見がある回の定期更新（模擬は新規0件）。
- 予想2問・一次資料クイズ・資料にしかない話（潜る操作）・編集部の横断整理を山なみに戻すかどうか（今回は戻していない。戻すなら content-map 14・15・17 の判断を見直す）。

## 11. 部活動型の圧縮（2026-10-12）

ブランチ `task/compact-ai-copyright`。オーナーの要望「文字数が多くて見づらい。部活動のページの収め方を当てはめたい」に合わせ、
論点ごとの読書面と、その周辺の長い節（推移・作り方・詳細データ）を部活動（`docs/bukatsu-chiiki-reaction-map.html`）と同じ型にした。
**文・件数・出典は1つも変えていない**。変えたのは見せる量だけ（折りたたみ・上位4件・選んだ1件だけ展開）。冒頭・対話式の山なみ・
投票・背景の開閉行・保護対象（作り方・詳細データ・推移カード・SEO・GA4・AdSense）の中身は変えていない。

### 11-1. 変えたもの

| ファイル | 変更 |
|---|---|
| `scripts/ai_copyright_reading.py` | 読書面の組み立てを部活動の型に：論点タブ（`nav.fr-tabs`、山なみ設定の絵文字＋論点名）、論点の説明は1段落目だけ見せて2段落目からは「くわしく」、「全体図へ戻る ↑」、「ひと目で見る、この論点の推移」（`.fr-glance`、前の1行の表は「収集ごとの割合と件数」の折りたたみへ）、理由一覧は理由名＋件数の1行を上位4件（`li.fr-reason`）、残りと数え方の注記は「ほかの理由を読む（残りN分類）」、理由の説明（どんな声か・立場の内訳）は区分ごとの `article.fr-reason-detail` に分け、最初は件数1位だけ（`data-on`）、「この論点の別の理由」で次へ。立場別集計・投稿例は折りたたみ。照合は「根拠にあたる：この論点の投稿と一次資料」の下に、主張・資料の確認・資料にしかない話・共通する心配・制度の確認を1件ずつ見出しだけの折りたたみ（照合の前置きの文は「投稿の主張を、一次資料で確かめる」の折りたたみ）。制度の確認（`render_checks`）は照合の節の中へ |
| `configs/ai-copyright-reading.json` | `compact`（見出し・折りたたみの名前だけ。上位件数 `top_reasons: 4`）を追加。本文のキーは変えていない |
| `scripts/build_ai_copyright_redesign.py` | ①推移カードのスクリプトにある回ごとの割合（`const panels`）を読み、読書面の各論点に小さな折れ線と数字2つ（初回と最新回の割合、％だけ。件数は描かない）を入れる。「その他」は推移の論点に無いので注記と案内だけ。②意見の推移は「ひと目で見る、意見の推移」（推移カードの立場の見出し・3本の小さな折れ線・最初の説明文）＋推移カードを**1文字も変えずに**入れた折りたたみ `#acp-trend-more`。③作り方（ARTICLE_TRUST）と詳細データを1つの折りたたみ `#acp-method`「調査方法と、集計の全データ」へ（部活動の `details#method` と同じ）。④旧アンカーの読み替えスクリプトに、折りたたみの中の場所（`#ai-copyright-trend-panel-issue`・`#detail-data`・`#article-trust-title` など）へ来たら外側を開いてそこへ移る処理と、推移のタブ（`aria-controls`）を押す処理、推移の折りたたみを開いたら `resize` を送ってグラフを描き直させる処理を追加（推移のスクリプトは閉じた中では幅0で描くため） |
| `scripts/ai_copyright_redesign/reading.js` | 論点タブ（`.fr-tab`）も論点名と同じく切り替える。理由一覧の行・「別の理由」（`data-reason-pick`）で、その論点の中の説明を1つだけ見せる。`#fr-r-{論点ID}-{区分}` 付きで来たらその理由を開く。`window.AiCopyrightReading.select` と山なみからの飛び先は前のまま |
| `scripts/ai_copyright_redesign/reading.css`・`production.css` | タブ・折りたたみ（＋／－）・1行の理由一覧・選んだ理由の枠・ひと目の推移・作り方の折りたたみの見た目。375pxで余白を詰めた |
| `scripts/ai_copyright_redesign_provenance.py` | 区分ごとの立場の帯と「どんな声か」を、一覧の行ではなく理由の説明（`article.fr-reason-detail`）から照合。説明の件数も照合に追加 |
| `tests/test_ai_copyright_redesign.py` | `CompactReadingTests` 10件（折りたたみの初期状態、タブ、説明の1段落目と「くわしく」、上位4件と1件だけ展開、照合の折りたたみ、ひと目の推移の数字、推移カードと作り方が折りたたみの中に文字どおり、折りたたみの中への移動、出所検査の改ざん検知） |
| `tests/test_ai_copyright_redesign_browser.cjs` | 新しい構造に合わせた（`.fr-chip`→`.fr-tab`、山は対話式の山なみ、推移・作り方・投稿例は開いてから確かめる、理由の切替と「別の理由」、読書面の折りたたみ全開で横はみ出し0）。10節の時点で `.fr-chip` が無くなり動かなくなっていたのも直した |
| `DATA_REFRESH.md` | 生成AIの節に、折りたたみは生成器が作る旨を1行 |
| `docs/ai-copyright-reaction-map.html`・`quality/prototypes/ai-copyright-release/`・`quality/prototypes/ai-copyright-reading/` | 作り直し |

元HTML（`data/page-sources/ai-copyright.html`）は変えていない。新しい公開文言は見出し・折りたたみの名前と、ひと目の推移の注記1文
（「「その他」を除く意見の投稿で、この論点が占める割合を収集の回ごとに比べています。集めた投稿の中の動きを示すもので、世論の動きを表すものではありません。」）と
数字の並び（「8月3日 32.8% → 10月6日 26.1%（9回の収集）」の形）だけ。

### 11-2. 折りたたみの初期状態（375px・1280px 共通）

| 場所 | 初期表示で見えるもの | 折りたたんだもの（初期は閉） |
|---|---|---|
| 読書面の上 | 論点タブ7つ（選んだ論点が藍） | — |
| 論点の見出し | 分類名・論点名・説明の1段落目・件数と割合・「全体図へ戻る ↑」 | 説明の2段落目（「くわしく」） |
| ひと目で見る、この論点の推移 | 小さな折れ線・初回と最新回の割合・「詳しいグラフを開く ↓」 | 最新の累計の表と注記（「収集ごとの割合と件数」） |
| 理由一覧（N分類） | 件数上位4件の理由名＋件数＋割合 | 残りの理由と数え方の注記（「ほかの理由を読む（残りN分類）」） |
| 選んだ理由 | 件数1位の理由の見出し・どんな声か・立場の内訳・「この論点の別の理由」 | 他の理由の説明（JSで非表示。JSなしでは全部並ぶ） |
| 立場 | — | 「この論点の立場別集計」（帯・3立場の件数・注記） |
| 投稿 | — | 「投稿の例を読む（2件）」（要約2件・元の投稿の埋め込み） |
| 根拠にあたる | 主張・資料の確認・資料にしかない話・共通する心配・制度の確認の見出し（判定ラベル付き） | 各項目の中身（照合の結果・該当投稿数・出典）、照合の前置き |
| あわせて確かめる | リンク（前のまま） | — |
| 意見の推移 | 見出し・3本の小さな折れ線と凡例・最新回の説明文1つ | 推移カード全体（立場と論点のタブ・グラフ・表・画像4枚・埋め込みコード）＝「詳しいグラフと表を開く」 |
| 背景 | 前のまま（7行すべて閉。初期で開いている行は無いことを確認） | — |
| 作り方・詳細データ | 「調査方法と、集計の全データ」1行 | このページの作り方・詳細データ（中身は元HTMLのまま） |

ページ全体の `<details>` は48個→118個。初期状態で `open` なのは3個（推移カードの「このグラフを画像で使う」2個と詳細データの「分類別件数」1個。
元HTMLのまま）で、3個とも閉じた折りたたみの中にあるため、初期表示で開いて見えるものは0個。JavaScriptが無くても、すべて `<details>` で開閉できる。

### 11-3. 前後の計測（Playwright・Chromium、`docs/` を 127.0.0.1 で配信、x.com・platform.twitter.com・twimg.com を遮断）

司令塔と同じ測り方（h2ごとの高さ＝その h2 の上端から次の表示中の h2 の上端まで）に加え、選んだ論点の読書面（`.fr-panel[data-selected]`）を直接測った。
文字数は2通り：**表示中**は `checkVisibility()` が真の要素のテキスト、**旧方式**は `getClientRects()` が空でない要素のテキスト。
旧方式は閉じた `<details>` の中身も数えてしまう（Chrome は閉じた中身を `content-visibility:hidden` で残すため）。部活動も旧方式 1,650字・表示中 857字と差が出る。

| 375px | 前 | 後 |
|---|---|---|
| ページ全体の高さ | 24,380px | **12,255px** |
| 論点1つの読書面（`.fr-panel`、学習データ・無断利用） | 9,981px | **2,943px** |
| 同、7論点の最大／最小 | — | 2,943px（学習データ）／1,394px（利用者モラル） |
| 同、表示中の文字数 | 4,344字 | **1,032字**（旧方式 5,880字→4,881字） |
| h2「📚 学習データ・無断利用」の節（山なみの選択パネル1,213px＋タブ＋読書面） | 11,499px・旧方式 6,382字 | 4,381px・表示中 1,587字（旧方式 5,436字） |
| 意見の推移 | 3,969px（h2の節 3,845px） | 444px（開くと前と同じ） |
| 作り方＋詳細データ | 1,118＋558px | 70px（閉じた1行） |
| 制度の背景 | 1,347px | 1,347px（変えていない） |

| 1280px | 前 | 後 |
|---|---|---|
| ページ全体の高さ | 12,118px | 7,033px |
| 論点1つの読書面 | 3,398px | 1,423px |

目標（375pxで読書面 3,000px以下・表示文字 2,000字以下・ページ全体 13,000px以下）は、読書面を `.fr-panel` で測った値と表示中の文字数で満たした。
h2 の節で測ると、山なみの選択パネル（保護対象、1,213px）が読書面の前に入るため 4,381px になる。旧方式の文字数は閉じた中身を数えるので 4,881字のまま。

### 11-4. 検査結果（作業ツリー、2026-10-12）

| 検査 | 結果 |
|---|---|
| `build_ai_copyright_arena.py` → `--check` | 「UPDATE: HTMLを更新しました」→「OK: 差分なし」 |
| 2回生成 | md5 一致（`47e38fb5…`、`PYTHONHASHSEED=0` でも同じ、docs・公開候補とも一致） |
| `verify_theme_page.py ai-copyright` | NG 0（OK 33）。全10テーマ NG 0 |
| `verify_number_provenance.py ai-copyright` | 654/654 説明済み・終了0（折りたたみの中の件数も読む） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `run_public_checks.py` | 終了0 |
| `python3 -m unittest discover tests` | 1,849件 OK（skip 8） |
| よみやす（docs、`--strict`） | 完成を止める指摘 0件・PASS（info 17件は変更前と同数）。`--original` 付きは「増えた値」（ひと目の推移の日付・割合、N分類）で要修正と出る。増えた値は推移カードと理由一覧にすでにある数字の写し |
| `verify_page_originality.py` | 使い回し0（最初の注記案が部活動と同じ文だったので書き直した） |
| `verify_ai_tone.py` | 問題なし |
| 10/16 の模擬（新規0件、4節と同じ手順をスクラッチ複製で） | 公開対象71件。候補の新ページは基準日 2026-10-16 でタブ・推移の折りたたみ・作り方の折りたたみ入り、読書面 2,943px・ページ 12,255px（375px）。候補の中で `verify_theme_page.py` 全テーマ NG 0、`verify_number_provenance.py ai-copyright` NG 0、よみやす PASS、部活動・皇室・副首都の公開ページは変わらず |
| Playwright（`tests/test_ai_copyright_redesign_browser.cjs`、1280/375px） | 合格。横はみ出し0（読書面の折りたたみを全部開いても0）、ページのコンソールエラー0（遮断した外部読み込みの失敗だけ）。タブ7つで scrollY 不変、山を押すと読書面が画面上部へ・見出しにフォーカス、理由の行で説明が1つだけ・「別の理由」で次へ、推移を開くとグラフが幅いっぱいに描かれタブも切替、`#ai-copyright-trend-panel-issue`・`#detail-data` 付きで来ると外側が開く、`#fb-…`・`#issue-…` 付きで論点が選ばれる、JSなしで7論点・推移・作り方・詳細データが開ける、X埋め込み遮断で案内と元投稿リンク2件。投票は押していない |

撮影: `quality/prototypes/ai-copyright-release/evidence/compact/`（`page-{desktop,mobile}.png` 全体、`reading-1/2-*.png` 読書面の先頭2画面、
`reason-open-*.png` 理由を1つ開いた画面、`trend-open-*.png` 推移を開いた画面、`background-open-*`・`nojs-desktop`・`x-embed-fallback`）。

### 11-5. 皇室・副首都・今後の5テーマへ広げる手順

皇室（`koshitsu_reading.py`）・副首都（`fukushuto_reading.py`）は生成AIと同じ部品名（`render_stance`・`render_reasons`・`render_posts`・
`render_evidence`・`render_checks`・`render_trend`・`render_panel`）なので、ほぼ同じ差し替えで済む見込み。

1. 設定JSONに `compact`（この節の見出し文言。テーマに合わせて書き、`verify_page_originality.py` で使い回しを確かめる）を足す。
2. 読書面の生成器の `render_*` を、この節の `ai_copyright_reading.py` の形に差し替える（`fold()`・`ordered_reasons()`・`render_reason_details()`・`render_glance()`・`render_tabs()`）。
   テーマ固有の部品（副首都の「あわせて確かめる」など）は折りたたみにするかだけ決める。
3. 公開ページの組み立て（`build_*_redesign.py`）に `_trend_rounds`・`_issue_glances`・`_trend_band` と作り方の折りたたみを写す。
   推移カードのスクリプトに `const panels = {…};` がそのテーマにもあるか、論点名が公開JSONの label と一致するかを先に確かめる
   （一致しない論点は注記と案内だけになる）。旧アンカーの読み替えスクリプトの「外側を開く」処理も写す。
4. 出所検査（`*_redesign_provenance.py`）の、区分ごとの立場と説明の照合先を `article.fr-reason-detail` に変える。
5. テスト（`CompactReadingTests` と Playwright）を写し、375pxで読書面・ページ全体を測って記録する。

見込み：皇室（読書面 7,281px）・副首都（5,749px）は生成AIより理由区分と照合が少ないので、同じ型で 2,000〜2,500px 程度に収まる見込み（未計測）。
山なみの選択パネル（対話式に戻した部分）は保護対象として残るので、h2 の節で測る値はその分だけ大きくなる。
今後の5テーマは、新デザインの読書面を作るときに最初からこの型で作る。

### 11-6. 確認していないこと

- 実機（iPhone Safari など）。Playwright の Chromium だけ。Safari は閉じた `<details>` の中をページ内検索で開かない。
- スクリーンリーダーでの読み上げ（理由の切替はページ内の表示切替で、読み上げ用の通知は付けていない）。
- 新規の意見がある回の定期更新（模擬は新規0件）。主張や資料が増えると「根拠にあたる」の見出しが1行ずつ増え、学習データの読書面は 3,000px を超えうる（いまは 2,943px）。
- GA4 の `issue_view` の送信（山なみのスクリプトのまま変えていない。実際の送信は見ていない）。
