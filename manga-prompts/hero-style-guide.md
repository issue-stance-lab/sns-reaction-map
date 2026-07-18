# SNS反応まっぷ ヒーロー画像共通スタイルガイド

このファイルは、各テーマページのファーストビューやポータルカードで使うヒーロー画像の作風・配色・プロンプト雛形をまとめたものです。

対象:

- `docs/images/<topic>-hero.webp`
- テーマページのヒーロー背景
- ポータルのテーマカード画像
- 必要に応じたOGP画像のベース

## 1. 共通コンセプト

ヒーロー画像は、記事内容を詳しく説明する画像ではなく、**テーマの空気と争点を一目で伝える入口画像**です。

狙い:

- ページを開いた瞬間に「何のテーマか」が分かる
- ニュース解説らしい信頼感を出す
- SNS反応まっぷ全体で統一された civic-media 感を出す
- 過度に煽らず、論点の入口として機能させる

## 2. 見た目のルール

共通スタイル:

- 明るい白〜淡い水色、淡い青紫、薄いグレーの背景
- 中央または右寄せにテーマを象徴するモチーフ
- 背景には柔らかいグラフ、カード、地図、SNS反応ドットなどの抽象要素
- 角丸、柔らかい影、軽い奥行き
- 写実よりもクリーンな編集イラスト・政策図解寄り
- 文字を載せる前提で、左側または中央上部に余白を残す

避けるもの:

- 実在人物の顔
- 政治家、政党ロゴ、公式エンブレム
- 実在SNSロゴ
- ショッキングな事故・災害・暴力描写
- 暗く重いフォトリアル背景
- 文字を大量に入れたバナー化
- ランダムな英字・日本語
- ウォーターマーク

## 3. 基本配色

ベース:

- 背景: `#ffffff`, `#f0f8ff`, `#eef2ff`, `#f8fafc`
- 見出しが乗る領域: 白〜淡色で読みやすく
- メイン青: `#1d4ed8`, `#2563eb`
- 濃紺: `#06164a`, `#0f172a`

アクセント:

- 安全・賛成: `#059669`
- 警戒・反対: `#dc2626`
- 中立・未確定: `#64748b`
- 注意・費用: `#f59e0b`
- 制度・比較: `#7c3aed`
- 情報・技術: `#0891b2`

注意:

- ヒーロー画像はページ上で濃いグラデーションを重ねる場合があるため、細かい文字は入れない
- 背景全体を暗くしない
- 1枚の中で主役色を増やしすぎない

## 4. 推奨サイズ

生成:

- `16:9`
- 推奨: `1792×1024` または `1536×864`

Web配置:

- `docs/images/<topic>-hero.webp`
- 横幅はページ側で `background-size: cover` またはカード画像として使用

WebP変換:

```bash
cwebp -q 78 -resize 1400 0 input.png -o docs/images/<topic>-hero.webp
```

目標:

- 150KB〜300KB目安
- ファーストビュー画像のため、重すぎる場合は `q 72` まで下げる
- ヒーロー画像に `loading="lazy"` は付けない

## 5. 構図パターン

### A. 余白つきテーマ象徴型

用途:

- 多くのテーマページで標準

構成:

- 左側または中央にテキスト用の余白
- 右側にテーマを象徴するイラスト
- 背景に淡いグラフ・反応カード・ドット

例:

- 高齢者免許: 車、免許証、横断歩道、安全マーク
- 部活地域移行: 学校、体育館、地域クラブ、時計
- 副首都: 日本地図、東京ハブ、バックアップ拠点

### B. 中央モチーフ型

用途:

- ポータルカードやOGPにも転用したい場合

構成:

- 中央に大きな象徴アイコン
- 周囲に論点を示す小さなカード
- 文字は最小限

### C. 比較・対立型

用途:

- 明確な賛否軸があるテーマ

構成:

- 左右に異なる視点を象徴する要素
- 中央に問い、天秤、分岐線
- どちらかを勝たせない

## 6. 共通プロンプトブロック

```text
Use the common “SNS反応まっぷ hero image style”.

Style:
Bright, clean Japanese civic-media hero illustration.
White, pale blue, and soft indigo background.
Modern editorial infographic atmosphere with rounded cards, soft shadows, small dots, subtle chart accents, and airy whitespace.
Professional, neutral, nonpartisan, suitable for a web article first view.
Leave clean negative space for HTML text overlay.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no real person likeness, no dramatic disaster destruction, no dark photo-realistic scene,
no dense text, no random letters, no watermark.
```

## 7. ヒーロー画像テンプレ

```text
Create a polished 16:9 hero image for a Japanese civic explainer web page.

Theme:
<テーマ名>

Core visual message:
<このテーマを一目で示す中心イメージ>

Main motif:
<大きく描く象徴物。例: 日本地図、学校、道路、政策文書、家計、データ画面>

Supporting elements:
- <補助要素1>
- <補助要素2>
- <補助要素3>

Composition:
Leave clean empty space on the left side for title and lead text overlay.
Place the main motif on the right or center-right.
Use subtle SNS reaction/chart/map elements in the background.

Color:
Use blue and navy as the base.
Use <テーマに合うアクセント色> only as accents.

Use the common “SNS反応まっぷ hero image style”.
```

## 8. OGP派生テンプレ

```text
Create a 1200×630 Japanese OGP image based on the same hero visual style.

Theme:
<テーマ名>

Text:
「<短いタイトル>」
「<短い問い>」

Visual:
Use the same main motif as the hero image.
Add 3 small issue chips:
「<論点1>」 「<論点2>」 「<論点3>」

Style:
Same SNS反応まっぷ hero image style.
Readable at social card size.
```

## 9. テーマ別差し替え項目

新テーマで決めるもの:

- テーマ名
- ヒーローの中心モチーフ
- HTMLテキストが乗る余白位置
- 補助モチーフ3点
- 避けるべき固有表現
- OGPで使う短いタイトル

## 10. 品質チェック

- 何のテーマか一目で分かる
- テキストを重ねる余白がある
- ページのヒーローCSSと相性がよい
- 暗すぎない
- 政治的に偏った記号がない
- スマホでトリミングされても主題が残る
- WebP化後に重すぎない
