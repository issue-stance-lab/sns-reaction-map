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
- refresh_at を過ぎていないか

## ② 選定

次の一手を**1つ**選ぶ。優先順位ルール:

1. **公開済みページの破損・バグ**（最優先）
2. **blocked の解除** — 人間への依頼事項を明確にして報告
3. **未完テーマの次工程を1つ進める** — 完成に近いテーマから
4. **refresh_at を過ぎたテーマのデータ補充**
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

## 人間（オーナー）の役割

- プロンプトの受け渡し（ワーカーAIへの入力）
- 画像生成（GPTimage2）
- AdSense/GA4などの管理画面操作
- 最終判断が必要な場面での意思決定

判断はループが行う。人間は実行のみ。
