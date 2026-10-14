# 部活動の地域移行（bukatsu-chiiki）最新の型の公開候補と検査（手順7）

2026-10-14。ブランチ `task/renew-bukatsu-chiiki`。手順書23の「7. 更新と公開を検査する」。
消費税減税の [2026-10-13-consumption-tax-cut-production-candidate.md](2026-10-13-consumption-tax-cut-production-candidate.md)（最新の型）にそろえた。
部活動は **2026-10-10 に初期型の新デザインで公開済み**（[2026-10-10-bukatsu-production-candidate.md](2026-10-10-bukatsu-production-candidate.md)）なので、
今回は「旧形式→新デザイン」ではなく「初期型の新デザイン→最新の型」への組み替え。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/bukatsu-layout.json` に `version: "redesign-v2"` を足して docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/bukatsu-chiiki-release-v2/bukatsu-chiiki-reaction-map.html` と `bukatsu-chiiki-full.html`（基準日＝公開JSONの更新日 2026-10-08）
確認画面: `quality/prototypes/bukatsu-chiiki-release-v2/evidence/`（PC・375px の全体、山なみ、立場モード切替、山を押して読書面へ、読書面、
理由を開いた画面、背景を開いた画面、自治体の絞り込み、推移を開いた画面、X遮断時、JSなし、全文・印刷版（画面と印刷の見た目））

## 0. 手順7の前に直したこと（コミット 279f9889）

| 項目 | 処理 |
|---|---|
| 1. 公開JSON由来のよみやす11件 | 重なる心配 `vein-1`・`vein-2` の `diverging_reason`、資料にしかない話 `sc-4` の `life_impact`・`sns_note`（本文の部分）を、数字・出典・判定を変えずに文で区切った（`data/verification/bukatsu-chiiki-{veins,sunk-continents}.json`）。`build_public_registry.py --topic bukatsu-chiiki` で公開JSON・catalog を、`build_adoption_registry.py` で採用台帳の指紋を作り直した。読書面の試作のよみやす `--strict` は完成を止める指摘 11件→0件。`verify_number_provenance.py bukatsu-chiiki` NG 0、`verify_ocean_layer.py` は直す前と出力が完全に同じ（他テーマの既存の指摘で終了1） |
| 2. 「試作」の語 | `scripts/bukatsu_redesign/parity.py` が投票の保存注記を「試作では、この端末に選択内容を保存します。本番の投票集計には送信しません。」に書き換えていたのをやめ、元HTMLの文（「※ サイト参加者の集計であり、世論調査ではありません。回答と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。」。他テーマと同じ）のままにした。`template.html` のJSなし案内を「論点の切り替えにはJavaScriptを使います。全文・印刷版ですべての論点を読む」にした。初期型の出力の差はこの2か所だけ（初期型の経路で作り直しても誤りが出ない）。なお `docs/vote-store.js` は、JavaScriptが動くと注記を「本番ホストで送信あり／なし」に合わせて書き換えるので、誤った文が見えていたのは読み込み直後とJSなしのとき |
| 3. 手順7の中で直した文（コミット2） | 使い回し検査（他テーマと似すぎ）で、読書面の前置き・論点の件数の注記・読書面の最後の1文を書き直した（`configs/bukatsu-chiiki-reading.json`）。ページの検査（論点数は1ページに1通り）が「7つの論点で最も多い件数です」と「ほかの6つの論点」を食い違いとして止めたので、順位の文から論点数を外した。ページの検査（意見数は1ページに1通り）が資料にしかない話 sc-1 の記録「意見1139件の母数には含まれない」を止めたので、「当時の意見1139件」とした（記録時点の母数。公開JSONを作り直した） |

### 申し送り（読書面の設計記録5節）の処理

| 申し送り | 処理 |
|---|---|
| 1. 更新経路の組み替え | `scripts/build_bukatsu_redesign_v2.py`（新規）を作り、`bukatsu_layout.py` の `finish`・`rebuild` が設定 `version` で初期型と最新の型を選ぶようにした（1節）。最新の型は `editorial-review.json` の指紋を読まない（テストで確認）。凍結した `editorial-source.html`・`template.html`・`parity.py`・`build.py` の `copy`・`featured`・`default`・`refresh_inputs.py`・`app.js` も読まない |
| 2. 10/17 の定期更新との順番 | 設計記録の「10/17 は公開中の経路のまま通す」を改め、どちらの順でも通るようにした。最新の型で 10/17 を模擬して最後まで通ることを確かめ（4-2）、公開が 10/17 以降になる場合の初期型の指紋の更新手順を DATA_REFRESH.md に書いた（4-3） |
| 3. 「試作」の語 | 0節の2。新しいページと全文・印刷版に「試作」の語が無いことをテストで確認 |
| 4. FAQ の JSON-LD | `bukatsu_background.faq_jsonld()` から作り、画面の問いと答えに突き合わせてから埋め込む（違えば止まる）。元HTMLの `SEARCH_FAQ_JSONLD` は引き継がない |
| 5. ページ全体の「ひと目」 | 推移の要約（立場4本の折れ線・最初と最新の回で最も多かった立場の1行・注記1行）を山なみ・読書面の後ろに置き、13回分のカードを折りたたみに入れた（2節）。外部の埋め込みが指す2つの id はそのまま |
| 6. 公開JSON由来のよみやす | 0節の1 |
| 7. 山なみ | 元HTMLの `#planet-block` を論点タブの上に写した。入口は `window.BukatsuReading.select`。旧アンカーの読み替え表は2節 |
| 8. 継承 | 2節。「論点をまたいで分かること」（編集部の横断整理）は載せない（他の新デザイン9テーマと同じ。7節） |
| 9. 代表投稿の生存 | 14件は 10/14 に確かめた（読書面の記録）。公開切替の前の再確認はしていない（8節） |
| 10. 自治体の一覧 | 2026-09-23 の確認のまま。冒頭の確認日（10/14）とは別の日付で表示 |

## 1. 仕組み（消費税減税と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_bukatsu_redesign_v2.py`（新規） | 冒頭・読書面・背景の生成器（`bukatsu_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLと全文・印刷版を組む。`--mode preview\|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/bukatsu_layout.py`（書き換え） | `enabled`・`version`・`source_for_refresh`・`materialize`・`finish`・`rebuild`。`version: "redesign-v2"` なら最新の型、無ければ初期型（`build_bukatsu_redesign.py`） |
| `configs/bukatsu-layout.json` | 公開候補の段階は `version` 無し（初期型）。公開切替で `"version": "redesign-v2"` |
| `scripts/bukatsu_redesign/planet_v2.js`（新規） | 山なみの橋渡し（消費税の planet.js と同じ動き）。山を押すと URL を `#issue-…` に置き換え、山なみ自身の画面を動かさない着地で合わせ、読書面へ移る |
| `scripts/bukatsu_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（青・黄・珊瑚）に合わせる。本文の書体は部活動の冒頭と同じ（topic-modern.css の `!important` をこのページだけ上書き）。topic-modern.css の `main` の左右の余白を外す（読書面の試作と同じ幅）。375px で冒頭の段の一覧を詰め、山なみの100マスを小さくする |
| `scripts/bukatsu_redesign_readable.py` の `readable_v2`（追加） | 全文・印刷版。同じ生成結果からスクリプト・山なみ・投票・論点タブを除き、折りたたみを開いた形で並べる |
| `scripts/bukatsu_redesign_provenance.py` の `verified_selectors_v2`・`verify_glance_v2`（追加） | 新デザインの件数を公開JSON・再読データ3ファイルの明細・立場の対応表・設定から数え直して照合（冒頭の件数欄・7論点の欄・推移の要約の注記）。論点ごとの折れ線は非公開正典を収集日別に数え直して SVG と照合。初期型の `verify_counts`・`verify_glance` は残す |

ページの並び：共通ヘッダー → 冒頭（パンくず・題名・件数札・段階の一言・短答3問・改革の期間と段の一覧・SNSの意見の件数・確かめた一次資料）→
論点ごとに読む（見出し → **対話式の山なみ**（調査条件・立場モード・山・論点ボタン・選択パネルと100マス・見かた）→ 論点タブ → 選んだ論点の欄 → 全文・印刷版への案内）→
推移の要約（折りたたみに13回分のカード）→ 投票 → 背景の開閉行7行 → 集め方・分類のしかたと全体の件数表（折りたたみ1つ）→ 次に見るテーマ → フッター。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 公開中のページ（初期型） | 公開候補（最新の型） | 結果 |
|---|---|---|---|
| title | 「部活動の地域展開（地域移行）はいつから？費用・問題点・賛否を整理｜SNS反応まっぷ」 | 同じ（元HTMLから） | 継承 |
| meta description・SEO_META（canonical・OGP・Twitter） | 元HTMLから写し | SEO_META 区間を文字どおり複写 | 継承（description は変えていない） |
| Article JSON-LD | 元HTMLから写し | ARTICLE_JSON_LD 区間を文字どおり複写 | 継承 |
| FAQ JSON-LD | 元HTMLの `SEARCH_FAQ_JSONLD`（6問。画面と回答の言い回しが3問ずれていた） | 背景の「よくある質問」6問と同じ設定の items から作る | 画面と構造化データの一致を生成時とテストで確認 |
| H1 | 「部活動の地域移行はいつから？費用・問題点と、意見が分かれる理由」 | 同じ（冒頭の設定。`display_headline` と一致しないと止まる） | `configs/theme-seo.json` の `display_headline` は既に同じ文なので変えていない |
| GA4（G-K10S4YCZFH） | release だけ | GA_TAG 区間を release だけ複写 | 継承 |
| AdSense（ca-pub-2542211932832864） | release だけ | ADSENSE_TAG 区間を release だけ複写（元HTMLに `google-adsense-account` の meta は無い） | 継承 |
| 共通CSS/JS | 独自の site_chrome・`topic-modern.js?v=15` | site-tokens（v=3）・topic-modern（css v=32・js v=13。元HTMLの版） | 初期型の site_chrome・planet.css・parity.css は読まない |
| 投票（Supabase） | topic `bukatsu-chiiki-issue-stance-v1`、論点7×立場3、`choiceIdx:issueIdx*STANCES.length+stanceIdx`。保存の注記が「試作では…送信しません」 | 投票節・失敗の案内（voteMsg）・投票スクリプトを複写。VOTE_ISSUES・V2I・STANCES は元と完全一致。保存キーは本番ホストだけ既存キー、他は `…_my_preview`。保存の注記は元の文（違えば止まる） | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。投票ボタンの論点には元HTMLの絵文字が戻る（初期型は外していた） |
| 調査条件（#caution）・PLANET_DATA | 山なみの中 | 山なみの中に #caution（RESEARCH_CONDITIONS、`#research-conditions`）、PLANET_DATA は1つだけ | 継承 |
| 共通ヘッダー・パンくず | 初期型の site_chrome | 消費税と同じ静的な共通ヘッダー、冒頭のパンくず | JSなしでもトップへ戻れる |
| 意見の推移（TREND_CARD） | 背景の開閉行の中 | 枠と CSS 区間を文字どおり複写し、要約の下の折りたたみ `#cap-trend-more` へ | 継承。外部の埋め込みが指す2つの id はそのまま |
| 作り方（ARTICLE_TRUST）・詳細データ（#detail-data） | 「調査方法」の開閉 | 文字どおり複写し、1つの折りたたみ `#cap-method` へ。詳細データの論点別・スタンス別の件数は公開JSONと照合して違えば止まる | 継承 |
| 次に見るテーマ・クリック計測 | `#related-topics`（見出しを「関連する論点も読む」に置換）・計測 | 両方文字どおり複写（見出しは元HTMLの「次に見るテーマ」） | 継承 |
| フッター | 初期型の parity-footer | 元HTMLの footer を文字どおり複写 | 継承 |
| 授業節 | `#classroom`（CLASSROOM マーカー） | 背景「授業や話し合いで使う」を CLASSROOM マーカーで囲み、印刷ボタンと授業用の印刷画面（`bukatsu-chiiki-classroom.html`）への案内 | 継承。`apply_classroom_section.py` は最新の型で skipped |
| 全文・印刷版 `bukatsu-chiiki-full.html` | 初期型のページから作る | 最新の型のページから作る（同じ生成結果。スクリプト0） | 中身は新しいページと同じ。noindex,follow |
| 授業用の印刷画面 `bukatsu-chiiki-classroom.html` | 初期型が毎回作る | 作り直さない（docs のまま。中身は授業の設定から作った静的ページで、リンク先の `#classroom`・論点の素のIDは読み替えで届く） | 7節 |
| 論点の図解画像 | 論点ごとの開閉 | 載せない（画像の中の数字を一次資料と突き合わせていない。内容対応表20） | 画像ファイルは docs に残る |
| 編集部の横断整理・比較欄・目次 | あり | 載せない（内容対応表 10・12・28） | 7節 |

### 旧アンカーの到達確認

`grep -rn "bukatsu-chiiki-reaction-map.html#" docs/ scripts/ configs/ company/` で外から指されているのは、推移の2タブ（埋め込みコード。新ページにそのまま残る）、
`#vote-section`・`#detail-data`（残る）、`#issue-{論点ID}`（残る）、授業用の印刷画面の `#classroom` と論点の素のID（読み替え）、`#bukatsu-check`（読み替え）、`#quiz`（読み替え）。
外から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開き、推移のタブならそのタブに切り替える）。

| 旧ID | 読み替え先 |
|---|---|
| 論点の素のID（初期型の読書面の欄・授業用の印刷画面のリンク）・`#fb-…`・`#extras-…`・`#bukatsu-reading-…`・`#illustration-…`・`#heading-{0〜6}`・`#sources-{0〜6}` | その論点の欄 `#issue-{論点ID}`（選んだ状態になり、山なみも合う） |
| 初期型の理由の欄 `#{論点ID}--{理由}` | 新しい理由の説明 `#fr-r-{論点ID}-{理由}`（一覧に出さない区分なら論点の欄） |
| `#answers`・`#progress`・`#bukatsu-search-entry-title` | 冒頭 `#bukatsu-open` |
| `#schedule` | 改革の期間と段の一覧 `#bko-steps` |
| `#faq`・`#faq-guide` | 背景「よくある質問」`#bg-faq`（開く） |
| `#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`） | 冒頭の件数欄 `#bko-count` |
| `#map`・`#stance-map-section` | 山なみ `#planet-block` |
| `#reading`・`#reading-announcement`・`#reading-progress`・`#issue-tabs`・`#comparison`・`#source-only`・`#editorial-notes`・`#editorial`・`#ocean`・`#issue-cards`・`#bukatsu-chiiki-audit`・`#bukatsu-connected-data`・`#bukatsu-role-title`・`#fallback`・`#fallback-nav`・`#quiz`・`#guesses` | 読書面 `#bukatsu-chiiki-reading` |
| `#trends` | 推移の要約 `#cap-trend` |
| `#background` | 背景 `#bukatsu-chiiki-background` |
| `#bukatsu-background`・`#bg-title` | 背景「地域展開とは何か、認定とお金の仕組み」`#bg-system`（開く） |
| `#local`・`#bukatsu-check`・`#ck-title`・`#local-check-tool-title` | 背景「自分の自治体は？」`#bg-municipal`（開く） |
| `#classroom`・`#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |
| `#method` | 作り方と詳細データの折りたたみ `#cap-method`（開く） |

そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`research-conditions`・`planet-block`・`planet-data`・`modes`・`bukatsu-chiiki-trend`・
`bukatsu-chiiki-trend-panel-stance`・`-issue`・`article-trust-title`・`issue-{論点ID}`。**到達できなくなった旧アンカーは無い**（元HTMLと公開中の初期型のページの
すべての id について、新ページにあるか読み替え先があることをテストで確認。読み替え先が無いのは JS・CSS の内部用IDだけ）。JSなしのときは読み替えが働かず、ページ先頭に表示される。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_bukatsu_redesign_v2.py --mode release --output-dir quality/prototypes/bukatsu-chiiki-release-v2
```
成功すると `Built 2 files (release, as_of 2026-10-08); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文・論点の目印・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。部活動の山なみは論点を選ぶと URL を素の論点IDに書き換えて
  履歴を1つ増やし、読み込み時には画面を動かす着地をし、画面を動かさない着地でも選択パネルの見出しへフォーカスを移していた。この3か所だけ書き換える（`PLANET_PATCHES`）。
  読み込み時の論点は、連動表示の橋渡しの `initialLand`（ハッシュが無ければ件数1位、`#issue-…`・素の論点IDならその論点）が画面を動かさずに選ぶ。
  初期型の「仮に #map を置く」細工と、読書面の欄の ID を一時的に外す細工（初期型の planet.js）は要らなくなった
- **論点ごとの折れ線**：読書面の生成器の既定の入力（`data/page-sources/bukatsu-chiiki.html`）は、公開候補の隔離コピーでは `finish` が保存し直すまで古いので、
  組み立てに使う元HTMLの推移を渡して描く
- **推移の要約**：推移のカードの `const panels` を読み、立場4本の13点の折れ線と、最初と最新の回で最も多かった立場の1行を作る。注記の数字（1回あたり65〜239件、±9ポイント、
  古い投稿は最大46%）は推移の立場の注意書きから写す（手で書かない。カードの件数の幅が回ごとの件数と違えば止まる）。分類AIの切替（10/1）は論点だけの記録なので、
  立場の要約には出さない（立場は全回を同じAIで判定し直している）
- **見出しの書き分け**：使い回し検査で、読書面の前置き（高齢者と0.78）・論点の件数の注記（消費税と0.96）・読書面の最後の1文（消費税と0.72、自転車と0.70）・
  推移の要約の1文（消費税と0.85）が似ていたので書き直した
- **375px の高さ**：最初はページ全体 13,868px・論点の欄 2,482〜2,605px。topic-modern.css の `main` の左右の余白（12px・!important）と本文の書体（Noto Sans JP・!important）で
  欄が狭く・文字が大きくなっていたので、このページだけ外した（読書面の試作と同じ）。冒頭の段の一覧を詰め、山なみの100マスを小さくし、投票の論点ボタンを2列にした

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、これまでどおり隔離コピーで `materialize` → 旧形式の全処理 → 最後に `bukatsu_layout.finish`（変更なし）。
  `finish` は設定 `version` で組み立て方を選ぶ。最新の型の公開物は、元HTML・ページ・全文・印刷版の3つ（初期型は授業用の印刷画面・画像・投票クライアントの写しも書いた）
- `refresh_adapters/bukatsu.py` は `source_for_refresh` を入力にする（変更なし）。**立場の対応表（`data/bukatsu-chiiki_reread-stances.json`）を累積候補と再読データから作り直して公開対象に含める**（2回作って一致を確かめる）。
  新しい意見が再読データの明細に無いと「追い読みが要ります」で止まる（テストで確認）
- `refresh_bukatsu_pilot.validate_candidate` の保護タグの数の比較を、docs/ のページではなく旧形式の入力（`source_for_refresh`）と比べるようにした。新デザイン公開中の docs/ のページと比べると、
  データが正しくても数が合わず止まる（初期型の公開後、部活動の更新回は一度も通っていなかったので表に出ていなかった）
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。データが変わっても、照合が合えば止まらない（指紋は無い。テストで確認）
- `build_bukatsu_arena.py` は、公開後に引数なしで動かすと `rebuild`（`--check` で差分の有無だけ）

### 4-1. データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの件数・一覧に出さない区分 | 再読データ3ファイル（論点ごとの `buckets`・`items`）と `configs/bukatsu-chiiki-reading.json` の `excluded_buckets` | **新しい意見の追い読み（人が読む）**。明細が正典の意見と合わないと生成が止まる |
| 区分ごとの立場・投稿の立場 | `data/bukatsu-chiiki_reread-stances.json` | 更新経路では adapter が作り直す。経路の外では `bukatsu_reread_stances.py --made-on` |
| 理由の説明（上位4件の voice）・論点の説明・投稿2件・折りたたみの名前 | `configs/bukatsu-chiiki-reading.json` | 上位4件が入れ替わったとき・区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`・`data/bukatsu-chiiki_claim_posts.json` | 主張を足すとき |
| 資料にしかない話・重なる心配 | `data/verification/bukatsu-chiiki-{sunk-continents,veins}.json` → 公開JSON `ocean_layer` | 母数が増えたら再検索の記録と `sns_base`。文は1文80字以内・読点3つまで |
| 冒頭（短答・段の一覧・件数欄）・確認日・段階 | `configs/bukatsu-chiiki-opening.json`（`checked_on`・`period`・`steps`・`answers`） | 確かめ直したら `checked_on`。中間評価を確かめたら `period.midterm_checked_on` |
| 背景（仕組み・決まったこと・年表・自治体・FAQ・授業・未確認） | `configs/bukatsu-chiiki-background.json`・`configs/classroom/bukatsu-chiiki.json`・自治体カタログ・一次資料メモ | 一次資料の再確認時 |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION | 自動 |
| 意見の推移・論点ごとの折れ線・要約の注記 | 元HTMLの TREND_CARD（adapter の `trend_support.render_trend`） | 自動。分類AIが変わったら `model_breaks` |
| 公開日・次回更新予定・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・詳細データ・次に見るテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

### 4-2. 10/17 の定期更新の模擬（切替後の作業ツリーの隔離コピー、完了記録の検査だけ外した）

実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む。ここでは、より多くの経路を通すため、前回（10/08）の回と同じ収集結果を
10/17 の回として置き、正典をそのまま累積候補にして **adapter の `build`（元HTMLから候補ページ・推移・立場の対応表・推移の画像を2回作って一致）→
`prepare_public_candidate_bundle`（公開JSON・finalize・SEO・授業節・他テーマの新デザイン・`bukatsu_layout.finish`）** を通した。**最後まで通った**（公開対象60ファイル）。
- 候補の docs/ は最新の型（`redesign-v2`、基準日 2026-10-17、次の収集予定 10月31日）、元HTMLは旧形式、立場の対応表は立場の中身が同じで `made_on`・`public_updated_on` だけ 2026-10-17
- 他テーマの新デザイン9ページは変わらず（変わったのは部活動のページだけ）
- 候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0、`verify_builder_rebuildability.py` 10テーマ NG 0、`validate_theme_seo.py` OK、使い回し 0件。
  よみやすは最初「同じ文末『ます』の3連続」が1件（基準日が変わって前後の文が並んだ）→読書面の最後の1文と全文・印刷版の案内の文末を直して 0件。
  全文・印刷版でも、推移の注記の2文目と背景の前置きが並んで同じことが起きたので、注記の2文目の文末を直した（9-1）
- 新しい意見がある回（明細が足りない回）で止まることは、`tests/test_bukatsu_redesign_v2.py` の `test_count_mismatch_stops_before_writing`（finish）と
  `test_adapter_rebuilds_stance_table_and_stops_without_reread`（adapter）で確かめた
- 模擬に使った隔離コピーは作業ツリーの外（セッションの作業用フォルダー）で、作業ツリーには何も書いていない

### 4-3. 公開が 10/17 以降になった場合（初期型の経路のまま 10/17 の回を通す）

同じ模擬を初期型の設定（`version` 無し）の隔離コピーで流すと、`refresh_inputs.py` の「集計と推移の最終日が一致しません」で止まった（新規0件の回は推移の最終日が前回のまま。
2026-10-11 の記録と同じで、新規0件の回は公開候補を作らないので実害は無い）。新規の意見がある回は、元HTMLの論点別・理由別の件数が変わるので、初期型は指紋で止まる。
そのときの指紋の更新手順を DATA_REFRESH.md の部活動の節の最後に1段落で書いた（隔離コピーの更新済みの元HTMLから `data_sha256` と `editorial_sha256` を出すコマンド。
今の元HTMLで実行すると、いまの `editorial-review.json` の2つの値と一致することを確かめた）。新規の意見がある回を初期型の経路で最後まで通す模擬はしていない（8節）。

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/bukatsu_layout.py` | 設定 `version` で初期型と最新の型を選ぶ。`finish(root, as_of=None)` | 初期型の経路を残したまま切り替えられるように |
| `scripts/refresh_adapters/bukatsu.py` | `build_reread_stances`・`REREAD_STANCES` を公開対象に | 追い読みの後の対応表の作り直し忘れで止めるため |
| `scripts/bukatsu_reread_stances.py` | `table`・`reread_rows` に `root` 引数（既定は従来どおり） | adapter が作業ツリーの再読データを読むため |
| `scripts/refresh_bukatsu_pilot.py` | 保護タグの数を旧形式の入力と比べる | 4節 |
| `scripts/bukatsu_count_provenance.py`・`bukatsu_redesign_provenance.py` | `redesign-v2` なら新しい照合へ | 新デザインの件数を照合するため（初期型の照合はそのまま） |
| `scripts/verify_theme_page.py` | `redesign-v2` を他の新デザインと同じ「論点の欄の中で照合する」分岐へ。`excluded_buckets` の区分は数え方の注記（`data-excluded`）の合計と照合 | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | `redesign-v2` のページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ（初期型には従来どおり掛ける） |
| `scripts/seo/validate_theme_seo.py` | 初期型だけの必須の部品（`.site-chrome`）を `redesign-v2` では求めない | 最新の型は共通の CSS を読む |
| `scripts/refresh_planet_section.py`・`inject_tide_widget.py`・`apply_theme_design.py`・`verify_builder_rebuildability.py`・`refresh_topic.py` | 変更なし | `name="bukatsu-layout"` の目印で既に停止・SKIP・対象外、materialize・finish も既にある（確認のみ） |
| `configs/bukatsu-chiiki-reading.json` | 推移の要約・作り方の折りたたみの文言（`compact`）、書き直した文（0節の3） | 2節・3節 |
| `tests/test_cite_button.py`・`test_issue_anchors.py`・`test_theme_hero_assets.py`・`test_theme_typography.py` | 初期型だけの分岐を `redesign-v2` 以外に限り、最新の型は他の新デザインと同じ基準で見る | 受け皿・書体・件数札の形が変わった |
| `tests/test_bukatsu_redesign_v2.py` の `test_posts_not_reused_from_current_page` | 公開ページが最新の型になった後は skip（切替前に初期型のページに対して確認済み） | 比べる相手（初期型のページ）が無くなる |

既存の `tests/test_bukatsu_redesign.py`・`test_bukatsu_layout.py`（初期型向け）は **消さず、skip もしていない**。初期型の生成器は「公開が 10/17 以降になった場合」と「最新の型を戻すとき」の経路として残るので、
その経路が壊れていないことを確かめ続ける（どちらも設定ではなく生成器を直接呼ぶので、切替後も意味がある）。

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも `bukatsu_layout.finish` が走る（これまでと同じ）。最新の型の照合が合わないと、その回の
**公開候補生成全体が止まる**（他の新デザイン9テーマと同じ設計）。**10/17 の部活動の回で5論点に新しい意見があり追い読みしないと、adapter が止まる
（複数テーマをまとめて作る回なら全テーマが止まる）。** 部活動の adapter が立場の対応表も公開対象に含めるようになったので、部活動の回の公開物が1つ増える。

## 6. 検査結果（作業ツリー）

切替後の結果は9節。公開候補の段階（`version` 無し、docs/ は初期型のまま）：

| 検査 | 結果 |
|---|---|
| 生成器の内蔵照合（件数・理由区分・除いた明細・区分ごとの立場・資料・日付・推移の時点と件数の幅・詳細データの表・FAQ と画面） | 合格 |
| `verify_theme_page.py bukatsu-chiiki --html <候補>` | NG 0（現行ページも全10テーマ NG 0） |
| `verify_number_provenance.py` | 候補の照合関数で9領域（冒頭の件数欄・7論点・推移の注記）＋折れ線。隔離コピーで切り替えた状態で 部活動 815/815。現行ページ 10テーマ NG 0 |
| 2回生成 | md5 一致（`PYTHONHASHSEED` 0・1・999・random。最終はページ `f16fdd21…`・全文・印刷版 `f72a067f…`。9-2） |
| `--as-of 2029-04-01` | 冒頭・背景が後期（中間評価は未確認）の文に切り替わり、生成は止まらない（テストあり） |
| よみやす（`--strict`） | 完成を止める指摘 0件・PASS（平均33.5字、最長79字） |
| 使い回し（`verify_page_originality.py`、隔離コピーで切替後） | 「10ページに、使い回された見出し・文はありません」（最初は4件→3節、もう1件→直した） |
| AI臭（`verify_ai_tone.py`、隔離コピーで切替後） | 問題なし（公開ページ10本。ペルソナ検査は `configs/persona.private.json` が無く飛ばした） |
| `python3 -m unittest discover tests` | 2,352件 OK（skip 8） |
| `tests/test_bukatsu_redesign_v2.py` | 70件 OK（手順7分27件） |
| Playwright（`tests/test_bukatsu_redesign_v2_browser.cjs`） | 下に記す。すべて合格 |

操作（Playwright、Chromium、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信、投票ボタンは押していない）:
- 1280px・375px とも横はみ出し0（読書面の折りたたみ全開・背景7行・推移・詳細データを開いても0）、ページのコンソールエラー0。
- 読み込み時：URL にハッシュが付かず、画面とフォーカスは動かない。読書面と山なみの選択パネルはどちらも件数1位の「教員の働き方」。
- 山なみ：立場モードに切り替わる。山（2つ目＝制度・移行プロセス）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`、山なみの選択パネルも同じ論点。
  論点ボタン（山なみの一覧）を押すと山なみの中で切り替わり、読書面と URL も合う。
- 論点タブ7つで scrollY 不変、論点の切替・山の選択・論点ボタンで history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「次の理由」で次へ。理由が未公開の2論点は「未公開」と出る。
- 背景7行の開閉、自治体の絞り込み（「神戸」で54行→1行）。推移：開くとグラフが描かれ「論点の変化」に切り替わる。
- 旧アンカー：2節の表の主な読み替え（論点の素のID・`#heading-3`・`#fb-…`・`#{論点}--L`・`#classroom`・`#faq`・`#bukatsu-check`・`#bukatsu-background`・`#local`・`#method`・`#schedule`・`#map`・`#stance-glance` など）と、外部の埋め込みが指す推移の2タブをブラウザで確認。
- キーボード：Tab で論点名を移り Enter で選択（位置不変）、背景の行を Enter で開く、投票ボタン7つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：7論点すべて表示、図が使えないときの論点一覧・本文・推移の要約・作り方・詳細データ・背景の開閉・全文・印刷版への案内とも可、「試作」の語なし。
- 全文・印刷版：スクリプト0、7論点表示、1280/375px と印刷の見た目（`emulateMedia print`）で横はみ出し0。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 公開中のページ（初期型） | 最新の型 | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 11,169px | **12,945px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数（main） | 2,962字 | 4,744字 | — |
| うち冒頭 | — | 4,393px | — |
| 山なみ（選択パネル込み） | — | 1,787px | — |
| 推移の要約 | — | 466px | — |
| 背景（7行、閉じた状態） | — | 1,377px | — |
| 1280px のページ全体 | 7,658px | 8,175px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 教員の働き方はどうなる | 2,443px（公開中のページは 2,846px・819字） | 812字 | 1,458px |
| 制度と移行の進め方 | 2,448px | 817字 | 1,432px |
| 子どもの機会と部活動の意義 | 2,393px | 749字 | 1,458px |
| 受け皿と指導者は足りるか | 2,444px | 790字 | 1,458px |
| 費用と家庭の負担 | 2,425px | 806字 | 1,432px |
| 住む地域で差が出る | 1,932px | 550字 | 1,067px |
| その他 | 1,450px | 487字 | 874px |

7論点とも目標（2,500px以下）を満たす。ページ全体は公開中のページより約1,800px長い（冒頭の段の一覧・件数欄、推移の要約、背景7行を新たに出したため）。目標までの余裕は55pxしかない。

## 7. 公開前の残作業・判断待ち

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. **ページ全体の高さの余裕が小さい**（375pxで 12,945px、目標 13,000px）。データが増えて冒頭の件数欄や理由の行が1行ずつ増えると超える。超えたら冒頭の段の一覧を折りたたむのが一番効く。
3. **載せなかったもの**：編集部の横断整理（「論点をまたいで分かること」）、論点ごとの図解画像、比較欄、目次。他の新デザインと同じ判断。授業用の印刷画面（`bukatsu-chiiki-classroom.html`）は作り直さない
   （docs のまま。授業の設定を変えたら初期型の生成器でしか作り直せない）。
4. **投票ボタンの論点の絵文字**：初期型は外していたが、元HTMLの投票スクリプトをそのまま写すので戻った（消費税と同じ）。選択肢と送信内容は同じ。
5. **meta description**は元HTMLのまま「SNS反応1,578件」（更新経路の adapter が件数を書き換える）。変えていない。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認）。代表投稿14件の生存は 10/14 に確かめたきりで、公開切替の前には確かめ直していない。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンと実際の紙・PDF への印刷結果（印刷の見た目の画面検査だけ）。
- 他サイトに貼られた推移の埋め込みコードの実在（id は残したので、貼られていても飛び先はある）。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は新規0件相当の模擬（4-2）と、明細不足で止まる単体テストだけ。初期型の経路で新規の意見がある回を最後まで通す模擬もしていない（4-3）。

## 9. 2026-10-14 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/bukatsu-layout.json` | `"version": "redesign-v2"` を足した（`enabled` は前から true） |
| `docs/bukatsu-chiiki-reaction-map.html`・`docs/bukatsu-chiiki-full.html` | 最新の型（`python3 scripts/build_bukatsu_arena.py` の rebuild で作り直し。公開候補とバイト一致、md5 ページ `f16fdd21…`・全文・印刷版 `f72a067f…`） |
| `data/page-sources/bukatsu-chiiki.html` | 変更なし（旧形式の元HTMLのまま。rebuild の旧形式の生成を掛けてもバイト不変で、新しい作りで読めることを確かめた） |
| `configs/bukatsu-chiiki-reading.json` | 全文・印刷版で推移の注記と背景の前置きが並び、同じ文末「ます」が3つ続いたので、注記の2文目の文末を直した |
| `company/APPROVALS.yaml` | 末尾に `approval-20261014-bukatsu-chiiki-v2`（`status: pending`、`decided_at: null`）。既存の記録は動かしていない |
| `themes/bukatsu-chiiki.md` | 作業記録 |
| `docs/bukatsu-chiiki-classroom.html`・論点の図解画像 | 変更なし（7節の3） |

### 9-2. 切替後の検査（作業ツリー）

| 検査 | 結果 |
|---|---|
| `verify_theme_page.py`（全テーマ） | 全10テーマ NG 0 |
| `verify_number_provenance.py` | 部活動 815/815、10テーマ NG 0 |
| `verify_top_page.py` | 終了0 |
| `build_bukatsu_arena.py --check` | OK（公開後の経路＝元HTMLに旧形式の生成を掛けてから新ページを作り直して比較。元HTMLはバイト不変） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（他テーマの既存の指摘で終了1。部活動の指摘は無い） |
| `seo/validate_theme_seo.py` | OK（themes=10） |
| `python3 -m unittest discover tests` | 2,352件 OK（skip 9。増えた1件は `test_posts_not_reused_from_current_page`。5節） |
| `run_public_checks.py` | 終了0 |
| よみやす（`--strict`、ページ・全文・印刷版・読書面の試作） | 3つとも完成を止める指摘 0件・PASS（平均33.5字、最長79字） |
| 使い回し（`verify_page_originality.py`） | 「10ページに、使い回された見出し・文はありません」 |
| AI臭（`verify_ai_tone.py`） | 問題なし（公開ページ10本。ペルソナ検査は飛ばした） |
| 採用台帳（`build_adoption_registry.py --check`）・`build_data_sheet.py --check` | 一致・最新 |
| Playwright（docs/ を配信して `tests/test_bukatsu_redesign_v2_browser.cjs`） | すべて合格（6節の項目）。確認画面は切替後のページで撮り直した（`evidence/` 23枚） |
| 2回生成 | md5 一致（`PYTHONHASHSEED` 0・7、docs のページとも一致） |
