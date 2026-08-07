# 課題26 Phase B-4: elderly-license-revocation をトピックページv3へ展開

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md を参照
- 現在のタスク一覧: TASK_BOARD.md を参照（**課題26のセクションを必ず読むこと**）
- 技術スタック: Python, HTML/CSS/JS, Ollama, GitHub Pages（静的HTML）

## 前提

**このタスクを始める前に、課題26 Phase B-1（bike-blue-ticket）・B-2（bukatsu-chiiki）・B-3（constitutional-amendment）が完了・マージ済みであることをTASK_BOARD.mdで確認すること。** 未完了の場合は着手せず、状況を報告すること。これが Phase B の最後の1テーマである。

## 背景

課題26 Phase Aで、`docs/ai-copyright-reaction-map.html` を「トピックページ標準フォーマット v3」に試験改修し、mainにマージ済み。この形式を残り4テーマへ順に展開する Phase B のうち、**このタスクは elderly-license-revocation 1テーマのみを担当する**。

v3の正典仕様は `templates/topic-page-v3.md` に定義されている。**必ず全文を読んでから作業を始めること**。参考実装は `docs/ai-copyright-reaction-map.html`（コミット `37e09d5` 以降の版）。B-1〜B-3で他テーマにも展開済みのはずなので、そちらも参考にしてよい。

## あなたのタスク

`docs/elderly-license-revocation-reaction-map.html` を `templates/topic-page-v3.md` の8セクション構成に改修する。

### 実装すべき8セクション（順序厳守）

1. ヒーロー（`.question-line` に問い1行 + `.thirty-summary` に30秒サマリー3点）
2. 漫画で読む対立（既存維持、`loading="lazy"` 確認）
3. 投票（投票後に `#vote-comparison` で「あなたの選択 vs SNS分布」を即時表示）
4. 2Dスタンスマップ（canvas IDを正典 `smCanvasMain` / `smCanvasHeat` に統一。投票後に `window.setStanceMapVoteMarker(choiceIndex)` を呼び「あなたはこのあたり」マーカーを表示）
5. 象限別の代表的な声（象限ナビ付き）
6. 争点カード（`.axis-card` 形式）
7. 回遊セクション（他テーマへのカード2-3枚。**elderly-license-revocation以外の4テーマから選ぶ**）
8. 詳細データ（`<details>` に格下げ、分類別件数のみ初期open）

### 重要: 投票選択肢→2Dマップ座標の対応表は自分で考えること

**他テーマの座標をそのまま流用しないこと。** テーマごとに投票選択肢の意味もスタンス軸の意味も異なるため、機械的なコピペは誤った可視化になる。

手順:
1. `configs/elderly-license-revocation-reaction-map.json` を読み、投票セクションの質問・選択肢と、2DスタンスマップのX軸・Y軸の定義（何を+方向/-方向とするか）を把握する
2. 各投票選択肢が、2軸の意味的にどのあたりに位置するかを自分で判断し、`templates/topic-page-v3.md` の「4. 2Dスタンスマップ」セクションにある ai-copyright の記法（座標目安付き）にならって、elderly-license-revocation版の対応表を作成する
3. 実装後、この対応表を完了報告に明記する（座標と判断理由を含む）

## 制約・注意（重要）

- **変更してよいファイル**: `docs/elderly-license-revocation-reaction-map.html` のみ。他テーマのHTML・ポータル(index.html)・スクリプト・`templates/topic-page-v3.md` は変更しない
- **絶対に維持するもの**（削除・破壊禁止。改修後にgrepで存在確認すること）:
  - GA4タグ: `G-K10S4YCZFH`
  - AdSenseコード: `ca-pub-2542211932832864`
  - Supabase URL / APIキーと投票ロジック（重複投票 `23505` 判定含む）
  - OGPメタタグ・canonicalリンク（`SEO_META_START` / `SEO_META_END` ブロック）
  - 漫画セクションと投票画像カード（既存資産をそのまま使う）
  - Buy Me a Coffee リンク（`buymeacoffee.com/issue.stance.lab`）
- 投票の質問・選択肢の文言は変更しない（課題10で確定済み）
- 新しい画像は追加しない（既存の `docs/images/` 内の画像のみ使用）。漫画・回遊カード画像には必ず `loading="lazy"`
- `ctx.filter` を描画アニメーション中に使わない（Safari重量化の既知の罠）
- モバイルファーストで確認（375px幅で崩れないこと）

### ブランチ運用

- mainに直接コミットしない。ブランチ `task/26-phaseb-4-elderly` で作業し、完了後PRを作成する（マージはClaude Codeが行う）

## 完了条件・報告（Phase B全体の完了報告も兼ねる）

1. `docs/elderly-license-revocation-reaction-map.html` がv3構成になり、ローカルでブラウザ表示確認済み（コンソールエラーなし、投票→比較表示→マーカー表示が動作）
2. 投票選択肢→2Dマップ座標の対応表を、座標と判断理由付きで報告する
3. GA4 / AdSense / Supabase / OGP / Buy Me a Coffee のタグ残存をgrepで確認した結果を報告する
4. 変更内容のサマリーを出力する
5. 判断に迷った点・仮定した点を明記する
6. これでPhase B（4テーマ展開）が完了する旨を明記し、Phase C（takaichi/henoko/schoolの扱い決定）が次のステップであることに触れる
