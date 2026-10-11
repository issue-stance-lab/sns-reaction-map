# 副首都（fukushuto）新デザインの公開候補と検査（手順7）

2026-10-11。ブランチ `task/renew-fukushuto`。手順書23の「7. 更新と公開を検査する」。皇室典範改正の
[2026-10-11-koshitsu-tenpakai-production-candidate.md](2026-10-11-koshitsu-tenpakai-production-candidate.md) の型をそのまま踏襲した。
**main への統合・push・投票の送信（POST）はしていない。** 手順7の公開候補と検査のあと、同じ日の公開切替（9節）で
`configs/fukushuto-layout.json` を `enabled: true` にして docs/ に適用した。

公開候補: `quality/prototypes/fukushuto-release/fukushuto-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-10）
確認画面: `quality/prototypes/fukushuto-release/evidence/`（PC・375px・論点選択・背景を開いた画面・X遮断時・JSなし）

## 1. 仕組み（皇室 `koshitsu_layout.py` と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_fukushuto_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`fukushuto_opening/reading/background.py`）を呼び、元HTMLの保護対象を文字どおり継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力は拒否。新デザインのページを入力に渡すと拒否 |
| `scripts/fukushuto_layout.py`（新規） | `enabled` / `source_for_refresh`（公開後は `data/page-sources/fukushuto.html`）/ `materialize`（隔離コピーで元HTMLを docs/ に戻す）/ `finish`（全生成の最後に元HTMLを保存し、新デザインを docs/ に書く）/ `rebuild`（公開後に `build_fukushuto_arena.py` を単独で動かしたとき用） |
| `configs/fukushuto-layout.json`（新規） | 公開候補の段階は `enabled: false`。公開切替で true |
| `scripts/fukushuto_redesign/production.css`（新規） | 共通ヘッダー・投票・作り方・詳細データ・次に読むテーマ・フッターを藍と朱の配色に合わせる追加分（冒頭・読書面の CSS は変えない） |
| `scripts/fukushuto_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・設定から数え直して照合（`fukushuto_count_provenance.py` 経由で `verify_number_provenance.py` から呼ぶ） |

時制：静的HTMLは公開JSONの更新日（`--as-of` で上書き）で段階を決める。読む日が意見募集の締切（10/16）・施行予定日（10/30）を
過ぎたら、冒頭の路線図の2行と「いつ決まる？」の答えだけを JavaScript が次の段階の文に切り替える（皇室の施行札と同じ考え方）。
生成日に依存しないので、同じデータなら同じページになる（`build_fukushuto_arena.py --check` が日をまたいでも崩れない）。

## 2. 保護対象の一覧と継承結果

棚卸し記録（`2026-10-11-fukushuto-renewal-inventory.md` 2-1・2-5節）と内容対応表で「手順7」とした部品。

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| H1 title | 「副首都はいつ・どこに決まる？大阪の指定状況と法案の問題点｜SNS反応まっぷ」 | 同じ | 継承 |
| H1 SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 区間を文字どおり複写 | 継承（テストで一致確認） |
| H2 Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| H3 FAQ JSON-LD | `fukushuto_search_entry.py` の6問 | 背景「よくある質問（4問）」から作り直し（6問版は載せない） | 画面と構造化データの一致をテストで確認。時制も画面と同じ |
| H4 GA4（G-K10S4YCZFH） | GA_TAG 区間 | release だけ文字どおり複写。preview には載せない | 継承 |
| H4 AdSense タグ・`google-adsense-account` meta | ADSENSE_TAG 区間・meta | release だけ複写（meta は両方） | 継承 |
| H4 共通CSS/JS | site-tokens・topic-modern・theme-design・connected・search-entry | site-tokens・topic-modern（v=32/13）だけ | theme-design・connected・search-entry は意図的に外した（独自の見た目） |
| D3 Supabase 投票 | topic `fukushuto-issue-stance-v1`、論点7×立場3＝21、`V2I`、`choiceIdx:issueIdx*STANCES.length+stanceIdx` | 投票節とスクリプトを複写。VOTE_ISSUES・V2I・STANCES は元と完全一致。保存キーは本番ホストだけ既存キー、他は `sns_vote_preview_` | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順。adapter の `vote_fingerprint` も元と一致 |
| 投票の参加者数・やり直し・シェア | topic-modern.js・投票スクリプト | 同じ | 継承（山なみの投票マーカーは描く先が無いので呼ばれない。関数の有無を確かめてから呼ぶ元のコードのまま） |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの注記の下に #caution（RESEARCH_CONDITIONS で囲む）、末尾に PLANET_DATA | 継承（公開検査が読む契約） |
| T2 共通ヘッダー・パンくず | topic-modern.js が差し込むヘッダー・`top-nav` | 静的ヘッダー（JSなしでもトップへ戻れる）、冒頭の crumb | 継承 |
| D5 作り方（編集・分析情報） | ARTICLE_TRUST 区間 | 背景の後に区間を文字どおり複写 | 継承（公開日・最終更新日の `<time>` も残る） |
| D6 詳細データ | `#detail-data` | 文字どおり複写（枠の class だけ足す） | 継承（「投票の選択とアリーナ上の位置」の行は旧デザインの説明のまま。7節） |
| D7 次に読むテーマ | `#related-topics` | 文字どおり複写 | 継承 |
| D8 フッター（運営者情報・訂正窓口・プライバシー・免責） | footer | 文字どおり複写 | 継承 |
| D4 授業節（印刷ボタン・GA4計測） | CLASSROOM 区間 | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ CLASSROOM マーカーで囲む | 継承。`apply_classroom_section.py` は新デザインで skipped |
| T1 進捗表示 | 「探ったところ 0／18」（`isa-seen-fukushuto`） | 載せない。保存値は消さない | 継承しない（内容対応表どおり。皇室も同じ） |
| B5 編集部の横断整理 | `#editorial`（2026-10-03 時点の手入力の％） | 載せない | 継承しない（文中の数字が10/3時点のまま。更新の仕組みができるまで外す。旧アンカーは読書面へ） |
| B7 推移（潮目） | TIDE_CARD | 載せない。元HTMLでは adapter が引き続き更新 | 継承しない（内容対応表どおり。入力が非公開、読書面に「推移はまだ公開データに無い」と明記） |
| 既存アンカー | 外部・他ページからの `#` 付き参照は0件（下記） | `#issue-{論点ID}` は同じIDで論点欄に。旧ID 26件と論点ごとの旧ID（`fb-`・`extras-`・`fukushuto-reading-`・`fuk-entry-panel-`）は `location.replace` で新しい置き場所へ（背景の行なら開く） | 継承（Playwright で確認） |
| noscript 本文 | noscript なし | JSなしで7論点・背景・作り方・詳細データがすべて読める | 確認済み |
| llms.txt・sitemap | URL のみ参照 | URL 不変 | 継承（`validate_theme_seo.py` OK） |

旧アンカーの飛び先調べ：`grep -rn "fukushuto-reaction-map.html#" docs/ scripts/ configs/`（data・tests・themes・quality/research も）で **0件**。
外部から旧アンカー付きで来た場合に備え、現行ページの主なIDを新しい置き場所へ読み替える。新ページにそのまま残るID：
`vote-section`・`detail-data`・`related-topics`・`article-trust-title`・`caution`・`planet-data`・`issue-{論点ID}`（7）。
**到達できなくなった旧アンカーは無い**（読み替え先が無いのは、JSの内部用ID〔`vote-step1`・`pbar` など、外から指す意味の無いもの〕だけ。
JSなしのときは読み替えが働かず、ページ先頭に表示される）。

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_fukushuto_redesign.py --mode release --output-dir quality/prototypes/fukushuto-release
```
成功すると `Built 1 file (release, as_of 2026-10-10); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）:
```sh
python3 scripts/build_fukushuto_redesign.py --mode preview --output-dir /tmp/fukushuto-preview
```

公開切替（9節で実施）:
1. `configs/fukushuto-layout.json` を `enabled: true` にする。
2. 同じコミットで `configs/theme-seo.json` の fukushuto に `display_headline` を足す（H1 が変わるため）。
3. `python3 -c "import sys;sys.path.insert(0,'.');from pathlib import Path;from scripts import fukushuto_layout as l;l.finish(Path('.'))"`
   で元HTMLを `data/page-sources/` に保存し、docs/ のページを新デザインにする。

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理（adapter・潮目・finalize・SEO・
  信頼情報・授業節・テーマ共通の見た目・皇室の finish）→ 最後に `fukushuto_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/fukushuto.py` は `source_for_refresh` を入力にする。`_apply_tide` も元HTMLから作った候補に掛かる（新デザインには載せない）。
- 新デザインの照合（再読データの明細＝論点の件数、明細の立場＝公開JSON、`sns_base`＝意見数など）が合わないと `finish` は ValueError で
  止まり、元HTMLも公開ページも書き換えない（テストで確認）。締切・施行日を過ぎても止まらない（テストで確認）。
- **次回 10/19 の模擬**：切替後のスクラッチ複製で、新規0件の 10/19 回として `refresh_adapters/fukushuto.build` →
  `refresh_topic.prepare_public_candidate_bundle` を実行した（完了記録の検査だけ外した。保存回は 10/10 の分を代用）。
  公開対象65件が作られ、候補の docs/ は新デザイン（基準日 2026-10-19・意見募集は「締め切り済み」・施行は「予定」）、
  元HTMLには潮目が入ったまま。候補の中で `verify_theme_page.py fukushuto` NG 0、`verify_number_provenance.py fukushuto` 297/297（切替後の最終版で再実行）、
  よみやす「完成を止める指摘 0件」、皇室の公開ページは変わらず。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・立場別）、収集期間、更新日 | 公開JSON `docs/data/themes/fukushuto.json`（正典から `build_public_registry.py`） | 自動 |
| 理由区分・区分ごとの立場 | `data/fukushuto_5issues-reread.json`（5論点） | **新しい収集回の意見を再読して追記**（件数が論点の件数と合わないと生成が止まる） |
| 理由の言い換え・「どんな声か」・論点の説明・投稿2件の選定 | `configs/fukushuto-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合 | `build_fukushuto_process_sections.py` の FACT_CHECKS → 公開JSON `claim_verification`（投稿数は投稿IDから数え直し） | 主張を足すとき |
| 資料にしかない話 | `data/verification/fukushuto-sunk-continents.json` → 公開JSON | 再検索の記録を追記（`sns_base` が意見数と違うと止まる） |
| 制度の確認（論点内）・背景の定義・年表・未確認事項 | `data/verification/fukushuto-background.json`、一次資料メモ | 一次資料の再確認時 |
| 冒頭の短答・路線図・地図・候補地8地域・日付 | `configs/fukushuto-opening.json` | 結果公示を確かめたら `comment.result_published_on`、施行後の条文を確かめたら `law.enforcement_confirmed_on` |
| 背景の行・FAQ・授業 | `configs/fukushuto-background.json`、`configs/classroom/fukushuto.json` | 段階の文を直すとき |
| 公開日・次回更新予定・収集元 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・JSON-LD（Article）・GA・AdSense・投票・作り方・詳細データ・次に読む | 元HTML（`data/page-sources/`、公開前は docs/） | 変更しない（継承するだけ。数字は元HTML側の生成器で直る） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の新デザイン停止条件に副首都／`_copy_candidate_tree` で副首都の `materialize`／単一・複数の公開候補生成で、皇室の後に副首都の `finish` | 皇室の分岐と並べた最小の追加（計9行） |
| `scripts/refresh_adapters/fukushuto.py` | 入力を `source_for_refresh(root)` に | 公開後も元HTMLから生成し、潮目も元HTMLに掛けるため |
| `scripts/build_fukushuto_arena.py` | 公開ページが新デザインで引数なしのとき `fukushuto_layout.rebuild`（`--check` も同じ経路） | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/fukushuto_search_entry.py` | 検索入口の CSS/JS が既にあればその位置のまま版だけ合わせる | **既存の不具合**：`build_fukushuto_arena.py --check` が main でも NG だった（アセットが THEME_DESIGN の後ろへ毎回移動）。切替後の `--check` は元HTMLの再生成一致を見るので直した |
| `scripts/refresh_planet_section.py` | 副首都の新デザインも停止 | 皇室と同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped と表示） | 単独実行で授業節・作り方・H1 を旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/inject_tide_widget.py` | 単独実行で `-layout` の meta を持つページを飛ばす | 単独実行すると副首都の固定比較ファイル（7月）で新ページの `</style>` に潮目を差し込む恐れがあったため（皇室も同時に保護） |
| `scripts/verify_builder_rebuildability.py` | 副首都の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐を副首都にも（`.fr-reason-n b`・`.fr-count b`） | 表示形式が変わった照合だけの対応（基準は緩めていない） |
| `scripts/fukushuto_count_provenance.py` | 新デザインなら `fukushuto_redesign_provenance` を呼ぶ | 数字の出所検査 |
| `scripts/fukushuto_reading.py` | 論点欄の順位の文「7つの論点で」→「7つの分類で」 | 1ページの論点数の表記を「その他を除く6」に統一（皇室と同じ書き方。`verify_theme_page.py` の論点数検査） |
| 切替時（9節）の共有テスト | 9-4 を参照 | 公開後は旧形式の検査を元HTMLに向けるため |

**他テーマへの影響**：`enabled: true` の間、どのテーマの公開候補生成でも最後に副首都の `finish` が走る。副首都の照合
（再読データの件数・`sns_base` 等）が合わないと、その回の**公開候補生成全体が止まる**（皇室と同じ設計）。副首都の再読データの
追記を後回しにしないこと（DATA_REFRESH.md に記載）。

## 6. 検査結果（公開前＝作業ツリー、enabled=false）

| 検査 | 結果 |
|---|---|
| 生成器の内蔵照合（件数・理由区分・区分ごとの立場・資料・日付） | 合格 |
| `verify_theme_page.py`（候補は `--html`） | 候補 NG 0、全10テーマ NG 0 |
| `verify_number_provenance.py` | 10テーマ NG 0（現行ページ 241/241。新ページは切替後 297/297） |
| `verify_top_page.py` | 終了0 |
| `build_fukushuto_arena.py --check` | OK（直す前は main でも NG。5節） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `run_public_checks.py` | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） |
| 全テスト `python3 -m unittest discover -s tests` | 1,777件 OK（skip 4）。開始時の1,758件では失敗7・エラー4（すべて自転車青切符。作業ツリーの非公開正典が古かった。共有ツリーと `rsync -anc` で比べ、自転車の4ファイルを共有ツリー→作業ツリーへコピーして解消） |
| `tests/test_fukushuto_redesign.py` | 46件合格（手順7分19件：保護対象・投票定義・FAQ・docs出力拒否・新デザイン再入力拒否・materialize/finish の往復・2回生成の一致・照合不一致で書かない・締切/施行後も止まらない・数字の照合の改ざん検知 ほか） |
| 2回生成 | md5 一致（`PYTHONHASHSEED` を変えた3回も一致。最初は FAQ 時制の辞書の並びが実行ごとに変わり不一致→修正） |
| `--as-of 2026-10-17` / `2026-10-31` | 生成は止まらず、冒頭・背景が「締め切り済み・施行前」／「締め切り済み・施行日を過ぎた（未確認）」に切り替わる |
| よみやす（候補） | 「完成を止める指摘 0件」判定 PASS（直す前 17件） |
| `verify_ocean_layer.py` | 副首都は指摘なし（全体の終了コードは school-nickname-ban・constitutional-amendment の既存の指摘で1。変更前の HEAD でも同じ） |

投票：本番 Origin（https://sns-reaction-map.jp）から GET `cast-vote?topic_id=fukushuto-issue-stance-v1` → HTTP 200、CORS 一致、
既存 counts（2票、choice 0 と 5）を取得。POST はしていない。

操作（Playwright、`tests/test_fukushuto_redesign_browser.cjs`、x.com・platform.twitter.com・twimg を遮断）:
- 1280px・375px とも横はみ出し0、コンソールエラー0。論点7つと山を押しても scrollY 不変。背景8行の開閉、詳細データを開いても横はみ出し0。
- 戻る：論点を7回切り替えても history.length 不変、「戻る」で前のページ（index.html）へ。
- 旧アンカー：`#fb-fukushuto-finance` は論点、`#fukushuto-faq` はよくある質問を開く、`#bukatsu-background` は背景へ。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、投票ボタン7つにフォーカス可。
- X埋め込みを遮断：「表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- 読む日：10/12・10/17・10/31 に時計を合わせると、路線図と「いつ決まる？」が意見募集中→締切済み→施行日を過ぎた（未確認）に切り替わる。
- JSなし：7論点すべて表示、作り方・詳細データ・背景も読める。

### よみやすの直し（入力データの文 15文・17件）

意味・数字・日付・検索語・判定は変えず、文を区切るか読点を減らしただけ。

| 場所 | 直し方 |
|---|---|
| `fukushuto-sunk-continents.json` sc-1（東成区）`life_impact` | 128字の1文を3文に（「確定している。ただし…上回っていた。2020年は…転じた。」） |
| 同 sc-1 `sns_note` | 括弧内の再検索の記録を「再実行した。新規ヒットは無かった。」の2文に |
| 同 sc-2（代替地域）`life_impact` | 95字を「除かれる。そのため…」の2文に |
| 同 sc-2 `sns_note` | 106字を3文に、括弧内の記録を2文に |
| 同 sc-3（推進局予算）`life_impact` | 132字を3文に（「見える。しかし内訳では…占める。…とどまる。」） |
| 同 sc-3 `sns_note` | 括弧を外して「2026-09-25に、…確認した。」、「批判だった。…には触れていない。」の2文に |
| 同 sc-4（2016年代表質問）`life_impact` | 2文（97字・91字＋読点4）を4文に。発議者の情報は同じ |
| 同 sc-4 `sns_note` | 括弧内の記録を独立させ、「別の文脈での使用だった。…などである。…0件。」に。末尾の 10/10 記録を「検索した。一致は0件。」に |
| `fukushuto-background.json` `cause[1]` | 読点4→3（「…は、同じ判断ではありません」→「…は別の判断です」） |
| 同 `checklist.items[1].found` | 読点4を「指定には要件を満たす必要があります。要件は…に関するものです。」の2文に |
| `build_fukushuto_process_sections.py` FACT_CHECKS（整備費4〜7.5兆円）`note` | 81字を「実在する。ただし…」の2文に |

確かめ方：直したあと `build_public_registry.py --topic fukushuto`・`build_fukushuto_process_sections.py`・`build_fukushuto_arena.py`・
`build_adoption_registry.py` を実行し、`verify_number_provenance.py fukushuto`（241/241）・`verify_ocean_layer.py`（副首都の指摘なし）・
`build_fukushuto_arena.py --check`（OK）・全テストが通ることを確認。数字の出所検査は文中の件数を「記録の文と画面の文が完全一致のときだけ」
認めるため、数字や件数を書き換えていれば NG になる。`git diff` で、変わったのが句読点・接続の言葉・括弧の位置だけであることを目視で確認した。

## 7. 公開前の残作業

1. 本番反映（release スキル。main 取り込み・push は司令塔が行う）。
2. 「詳細データ」の「投票の選択とアリーナ上の位置」の行は、旧デザインの山なみ（アリーナ）のマーカーの説明で、新デザインには描く先が無い。
   元HTMLの生成器（`build_fukushuto_arena.py`）が書く文なので今回は継承のまま残した（私なら、次の更新までに新デザインでは行ごと外す）。
3. 再読データの無い2論点（都構想・維新 677件、定義・中身 332件）は「未公開」表示のまま。再読すれば自動で理由区分が出る。
4. 編集部の横断整理（B5）・潮目（B7）・進捗表示（T1）は外した。潮目は公開JSONに推移が入ったら読書面の推移欄に統合する。
5. `data/fukushuto_5issues-reread.json` の `population`・`method` 文が古い（表示には使っていない）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。14件の投稿が今も閲覧できるかは未確認）。
- 印刷ボタンの実際の印刷結果。
- 次に読むテーマの画像は全画面撮影で空白に写った（遅延読み込みの撮影上の問題とみられる。皇室と同じ。目視は未確認）。
- 10/19 の模擬は新規0件の回。新規の意見があり再読データを追記しない場合は、設計どおり止まる（実データでは未確認）。

## 9. 2026-10-11 公開切替

### 9-1. 変えたファイル

| ファイル | 変更 |
|---|---|
| `configs/fukushuto-layout.json` | `enabled: true` |
| `configs/theme-seo.json` | fukushuto に `display_headline`「副首都はどこに、いつ決まる？候補地とメリット・デメリット、SNSで意見が分かれる理由」 |
| `data/page-sources/fukushuto.html`（新規） | 旧形式の元HTML（6節の文の直しを反映した版） |
| `docs/fukushuto-reaction-map.html` | 新デザイン（`fukushuto_layout.finish`。`--mode release --output-dir` の公開候補とバイト一致） |
| `DATA_REFRESH.md` | 「副首都の定期更新（新デザインを維持する、2026-10-11〜）」の節 |
| `company/APPROVALS.yaml` | 副首都ページの新デザイン公開の承認記録（`approval-20261011-003`、承認待ち） |
| `data/verification/fukushuto-sunk-continents.json`・`fukushuto-background.json`・`scripts/build_fukushuto_process_sections.py` | 6節のよみやすの直し（15文） |
| `docs/data/themes/fukushuto.json`・`docs/data/catalog.json`・`data/public/` の同名・`data/verification/adoption/registry.json` | 上の文の変更の反映と公開JSONの指紋 |
| `configs/fukushuto-reading.json`・`fukushuto-opening.json`・`fukushuto-background.json` | 9-2 の使い回しの書き直し（14文） |
| `DATA_SHEET.md` | 9-2 |
| `quality/prototypes/fukushuto-release/` | 公開候補と確認画面を最終版で作り直し |
| 共有テスト | 9-4 |

### 9-2. 切替で初めて見つかったことと対応

- **ページ間の言い回しの使い回し**（`verify_page_originality.py`、全テストの `test_page_originality`）：新デザインの共通の文
  （読書面の説明・注記など）が皇室の新デザインと同じ文だった（同一文12件・書き出しの類似4件）。副首都の設定
  （`configs/fukushuto-reading.json` 12文・`fukushuto-opening.json` の lead・`fukushuto-background.json` の lead）を、意味を変えずに
  副首都向けの言い方へ書き直した（例：「山の幅には下限を設けています」→「山の幅は一定より細くしていません」）。
  書き直しの途中で「1つの山が1つの論点」が論点数の検査（1と6の2通り）に掛かったため、数を書かない文にした。
  よみやす「完成を止める指摘 0件」、`verify_page_originality.py`「10ページに、使い回された見出し・文はありません」。
- **DATA_SHEET.md**：副首都の「マップの点」が旧ページの点の数（1452）から「—」に変わった（皇室と同じ。新デザインに点の図が無いため）。
  `build_data_sheet.py` で作り直した。
- 承認台帳は `approval-20261011-003` を **`status: pending`（承認待ち）** で足した。オーナーの公開承認は受けていない。

### 9-3. 切替後の検査（作業ツリー）

| 検査 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests` | 1,777件 OK（skip 4、失敗0・エラー0） |
| `verify_theme_page.py fukushuto` / 全テーマ | NG 0 / 10テーマ NG 0 |
| `verify_number_provenance.py fukushuto` / 全テーマ | 297/297 説明済み・終了0 / 10テーマ NG 0 |
| `verify_top_page.py` | 終了0 |
| `run_public_checks.py` | 終了0（「公開ファイルだけで確かめられる範囲はすべて通りました」） |
| `build_fukushuto_arena.py --check` | OK: 差分なし（公開後の経路＝元HTMLと新ページの両方を作り直して比較） |
| `verify_builder_rebuildability.py` | 10テーマ NG 0 |
| `seo/validate_theme_seo.py` | OK（themes=10、sitemap URLs=16） |
| `verify_ai_tone.py` | 問題なし（公開ページ10本） |
| `verify_page_originality.py` | OK |
| よみやす（docs の新ページ） | 完成を止める指摘 0件・PASS |
| 2回生成 | md5 一致（`2f6333bf…`、docs のページとも一致） |
| Playwright（docs/ を 127.0.0.1 で配信） | 6節と同じ項目すべて合格。画像は `evidence/`（8枚、切替後に撮り直し） |
| 10/19 の模擬（4節） | 最終版で再実行して合格（候補の新ページは基準日 2026-10-19・意見募集「締め切り済み」） |

### 9-4. 切替に合わせて直した共有テスト

| テスト | 変更 | 理由 |
|---|---|---|
| `tests/test_fukushuto_connected.py`・`_public_counts.py`・`_search_entry.py`・`_taxonomy.py` | 読むページを「公開後は元HTML（data/page-sources）」に | 旧形式の連動表示・検索入口・潮目の検査。公開後も元HTMLに同じ構造で残る（皇室と同じ扱い） |
| `tests/test_cite_button.py` | 副首都の新デザインも論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わった |
| `tests/test_theme_design.py` | 副首都の新デザインを飛ばす | 共通の見た目を掛けない設計 |
