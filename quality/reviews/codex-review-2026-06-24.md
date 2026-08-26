# Codex レビューフィードバック — 2026-06-24

レビュアー: Claude Code（ハブ）

## 対象成果物

| ファイル | 内容 |
|---------|------|
| `tools/seo/generate_seo_assets.py` | sitemap.xml / robots.txt 生成 |
| `tools/seo/apply_meta_tags.py` | OGP / Twitter Card メタタグ一括適用 |
| `docs/seo-setup.md` | SEOセットアップ手順書 |
| `data/supabase_schema.sql` | 投票テーブルスキーマ |

## 総合評価: ⭐⭐⭐⭐☆

全体として品質が高く実用的。以下の対応が必要。

---

## 要対応（必須）

### 1. `data/supabase_schema.sql` は担当外 → Antigravity2に引き継ぎ
- これは課題2（投票バックエンド）の領域であり、Antigravity2の担当
- Codex側での追加作業は不要。ファイルはそのまま残してよい
- **Codex側のアクション: なし（認識だけしておく）**

### 2. `tools/seo/` のディレクトリ配置を修正
- 既存スクリプトは `scripts/` に統一されている
- `tools/seo/` → `scripts/seo/` に移動する
- 移動後、`docs/seo-setup.md` 内のパス参照も更新する
- **対象ファイル**:
  - `tools/seo/generate_seo_assets.py` → `scripts/seo/generate_seo_assets.py`
  - `tools/seo/apply_meta_tags.py` → `scripts/seo/apply_meta_tags.py`
  - `docs/seo-setup.md` 内の `tools/seo/` → `scripts/seo/`

### 3. OGP画像が存在しない場合のフォールバック
- `apply_meta_tags.py` が `ogp/default.png` を参照するが、このファイルは存在しない
- 対応として以下のいずれか:
  - (A) `og:image` を画像が存在する場合のみ出力するようにする
  - (B) プレースホルダー画像 `docs/ogp/default.png` を作成する
- 推奨: (A) — 画像なしで壊れたURLを入れるよりマシ

## 追加作業（課題3スコープ内の残タスク）

### 4. Google Analytics 導入スクリプト
- 課題3のスコープに「Google Analytics / Search Console 導入」があるが、GA部分が未実装
- `apply_meta_tags.py` と同様のマーカー方式で、GAスニペットを全HTMLに一括挿入するスクリプトを作る
- GA IDはコマンド引数で渡す形式にする

---

## 対応不要（参考情報）

- sitemap.xml の `<lastmod>` が全ページ同一日付 → 静的サイトなので許容
- supabase_schema.sql の `md5` ハッシュ → Antigravity2側で改善判断する
- `SECURITY DEFINER` 関数の環境依存 → Antigravity2側で対応

---

## チェックリスト

- [x] `tools/seo/` → `scripts/seo/` に移動
- [x] `docs/seo-setup.md` のパス参照を更新
- [x] `apply_meta_tags.py` のOGP画像フォールバック対応
- [x] GA導入スクリプト作成

## Codex対応メモ

対応日: 2026-06-24

- SEOスクリプトを `scripts/seo/` 配下へ移動。
- `docs/seo-setup.md` と `TASK_BOARD.md` の実運用パスを `scripts/seo/` に更新。
- `docs/ogp/default.png` が存在しない場合、`apply_meta_tags.py` は `og:image` / `twitter:image` を出力しないよう修正。
- `scripts/seo/apply_ga_tags.py` を追加し、GA4測定IDを引数で渡して全HTMLへマーカー付きで挿入できるようにした。
