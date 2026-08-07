# school-nickname-ban v3化（旧形式→2Dスタンスマップ統合ページ）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- テーマ台帳: THEMES.yaml を参照
- v3仕様書: `templates/topic-page-v3.md`（必読）
- 本タスクの対象テーマ: school-nickname-ban（学校でのあだ名禁止の是非）
- 対象ファイル: `docs/school-nickname-ban-reaction-map.html`

## 背景

school-nickname-banは現在「旧形式」バナーが付いた旧ページのまま残っている。しかし2D分類データが完成済み（103件、エラー0%）なので、他5テーマと同じv3フォーマットに移行できる。

v3完了済みの参考実装: `docs/ai-copyright-reaction-map.html`（正典テーマ）

## 参照すべきデータファイル

- 2D分類JSON: `social-samples/school-nickname-ban_2d_classified.json`（103件）
  - 軸: `stance_ban`（あだ名禁止への賛否: -2反対〜+2賛成）、`stance_culture`（文化・コミュニケーション重視度: -2制度的解決〜+2文化的解決）
- 1D分類JSON: `social-samples/school-nickname-ban_classified_v2_final.json`（344件）
- HTML設定: `configs/school-nickname-ban-reaction-map.json`
- トピック設定: `configs/topics/school-nickname-ban-v2.yaml`

## あなたのタスク

`docs/school-nickname-ban-reaction-map.html` を v3フォーマットに全面書き換える。

### 必須要素（templates/topic-page-v3.md 準拠）

1. **ヒーローセクション** — テーマ画像 + 問い1行 + 30秒サマリー3点
2. **漫画セクション** — 漫画画像が未生成のため、テキストカード形式で代替（bukatsu-chiiki実装を参照: `docs/bukatsu-chiiki-reaction-map.html`）
3. **投票セクション** — 4択投票。投票後にSNS分布との比較表を即表示
4. **2Dスタンスマップ** — canvas ID: `smCanvasMain` / `smCanvasHeat`。2D分類JSONからデータを描画
5. **象限別の代表的な声** — 4象限ナビ付き
6. **論点整理** — 争点カード形式
7. **次テーマへの回遊** — 他v3テーマへのカード
8. **詳細データ** — 折りたたみ

### 投票選択肢→2D座標の対応表

以下の4択を設計し、各選択肢を2D座標にマッピングすること:
- 投票選択肢は `docs/voting_design_guideline.md` 準拠（一般ユーザーが直感的に選べる文言）
- 2D分類データの象限分布を確認し、各選択肢が異なる象限に対応するよう設計
- **他テーマの対応表をコピーしない**。このテーマ固有のデータから導出すること

### 「旧形式」バナーの削除

v3化完了後、「旧形式」バナーを削除する。

## 保護タグ（絶対に維持すること）

HTML変更時は以下のタグが維持されていることを確認:

- **GA4**: `G-K10S4YCZFH`（`<script>` タグ）
- **AdSense**: `ca-pub-2542211932832864`（`<script>` タグ + `<meta>` タグ）
- **Supabase**: `supabaseUrl` / `supabaseKey` 変数（投票機能）
- **OGP/SEO**: `<meta property="og:*">` / `<meta name="twitter:*">` / `<link rel="canonical">`
- **Buy Me a Coffee**: `buymeacoffee.com/issue.stance.lab`

## ブランチ運用

- 作業ブランチ: `task/school-nickname-ban-v3`
- main に直接コミットしない
- 完了後 PR 作成（マージはハブが行う）

## 技術的制約

- canvas ID は `smCanvasMain` / `smCanvasHeat` を使用（正典ID）
- `ctx.filter` は使用禁止（Safari非対応）— ヒートマップのぼかしは手動ガウシアン計算で実装
- CSS特異度: セクション固有スタイルは `.stance-map-section .xxx` で囲む
- 画像: WebP形式、`loading="lazy"` 必須
- drawHeatmap 関数内でアニメーション用のフィルター操作を行わない

## 完了条件

- [ ] v3フォーマットの全8セクションが実装されている
- [ ] 2Dスタンスマップが103件のデータを正しく描画する
- [ ] 投票→比較表示→「あなたはこのあたり」マーカーが動作する
- [ ] 「旧形式」バナーが削除されている
- [ ] 保護タグgrep確認（GA4/AdSense/Supabase/OGP/BMC）
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

### 投票選択肢→2D座標 対応表
（設計した対応を記載）

### 迷った点・人間への質問
- （あれば記載）
```
