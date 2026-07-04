# 課題26 Phase E: 旧世代ページの整理・削除 + sitemap.xml更新

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- 現在のタスク一覧: TASK_BOARD.md を参照（**課題26 Phase Eのセクションを必ず読むこと**）
- 技術スタック: 静的HTML（GitHub Pages）

## 背景

課題26 Phase A〜Dで、v3トピックページへの移行・ポータル刷新が完了した。現在 `docs/` には、過去のセッションが生成した旧世代ページが残存し、SEO上のノイズになっている。Phase Eではこれらを削除し、`sitemap.xml` を現行ページ構成に合わせて更新する。

## 作業1: 旧世代ページの削除（6ファイル）

以下のファイルを **git rm** で削除すること（単なるファイル削除ではなくgit管理下から除去する）。

| ファイル | 削除理由 |
|---------|---------|
| `docs/theme-preview.html` | 開発時のデザインプレビュー用。公開不要 |
| `docs/takaichi-reaction-heatmap.html` | taikaichiの旧ヒートマップ。`takaichi-reaction-map-standard.html`（アーカイブ済み）に統合済み |
| `docs/constitutional-amendment-dashboard.html` | 旧ダッシュボード。`constitutional-amendment-reaction-map.html`（v3）に統合済み |
| `docs/constitutional-amendment-summary.html` | 旧サマリーページ |
| `docs/henoko-summary.html` | 旧サマリーページ |
| `docs/takaichi-summary.html` | 旧サマリーページ |

**削除前に確認すること**: 上記ファイルへのリンクが `docs/index.html` および各 `*-reaction-map.html` に残っていないことをgrepで確認する。残っている場合はリンクを除去してから削除する。

## 作業2: sitemap.xml の更新

`docs/sitemap.xml` を現行の公開ページ構成に書き直す。

**現在のsitemap.xml**（古い・不完全な状態）には以下の問題がある:
- 削除対象の旧世代ページURLが含まれている
- v3化完了テーマ（bike-blue-ticket / elderly-license-revocation）がない
- 旧3テーマ（takaichi / henoko / school）がアーカイブ状態なのに `priority` が高いまま

**更新後のsitemap.xmlに含めるページ**:

| URL | changefreq | priority | 備考 |
|-----|-----------|---------|------|
| `index.html` | weekly | 1.0 | ポータル |
| `ai-copyright-reaction-map.html` | weekly | 0.9 | v3テーマ |
| `bike-blue-ticket-reaction-map.html` | weekly | 0.9 | v3テーマ（新規追加） |
| `bukatsu-chiiki-reaction-map.html` | weekly | 0.9 | v3テーマ |
| `constitutional-amendment-reaction-map.html` | weekly | 0.9 | v3テーマ |
| `elderly-license-revocation-reaction-map.html` | weekly | 0.9 | v3テーマ（新規追加） |
| `takaichi-reaction-map-standard.html` | monthly | 0.4 | アーカイブ（旧形式） |
| `henoko-student-accident-reaction-map.html` | monthly | 0.4 | アーカイブ（旧形式） |
| `school-nickname-ban-reaction-map.html` | monthly | 0.4 | アーカイブ（旧形式） |
| `privacy.html` | yearly | 0.3 | |
| `disclaimer.html` | yearly | 0.3 | |

**削除するURL**（上記に含まれないもの）:
- `constitutional-amendment-dashboard.html`
- `constitutional-amendment-summary.html`
- `henoko-summary.html`
- `takaichi-reaction-heatmap.html`
- `takaichi-summary.html`

**lastmod** は各URLで `2026-07-05` に統一してよい。ベースURLは `https://issue-stance-lab.github.io/sns-reaction-map/` を使うこと。

## 制約・注意

- **変更してよいファイル**:
  - `docs/sitemap.xml`（更新）
  - 上記6ファイルの削除（`git rm`）
  - リンク除去が必要な場合のみ `docs/index.html` または各HTMLファイルの該当箇所のみ
- `docs/index.html` の GA4・AdSense・OGPタグは変更しない
- `docs/robots.txt` に `sitemap.xml` のURLが記載されている場合はそのまま維持する

### ブランチ運用

- mainに直接コミットしない。ブランチ `task/26-phasee-cleanup` で作業し、完了後PRを作成する（マージはClaude Codeが行う）

## 完了条件・報告

1. 6ファイルが `git rm` で削除されている（`git status` で確認）
2. `docs/sitemap.xml` が上記11URLの構成に更新されている
3. 削除ファイルへのリンクが他ページに残っていないことをgrepで確認した結果を報告する
4. 変更内容のサマリーを出力する
5. 判断に迷った点（リンク残存の有無など）を明記する
