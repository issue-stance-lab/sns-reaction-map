# henoko-student-accident v3化（旧形式→2Dスタンスマップ統合ページ）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- テーマ台帳: THEMES.yaml を参照
- v3仕様書: `templates/topic-page-v3.md`（必読）
- 本タスクの対象テーマ: henoko-student-accident（辺野古高校生死亡事故）
- 対象ファイル: `docs/henoko-student-accident-reaction-map.html`

## 背景

henoko-student-accidentは現在「旧形式」バナーが付いた旧ページのまま残っている。2D分類データが完成済み（295件）なので、他6テーマと同じv3フォーマットに移行できる。

v3完了済みの参考実装: `docs/ai-copyright-reaction-map.html`（正典テーマ）

## 参照すべきデータファイル

- 2D分類JSON: `social-samples/henoko_student_accident_2d_classified.json`（295件）
  - X軸: `stance_mext`（文科省判断への態度: -2反発〜+2支持）
  - Y軸: `stance_focus`（関心の焦点: -2事故・追悼中心〜+2政治・制度中心）
- HTML設定: `configs/henoko-student-accident-reaction-map.json`
- トピック設定: `configs/topics/henoko-v2.yaml`

### データ分布

```
stance_mext: 反発(43件) / 中立(58件) / 支持(194件)
stance_focus: 事故中心(53件) / 混合(15件) / 政治中心(227件)

象限分布:
  文科省支持×政治中心: 181件（最大）
  文科省反発×政治中心: 41件
  文科省支持×事故中心: 27件
  文科省反発×事故中心: 2件（最少）
```

## あなたのタスク

`docs/henoko-student-accident-reaction-map.html` を v3フォーマットに全面書き換える。

### 実装すべき8セクション（順序厳守）

1. **ヒーローセクション** — テーマ画像（既存hero_imageがあれば使用、なければCSS背景）+ 問い1行 + 30秒サマリー3点
2. **漫画セクション** — 漫画画像が未生成のため、テキストカード形式で代替（bukatsu-chiiki実装を参照: `docs/bukatsu-chiiki-reaction-map.html` のv3化前の漫画セクション）
3. **投票セクション** — 4択投票。投票後にSNS分布との比較表を即表示
4. **2Dスタンスマップ** — canvas ID: `smCanvasMain` / `smCanvasHeat`。2D分類JSONからデータを描画
5. **象限別の代表的な声** — 4象限ナビ付き
6. **論点整理** — 争点カード形式
7. **次テーマへの回遊** — 他v3テーマへのカード
8. **詳細データ** — 折りたたみ

### 投票選択肢→2D座標の対応表（自分で導出すること）

既存の投票4択（`configs/henoko-student-accident-reaction-map.json` の `vote_labels`）:
1. 安全管理の問題が一番大きい
2. 文科省の判断は妥当だと思う
3. 平和教育が萎縮しないか心配
4. よくわからない・情報不足

各選択肢を2D座標にマッピングする。データ分布を参考に、各象限に対応させること:
- 選択肢1「安全管理」→ 事故・安全中心 → focus < 0 方向
- 選択肢2「文科省妥当」→ 文科省支持×政治中心 → mext > 0, focus > 0 方向
- 選択肢3「平和教育萎縮」→ 文科省反発×政治中心 → mext < 0, focus > 0 方向
- 選択肢4「わからない」→ 中立付近

**上記は目安。実際の座標は2D分類データの分布を見て自分で決めること。**

### 2Dスタンスマップの軸ラベル

- X軸: 「文科省判断に反発」← → 「文科省判断を支持」
- Y軸: 「事故・安全・追悼」↓ ↑「政治・制度・思想」

## 制約・注意（重要）

- **変更してよいファイル**: `docs/henoko-student-accident-reaction-map.html` のみ。他テーマのHTML・ポータル(index.html)・スクリプト・`templates/topic-page-v3.md` は変更しない
- **絶対に維持するもの**（削除・破壊禁止。改修後にgrepで存在確認すること）:
  - GA4タグ: `G-K10S4YCZFH`
  - AdSenseコード: `ca-pub-2542211932832864`
  - Supabase URL / APIキーと投票ロジック（重複投票 `23505` 判定含む）
  - OGPメタタグ・canonicalリンク（`SEO_META_START` / `SEO_META_END` ブロック）
  - Buy Me a Coffee リンク（`buymeacoffee.com/issue.stance.lab`）
- 投票の質問・選択肢の文言は変更しない（既定済み）
- 新しい画像は追加しない（既存の `docs/images/` 内の画像のみ使用）
- `ctx.filter` を描画アニメーション中に使わない（Safari重量化の既知の罠）
- モバイルファーストで確認（375px幅で崩れないこと）

### ブランチ運用

- mainに直接コミットしない。ブランチ `task/henoko-page-v3` で作業し、完了後報告する（マージはClaude Codeが行う）

## 完了条件・報告

1. `docs/henoko-student-accident-reaction-map.html` がv3構成になり、ローカルでブラウザ表示確認済み（コンソールエラーなし、投票→比較表示→マーカー表示が動作）
2. 投票選択肢→2Dマップ座標の対応表を、座標と判断理由付きで報告する
3. GA4 / AdSense / Supabase / OGP / Buy Me a Coffee のタグ残存をgrepで確認した結果を報告する
4. 変更内容のサマリーを出力する
5. 判断に迷った点・仮定した点を明記する
