# 課題26 Phase F: パフォーマンス最適化

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- 現在のタスク一覧: TASK_BOARD.md を参照（**課題26 Phase Fのセクションを必ず読むこと**）
- 技術スタック: 静的HTML（GitHub Pages）

## 背景

課題26 Phase A〜Eで、v3フォーマット移行・ポータル刷新・旧ページ削除が完了した。Phase Fでは、残存するパフォーマンス上の問題を解消し、モバイルでの体験品質を向上させる。

## 作業1: PNG重複ファイルの削除

`docs/images/` に `.webp` ファイルと同名の `.png` ファイルが18枚残存しており、不要なサイズを消費している。WebP版が存在するPNGのみを `git rm` で削除する。

**削除対象（WebPが存在するPNGのみ）**:

以下コマンドで削除対象を特定してから実行すること:
```bash
for f in docs/images/*.png; do
  base="${f%.png}"
  if [ -f "${base}.webp" ]; then
    echo "$f"
  fi
done
```

**注意**: WebP版が存在しないPNGは削除しない。

### HTMLファイルの参照確認

PNG削除後、各HTMLファイルが `.png` を参照していないかを確認する。

```bash
grep -rn '\.png' docs/*.html
```

`.png` を参照している箇所があれば `.webp` に書き換える（ただし OGP / og:image は `png`のまま維持してよい。大半のSNSクローラーはWebPに対応していないため）。

---

## 作業2: 画像への `loading="lazy"` 追加

v3形式の5テーマ（ai-copyright / bike-blue-ticket / bukatsu-chiiki / constitutional-amendment / elderly-license-revocation）の `*-reaction-map.html` において、`<img>` タグに `loading="lazy"` が付いていないものを補完する。

**確認コマンド**:
```bash
for f in docs/ai-copyright-reaction-map.html docs/bike-blue-ticket-reaction-map.html docs/bukatsu-chiiki-reaction-map.html docs/constitutional-amendment-reaction-map.html docs/elderly-license-revocation-reaction-map.html; do
  echo "=== $f ==="
  grep -n '<img' "$f"
done
```

- ヒーロー画像（ファーストビューに表示されるもの）は `loading="lazy"` を付けない（LCP に影響するため）
- 漫画ページ画像・キャラクターシート画像・投票ボタン画像にはすべて `loading="lazy"` を付ける

---

## 作業3: スクリプトの遅延読み込み

各 `*-reaction-map.html` において、GA4・AdSense以外の外部スクリプトに `defer` を追加する。

**対象候補**:
- Twitter/X Widgets: `<script async src="https://platform.twitter.com/widgets.js">`
  - `async` がすでに付いている場合はそのまま（`async` で問題なし）
- Buy Me a Coffee ボタン: `<script ... src="https://cdnjs.buymeacoffee.com/...">` がある場合は `defer` を追加

**変更してはならないもの**:
- GA4タグ（`G-K10S4YCZFH`）は現在の `async` 属性のまま維持
- AdSenseコード（`ca-pub-2542211932832864`）は変更しない
- Supabase の `<script>` は変更しない
- インライン `<script>` ブロック（`<script>` タグの中にコードが書かれているもの）は変更しない

---

## 制約・注意

- **変更してよいファイル**:
  - `docs/images/` のPNGファイル（`git rm` で削除）
  - v3形式の5テーマ `*-reaction-map.html`（`loading="lazy"` 追加・`.png` → `.webp` 参照修正・`defer` 追加）
  - 旧形式3テーマ（takaichi / henoko / school）の HTML は変更しない
- `docs/index.html` の変更は最小限に（OGP img参照の `.png` → `.webp` 書き換えは対象外）
- **絶対に維持するもの**（削除・破壊禁止）:
  - GA4タグ: `G-K10S4YCZFH`
  - AdSenseコード: `ca-pub-2542211932832864`
  - OGP/canonicalタグ（`SEO_META_START` / `SEO_META_END` ブロック）
  - Supabase URL / API キー

### ブランチ運用

- mainに直接コミットしない。ブランチ `task/26-phasef-performance` で作業し、完了後PRを作成する（マージはClaude Codeが行う）

---

## 完了条件・報告

1. WebPと重複していたPNGファイルが `git rm` で削除されている（削除件数を報告する）
2. 各v3 HTMLファイルの `<img>` タグに `loading="lazy"` が適切に付いている（ヒーロー画像は除く）
3. 外部スクリプトの `defer` / `async` 状態を確認し、変更した箇所を報告する
4. HTMLのOGP以外の `.png` 参照が `.webp` に置き換えられている（または変更不要だった場合はその旨報告）
5. GA4 / AdSense / OGPタグの残存をgrepで確認した結果を報告する
6. 変更内容のサマリーを出力する
7. 判断に迷った点・仮定した点を明記する
