# LOOP.md — ハブの定常ループ手順書

ハブAI（Claude Code）が毎セッション実行する手順。1セッションで複数周回してよい。

---

## ① 監査

THEMES.yaml と実ファイルを突き合わせ、ズレがあれば台帳を直す。

チェック項目:
- HTMLに smCanvasMain/smCanvasHeat が存在するか
- docs/images/ に漫画・投票画像が存在するか
- 2D分類JSONの件数とエラー率
- sitemap.xml への掲載有無
- `collect_at` を過ぎていないか（内部作業期限。超過は `verify_top_page.py` を失敗させる）
- `refresh_at` を過ぎていないか（公開更新予定。トップ表示にも反映する）

## ② 選定

次の一手を**1つ**選ぶ。優先順位ルール:

1. **公開済みページの破損・バグ**（最優先）
2. **blocked の解除** — 人間への依頼事項を明確にして報告
3. **未完テーマの次工程を1つ進める** — 完成に近いテーマから
4. **collect_at を過ぎたテーマのデータ補充**
5. **新テーマの追加** — 2日に1本ペース、全テーマがdoneに近いときのみ

## ③ 発注

`configs/prompts/` にワーカープロンプトを生成する。

命名規則: `{YYYYMMDD}_{theme}-{工程}.md`
配置先: テーマに応じて `configs/prompts/hermes/` or `configs/prompts/claude-code/`

共通の制約（必ず含める）:
- GA4: `G-K10S4YCZFH`
- AdSense: `ca-pub-2542211932832864`
- OGP/SEO meta を維持
- Supabase接続を維持
- ブランチ: `task/{theme}-{工程}`
- 座標対応表は自テーマのデータから導出（他テーマからの流用禁止）

## ④ 検証

ワーカー報告後、ハブがブラウザ検証を行う:
- コンソールエラーなし
- 375px幅で横スクロールなし
- 保護タグgrep（GA4/AdSense/Supabase/OGP）

## ⑤ 統合

- main へマージ
- THEMES.yaml 更新
- 必要なら人間に手動作業を依頼（画像生成など）

## ⑥ ループ

①へ戻る。

---

## 漫画プロンプト作成ルール

`manga-prompts/{theme}-prompts.md` を新規作成するときの必須チェック:

- **本番ページ生成プロンプトの末尾に必ず比率を明記する**
  - `Output image: portrait, 3:4 aspect ratio (e.g. 900×1200px).`
  - HTMLの `.manga-page-card img` は `aspect-ratio:3/4` で固定されているため、正方形や横長で生成すると上下または左右が切れる
- キャラシートは比率指定不要（HTMLには表示しない）
- 保存時の WebP 変換・リサイズ基準（漫画≤100KB、900px）は変わらない

## データ補充（refresh）完了後の更新チェックリスト

collect_at を迎えたテーマにデータを追加した後、以下を順番に確認する。

### 1. データ分類

- [ ] Yahoo リアルタイム検索で収集（fetch_yahoo_realtime_node.mjs / fetch_topic_refresh.py）
- [ ] 重複チェック（既存 tweet_id と照合、件数を記録）
- [ ] Hermes 分類実行（classify_{theme}_arena_hermes.py）
- [ ] 新規分類データを既存 `{theme}_hermes_arena_classified.json` にマージ

### 2. THEMES.yaml

- [ ] `updated_at` → 今日の日付
- [ ] `collect_delta` → 今回追加件数（重複除外後）
- [ ] `collect_at` → 次回の収集・staging作成予定日
- [ ] `refresh_at` → 次回目安日（通常1週間後）

### 3. テーマページ（潮目ウィジェットがある場合）

- [ ] `tide-widget-period` テキスト（例: 6月27日 → 7月26日）
- [ ] SVG `tide-slope-date` テキスト（前回/今回の日付）
- [ ] `aria-desc` 内の件数
- [ ] `datasets` JS変数（`max`・`headline`・`rows` の `previous`/`current` 値）
- [ ] `tide-widget-note` 注釈テキスト（収集件数・日付・背景説明）

### 4. テーマページ（insight-stats カード 4枚）

- [ ] 「分析対象の意見」件数（`insight-value`）
- [ ] 「最も多い立場」% + 件数注（`insight-note`）+ `insight-meter` 幅
- [ ] 「最も話された論点」件数（`insight-value`）
- [ ] 「論点による逆転」注釈（件数が変わる場合）
- [ ] ヒーローセクション「議論の中心」バッジ件数（`conclusion-count`）
- [ ] lead文の件数
- [ ] `data-method` テキスト（データの集め方）

### 5. index.html（ポータル）

- [ ] `rank-card` スタンス比率バー（`rank-dist` + `rank-track` の4項目）
- [ ] 割れ度スコア（`split-score` の meter 幅 + 数値）
- [ ] スコアが変動した場合: `rank-num` 順位番号 + カードの DOM 順序を更新
- [ ] `topic-card` スタンス比率バー（`topic-percent` + `topic-bar` の各項目）
- [ ] `topic-card` 件数（`topic-meta` 内の「投稿 XX件」）
- [ ] `topic-card` 更新バッジ（`.topic-fresh` テキストと日付）
- [ ] badge data `B` 変数（`upd` → 今日の日付、`delta` → 今回追加件数）
- [ ] `hero-total-samples` → 全テーマ topic-card 件数の合計に更新
- [ ] `hero-total-samples` の横の更新日テキスト（例: `7/26更新`）

### 6. sitemap.xml

- [ ] 該当テーマの `lastmod` → 今日の日付

### 7. 論点カードの件数

- [ ] `python3 scripts/sync_issue_counts.py {theme}` を実行（件数は分類結果から生成する。HTMLに直接書かない）
- [ ] 論点のラベルが変わった場合は `configs/{theme}-reaction-map.json` の `issue_counts.cards` を先に直す
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] `data/issue-counts/` を source にしているテーマ（constitutional-amendment / elderly-license-revocation / henoko-student-accident / koshitsu-tenpakai）は、再分類したら `issue_counts.source` を `sample_file` へ戻す（TASK_BOARD 課題29）

---

**注意事項:**
- `hero-total-samples` は全 topic-card の「投稿 XX件」の合計値。新テーマ公開直後に更新漏れが起きやすいので都度合算して確認する。
- 割れ度スコアを変更するとランキング順位も変わる。DOM 順序（first-child が金色）も連動して並び替えること。
- 論点アリーナ（P=[...] データ）は今回の分類結果を反映していないが、潮目ウィジェットで最新比較を表示しているため、現状はそのままでよい。

---

## 人間（オーナー）の役割

- プロンプトの受け渡し（ワーカーAIへの入力）
- 画像生成（GPTimage2）
- AdSense/GA4などの管理画面操作
- 最終判断が必要な場面での意思決定

判断はループが行う。人間は実行のみ。
