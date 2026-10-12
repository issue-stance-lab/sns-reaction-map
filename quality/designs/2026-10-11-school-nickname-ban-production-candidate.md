# 学校でのあだ名禁止（school-nickname-ban）新デザインの公開候補と検査（手順7）

2026-10-13。ブランチ `task/renew-school-nickname-ban`。手順書23の「7. 更新と公開を検査する」。
高齢者免許返納の [2026-10-11-elderly-license-revocation-production-candidate.md](2026-10-11-elderly-license-revocation-production-candidate.md)
（対話式の山なみを元HTMLから写す＋部活動型の圧縮）をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/nickname-layout.json` を `enabled: true` にして docs/ に適用した（オーナーの承認待ち）。

公開候補: `quality/prototypes/school-nickname-ban-release/school-nickname-ban-reaction-map.html`（基準日＝公開JSONの更新日 2026-09-20）
確認画面: `quality/prototypes/school-nickname-ban-release/evidence/`（PC・375px の全体、冒頭、相談の電話番号、山なみ、立場モード切替、山を押して読書面へ、
読書面、理由を開いた画面、背景を開いた画面、前の収集回との比較を開いた画面、X遮断時、JSなし）

## 0. 手順7の前に直したこと（コミット 2f722851）

| 項目 | 処理 |
|---|---|
| 1. よみやすの残り7件 | 公開JSON由来の文を、数字・出典・判定を変えずに文体だけ直した。重なる心配 `vein-safety` の `diverging_reason`（「ます」3連続。3論点に出るので3件）、照合 `unwanted-name` の `finding`（正本は `scripts/build_nickname_process_sections.py` の FACT_CHECKS `note`。2論点で2件）、資料にしかない話 `sc-4` の `life_impact`（105字）と `sns_note`（114字）。`build_public_registry.py --topic school-nickname-ban` で公開JSON・catalog を、`build_adoption_registry.py` で採用台帳の指紋を作り直した。元HTML（当時の docs）の旧形式の部分も `refresh_planet_section.py --for-docs` → `build_nickname_arena.py` で作り直した（文の差し替えだけ。13行）。`verify_number_provenance.py school-nickname-ban` NG 0、`verify_ocean_layer.py` は直す前と出力が完全に同じ（他テーマとあだ名禁止の既存の指摘で終了1）。読書面の試作のよみやす `--strict` は完成を止める指摘 7件→0件 |
| 2. 相談窓口 | 24時間こどもSOSダイヤル（0120-0-78310）を冒頭の「今、嫌な呼び方でつらい場合」にも出した（司令塔の決定）。番号は冒頭の設定 `safety.phone` の1か所に移し、背景の相談先の行（`body_help`）もそこから読む。冒頭の文は「言いにくいときは、24時間いつでも電話で相談できます。」と短くし、背景の行へのリンクは「SNSや地元の相談窓口を見る」にした |

### 申し送り（読書面の設計記録10節）の処理

| 申し送り | 処理 |
|---|---|
| 1. 山なみ | 元HTMLの `#planet-block` を写して論点タブの上に置いた（2節・3節）。冒頭の「6つの論点を山なみで比べる」の飛び先ができた |
| 2. 推移 | 潮目のカードを「2回の収集の比較」の折りたたみに写し、各論点の「前の回との違い」に小さな折れ線と数字2つを入れた。「さん付け・ジェンダー配慮」は潮目の論点に無いので数字が出ない（テストで確認） |
| 3. よみやす7件 | 0節 |
| 4. FAQ | 構造化データは画面の6問（冒頭の短答2問＋背景の4問）から作り直した。元HTMLの SCHOOL_NICKNAME_FAQ_JSONLD（旧FAQ10問）は使わない。`school_nickname_connected_content.py` の `FAQS` は旧ページ（元HTML）だけが使うので、新デザインでは冒頭の設定が正。二重管理の解消（`FAQS` を冒頭の設定から読む）は旧ページを生成し続ける間は手を付けていない |
| 5. 編集部の横断整理 | 文中に件数が直書きなので新ページには載せない（山なみから `#editorial` を外した。高齢者と同じ） |
| 6. 10/18 の追い読み | DATA_REFRESH.md に書いた。立場の対応表は更新経路の adapter が作り直すようにした（4節） |
| 7. 背景台帳の年表・checklist | 台帳は旧ページと共有なので変えていない。設定の `extra`・`checks` はそのまま |
| 8. 代表投稿の生存 | 2026-10-13 に cdn.syndication.twimg.com で11件とも本文が返ることを確かめた（`__typename: Tweet`） |
| 9. 冒頭の試作単独のリンク | 公開ページでは「よくある質問を読む」「SNSや地元の相談窓口を見る」とも背景の行へ飛び、行が開く（ブラウザで確認） |

## 1. 仕組み（高齢者免許返納と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_nickname_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`nickname_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力と新デザインのページの再入力は拒否 |
| `scripts/nickname_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/school-nickname-ban.html`）/ `materialize` / `finish` / `rebuild`（公開後に `build_nickname_arena.py` を単独で動かしたとき。元HTMLに旧形式の生成（山なみの件数・連動表示・アリーナの点）と公開JSONの集計を掛けてから新デザインを組む。アリーナの点のファイルも作り直す） |
| `configs/nickname-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/nickname_redesign/planet.js`（新規） | 山なみの橋渡し（高齢者と同じ。入口は `window.NicknameReading.select`） |
| `scripts/nickname_redesign/production.css`（新規） | 引き継ぐ部品を冒頭の配色（黒板の緑・チョークの黄・方眼ノートの紙）に合わせる。立場は4つなので立場ボタンは5つ（スマートフォンでは「すべて」を1行、4立場を2列）。投票ボタンは元HTMLの投票スクリプトが作る中身（論点＝絵文字・名前と件数、立場＝名前・説明）に合わせた |
| `scripts/nickname_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・立場の対応表・設定から数え直して照合（`verify_number_provenance.py` から呼ぶ。旧ページでは空を返す）。冒頭の件数欄、6論点の欄 |

ページの並び：共通ヘッダー → 冒頭（パンくず・題名・短答2問・止める呼び方の範囲の表・SNSの意見の件数・今つらい場合（電話番号）・リンク2つ・出典）→
論点ごとに読む（見出し → **対話式の山なみ**（立場モード・山・論点ボタン・選択パネルと100マス・見かた・調査条件）→ 論点タブ → 選んだ論点の欄）→
2回の収集の比較（要約＋折りたたみ）→ 投票 → 背景の開閉行9行 → 作り方と調査上の注意（折りたたみ1つ）→ 次に読むテーマ → フッター。

時制：期限付きの制度イベントは無いので段階の切り替えは無い。「◯月◯日時点」は冒頭の設定 `checked_on`（2026-10-13）1か所から出る。同じデータなら同じページになる。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 文字どおり複写 | 継承（OGP画像も同じ） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 旧FAQ10問（SCHOOL_NICKNAME_FAQ_JSONLD） | 冒頭の短答2問（問いと1文の答え）＋背景「よくある質問」4問＝6問から作り直し | 画面と構造化データの一致をテストで確認。旧の10問は画面に無いので使わない |
| GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ複写。preview には載せない | 継承 |
| AdSense（ca-pub-2542211932832864） | ADSENSE_TAG 区間と `google-adsense-account` meta | 区間は release だけ、meta は両方 | 継承 |
| 共通CSS/JS | site-tokens・topic-modern・school-nickname-connected（css/js/page.js）・theme-design | site-tokens・topic-modern（v=32、JS v=13）だけ | 検索入口・連動表示・テーマ共通の見た目は意図的に外した |
| 投票（Supabase） | topic `school-nickname-ban-issue-stance-v1`、論点6×立場3＝18、`choiceIdx:issueIndex*stances.length+stanceIndex`、保存キー `nickname-arena-vote` | 投票節とスクリプトを複写。論点（`var issues=[…]`、件数を含む）・立場（`var stances=[…]`）は元と完全一致。保存キーは本番ホストだけ既存キー、他は `nickname-arena-vote-preview`。前置きの文も元のまま | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致（18通り）。**元のスクリプトは投票の後に、旧ページにも無い `#issue-arena-section` へ移ろうとして TypeError で止まる。この1文だけを外した**（元HTMLのこの1文が変わると生成が止まる。テストで確認） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの中に #caution（RESEARCH_CONDITIONS で囲み、`#research-conditions`）、PLANET_DATA は山なみの直後の1つだけ | 継承 |
| 共通ヘッダー・パンくず | 元HTMLは静的ヘッダーが無い（topic-modern.js が差し込む） | 高齢者と同じ静的な共通ヘッダー、冒頭のパンくず「教育・日常論争 ／ 学校でのあだ名禁止」 | JSなしでもトップへ戻れる |
| 前の収集回との比較（TIDE_CARD） | 8/17→9/20、立場・論点の2タブ、再生ボタン | 枠と CSS 区間を文字どおり複写し、要約（立場3本の小さな折れ線・カードの見出しの1文・注記）の下の折りたたみ `#cap-trend-more` へ | 継承。読書面の「回ごとの比較へ」の飛び先（設定 `trend.widget_id`）は実際の id と一致（テストで確認） |
| 作り方（ARTICLE_TRUST） | 区間 | 文字どおり複写し、調査上の注意と一緒に折りたたみ `#cap-method` へ | 継承（公開日・最終更新日の `<time>` も残る） |
| 調査上の注意（#detail-data） | 「読み方」の注意2行（表は無い） | 文字どおり複写 | 継承 |
| 次に読むテーマ・クリック計測 | `#related-topics`・`script#related-theme-tracking` | 両方文字どおり複写 | 継承 |
| フッター | footer | 文字どおり複写 | 継承 |
| 授業節 | CLASSROOM 区間（元HTML） | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| アリーナの点（`docs/school-nickname-ban-arena-data.js`） | 旧ページのアリーナが読む | 新ページは読み込まない | 更新経路（adapter・`build_nickname_arena.py`・`rebuild`）で引き続き生成され、公開対象に入ることを10/18の模擬で確認 |
| 進み具合の帯「探ったところ」 | `#progress` | 載せない（山なみのスクリプトの書き込み先だけ隠して置く） | 内容対応表2 |
| ヒーロー写真 | `images/topics/school-nickname-ban/school-nickname-hero.webp` | 載せない（冒頭の名札と国の資料3枚の図柄が役目を持つ。OGP画像は継承） | 内容対応表3 |
| 検索入口（3タブ）・立場の帯・背景パネル・確認リスト・旧FAQ | SEARCH_ENTRY・`#stance-glance`・`#bukatsu-background`・`#bukatsu-check`・SCHOOL_NICKNAME_FAQ | 載せない | 冒頭・読書面・背景に置き換え（旧アンカーは読み替え） |
| 編集部の横断整理・一次資料クイズ・予想2問 | `#editorial`・`#quiz`・`#guesses` | 整理は外し、クイズと予想は受け皿だけ隠して残す | 申し送り5 |
| 論点カード（NICKNAME_ISSUE_MEDIA） | `#issue-cards` | 載せない | 読書面の投稿の例（11件）に置き換え |
| llms.txt・sitemap | URL のみ | URL 不変 | 継承 |

### 旧アンカーの到達確認

`grep -rn "school-nickname-ban-reaction-map.html#" docs/ scripts/ configs/` の結果は**0件**。リポジトリ全体では `company/CORRECTIONS.yaml` の
`#correction-20260906`（2026-09-06 の訂正の告知）が1件。この告知の枠は 2026-09-13 にオーナーの指摘で旧ページから外れていて、現行ページでも既に飛び先が無かった。
新ページでは訂正窓口への案内がある「このページの作り方」へ読み替える（折りたたみを開く）。
外から旧アンカー付きで来た場合に備え、新ページに無い旧IDを読み替える（`ALIASES`、`location.replace`。背景の行なら開く。折りたたみの中なら外側を開く）。

| 旧ID | 読み替え先 |
|---|---|
| `#progress`・`#school-nickname-guide`・`#school-nickname-guide-title` | 冒頭 `#school-nickname-open` |
| `#school-nickname-guide-tab-national-rule`・`-panel-national-rule` | 冒頭の「本当に禁止なの？」`#nop-q-rule` |
| `#school-nickname-guide-tab-harm`・`-panel-harm` | 背景「期待と懸念：SNSで語られていること」`#bg-voices`（開く） |
| `#school-nickname-guide-tab-scope`・`-panel-scope` | 冒頭の止める呼び方の範囲の表 `#nop-scope-title` |
| `#stance-glance`（`-title`・`-buttons`・`-result`・`-result-text`） | 冒頭の件数欄 `#school-nickname-opening-count` |
| `#bukatsu-background`・`#bg-title` | 背景「なぜ、あだ名のルールが議論になるのか」`#bg-why`（開く） |
| `#bukatsu-check`・`#ck-title` | 背景「学校のルールは、どう決まり、どう見直せるのか」`#bg-school`（開く） |
| `#fallback`・`#fallback-nav`・`#quiz`・`#ocean`・`#editorial`・`#issue-cards` | 読書面 `#school-nickname-ban-reading` |
| `#fb-{論点ID}`・`#extras-{論点ID}`・`#school-nickname-ban-reading-{論点ID}` | その論点の欄（選んだ状態になる） |
| 論点の素のID（`#school-nickname-ban-psychological-safety` など。旧ページの検索入口が使っていた） | 読み込み時だけ、その論点の欄（山なみの着地と読書面が同じ論点を選ぶ） |
| `#classroom-title` | 背景「授業や話し合いで使う」`#bg-classroom`（開く） |
| `#school-nickname-faq-title` | 背景「よくある質問」`#school-nickname-faq`（旧ページのFAQの節と同じid。開く） |
| `#correction-20260906` | 「このページの作り方」`#article-trust-title`（折りたたみを開く） |

そのまま残るID：`vote-section`・`detail-data`・`related-topics`・`caution`・`planet-block`・`planet-data`・`school-nickname-ban-tide-widget`・
`article-trust-title`・`school-nickname-faq`・`issue-{論点ID}`。
**到達できなくなった旧アンカーは無い**。読み替え先が無いのは JS・CSS の内部用ID（`school-nickname-reason-count-…`・`school-nickname-check-note-…`・
`school-nickname-source-…`・`explainer-modal`・`school-nickname-connected-data`・`pbar` など）だけ。JSなしのときは読み替えが働かず、ページ先頭に表示される。
`#fb-…`・`#issue-…`・論点の素のIDで来ると、山なみの着地がハッシュを論点の素のIDに書き直す（旧ページと同じ動き。読書面はその論点を選ぶ）。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_nickname_redesign.py --mode release --output-dir quality/prototypes/school-nickname-ban-release
```
成功すると `Built 1 file (release, as_of 2026-09-20); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense の読み込みなし、noindex、投票は送らない）: `--mode preview --output-dir /tmp/nickname-preview`。

組み立ての要点：
- **山なみ**：元HTMLの `PLANET_SECTION` から `section.planet-panel`・`#planet-data`・山なみのスクリプトを写し、読書面の見出しと論点タブのあいだに置く。
  外すのは JSなし用の論点別本文（`section.landing-panel`）・`#ocean`・`#editorial`。部品が1つずつ無ければ止まる。
  連動表示の橋渡し（`SCHOOL_NICKNAME_CONNECTED_BRIDGE` の `initialLand`）は、読み込み時（ハッシュが無いか `#planet-block` など）に件数最多の論点へ着地して
  `location.hash` を書く（履歴が1つ増える）。さらに旧ページの論点テンプレートが無いと同じ論点へもう一度着地する。この4行を「読書面の既定の論点
  （`data-default-issue`）を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」処理に置き換える（`AUTO_LAND`／`AUTO_LAND_OFF`）。旧ページの論点テンプレート
  （`template#school-nickname-ban-reading-…`）は写さないので、山なみの選択パネルは山なみ本来の表示（件数・立場の帯・100マス）になる
- **細い山の注記**：意見100件なので、細すぎて押せない山を広げた注記が出る。すべて＝本人意思・柔軟運用、禁止支持・条件付き＝なし（強い表現0%の点の案内だけ）、
  一律禁止に反対＝いじめ・心理的安全と学校運用・現場体験、中立・情報＝一律禁止の実効性とさん付け・ジェンダー配慮（Playwright で立場ごとに記録）
- **2回の収集の比較**：潮目のカードの `const datasets` と比べた日付（8月17日→9月20日）だけを読み、要約に立場3本の2点の折れ線、読書面の各論点に2点の折れ線と
  「8月17日 26.1% → 9月20日 61.5%」の形の数字を入れる（件数は描かない）。潮目の論点は5つ（`inject_tide_widget.py` の `issue_labels`）なので
  「さん付け・ジェンダー配慮」には数字が出ない（読書面の注記 `compact.glance_note` に母数を書いてある）。「学校運用・現場体験」は潮目の数え方では
  2回とも0.0%と出る（潮目のカードの数字のまま）
- **見出しの書き分け**：要約の見出し・注記・折りたたみの名前（`compact.trend_*`・`method_fold`）は高齢者と使い回しにならないよう書き分けた
  （使い回し検査 0件）
- **論点の欄の高さ**：最初は「一律に禁止して、効果はあるのか」が375pxで 2,513px になった。理由の区分の前置きの2文（`reasons_common.lead`・`note`）を短くし、2,488px にした

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理 → 最後に `nickname_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/nickname.py` は `source_for_refresh` を入力にする。山なみの件数・連動表示・アリーナの点（`build_nickname_arena.py`）・潮目（`_apply_tide`）は
  元HTMLから作った候補に掛かる。**立場の対応表（`data/school-nickname-ban_reread-stances.json`）は、自転車と同じく累積候補と再読データから作り直して公開対象に含める**
  （`build_reread_stances`。2回作って一致を確かめる）。新しい意見が再読データの明細に無いと「追い読みが要ります」で止まる（テストで確認）。
- 新デザインの照合が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。
- **模擬（切替後の作業ツリーのスクラッチ複製、完了記録の検査だけ外した）**:
  - **10/18 の新規0件相当の回**: 実際の定期更新では新規0件なら公開候補を作らず予定日だけ進む。ここでは、より多くの経路を通すため、前回（9/20）の回と同じ投稿を
    10/18 の回として置き、正典をそのまま累積候補にして **adapter の `build`（元HTMLから候補ページ・潮目・アリーナの点・立場の対応表を2回作って一致）→
    `prepare_public_candidate_bundle`（公開JSON・finalize・SEO・授業節・他テーマの新デザイン・`nickname_layout.finish`）** を通した。**最後まで通った**。
    候補の docs/ は新デザイン（最終更新日 2026-10-18、次回の収集予定 10月28日）、元HTMLは旧形式、立場の対応表は立場の中身が同じで `made_on`・`public_updated_on` だけ 2026-10-18。
    公開対象に元HTML・アリーナの点・立場の対応表が入る。他の新デザイン8ページ（部活動・皇室・副首都・生成AI・憲法・自転車・高齢者・消費税）は変わらず。
    候補の中で `verify_theme_page.py` 全10テーマ NG 0、`verify_number_provenance.py` 10テーマ NG 0、`build_nickname_arena.py --check` OK、
    `verify_builder_rebuildability.py` 10テーマ NG 0、`validate_theme_seo.py` OK、よみやす PASS（完成を止める指摘0）
  - 新しい意見がある回（明細が足りない回）で止まることは、`tests/test_nickname_redesign.py` の `test_count_mismatch_stops_before_writing`（finish）と
    `test_adapter_rebuilds_stance_table_and_stops_without_reread`（adapter）で確かめた
  - 候補の DATA_SHEET.md の作り直しで「副首都・部活動の意見とマップの点のずれ」が出る（隔離コピーでは他テーマの元HTMLが戻っているため。あだ名禁止の変更とは関係ない既存の動き）

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・論点×立場）、収集期間、更新日 | 公開JSON `docs/data/themes/school-nickname-ban.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの件数 | `data/school-nickname-ban_issues-reread.json`（`buckets` と明細 `items`） | **新しい意見の追い読み（人が読む）**。明細が正典の意見と合わないと生成が止まる |
| 区分ごとの立場・投稿の立場 | `data/school-nickname-ban_reread-stances.json`（post_key → 立場） | 更新経路では adapter が作り直す。経路の外では `nickname_reread_stances.py --made-on` |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件・折りたたみの名前 | `configs/school-nickname-ban-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | 公開JSON `claim_verification`（正本 `scripts/build_nickname_process_sections.py` の FACT_CHECKS）・`data/school-nickname-ban_claim_posts.json` | 主張を足すとき |
| 資料にしかない話・重なる心配 | `data/verification/school-nickname-ban-sunk-continents.json`・`-veins.json` → 公開JSON `ocean_layer` | 文を直すときは1文80字以内・同じ文末3連続なし |
| 背景（国の定め・学校の決め方・期待と懸念・なぜ・年表・FAQ・相談先・授業・未確認） | `configs/school-nickname-ban-background.json`・`data/verification/school-nickname-ban-background.json`・`configs/classroom/school-nickname-ban.json` | 一次資料の再確認時 |
| 冒頭（短答・範囲の表・件数欄・相談の電話番号）・確認日 | `configs/school-nickname-ban-opening.json`（`checked_on`・`safety.phone`） | 制度を確かめ直したら `checked_on` |
| 山なみ（PLANET_DATA・100マス・論点の一覧・見かた・調査条件） | 元HTMLの PLANET_SECTION（`build_nickname_arena.py` の山なみの件数・連動表示の橋渡し） | 自動 |
| 2回の収集の比較 | 元HTMLの TIDE_CARD（adapter の `_apply_tide`） | 自動 |
| 公開日・次回更新予定・収集元・作り方の文 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・Article JSON-LD・GA・AdSense・投票・調査上の注意・次に読むテーマ | 元HTML（`data/page-sources/`） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の停止条件にあだ名禁止／`_copy_candidate_tree` で `materialize`／単一・複数の公開候補生成で高齢者の後に `finish` | 高齢者の分岐と並べた最小の追加 |
| `scripts/refresh_adapters/nickname.py` | 入力を `source_for_refresh(root)` に／`build_reread_stances`（累積候補から立場の対応表を作り、2回一致を確かめ、公開対象に含める） | 公開後も元HTMLから生成するため／追い読みの後に対応表の作り直しを忘れて止まる事故をなくすため（自転車と同じ） |
| `scripts/build_nickname_arena.py` | 公開ページが新デザインで、入出力・`--connected-layout` の指定が無いとき `nickname_layout.rebuild`（`--check`・`--public-counts-only` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/nickname_issue_media.py` | `--write-html` で新デザインのページには書かない（停止） | 投票節の前に旧形式の節を差し込む事故を防ぐ |
| `scripts/verify_number_provenance.py` | あだ名禁止に `nickname_redesign_provenance` を登録（旧ページでは空を返す） | 新デザインの理由区分などの件数を照合するため |
| `scripts/inject_tide_widget.py` | コメントのみ（新デザインのページは既に SKIP） | — |
| `scripts/refresh_planet_section.py` | あだ名禁止の新デザインも停止 | 他の新デザインと同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped） | 単独実行で旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | あだ名禁止の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐をあだ名禁止にも | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/nickname_opening.py`・`nickname_background.py` | 冒頭の相談の電話番号（`safety.phone`）／背景の相談先の番号を冒頭の設定から読む | 0節2 |
| 切替時の共有テスト | 9-3 | — |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後にあだ名禁止の `finish` が走る。あだ名禁止の照合が合わないと、その回の
**公開候補生成全体が止まる**（皇室・副首都・生成AI・憲法・自転車・高齢者と同じ設計）。**10/18 のあだ名禁止の回で新しい意見を追い読みしないと、adapter が止まる
（複数テーマをまとめて作る回なら全テーマが止まる）。** あだ名禁止の adapter が立場の対応表も公開対象に含めるようになったので、
あだ名禁止の回の公開物が1つ増える。単独スクリプトは：`nickname_issue_media.py --write-html` は停止、`apply_classroom_section.py`・`apply_theme_trust.py`・
`apply_theme_design.py`・`inject_tide_widget.py` は新ページを飛ばす、`refresh_planet_section.py` は停止、`build_nickname_arena.py` は元HTMLから作り直す
（`--check` で「OK: 差分なし」）。

## 6. 検査結果（作業ツリー）

| 検査 | 公開候補（enabled=false） | 切替後（9節） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付・潮目の日付） | 合格 | 合格 |
| `verify_theme_page.py school-nickname-ban`（候補は `--html`） | NG 0 | NG 0、全10テーマ NG 0 |
| `verify_number_provenance.py` | NG 0（現行ページ 51/51。候補は `nickname_redesign_provenance` で7領域を照合） | あだ名禁止 289/289・10テーマ NG 0 |
| `verify_top_page.py` | 終了0 | 終了0 |
| `build_nickname_arena.py --check` | OK: 差分なし | OK: 差分なし（公開後の経路＝元HTMLと新ページ・アリーナの点を作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 | 10テーマ NG 0 |
| `verify_ocean_layer.py` | 直す前と出力が完全に同じ（既存の指摘。終了1） | 同じ |
| `python3 -m unittest discover tests` | 2,132件 OK（skip 4） | 2,132件 OK（skip 4。共有テストを直す前は失敗3・エラー3） |
| `run_public_checks.py` | 終了0 | 終了0 |
| `tests/test_nickname_redesign.py` | 70件 OK（手順7分29件：同じ入力で同じ出力・docs出力と新ページ再入力の拒否・保護対象・GA/AdSense・投票定義・adapter の指紋・FAQ と画面の一致・継承部品・調査上の注意・潮目の継承と折りたたみ・論点ごとの折れ線と飛び先・作り方の折りたたみ・初期状態・「少数」の印・「その他」0件で出さない・授業節・相談の電話番号・旧アンカー（サイト内リンクを含む）・山なみの写し・元HTMLの更新への追随と自動着地／投票の移動の変化で停止・旧部品なし・出所検査の改ざん検知3種、レイアウト8件：無効時・状態の一貫・元HTML無し・往復・照合不一致で書かない・adapter の対応表の作り直しと追い読み不足で停止・更新経路の配線） | 同じ |
| 2回生成 | md5 一致（`0119b753…`、`PYTHONHASHSEED` 0・1・999・random） | docs のページとも一致 |
| よみやす（`--strict`） | 候補 60/100・完成を止める指摘 0件・PASS（平均35.4字、最長75字） | 同じ |
| 使い回し（`verify_page_originality.py`、切替後） | — | 「10ページに、使い回された見出し・文はありません」 |
| AI臭（`verify_ai_tone.py`、切替後） | — | 問題なし（公開ページ10本） |
| `seo/validate_theme_seo.py` | — | OK（themes=10。H1 が変わるので `display_headline` を足した） |
| 代表投稿の生存（cdn.syndication.twimg.com） | 11件とも本文あり（2026-10-13） | — |

操作（Playwright、`tests/test_nickname_redesign_browser.cjs`、x.com・platform.twitter.com・twimg.com を遮断、docs/ の写しを 127.0.0.1 で配信）:
- 1280px・375px とも横はみ出し0（scrollWidth＝画面幅。読書面の折りたたみ全開・背景9行・比較・調査上の注意を開いても0）、ページのコンソールエラー0。
- 冒頭の「今、嫌な呼び方でつらい場合」に電話番号が見える（両方の幅）。
- 山なみ：立場モード（3つ目）に切り替わる。山（3つ目）を押すと読書面がその論点に切り替わり、欄の上端が画面上部・見出しにフォーカス・URL `#issue-…`。
- 読み込み時：URL にハッシュが付かず、山なみの選択パネルと読書面はどちらも「一律禁止の実効性」（読書面の表示名「一律に禁止して、効果はあるのか」）。
- 論点タブ6つで scrollY 不変、論点の切替で history.length 不変・「戻る」で前のページへ。理由の行で説明が1つだけ・「この論点の別の理由」で次へ。
- 前の収集回との比較：開くとグラフが描かれ「論点の変化」に切り替わる。読書面の「回ごとの比較へ」で折りたたみが開き論点の変化になる。
- 旧アンカー：2節の表の主な読み替えをブラウザで確認（`#fb-…`・`#school-nickname-ban-reading-…`・論点の素のID・`#bukatsu-background`・`#bukatsu-check`・
  `#school-nickname-guide`・`-tab-national-rule`・`-panel-harm`・`#stance-glance`・`#classroom-title`・`#school-nickname-faq`・`#correction-20260906`・`#issue-…`・`#fr-r-…`・潮目のカード・`#detail-data`）。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン6つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：6論点すべて表示、図が使えないときの論点一覧・電話番号・「少数」の印・比較の要約・作り方・調査上の注意・背景の開閉とも可。
- 投票ボタンは押していない（POST していない）。

### 375px の計測（Playwright・Chromium、表示中の文字数は `checkVisibility()` が真で閉じた `<details>` の中でない文字）

| | 現行ページ（元HTML） | 新デザイン | 目標 |
|---|---|---|---|
| ページ全体の高さ（初期表示） | 14,704px | **11,788px** | 13,000px以下 ✓ |
| ページ全体の表示中の文字数（main） | 4,999字 | 4,437字 | — |
| うち冒頭 | — | 3,546px | — |
| 山なみ（選択パネル込み） | — | 1,548px | — |
| 1280px のページ全体 | 9,163px | 7,666px | — |

| 論点の欄（`.fr-panel[data-selected]`） | 375px 高さ | 表示文字 | 1280px 高さ |
|---|---|---|---|
| 一律に禁止して、効果はあるのか | 2,488px | 849字 | 1,281px |
| 嫌な呼び名と、いじめ | 2,423px | 831字 | 1,334px |
| あだ名の親しさを残したい | 2,102px | 701字 | 1,204px |
| 学校での運用と体験 | 2,214px | 780字 | 1,228px |
| さん付けと、性別の呼び分け（少数） | 2,035px | 722字 | 1,142px |
| 本人の希望と、悪意の有無（少数） | 1,962px | 701字 | 1,148px |

論点の欄は6論点とも目標（2,500px以下）を満たす。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. 山なみの山の色は、「すべて」のとき元HTMLの山なみのスクリプトが決める青（`#075ef2`）のまま。冒頭の配色（黒板の緑）と合わないが、写した部品の色は変えない方針なので変えていない。
3. title・description（「なぜ？さん付け・いじめとの関係と賛否」）は保護対象として変えていない。H1 は新デザインの見出しに変わる（`display_headline`）。
4. 申し送り4の後半（`school_nickname_connected_content.py` の `FAQS` と冒頭の設定の二重管理）：旧ページ（元HTML）を生成し続ける間は残る。新ページは冒頭の設定だけを使う。
5. 申し送り5（編集部の横断整理）：差し込み式にするのは別作業。
6. 山なみの選択パネルの見出しと論点ボタンは、元HTMLのとおり分類名（「一律禁止の実効性」）を出す（読書面の見出しは言い換えた表示名）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）、`related_theme_click` の送信。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。11件の投稿が残っていることは 10/13 に確認済み）。
- 実機（iPhone Safari など）。Playwright の Chromium だけ。スクリーンリーダーの読み上げ。印刷ボタンの結果。電話番号のリンクを押したときの端末の動き。
- 実際の新しい収集回（新規の意見あり）を adapter に通した結果。今回は新規0件相当の模擬と、明細不足で止まる単体テストだけ。

## 9. 2026-10-13 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/nickname-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | school-nickname-ban に `display_headline`（新しい H1 の文字列そのまま） |
| `data/page-sources/school-nickname-ban.html`（新規） | 旧形式の元HTML（切替直前の docs/ のページとバイト一致） |
| `docs/school-nickname-ban-reaction-map.html` | 新デザイン（`nickname_layout.finish`。公開候補とバイト一致、md5 `0119b753…`） |
| `company/APPROVALS.yaml` | 末尾に `approval-20261013-school-nickname-ban`（`status: pending`、`decided_at: null`）。既存の記録は動かしていない |
| `DATA_REFRESH.md` | 「学校でのあだ名禁止の定期更新（新デザインを維持する、2026-10-13〜）」の節と、旧「人が読む工程なし」の節への注記 |
| `themes/school-nickname-ban.md` | 作業記録 |
| 共有テスト | 9-3 |

DATA_SHEET.md は作り直しても差分なし（全テーマで意見＝論点＝賛否＝マップの点）。

### 9-2. 切替後の検査（作業ツリー）

6節の「切替後」の列。切替後の docs/ のページは公開候補とバイト一致なので、Playwright の確認画面（`evidence/`）は切替後のページにもそのまま当てはまる。
単独スクリプトは複製で確かめた：`nickname_issue_media.py --write-html` と `refresh_planet_section.py --for-docs` は停止、`inject_tide_widget.py`・`apply_classroom_section.py`・
`apply_theme_trust.py`・`apply_theme_design.py`・`build_nickname_arena.py`（`--public-counts-only` を含む）・`sync_issue_counts.py` を流しても新デザインのページ・元HTML・
アリーナの点はバイト不変。

### 9-3. 切替に合わせて直した共有テスト

切替直後の全テストは失敗3・エラー3（2,124件中）。高齢者の切替（同じ記録の9-3）と同じ直し方で、検査の基準は緩めていない。

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_nickname_adapter.py`・`test_nickname_public_counts.py`・`test_school_nickname_connected.py` | 読むページを「公開後は元HTML（`source_for_refresh`）」に（adapter の公開先の照合だけは docs/ のパスのまま） | 旧形式のアリーナ・山なみの件数・連動表示の検査。公開後も元HTMLに同じ構造で残る（高齢者と同じ扱い） |
| `tests/test_cite_button.py` | あだ名禁止の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | あだ名禁止の新デザインを飛ばす | 共通の見た目を掛けない設計 |

`tests/test_school_nickname_connected_browser.cjs`（旧ページの連動表示のブラウザ検査。unittest には入らない）は docs/ のページを開く作りのままで、切替後は走らせていない。
