# グロース施策: design-tokens-unify

## 目的

全テーマの配色・フォント・余白のばらつきを減らし、初見の「作りかけ感」を下げる。

対象施策:

- `GROWTH.yaml` capabilities `design-tokens-unify`
- 仮説: ページごとにトーンがバラつくと再訪意欲を下げる。共通CSSトークン化で一貫した世界観にする
- 指標: 直帰率、pages_per_session（間接指標。主目的はサイト魅力）

## ブランチ

- `task/growth-design-tokens-unify`
- main 直接コミット禁止

## 対象

全公開ページ:

- `docs/index.html`
- `docs/ai-copyright-reaction-map.html`
- `docs/bike-blue-ticket-reaction-map.html`
- `docs/bukatsu-chiiki-reaction-map.html`
- `docs/constitutional-amendment-reaction-map.html`
- `docs/elderly-license-revocation-reaction-map.html`
- `docs/school-nickname-ban-reaction-map.html`
- `docs/henoko-student-accident-reaction-map.html`
- `docs/takaichi-reaction-map-standard.html`
- `docs/about.html`
- `docs/privacy.html`
- `docs/disclaimer.html`

## 実装要件

1. 共通CSSトークンを `docs/site-tokens.css` として新規作成する。
2. 各HTMLから `<link rel="stylesheet" href="site-tokens.css">` で読み込む。
3. 既存のテーマ固有アクセントは残すが、以下の基礎トークンは共通化する。
   - `--bg`
   - `--ink`
   - `--muted`
   - `--line`
   - `--panel`
   - `--shadow`
   - `--font`
   - `--radius`
4. 既存CSSのうち、上記と同じ値を各ページで重複定義している箇所を削減する。
5. テーマごとの意味色・チャート色・投票選択肢色は変更しない。
6. `docs/index.html` のファーストビュー構造や featured slot の表示位置は変更しない。
7. 計測中施策を壊さない。
   - `share-after-vote`: Xシェア文言・URL・UTMを変更しない
   - `related-themes-block`: 関連テーマリンク・`related_theme_click` イベントを変更しない
   - `portal-featured-slot`: featured テーマ指定やカード遷移を変更しない
   - `x-post-templates`: `docs/x-posts.md` は変更しない
8. 見た目の差分は「整理」に留める。大規模なリデザイン、ヒーロー改修、カード構成変更はしない。

## 保護タグ・保持条件

以下は絶対に壊さない。

- GA4: `G-K10S4YCZFH`
- AdSense: `ca-pub-2542211932832864`
- Supabase投票ロジック
- OGP / SEO meta
- `#smCanvasMain` / `#smCanvasHeat`
- 既存の投票後Xシェア導線と `utm_source=share_button`
- 関連テーマクリック計測 `related_theme_click`

## 検証

最低限、以下を確認して報告する。

1. 代表3ページ（`index.html`、`school-nickname-ban-reaction-map.html`、`takaichi-reaction-map-standard.html`）でコンソールエラーがない。
2. 代表3ページで 375px 幅の横スクロールがない。
3. 代表3ページで主要UI（hero、投票ボタン、スタンスマップ、関連テーマ）が崩れていない。
4. 保護タグgrep:
   - `G-K10S4YCZFH`
   - `ca-pub-2542211932832864`
   - `og:image` または `twitter:image`
   - `supabase`
5. `share-after-vote` のシェアリンクに `utm_source=share_button` が残っている。
6. `related_theme_click` が残っている。

## 完了状態

この施策は、実装と検証が済んだら `built` 扱いにする。計測開始タイミングは、既存の全ページ横断施策の判定日を見てハブが決める。

成果物:

- 実装ブランチ
- 変更ファイル一覧
- 検証結果
- `GROWTH.yaml` の `design-tokens-unify.status` を `built` に更新する提案
