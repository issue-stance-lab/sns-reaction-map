# 品質監査: 課題77 Part A（案1）「引用され、検索される構造」の機械が読める側

- 監査日: 2026-09-20
- 対象: 作業ツリー `isa-wt-growth-cite-search`（ブランチ `task/growth-cite-and-search-structure`、分岐元 0877fa6）の未コミットの変更。
  公開JSONの写し（`docs/data/`）・`docs/llms.txt`・論点の固定リンク（`id="issue-{id}"`）・「引用」ボタン（`docs/topic-modern.js`）・
  GA4のAI参照元レポート（`scripts/fetch_ga4_metrics.py`）。発注書は `configs/prompts/20260920_growth-cite-and-search-structure.md`
- 監査者: 発注書を書いたセッション（実装したセッションとは別）
- 判定: **ready_for_ceo（条件付き）**。公開前に下の「公開前にやること」2件を実装セッションが済ませること。
  推奨修正1件は Part B 着手前まででよい

## 判定の根拠

### 自動検査（作業ツリーで実行）

| 検査 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests` | 1,007件 OK（新規テスト3ファイル含む） |
| `python3 scripts/run_public_checks.py` | OK（CIと同じ範囲） |
| `python3 scripts/verify_theme_page.py` | 11テーマ NG 0件（ビルダ差分なし・保護タグ維持） |
| `python3 scripts/verify_number_provenance.py` | 11テーマ NG 0件（ページに新しい数字を書いていない） |
| `python3 scripts/verify_page_originality.py` | OK |
| `python3 scripts/seo/validate_theme_seo.py` | OK（llms.txt の存在・全テーマ掲載・URL実在を含む） |
| `python3 scripts/verify_public_registry.py --against-private` | 10テーマが非公開正典と完全一致 |
| `python3 scripts/verify_top_page.py` | NG 1件のみ。collect_at 期限超過（ai-copyright 9/12・elderly 9/11）で本件と無関係 |
| llms.txt の再現性 | `docs/` の写しに `generate_seo_assets.py` を再実行し、llms.txt・sitemap.xml・robots.txt とも byte 一致 |
| GA4 AI参照元（A-5） | 共有ツリーで `--details --days 28` を実行して表が出た。chatgpt.com 経由 5セッション（着地 `/` 3、`/ai-copyright-reaction-map.html` 1、`/index.html` 1） |

### 実機確認（作業ツリーの `docs/` を 127.0.0.1 で配信）

- 副首都（デスクトップ）: 論点を選ぶと選択パネルの見出し直後に「引用」が出る。押すとクリップボードに
  `SNS反応まっぷ「副首都法案・副首都構想」論点「定義・中身」（2026年9月時点、SNS公開投稿サンプル1681件の整理。社会全体の世論調査ではありません）` と
  `…/fukushuto-reaction-map.html#issue-fukushuto-definition` の2行が入る。GA4 に `cite_copy {theme_id, issue_id}` が送られる。「コピーしました」が出て消える。コンソールエラーなし
- 固定リンクで開く: `#issue-fukushuto-finance` 付きで読み込むと「費用・財源」が選択され、パネルが画面内に来る
- 論点カード型の5テーマ（生成AI著作権で確認）: `#issue-ai-copyright-learning-data` 付きで読み込むと選択パネルに着地し（scrollY 3,754、パネル上端 338px）、カード側（7,173px）ではなく論点の説明が先に見える。カードにも「引用」がある（7個）。id の重複なし
- 375px: 横スクロールなし（scrollWidth 375 = innerWidth 375）。ボタン 47×26px、「コピーしました」はボタンの下に出て画面内に収まる。スクリーンショットで確認
- 投票導線: 論点→立場まで進み Supabase への送信に達する（127.0.0.1 からは CORS で拒否されるのが正常）。結果欄には「Xでシェア」「投票をやり直す」の両方がある。投票のコードは本件で触っていない

### 発注書との突き合わせ

- A-1 公開JSON: `build_public_registry.py` が `data/public/` と `docs/data/` に同じ bytes を書く。`verify_public_registry.py --public-only` に写しの一致を追加。`refresh_topic.py` の公開候補にも `docs/data/`・`docs/llms.txt` を追加。投稿本文なし（禁止キーなし・最長277文字、上限600のテストあり）。sitemap に載らない。robots.txt は全許可のまま
- A-2 llms.txt: `generate_seo_assets.py` が正典。1行説明は `configs/theme-seo.json` の description をそのまま使用（新しい文章なし）。訂正窓口のアンカー `about.html#corrections` は実在
- A-3 固定リンク: `build_planet_data.py` の静的一覧に `<span class="issue-anchor" id="issue-{id}">`。issue-cards を持つ5テーマは既存の `id="issue-{id}"` を再利用（重複回避）。テストが JSON の issues[].id と全論点一致・重複なしを固定
- A-4 引用ボタン: 共有JSのみ（テーマ別HTMLに書かない）。数字は `docs/data/themes/{id}.json` を fetch。失敗時は数字なしの定型文。CSS版数 28→29
- A-5 計測: 上記のとおり動作確認済み。`GROWTH.yaml` の「動作未確認」注記はマージ時に更新すること
- 対象外の遵守: タイトル・description・`THEMES.yaml` の updated_at・新規HTMLページ・図解画像はいずれも変更なし

## 公開前にやること（実装セッション）

1. **分岐元が古い。** ブランチは 0877fa6 から分岐しているが、main には 75c0865（副首都・皇室典範の「調査条件」ボックス、課題79）などが入っている。
   main を取り込んでから10ページを作り直し（`verify_builder_rebuildability.py` の一覧）、上の自動検査を全部やり直してからマージする
2. **副首都の論点画像7枚が公開差分に含まれる。** 本番の副首都ページは 2026-09-20 17:37 の課題74反映（134a6a0）以降、
   論点画像を失っている（画像参照 13→5、wide 図 8→0。builder `build_fukushuto_arena.py` には残っている）。Part A の再生成で戻る。
   オーナーが課題70で了承した図なので戻るのは正しいが、CEO承認のときに「画像が再表示される」ことを伝えること。原因の追跡は課題80

## 推奨修正（Part B 着手前まで）

- 同一ページ内でハッシュだけ変わったとき（`hashchange`）に論点を選び直していない。外部からの固定リンクは動くが、
  Part B の節から `#issue-{id}` への内部リンクを押しても、山なみ表示では論点が切り替わらない（実機で確認: `#issue-fukushuto-location` へ変えても選択は前のまま）。
  `window.addEventListener('hashchange', citeRestoreFromHash)` の1行で足りる。`land()` はハッシュを `#fukushuto-finance` 形式（issue- 無し）に書き換えるため、無限ループにはならない

## 軽微（対応任意）

- 着地後に URL のハッシュが `#issue-…` から `#…` に書き換わる（既存の `land()` の挙動）。アドレスバーから URL をコピーした人は旧形式のアンカーを渡すことになるが、動作はする
- `ISSUE_CARDS_OWNS_ANCHOR_ID`（5テーマ）は手書きの一覧。テーマが増えたときの重複はテストが検出する

## 残るリスク

- AI経由の来訪がどれだけ増えるかは未知。既に28日で5セッション（chatgpt.com）ある
- llms.txt は llmstxt.org の慣例で、標準化されたものではない

## 戻し方

- 公開後に不具合が出たら、マージコミットを `git revert` して10ページを作り直す（`docs/data/`・`docs/llms.txt` も消える）。
  部分的に戻すなら `docs/topic-modern.js` の「論点の引用ボタン」ブロックを外し、`apply_theme_trust.py` の `TOPIC_CSS_VERSION` を上げる
