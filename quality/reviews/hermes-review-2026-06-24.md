# Hermes レビューフィードバック — 2026-06-24

レビュアー: Claude Code（ハブ）

## 状態: 課題1 作業完了 → レビュー指摘あり

Hermes による成果物がリポジトリに反映されました。大幅なリデザインと品質改善。

---

## 対象成果物

| ファイル | 内容 |
|---------|------|
| `docs/index.html` (378行・全面リライト) | ポータルページ公開向けリデザイン |
| `docs/ai-copyright-reaction-map.html` (899行・新規) | 生成AIと著作権問題 |
| `docs/school-nickname-ban-reaction-map.html` (901行・新規) | あだ名禁止の是非 |
| `docs/takaichi-reaction-map-standard.html` (878行・新規) | 高市文春・中傷動画問題 |
| `docs/henoko-student-accident-reaction-map.html` (1037行・新規) | 辺野古高校生死亡事故 |
| `docs/constitutional-amendment-reaction-map.html` (969行・新規) | 憲法改正論議 |
| `docs/favicon.ico` (マルチサイズ 16x16/32x32) | favicon |
| `docs/favicon.svg` | SVGfavicon |
| `docs/ogp/default.png` (1200x630) | OGP画像 |

## 総合評価: ⭐⭐⭐⭐☆

レビュー指示の大半を高品質に実装。ポータルのリデザイン・全5トピックの反応マップ新規作成・favicon/OGP対応まで一気に完了。いくつかの修正点あり。

---

## 良い点

- **ポータルの完全リデザイン**: 「編集用ポータル」→「投票参加型メディア」に文言刷新。キャッチコピー「その話題、SNSでは実はどっちが多い？」を目立つ位置に配置
- **投票CTAの追加**: 全トピックカードに「投票してみる→」ボタン。導線が明確
- **管理画面風UIの排除**: 「登録テーマ6」等の内部統計を削除、「今週の注目トピック」に変更
- **サンプル0トピック（議員定数削減）の除外**: 公開に不要なカードを正しく除去
- **全5トピックの反応マップ新規作成**: SEOメタタグ・favicon・OGP参照を含む完全なHTML
- **投票UIのクリーン実装**: localStorage方式の投票機能。CSS `color:` / `width:` の使い方も正しい（Antigravity2版のバグなし）
- **投票やり直し・X共有**: 両方実装済み
- **favicon**: ICO（マルチサイズ）+ SVG の2形式対応
- **OGP画像**: 1200x630の正規サイズ
- **デザインシステム**: CSS変数ベースの統一デザイン。レスポンシブ対応（720pxブレークポイント）

---

## 要修正（必須）

### 1. 【バグ】簡体字の混入（index.html:354行）

```
紧急事態条項
```

「紧」は簡体字。正しくは「**緊**急事態条項」。

**対応**: `紧急` → `緊急` に修正。

### 2. OGP画像が相対パス（全ページ）

```html
<meta property="og:image" content="ogp/default.png">
```

OGP画像のURLは絶対パスでないとSNSのクローラーが正しく取得できない。デプロイ後に `https://YOUR-DOMAIN/ogp/default.png` に更新する必要がある。

**対応**: GitHub Pages のURL確定後に全ページの `og:image` を絶対URLに更新。Codexの `scripts/seo/apply_meta_tags.py` でも対応可能。現時点ではブロッカーではない（デプロイ時に対応）。

### 3. フッターのGitHubリンクが汎用URL（index.html:374行）

```html
<a href="https://github.com/">ソースコード</a>
```

実際のリポジトリURLに差し替えるか、非公開リポジトリなら項目自体を削除。

---

## 確認事項（要相談）

### 4. Supabase連携との統合

Hermesの反応マップページはlocalStorageのみの投票実装。Antigravity2が `build_reaction_map.py` にSupabase連携を追加済みだが、Hermesの手書きHTMLには含まれていない。

**選択肢**:
- (A) Hermesのページをそのまま使い、Supabase連携は後から追加（推奨: 公開優先）
- (B) `build_reaction_map.py` で再生成してSupabase対応版にする

→ 公開初期はlocalStorageで十分なので **(A)推奨**。Supabase統合は課題2の後続タスクで対応。

### 5. build_site_portal.py との関係

Hermesがindex.htmlを直接編集したため、`build_site_portal.py` で再生成するとHermesの変更が上書きされる。

**対応案**: 
- `build_site_portal.py` の自動生成は開発用として残し、公開版はHermes版を正とする
- または `build_site_portal.py` にHermesのデザインを反映して同期する

---

## 改善提案（任意）

### 6. canonical URLの追加

各ページに `<link rel="canonical">` がない。SEO観点で追加が望ましい。デプロイ後にCodexの `apply_meta_tags.py` で一括対応可能。

### 7. 「投票データはお使いのブラウザに保存されます」の文言

Supabase統合時にこの文言を更新する必要がある。現時点では正確。

---

## チェックリスト（前回指示の達成状況）

- [x] ポータルページの公開向けリデザイン
- [x] キャッチコピー・CTA追加
- [x] 管理画面風の文言・統計を削除
- [x] レスポンシブ対応確認
- [x] favicon作成・配置
- [x] 各トピックページの品質確認（全5ページ新規作成）
- [x] OGP画像プレースホルダー作成
- [x] 企画中トピック（サンプル0）の非表示対応

## 残対応チェックリスト

- [ ] `紧急` → `緊急` の簡体字修正（index.html:354行）
- [ ] フッターのGitHubリンクを実際のURLに修正 or 削除
- [ ] （デプロイ時）OGP画像パスを絶対URLに更新
