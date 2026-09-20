# 発注書: 課題77 案1＋案2「引用され、検索される構造」

- 作成日: 2026-09-20
- 出典: `tasks/task-77.md`（案1・案2）、`GROWTH.yaml` capabilities `cite-and-search-structure`
- 採用: オーナー決定（2026-09-20）。**公開（本番反映）は別途CEO承認が要る**（`company/COMPANY.md` 権限の原則1）
- 実行者: 別セッション（Claude Code）。Part A（案1）と Part B（案2）は別セッションで分けてよい。**Aを先に**（Bの内部リンク先のアンカーをAが作る）
- ブランチ: Part A `task/growth-cite-and-search-structure`、Part B `task/growth-cite-and-search-structure-b`

## 0. 着手前に必ずやること・読むこと

1. `OPERATIONS.md` ⓪ のとおり作業ツリー（作業用のコピー）を作り、非公開正典を tar から復元する。
   Part A は生成スクリプトを触るので `verify_theme_page.py` が正典を読む。Part B は文章を書くので
   `configs/persona.private.json`（ライターのペルソナ）の復元も確認する（無くても検査は黙って通る）。
   収集はしないので `node_modules` は不要。
2. `tasks/task-77.md` を読む（背景・制約・6案の位置づけ）。この発注書と食い違ったら発注書を優先し、食い違いを報告に書く。
3. `GROWTH.yaml` の `cite-and-search-structure` を `idea` → `building` に変え、`activity_log` に1行足す
   （`OPERATIONS.md`「台帳を更新するのは誰か」: 作業したセッションがその場で更新する）。
4. **前例を先に開く**（文面から結論せず、動いている実物を見る）:
   - 共有ブロック方式の前例: `scripts/seo/apply_theme_trust.py`（`<!-- ARTICLE_TRUST_START -->`〜`END` の間を
     `configs/theme-seo.json` から作り直す。同じ入力で2回実行しても差分ゼロ。`scripts/refresh_topic.py` の昇格列から呼ばれる）
   - GA4 イベントの前例: `docs/topic-modern.js` の `related_theme_click`（`window.gtag('event', ...)`）
   - 公開JSONの正典: `scripts/build_public_registry.py`（`data/public/themes/*.json` と `catalog.json` は生成専用・手編集禁止）
   - robots.txt / sitemap.xml の正典: `scripts/seo/generate_seo_assets.py`（`docs/robots.txt` を手で直すと次の生成で戻る）
   - 論点アンカーの既存規約: `scripts/build_planet_page_preview.py` の `id="issue-{iid}"`（issue-cards）。同じ規約に揃える
   - 山なみ区間の作り直し: `scripts/refresh_planet_section.py`。`<!-- PLANET_SECTION_START -->`〜`END` は毎回まるごと作り直される。
     **この区間に後付けで書いても次の更新で消える。** 区間の中身を変えるなら生成側を変える
   - 全テーマの作り直しコマンド: `scripts/verify_builder_rebuildability.py` の先頭にある `build_*_arena.py` の一覧
5. 守ること（`OPERATIONS.md`「サイト改善の進め方」）: 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない。
   375px で横スクロールなし・コンソールエラーなし。**新しい導線には GA4 イベントか UTM を必ず付ける（計測できない施策は実装しない）。**
   main への直接コミット禁止。公開は CEO 承認後に `release` スキルで行う。

## 1. 目的（なぜやるか）

週の利用者が数十人の段階では、来訪者がいなくても外から引っ張る仕掛けが先に効く。

- 案1: 生成AI（ChatGPT / Perplexity / Gemini / Copilot）は、両論を出典つきで構造化したページを引用しやすい。
  このサイトの論点整理はその形に合う。GA4 には 2026-07-06 に「AI Assistant」経由の来訪が1度記録されている。
  機械が読める形（JSON・llms.txt・論点ごとの固定リンク・引用の定型文）を用意し、AI経由の来訪を計測できるようにする。
- 案2: 中高生と教員は「〇〇 ディベート 反対 理由」「〇〇 メリット デメリット」で検索する。
  各テーマページに「授業・ディベートで使うとき」の節を足し、賛成・反対の理由と一次資料へ最短で届くようにする。
  営業はしない。検索で先生に見つけてもらう。

指標: GA4 の参照元（chatgpt.com / perplexity.ai / gemini.google.com / copilot.microsoft.com / claude.ai / bing.com）のセッション数、
Search Console の検索語（ディベート・探究・メリット デメリット・賛成 反対 理由）の表示回数・クリック。

## 2. 対象外（やらないこと）

- ページのタイトルタグ・description の変更（SEO台帳 `configs/theme-seo.json` と `validate_theme_seo.py` の領域。別課題）
- `THEMES.yaml` の `updated_at` の変更（6箇所に連鎖する。データ更新を伴わない今回は触らない）
- 新しい HTML ページの追加（AdSense 4回目審査中。薄いページを増やさない。今回はすべて既存ページ内の節と機械向けファイルで済ませる）
- PDF ワークシートの生成（印刷用 CSS で代替。反応を見てから判断）
- 図解画像の追加・流用（課題70で点検中）
- 案3〜案6（`tasks/task-77.md` 参照。別発注）
- 非公開正典（`social-samples/`）の内容変更

## 3. Part A（案1）: 機械が読める側

### A-1. 公開JSONをサイトに置く

- `data/public/themes/*.json` と `data/public/catalog.json` を `docs/data/themes/{theme_id}.json` と `docs/data/catalog.json` として公開する
  （現状 `docs/` には無く、本番 `https://sns-reaction-map.jp/data/public/catalog.json` は 404。2026-09-20 確認）。
- 手コピーしない。`scripts/build_public_registry.py` に `docs/data/` への書き出しを足すか、同期専用スクリプトを作り、
  `scripts/refresh_topic.py` の昇格列（`apply_theme_trust.py` を呼んでいる2箇所）にも足す。
- 検査: `scripts/verify_public_registry.py --public-only`（CI「公開ファイルの検査」で回る）に
  「`docs/data/` の写しが `data/public/` と同一（sha256）」を足す。
- 投稿本文を含まないことをテストで固定する。2026-09-20 時点の JSON の最長文字列は 277 文字（編集部の説明文）で、
  本文キー（`text` / `body` / `records` 等）は無い。「本文キーが無い」「文字列長の上限」の2点を `tests/` に置く。
- `sitemap.xml` に載せない（`generate_seo_assets.py` は `configs/site-cases.json` の pages しか載せないので自動で載らない。載らないことをテストで固定）。
- **robots.txt は「全許可」のまま。** AIクローラー（GPTBot / OAI-SearchBot / ChatGPT-User / PerplexityBot / Perplexity-User /
  ClaudeBot / Claude-User / Google-Extended / Bingbot）を塞ぐ行を足さない。JSON は HTML ではないので noindex の meta は付けられず、
  GitHub Pages は応答ヘッダーも付けられない。塞ぐと目的（AIに読まれる）が消える。
- `company/data-assets.json`（公開／非公開の境界台帳）の検査 `verify_data_assets.py` が新しい公開ファイルで落ちるなら、
  検査のメッセージに従って台帳を再生成する（`data-backup-status.json` とセットで）。

### A-2. llms.txt

- `docs/llms.txt` を `scripts/seo/generate_seo_assets.py` で生成する（robots.txt と同じく、ここを正典にする）。
- 形式は llmstxt.org の慣例: 1行目 `# SNS反応まっぷ`、次に `>` の要約1〜2文、以下 `##` 見出しごとに `- [題名](URL): 説明` の一覧。
- 中身:
  1. サイトの目的（`company/COMPANY.md` Mission を2文以内に）
  2. データの限界（「SNS公開投稿サンプルの整理であり、社会全体の世論調査ではない」を1文）
  3. 引用の書き方（A-4 の定型文と同じもの）
  4. テーマ一覧（10テーマ。題名・ページURL・JSON URL・更新日・意見件数。`data/public/catalog.json` から生成）
  5. 手法（`about.html`）、訂正窓口（`about.html` 5節）、免責（`disclaimer.html`）
- 各テーマの1行説明は `configs/theme-seo.json` の `description` をそのまま使う。**新しく文章を書かない**
  （AI臭検査・使い回し検査の対象を増やさない）。
- 検査: `scripts/seo/validate_theme_seo.py`（CIで回る）に、llms.txt の存在・公開10テーマ全部の掲載・URLが `docs/` に実在することを足す。

### A-3. 論点ごとの固定リンク（アンカー）

- 山なみの「論点の一覧」の各論点に `id="issue-{issue_id}"` を付ける。`issue_id` は `data/public/themes/{theme}.json` の `issues[].id`
  （例: `fukushuto-definition`）。同一ページで id を重複させない（既に `issue-cards` が `id="issue-{iid}"` を使うテーマがあれば、
  どちらか一方だけに付けるのではなく、同じ要素を指すよう整理する）。
- 生成側（`scripts/build_planet_page_preview.py` と各 `build_*_arena.py` が共有している論点一覧の描画）に足す。後付けしない。
- 生成側を変えたら **公開10テーマ全部を作り直す**（`verify_builder_rebuildability.py` の一覧のコマンドを1つずつ）。
  共有コードを直しても公開済みページは自動では変わらない（2026-09-13 に5テーマで反映漏れが起きた）。
- テスト: 各テーマで JSON の `issues[].id` と HTML の `id="issue-..."` が全論点で一致すること。

### A-4. 「この論点を引用」ボタン

- 各論点に小さなボタンを置き、押すと次の定型文をクリップボードへコピーする:

  ```
  SNS反応まっぷ「{テーマ名}」論点「{論点名}」（{更新年月}時点、SNS公開投稿サンプル{意見件数}件の整理。社会全体の世論調査ではありません）
  {ページURL}#issue-{issue_id}
  ```

- 更新年月と意見件数は `docs/data/themes/{theme_id}.json` を fetch して入れる（`updated_on` / `opinion_count`）。
  **ページのHTMLに新しい数字を書かない**（`verify_number_provenance.py` の対象を増やさない）。取得に失敗したら数字なしの定型文にする。
- 実装は共有JS `docs/topic-modern.js`（テーマごとの HTML に書かない）。GA4: `window.gtag('event', 'cite_copy', {theme_id, issue_id})`。
  CSS は `docs/topic-modern.css` に足し、`scripts/seo/apply_theme_trust.py` の `TOPIC_CSS_VERSION` を上げてキャッシュを切る。
- 見た目: 論点名の横に文字ボタン「引用」。押した後に「コピーしました」を2秒だけ出す。375px で折り返しが崩れないこと。
- テスト: `tests/test_share_utm.py` に倣い、JS に `cite_copy` があること、公開10ページに引用ボタンの受け皿があること。

### A-5. 計測（AI経由の来訪を見えるようにする）

- `scripts/fetch_ga4_metrics.py` の `share_button` 参照元表の隣に、`sessionSource` が
  `chatgpt.com` / `chat.openai.com` / `perplexity.ai` / `www.perplexity.ai` / `gemini.google.com` / `copilot.microsoft.com` /
  `claude.ai` / `bing.com` のいずれかのセッション表を足す（`inListFilter`）。
- 記録先は `GROWTH.yaml` の `kpi.snapshots`（月曜の kpi-snapshot）。列を足すなら `tests/test_admin_dashboard.py` が通ること。
- **`.env` と `secrets/` は共有ツリー（`issue-stance-aggregator` 本体）にしか無い。** 作業ツリーで実行すると必ず
  「GA4_PROPERTY_ID is required」で落ちる。動作確認は共有ツリーで `--days 7`。

### A-6. Part A の完了条件

- 本番相当の `docs/` に `data/catalog.json`・`data/themes/*.json`（10本）・`llms.txt` がある
- 公開10ページの全論点に `id="issue-..."` と引用ボタンがある。`cite_copy` イベントが実クリックで送られる（ローカルで確認）
- 追加したテスト（JSONの写しの一致・本文を含まない・sitemap非掲載・llms.txt・アンカー一致・JS）が `run_public_checks.py` で回る
- `verify_theme_page.py` で「ビルダ差分なし」NG 0件、`verify_number_provenance.py` NG 0件
- `GROWTH.yaml`: `building` → `built`（検証済み・マージ待ち）。公開後に `measuring`、`judge_at` は公開4週後

## 4. Part B（案2）: 「授業・ディベートで使うとき」の節

### B-1. 置き場と方式

- 対象: 公開10テーマ（`THEMES.yaml` の `status: done`。takaichi は非掲載で対象外）。
- 各ページに共有ブロック `<!-- CLASSROOM_START -->`〜`<!-- CLASSROOM_END -->` を、**`<!-- ARTICLE_TRUST_START -->` の直前**に入れる。
  相対順序を保証するため、相手のマーカーそのものをアンカーにする（共有の目印に後付けすると後勝ちになる）。
- 生成は `scripts/seo/apply_classroom_section.py`（新規）。`apply_theme_trust.py` と同じ「マーカー間を置き換える・同じ入力で差分ゼロ」。
  中身は `configs/classroom/{theme_id}.json`（新規）から作る。
- `scripts/refresh_topic.py` の昇格列（`apply_theme_trust.py` の直後、2箇所）と、`scripts/verify_theme_page.py` の冪等検査
  （「apply_theme_trust changed=0」と同じ形）に足す。これを忘れると次のデータ更新で節が消える、または検査が落ちる。

### B-2. 1テーマあたりの中身（`configs/classroom/{theme_id}.json`）

1. 見出し: 「授業・ディベートで使うとき」。サブ: 「賛成・反対それぞれの理由を、まず3つずつ」
2. 賛成の主な理由 3つ／反対の主な理由 3つ。ページに既にある論点・「島」の文言と `data/public/themes/{theme}.json` の
   `editorial_summary` から要約する。各理由の末尾に「→ 論点「◯◯」を見る」で `#issue-{issue_id}`（Part A のアンカー）へ内部リンク。
   立場の呼び方（賛成／反対／条件付き）は JSON の `stances[].label` に揃える。
3. **新しい数字を書かない。** 件数は論点側に既にある。どうしても要るなら `scripts/sync_issue_counts.py` 経由で出所を持たせる。
4. 確かめる一次資料 3つ: `quality/research/{theme}-primary-sources.md` から、原典（法令・議事録・白書・統計）へのリンク。
   年度ラベルのずれに注意（課題75: 実数÷母数で検算して年度を同定する）。
5. 問いの例 3つ: ディベートの論題の形（「〜すべきか」）。両側が使える問いにし、一方の立場を前提にしない。
6. 使い方 2〜3行: 「読む前に理由を書き出す → ページで確かめる → 自分の理由と比べる」の順。
7. 印刷: 節だけを A4 1枚に収める `@media print` を `docs/topic-modern.css` に足す。「印刷する」ボタンは GA4 `classroom_print`。
   内部リンクのクリックは GA4 `classroom_link_click`（`issue_id` 付き）。

### B-3. 文章の決まり

- `WRITING_VOICE.md`（AI臭の禁止）に従い、`scripts/verify_ai_tone.py` を通す（ペルソナ復元済みであること）。
- 行動原則（`company/COMPANY.md`）: 一方を正解にしない。SNSサンプルを世論として扱わない。怒りや恐怖で集客しない。
- 中高生が読める言葉。専門用語は初出で一言そえる。
- 検索意図に合わせ、節内の見出し・本文に「ディベート」「メリット・デメリット」「賛成・反対の理由」の語を自然に含める（タイトルタグは変えない）。
- 使い回し検査 `scripts/verify_page_originality.py`: 枠（見出し・使い方の定型）は `configs/page-originality.json` の
  `shared_selectors` に節のクラス名を登録する。**理由・問い・一次資料はテーマごとに書き分ける**（全ページ同じ文にしない）。

### B-4. 公開前

- `company/QUALITY_GATE.md` の共通確認と Website 項目を通す。品質監査は書いたセッションとは別のセッションで行う。
- CEO 承認（公開内容の変更）→ `release` スキル。
- `GROWTH.yaml`: `built` → 公開後 `measuring`。`activity_log` に1行。

### B-5. Part B の完了条件

- 公開10ページに節がある。`apply_classroom_section.py` を2回実行して差分ゼロ。
- `verify_ai_tone.py`・`verify_page_originality.py`・`verify_number_provenance.py`・`verify_theme_page.py` が通る。
- 375px で横スクロールなし。印刷プレビューで節が1枚に収まる。
- 各理由の内部リンク先アンカーが実在する（テストで固定）。

## 5. マージ後の main で回す検査（`release` スキル ④）

```
python3 scripts/verify_theme_page.py
python3 scripts/verify_number_provenance.py
python3 scripts/verify_top_page.py
python3 -m unittest discover -s tests
python3 scripts/run_public_checks.py
```

`verify_top_page.py` の「collect_at 期限超過」NG は収集予定の遅れで、この作業とは無関係（課題69）。
それ以外の NG が出たら push しない。

## 6. 報告の形（オーナー向け。`CLAUDE.md`「オーナーへの説明のしかた」）

1. 結論を先に: 何ができて、本番にはまだ出ていないこと（CEO承認待ち）。
2. 見てもらう場所: ローカルで開く URL か、作業ツリーのファイル名。**どう見えたら成功か**を1行添える。
3. 確認していないこと・できなかったことを箇条書きで。
4. 次にやることを1つだけ（例: 「承認をもらえたら release スキルで本番反映します」）。
