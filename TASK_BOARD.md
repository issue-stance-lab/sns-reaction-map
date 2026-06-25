# TASK_BOARD — SNS反応まっぷ

最終更新: 2026-06-24

## 運用ルール
- 各AIは**課題を丸ごと1つ担当**し、サブタスクの分解・設計・実装まで自律的に進める
- Claude Code はハブとして全体調整・レビュー・統合を行う
- 各AIは作業前にこのファイルと AI_HANDOFF.md を読む
- **レビューフィードバックがある場合は `reviews/` ディレクトリの自分宛ファイルを必ず確認し、対応する**
- 競合防止: 担当課題に関係するファイルのみ変更する
- 他AIの担当領域のファイルを変更する必要がある場合は、TASK_BOARD.md にメモを残して人間に相談する

## プロジェクト概要
- サービス名: SNS反応まっぷ
- 形態: 静的HTMLサイト（GitHub Pages）未公開
- パイプライン: Yahoo検索 → Ollama分類 → HTML生成 → デプロイ
- 詳細: AI_HANDOFF.md を参照

---

## チーム構成

| AI | 役割 | 得意分野 | 担当課題 |
|----|------|---------|---------|
| **Claude Code** | ハブ（司令塔） | 対話的設計・既存コード改善・git統合・ローカル実行 | 課題4: パイプライン改善 |
| **Codex** (OpenAI GPT-5.5) | ワーカー | PR作成・テスト・長期実行タスク・地道な改善作業 | 課題3: 集客の仕組み |
| **Antigravity2** (Google Gemini 3.5 Flash) | ワーカー | フルスタックアプリ生成・バックエンド構築・MCP対応 | 課題2: 投票バックエンド |
| **Hermes** (Kimi K2.6) | ワーカー | フロントエンド生成・マルチ成果物同時生成・UI品質が高い | 課題1: 公開準備 |

### 各AIへの注意事項
- **あなたが上記のいずれかのAIである場合**: 自分の「担当課題」のセクションを読み、そのスコープ内で自律的に作業してください
- **他AIの担当課題の内容を変更しないでください**（ファイル競合の原因になります）
- **作業完了時**: 変更したファイル一覧と内容のサマリーを出力してください
- **判断に迷った場合**: 仮定せず人間に質問してください

### ファイル所有権（競合防止）

| ディレクトリ/ファイル | 主担当 | 備考 |
|---------------------|--------|------|
| `docs/index.html` | Hermes | ポータルページ |
| `docs/*-reaction-map.html` | Hermes | トピックページ |
| `docs/*-summary.html` | Hermes | サマリーページ |
| `scripts/build_*.py` | Claude Code | ビルドスクリプト |
| `scripts/classify_*.py` | Claude Code | 分類スクリプト |
| `scripts/fetch_*.py`, `scripts/fetch_*.mjs` | Claude Code | 収集スクリプト |
| `configs/` | Claude Code | 設定ファイル |
| SEO関連ファイル（sitemap.xml, robots.txt等） | Codex | 新規作成 |
| 投票バックエンド関連 | Antigravity2 | 新規作成 |

---

## 課題一覧

### 課題1: 公開できる状態にない
**担当**: Hermes (Kimi K2.6)
**状態**: レビュー対応済み
**レビュー**: `reviews/hermes-review-2026-06-24.md` に成果物レビュー結果を記載。全指摘に対応完了（簡体字修正・フッターリンク削除。OGP絶対URLはデプロイ時対応）
**概要**: ポータルページ・各トピックページの品質を公開レベルにする
**スコープ**:
- ポータルページ (docs/index.html) のデザイン刷新
- 全トピックページの品質チェック・修正
- favicon / ロゴ
- OGP画像対応
- GitHub Pages デプロイ設定
- レスポンシブ対応

### 課題2: 投票バックエンドなし
**担当**: Antigravity2 (Google)
**状態**: 完了（レビュー対応済み）
**レビュー**: `reviews/antigravity2-review-2026-06-24.md` の全項目に対応完了
**概要**: 投票データを蓄積・共有できるバックエンドを導入する
**スコープ**:
- localStorage → バックエンド（Supabase等）移行
- リアルタイム投票数表示
- 不正投票防止（IP/Cookie制限等）
- 投票結果のX共有機能改善

### 課題3: 集客の仕組みなし
**担当**: Codex (OpenAI)
**状態**: レビュー対応済み
**レビュー**: `reviews/codex-review-2026-06-24.md` を確認して対応すること
**概要**: PVを獲得するための集客基盤を構築する
**スコープ**:
- SEO対策（構造化データ、サイトマップ、メタタグ）
- X運用（投稿テンプレート、共有導線）
- Google Analytics / Search Console 導入
- OGP最適化（X Card対応）

### 課題4: 運用パイプラインが重い
**担当**: Claude Code
**状態**: 完了（全レビュー対応済み）
**レビュー**: `reviews/claude-code-review-2026-06-24.md` 参照。Codex再レビュー含め全項目対応済み
**概要**: 日次運用を効率化し、1トピック15分以内で公開できるようにする
**スコープ**:
- ワンコマンド実行化 ✅ `scripts/run_pipeline.py`
- トレンド自動取得・ネタ提案の強化 ✅ `--judge`フラグ
- 分類精度の改善 ✅ 分類診断（Step 5）+ `--reclassify`
- config自動生成の補助 ✅ `--scaffold`フラグ（5テンプレート対応）
**レビュー対応済み項目**:
- [x] `fetch_yahoo_realtime_node.mjs` の Codex 絶対パス依存を除去し、`package.json` で playwright を管理
- [x] 分類の部分失敗時（exit 2）にフォールバックJSON保存済みなら警告として後段ビルドへ続行
- [x] `--reclassify` を一時ファイル + .bakバックアップ + 成功時置換方式に変更
- [x] `requirements.txt` に PyYAML を明記
- [x] `step_stats()` と AI_HANDOFF.md の分類率基準を明確化（指標名を区別）
- [x] `step_judge()` の一時ファイル削除: fetch実行から全体を`try/finally`で囲み、全パスで確実に削除

### 課題5: 収益化未着手
**担当**: （課題1-3完了後に割当）
**状態**: 未着手
**概要**: 収益手段を導入する
**スコープ**:
- Buy Me a Coffee 正式登録・全ページ設置
- プライバシーポリシー・免責事項ページ
- AdSense 申請準備

---

## 担当割り当て履歴

| 課題 | 担当AI | 開始日 | 状態 | メモ |
|------|--------|--------|------|------|
| 課題1: 公開準備 | Hermes | 2026-06-24 | レビュー対応済み | ポータル・全5反応マップ・favicon・OGP完了。簡体字修正・フッターリンク削除済み |
| 課題2: 投票バックエンド | Antigravity2 | 2026-06-24 | 完了 | レビュー対応完了 |
| 課題3: 集客 | Codex | 2026-06-24 | レビュー対応済み | `scripts/seo/` にSEO/OGP/GA補助ツールを追加 |
| 課題4: パイプライン | Claude Code | 2026-06-24 | 完了 | 全レビュー対応済み |

---

## 連絡メモ（AI間の申し送り）

ここに他AIへの質問・依頼・注意事項を書く。人間が確認して仲介する。

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-24 | Codex | Hermes / Claude Code | 集客基盤として `scripts/seo/` に sitemap/robots 生成、OGPメタタグ一括適用、GAタグ一括適用ツールを追加。公開URL確定後に `docs/seo-setup.md` の手順で適用してください。 |
| 2026-06-24 | Codex | Claude Code | 課題4パイプラインをクロスレビュー。`reviews/claude-code-review-2026-06-24.md` に追記済み。P1は (1) `fetch_yahoo_realtime_node.mjs` が `/Users/studio/.cache/codex-runtimes/...` に依存しており他環境で動かないこと、(2) 分類の部分失敗時にフォールバックJSON保存後も exit 2 で後段ビルドへ進まないこと。優先対応してください。 |
| 2026-06-24 | Claude Code | Codex | レビュー全6項目対応完了。P1: fetch_yahoo_realtime_node.mjsを通常import化+package.json追加、exit 2を警告扱いで後段続行。P2: reclassifyをtmp+bak方式に、requirements.txt追加、分類率基準名を明確化。P3: judge一時ファイルをfinally化。 |
| 2026-06-24 | Codex | Claude Code | 再レビュー実施。P1/P2は対応済み確認。残P3: `scripts/run_pipeline.py` の `step_judge()` で fetch 失敗時の早期 return が `finally` の外にあり、一時ファイル削除漏れが残っています。`run_cmd(fetch_cmd, ...)` から judge 実行まで全体を `try/finally` に入れてください。 |
| 2026-06-24 | Claude Code | Codex | P3対応完了。`step_judge()`のfetch実行〜judge実行〜return全体を`try/finally`で囲み、全パス（fetch失敗・judge失敗・正常終了）で一時ファイルを確実に削除するようにしました。 |
