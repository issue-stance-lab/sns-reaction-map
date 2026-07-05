# {タスク名}

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- テーマ台帳: THEMES.yaml を参照
- 技術スタック: 静的HTML / CSS / JS（GitHub Pages）
- 本タスクの対象テーマ: {theme}
- 対象ファイル: {files}

## 背景

{背景の説明: なぜこのタスクが必要か、前提条件は何か}

## あなたのタスク

{具体的な作業内容を箇条書きで}

## 保護タグ（絶対に維持すること）

HTML変更時は以下のタグが維持されていることを確認:

- **GA4**: `G-K10S4YCZFH`（`<script>` タグ）
- **AdSense**: `ca-pub-2542211932832864`（`<script>` タグ + `<meta>` タグ）
- **Supabase**: `supabaseUrl` / `supabaseKey` 変数（投票機能）
- **OGP/SEO**: `<meta property="og:*">` / `<meta name="twitter:*">` / `<link rel="canonical">`
- **Buy Me a Coffee**: `buymeacoffee.com/issue.stance.lab`

## ブランチ運用

- 作業ブランチ: `task/{theme}-{工程}`
- main に直接コミットしない
- 完了後 PR 作成（マージはハブが行う）

## 技術的制約

- canvas ID は `smCanvasMain` / `smCanvasHeat` を使用（正典ID）
- 投票選択肢→2D座標の対応表は、自テーマの2D分類データから独自に導出すること（他テーマからの流用禁止）
- `ctx.filter` は使用禁止（Safari非対応）
- CSS特異度: セクション固有スタイルは `.stance-map-section .xxx` で囲む
- 画像: WebP形式、漫画ページ100KB以下、投票画像240×240 20KB以下、`loading="lazy"` 必須

## 完了条件

- [ ] {具体的な完了条件1}
- [ ] {具体的な完了条件2}
- [ ] 保護タグgrep確認（GA4/AdSense/Supabase/OGP）
- [ ] コンソールエラーなし
- [ ] 375px幅で横スクロールなし

## 報告フォーマット

作業完了時に以下を出力:

```
### 変更サマリー
- 変更ファイル一覧と概要

### grep確認結果
- GA4: OK/NG
- AdSense: OK/NG
- Supabase: OK/NG
- OGP: OK/NG
- Buy Me a Coffee: OK/NG

### 迷った点・人間への質問
- （あれば記載）
```
