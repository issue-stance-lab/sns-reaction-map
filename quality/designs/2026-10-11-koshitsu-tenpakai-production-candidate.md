# 皇室典範改正（koshitsu-tenpakai）新デザインの公開候補と検査（手順7）

2026-10-11。ブランチ `task/renew-koshitsu-tenpakai`。手順書23の「7. 更新と公開を検査する」。
**docs/ は変更していない。main への統合・push・投票の送信（POST）はしていない。** `configs/koshitsu-layout.json` は `enabled: false` のまま。

公開候補: `quality/prototypes/koshitsu-tenpakai-release/koshitsu-tenpakai-reaction-map.html`（基準日＝公開JSONの更新日 2026-10-05）
確認画面: `quality/prototypes/koshitsu-tenpakai-release/evidence/`（PC・375px・論点選択・背景を開いた画面・X遮断時・JSなし）

## 1. 仕組み（部活動 `bukatsu_layout.py` と同じ型）

| ファイル | 役目 |
|---|---|
| `scripts/build_koshitsu_redesign.py`（新規） | 冒頭・読書面・背景の生成器（`koshitsu_opening/reading/background.py`）を呼び、元HTMLの保護対象を継承して完成HTMLを組む。`--mode preview|release`、`--output-dir`、`--as-of`。docs/ への出力は拒否。新デザインのページを入力に渡すと拒否 |
| `scripts/koshitsu_layout.py`（新規） | `enabled` / `source_for_refresh`（新デザイン公開後は `data/page-sources/koshitsu-tenpakai.html` を返す）/ `materialize`（隔離コピーで元HTMLを docs/ に戻す）/ `finish`（全生成の最後に元HTMLを保存し、新デザインを docs/ に書く）/ `rebuild`（公開後に `build_koshitsu_arena.py` を単独で動かしたとき用） |
| `configs/koshitsu-layout.json`（新規） | `enabled: false`。公開切替時に true |
| `scripts/koshitsu_redesign/`（移動＋新規） | 見た目の正本。`opening.css`・`reading.css`・`reading.js` を試作フォルダーから移した（試作の生成器は生成時に写しを置く）。`production.css` は共通ヘッダー・投票・次に読むテーマ・フッターをこの配色に合わせる追加分 |
| `scripts/koshitsu_redesign_provenance.py`（新規） | 新デザインの件数を公開JSON・再読データの明細・設定から数え直して照合（`verify_number_provenance.py` から呼ぶ） |

施行までの日数：静的HTMLは「施行は10月24日」と書き、日数は読む日に JS で数える（施行日を過ぎたら「施行日を過ぎました（条文は未確認）」に切り替わる）。生成日に依存しないので、同じデータなら同じページになる（`build_koshitsu_arena.py --check` が日をまたいでも崩れない）。

## 2. 保護対象の一覧と継承結果

| 保護対象 | 現行ページ | 公開候補 | 結果 |
|---|---|---|---|
| title | 「皇室典範改正で何が変わる？女性皇族・旧宮家養子の論点｜SNS反応まっぷ」 | 同じ | 継承 |
| SEO_META（description・canonical・OGP・Twitter） | マーカー区間 | 区間を文字どおり複写 | 継承（テストで一致確認） |
| Article JSON-LD | マーカー区間 | 文字どおり複写 | 継承 |
| FAQ JSON-LD | 旧FAQ 6問 | 新デザインの背景「よくある質問（6問）」から作り直し | 画面と構造化データの一致をテストで確認 |
| GA4（G-K10S4YCZFH、ホスト限定） | GA_TAG 区間 | release だけ文字どおり複写。preview には載せない | 継承 |
| AdSense タグ・`google-adsense-account` meta | ADSENSE_TAG 区間・meta | release だけ複写（meta は両方） | 継承。`docs/ads.txt` は変更なし |
| Supabase 投票 | topic `koshitsu-tenpakai-issue-stance-v2`、論点6×立場4＝24、`choiceIdx:issueIdx*STANCES.length+stanceIdx`、保存キー `sns_vote_<topic>_my` | 投票節とスクリプトを複写。VOTE_ISSUES・STANCES は元と完全一致。保存キーは本番ホストでだけ既存キー、他のホストでは `sns_vote_preview_` | 継承。`vote-config.js?v=1`→ホスト判定→`vote-store.js?v=1` の順 |
| 投票の参加者数 n= 表示・やり直し・シェア | topic-modern.js | topic-modern.js?v=13 を読み込み | 継承 |
| 調査条件（#caution）・PLANET_DATA | 山なみ節 | 山なみの注記の下に #caution、末尾に PLANET_DATA（公開検査が読む契約） | 継承 |
| 既存アンカー | 外部・他ページ・note からの `#` 付き参照は0件（`grep` 結果） | `#issue-{論点ID}` は同じIDで新しい論点欄に。旧 `#planet-block` `#fb-{ID}` `#detail-data` `#issue-cards` `#bukatsu-background` `#koshitsu-quick-guide` など17件は `location.replace` で新しい置き場所へ読み替え（背景の行なら開く） | 継承（Playwright で確認） |
| noscript 本文 | 現行ページに noscript は無い | JSなしで6論点・背景がすべて読める | 該当なし（JSなし表示は確認済み） |
| 関連テーマへの導線 | 次に読むテーマ（憲法改正・副首都） | 同じ節を複写 | 継承 |
| 運営者情報・訂正窓口 | フッターと信頼情報 | フッターを複写。背景「集め方と、この集計の限界」に `about.html#corrections` | 継承 |
| 公開日・更新日の `<time>` | ARTICLE_TRUST | 背景の事実欄を `<time datetime>` に | 継承 |
| 授業節（印刷ボタン・GA4 計測） | CLASSROOM 区間 | 背景「授業や話し合いで使う」を `classroom-section`・資料・問い・印刷ボタンの約束に合わせ、CLASSROOM マーカーで囲む | 継承 |
| 読書進捗のキー `isa-seen-koshitsu-tenpakai` | 進捗の帯で使用 | 新デザインには進捗の帯が無いので読み書きしない。既存の保存値は消さない | 継承しない（機能ごと移していない） |
| 引用ボタン（topic-modern.js の cite） | `article.ic` に付く | 論点欄に付けていない | 継承しない（論点欄の切替と並びが合わないため。残作業） |
| 世論の潮目ウィジェット | TIDE_CARD | 載せていない | 継承しない（入力が非公開の更新回で、公開JSONに推移が無い。読書面に「推移はまだ公開データに無い」と明記） |
| テーマ共通の見た目（theme-design.css/js・件数スタンプ） | THEME_DESIGN | 載せない。`apply_theme_design.py` は新デザインのページを飛ばす | 意図的に外した |
| llms.txt・sitemap | URL のみ参照 | URL 不変のため変更不要 | 継承（`validate_theme_seo.py` で確認） |

## 3. 生成方法

リポジトリ（作業ツリー）の直下で実行する。

公開候補（公開操作ではない）:
```sh
python3 scripts/build_koshitsu_redesign.py --mode release --output-dir quality/prototypes/koshitsu-tenpakai-release
```
成功すると `Built 1 file (release, as_of 2026-10-05); no deployment performed.` と出る。指紋は同じフォルダーの `build-manifest.json`。

確認用（GA・AdSense なし、noindex、投票は送らない）:
```sh
python3 scripts/build_koshitsu_redesign.py --mode preview --output-dir /tmp/koshitsu-preview
```

公開切替（release スキルの手順の中で行う。今回はしていない）:
1. `configs/koshitsu-layout.json` を `enabled: true` にする。
2. 同じコミットで `configs/theme-seo.json` の koshitsu-tenpakai に `"display_headline": "皇室典範改正、何が変わる？愛子さまは？　何が問題？"` を足す（H1 が変わるため。`validate_theme_seo.py` が H1 と照合する）。
3. `python3 -c "import sys;sys.path.insert(0,'.');from pathlib import Path;from scripts import koshitsu_layout as l;l.finish(Path('.'))"` で元HTMLを `data/page-sources/` に保存し、docs/ のページを新デザインにする。

この3段を作業ツリーの複製（スクラッチ）で実行し、下の検査を「切替後の状態」でも通した。

## 4. 定期更新との両立

- `refresh_topic.py` の公開候補生成（単一・複数テーマ）は、隔離コピーで `materialize` → 旧形式の全処理（adapter・finalize・SEO・信頼情報・授業節・テーマ共通の見た目）→ 最後に `koshitsu_layout.finish`。旧昇格経路（`promote`）は新デザイン有効時に止める。
- `refresh_adapters/koshitsu.py` は `source_for_refresh` を入力にする（公開後も元HTMLから2回生成・投票互換・保護タグを検査）。
- 新デザインの照合（再読データの件数＝意見数など）が合わないと `finish` は ValueError で止まり、元HTMLも公開ページも書き換えない（テストで確認）。

### データ更新時にどの生成元を直すか（データ対応表・最終版）

| 表示 | 生成元 | 更新時に直すもの |
|---|---|---|
| 件数（収集・意見・論点別・立場別）、収集期間、更新日 | 公開JSON `docs/data/themes/koshitsu-tenpakai.json`（正典から `build_public_registry.py`） | 自動（正典の更新で変わる） |
| 理由区分と件数 | `data/koshitsu-tenpakai_issues-reread.json` | **新しい収集回の意見を再読して追記**（件数が意見数と合わないと生成が止まる） |
| 理由の「どんな声か」・論点の説明・投稿2件の選定 | `configs/koshitsu-tenpakai-reading.json` | 区分が増えたとき・投稿を差し替えるとき |
| 主張の照合・共通の心配・資料にしかない話 | 公開JSON（`data/verification/koshitsu-tenpakai-sunk-continents.json` ほか） | 再検索の記録を追記したとき（母数 sns_base が意見数と違うと止まる） |
| 制度の確認（3項目）・年表・未確認事項 | `data/verification/koshitsu-tenpakai-background.json`、一次資料メモ | 一次資料の再確認時 |
| 冒頭の短答・問い・日付 | `configs/koshitsu-tenpakai-opening.json` | 施行後に条文を確かめたら `enforcement_confirmed_on` |
| 背景の行・FAQ・授業 | `configs/koshitsu-tenpakai-background.json`、`scripts/koshitsu_background_detail.py` | 施行日以降は時制の見直し（見直すまで生成が止まる） |
| 公開日・次回更新予定・収集元 | `THEMES.yaml`、`configs/theme-seo.json` | 自動（更新手順で変わる） |
| SEOメタ・JSON-LD・GA・AdSense・投票 | 元HTML（`data/page-sources/`、公開前は docs/） | 変更しない（継承するだけ） |

## 5. 共有スクリプト・共有テストの変更箇所と理由

| ファイル | 変更 | 理由 |
|---|---|---|
| `scripts/refresh_topic.py` | `promote` の新デザイン停止条件に皇室を追加／`_copy_candidate_tree` で皇室の `materialize`／単一・複数の公開候補生成で、テーマ共通の見た目の後に皇室の `finish` | 部活動の分岐と並べた最小の追加（計10行） |
| `scripts/refresh_adapters/koshitsu.py` | 入力を `source_for_refresh(root)` に | 公開後も元HTMLから生成するため |
| `scripts/build_koshitsu_arena.py` | 公開ページが新デザインで引数なしのとき `koshitsu_layout.rebuild` | 単独実行で新ページを旧形式で上書きしないため |
| `scripts/refresh_planet_section.py` | 皇室の新デザインも停止 | 部活動と同じ保護 |
| `scripts/apply_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を重ねないため |
| `scripts/seo/apply_classroom_section.py`・`apply_theme_trust.py` | 新デザインのページを飛ばす（skipped と表示） | 単独実行で授業節・H1を旧形式に戻す事故を防ぐ。更新経路では元HTMLに掛かる |
| `scripts/verify_builder_rebuildability.py` | 皇室の `materialize` | 更新経路と同じ入力で再生成を比べるため |
| `scripts/verify_theme_page.py` | 新デザインの理由件数を論点欄の中で照合する分岐／意見数パターンから「〜への意見」「〜しない意見」を除外 | 表示形式が変わった照合だけの対応（基準は緩めていない）。後者は理由区分の名前「制度の説明・背景への意見 18件」を意見数と誤認したため |
| `scripts/koshitsu_count_provenance.py` | 新デザインなら `koshitsu_redesign_provenance` を呼ぶ | 数字の出所検査 |
| `tests/test_koshitsu_connected.py`・`_public_copy.py`・`_quick_guide.py` | 読むページを「公開後は元HTML」に | 旧形式の連動表示の検査。公開後も元HTMLは同じ構造で残るため（前提が変わった検査） |
| `tests/test_classroom_section.py` | 新デザインでは授業節が `#bg-method` より前か | 信頼情報の置き場所が変わったため |
| `tests/test_cite_button.py` | 新デザインでは論点欄の `id="issue-…"` を受け皿とみなす | 受け皿の形が変わったため |
| `tests/test_theme_design.py` | 新デザインのページを飛ばす | 共通の見た目を掛けない設計に合わせた |

## 6. 検査結果

| 検査 | 公開前（作業ツリー） | 切替後（スクラッチで切替） |
|---|---|---|
| 生成器の内蔵照合（件数・理由区分・立場・資料・日付） | 合格 | 合格 |
| `verify_theme_page.py koshitsu-tenpakai`（候補は `--html`） | NG 0 | NG 0 |
| `verify_number_provenance.py koshitsu-tenpakai` | 298/298 説明済み（現行ページ） | 284/284 説明済み |
| `seo/validate_theme_seo.py` | OK | OK（display_headline 追加後） |
| `verify_builder_rebuildability.py` | 皇室 OK（消費税だけNG、下記） | 皇室 OK（同上） |
| `verify_ai_tone.py` | 問題なし | 問題なし（新ページを含む10本） |
| `verify_trend_images.py` | NG 0 | — |
| tests/test_koshitsu_*（6本）＋ `test_koshitsu_redesign.py`（15件） | 合格 | 合格 |
| 全テスト `python3 -m unittest discover -s tests`（pytest は未導入） | 1,719件中 失敗11・エラー5 | 1,719件中 失敗12・エラー5（消費税の16件＋授業節1件）。授業節を直したあと、関係する12ファイル84件を再実行して合格（全件の再実行はしていない） |
| `run_public_checks.py` | テスト2件だけNG（同じ原因） | — |

全テストの失敗16件は、すべて消費税減税（と推移の表の照合）。原因は main 側の「消費税減税 2026-10-11 更新回」（84451388）がこのブランチに入っておらず、復元した非公開正典は新しい版のため、公開JSONの source_sha256 が合わないこと。変更を外しても同じ失敗が出ることを `run_public_checks.py` で確認した。皇室・部活動・他テーマのテストで、今回の変更で落ちたものは無い。切替後に初めて落ちた12件（授業節・引用の受け皿・共通の見た目・旧形式の連動表示の検査）は、5.の更新と授業節の生成で0件にした。

数値と出典の照合：冒頭の総数2,016件・立場の3区分（476／1,511／29件）・6論点の件数・各論点の理由区分の件数（再読データの明細を数え直し）・論点×立場・主張に当たる投稿数・資料にしかない話の母数を、公開JSONと再読データから独立に数え直して一致（`koshitsu_redesign_provenance.py`）。リンクは `validate_theme_seo.py` の手元参照切れ0件。

操作（Playwright、`tests/test_koshitsu_redesign_browser.cjs`）:
- 1280px・375px とも横はみ出し0、コンソールエラー0。
- 論点名6つと山を押しても scrollY 不変。背景の10行の開閉（開いても横はみ出し0）。
- 戻る：論点を6回切り替えても history.length 不変、「戻る」で前のページ（index.html）へ。
- 旧アンカー：`#fb-…` は論点、`#detail-data` は件数表の行を開く、`#issue-…` で論点を選ぶ。
- キーボード：Tab で論点名を移り Enter で選択（位置・フォーカス不変）、背景の行を Enter で開く、フォーカス枠が見える。
- X埋め込みを遮断：「埋め込みを表示できません」の案内と元投稿リンク2件が残り、ページエラー0。
- JSなし：6論点すべて表示、背景も開ける。施行札は「施行は10月24日」。JSありでは「施行まで あと13日」、日付を10月25日にすると「施行日を過ぎました（条文は未確認）」。

投票：本番 Origin（https://sns-reaction-map.jp）から GET `cast-vote?topic_id=koshitsu-tenpakai-issue-stance-v2` → HTTP 200、CORS 一致、既存 counts（2票、choice 0 と 16）を取得。POST はしていない。

よみやす（`review_with_yomiyasu.py --medium website --strict`）：手順6で残った11件のうち、背景の既存文3件は直した（`koshitsu_background_detail.py` の読点4個2文、「ます」3連続1件）。投稿の導入文で生じた文末の連続2件も直した。残る8件はすべて `data/verification/koshitsu-tenpakai-sunk-continents.json`（公開JSONの `sns_note`＝再検索の記録7件、`life_impact` 1件）。画面に出る（再検索の記録は「検索の記録」を開いたとき、life_impact は常に表示）ので対象外ではない。直すには公開JSON（docs/data）と現行ページの再生成が要り、今回の「docs を変えない」範囲を超えるため残した。ほかに「世論調査ではありません」の文を「世論調査ではなく、…」に直した（サイト共通の信頼表示の文言検査に合わせた。意味は同じ）、件数表の要約「6論点×」を「論点（その他を含む）×」に直した（論点数の表記を5つに統一）。

## 7. 公開前の残作業

1. オーナーが公開候補の表示・内容を確認する（evidence の画像、またはローカル配信）。
2. `sunk-continents.json` の文8件をよみやす基準で直し、公開JSONを作り直す（公開切替と同じコミットで docs を再生成）。
3. 公開切替（3.の3段）を release スキルの手順で行う。その前に main（消費税の更新回など）を取り込み、全テストを再実行する。
4. 施行日（10月24日）以降の初回更新の前に、背景の年表・FAQの時制を直す（直すまで `finish` が止まり、有効時は全テーマの公開候補生成も止まる）。**10月15日の定期更新は enabled=false のままなら影響なし。**
5. 新しい収集回の意見を `issues-reread.json` に再読して追記する手順を、更新の正典（DATA_REFRESH.md）に足す。追記しないと有効化後の更新で止まる。
6. 引用ボタン・潮目ウィジェット・読書進捗の帯を新デザインに戻すかの判断（私なら、潮目は公開JSONに推移が入ってから読書面の推移欄に統合、引用ボタンは論点見出しに付ける形で別課題）。

## 8. 未確認事項

- 本番ホストでの GA4・AdSense の実際の発火、投票 POST の保存と重複防止（実票になるため未実施）。
- X埋め込みが実際に表示されるか（遮断時の表示だけ確認。8件の投稿が今も閲覧できるかは未確認）。
- 印刷ボタンの実際の印刷結果（OS の印刷ダイアログ・改ページ）。
- 次に読むテーマの画像は全画面撮影で空白に写った（遅延読み込みの撮影上の問題とみられるが、目視で確かめていない）。
- 全テストは pytest が無いため unittest で実行した。消費税減税の16件は main の取り込み後に通るかを確かめていない。
