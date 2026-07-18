# SNS反応まっぷ インフォグラフィック共通スタイルガイド

このファイルは、各テーマで共通して使う「SNS反応まっぷ」系インフォグラフィック画像の作風・配色・プロンプト雛形をまとめたものです。

副首都ページで作成した以下の画像群を基準テイストにします。

- 冒頭理解画像: `docs/images/fukushuto-infographic-*.webp`
- 投票ボタン画像: `docs/images/fukushuto-vote-*.webp`

## 1. 共通コンセプト

政策・社会論点を、SNS上の反応整理として読みやすく見せるための **明るい civic-tech インフォグラフィック**。

狙い:

- 難しい論点を、最初の数秒で「何が争点か」理解できるようにする
- 賛否を煽らず、論点の分岐点を見せる
- SNS反応まっぷ全体で統一感のあるビジュアルにする
- 漫画ではなく、記事冒頭・投票導線・論点カードとして使える画像にする

## 2. 見た目のルール

共通スタイル:

- 白〜淡い水色の明るい背景
- 濃紺・鮮やかな青の大きな日本語見出し
- 角丸カード、柔らかい影、余白のあるレイアウト
- 小さなドット、スパークル、グラフ風アクセント
- フラット寄りだが少し立体感のある清潔なイラスト
- SNS分析、世論可視化、政策ダッシュボードの雰囲気
- かわいすぎず、硬すぎない

避けるもの:

- 政治家の顔
- 政党ロゴ
- 政府・自治体の公式エンブレム
- 実在SNSロゴ
- 実在人物の似顔絵
- 暗い災害描写、倒壊、負傷者、恐怖演出
- 感情的な煽り、断定的な善悪表現
- ランダムな文字、読めない小さい文字
- 画面全体を埋め尽くす過密レイアウト
- ウォーターマーク

## 3. 基本配色

ベース:

- 背景: `#ffffff`, `#f0f8ff`, `#eef6ff`
- 見出し濃紺: `#06164a` から `#0b1f63`
- メイン青: `#0057ff`, `#1d4ed8`
- 補助線・カード枠: `#bfdbfe`, `#dbeafe`

論点アクセント:

- 賛成・安全・推進: green `#059669`
- 反対・警戒・リスク: red `#dc2626`
- 中立・保留: gray `#64748b`
- 費用・注意: amber/orange `#f59e0b`, `#f97316`
- 候補地・比較: purple `#7c3aed`
- 情報・通信: cyan/teal `#0891b2`, `#0d9488`

注意:

- ページ全体が単色テーマに見えないよう、青をベースに複数アクセントを使う
- ただし、1枚の主役色は多くても2〜3色に絞る
- 政党カラーに見えすぎる配色の固定は避ける

## 4. 画像タイプ別サイズ

### A. 冒頭説明インフォグラフィック

用途:

- 記事冒頭
- テーマの全体像
- 「まず1枚で理解」セクション

推奨サイズ:

- `16:9`
- 生成指定: `1792×1024` または `1536×864`
- Web配置: 横幅100%、最大幅はページ側で制御

構成:

- 大見出し
- 1〜2行の中核メッセージ
- 中央に構造図、フロー図、地図、比較図など
- 下部に3〜4個の問いカード

### B. 個別論点インフォグラフィック

用途:

- 投票前の論点整理カード
- 論点の深掘り

推奨サイズ:

- `1:1`
- 生成指定: `1254×1254` または `1024×1024`
- WebP変換: `900×900` 目安

構成:

- 大見出し
- 短い問い
- 中央図解
- 3〜5個の確認ポイント
- 下部に結論帯

### C. 投票ボタン画像

用途:

- 第1問の論点選択カード
- クリック可能な画像カード

推奨サイズ:

- `1:1`
- 生成指定: `1024×1024` または `768×768`
- WebP変換: `768×768`
- 目標サイズ: 100KB以下

構成:

- 論点名を大きく
- 短い問いを1行
- 中央アイコンまたは簡単な図
- 詳細文は画像内に入れすぎず、HTML側の補足文で出す

### D. OGP画像

用途:

- SNS共有カード

推奨サイズ:

- `1200×630`

構成:

- テーマ名
- 争点を3〜4個
- SNS反応まっぷ感のあるグラフ・地図・カード
- 文字は少なめ

## 5. 共通プロンプトブロック

各画像プロンプトの冒頭または末尾に入れる共通ブロック。

```text
Use the common “SNS反応まっぷ civic-tech infographic style”.

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with green, red, orange, purple, gray, and teal as issue accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no dark disaster scenes,
no clutter, no random extra text, no watermark.
```

## 6. 冒頭説明画像テンプレ

```text
Create a polished 16:9 Japanese infographic for the opening section of a web article.

Theme:
<テーマ名>

Main title:
「<まず1枚で理解系のタイトル>」

Core message:
<このテーマは単純な賛否ではなく、何をどう判断する論点なのかを1〜2文で説明>

Visual structure:
<左→中央→右のフロー、比較図、地図、チェックリストなど、主構造を指定>

Key issue cards:
1. 「<論点1>」 「<短い問い>」
2. 「<論点2>」 「<短い問い>」
3. 「<論点3>」 「<短い問い>」
4. 「<論点4>」 「<短い問い>」

Conclusion band:
「<論点の本質を一言でまとめる>」

Use the common “SNS反応まっぷ civic-tech infographic style”.
```

## 7. 個別論点画像テンプレ

```text
Create a polished 1:1 square Japanese infographic.

Theme:
<テーマ名> の個別論点「<論点名>」

Main title:
「<論点名>」
「<短い問い>」

Core message:
<この論点でユーザーに理解してほしいことを1〜2文>

Composition:
Center:
<中心に置く図解、アイコン、地図、文書、フローなど>

Around the center, place <3〜5> rounded check cards:
1. 「<確認項目1>」 「<短い説明>」
2. 「<確認項目2>」 「<短い説明>」
3. 「<確認項目3>」 「<短い説明>」

Bottom conclusion band:
「<この論点の見方を一言で>」

Use the common “SNS反応まっぷ civic-tech infographic style”.
```

## 8. 投票ボタン画像テンプレ

```text
Create a Japanese infographic-style vote button image.

Size:
1:1 square, 768×768px.

Purpose:
Clickable vote option card for a web page.

Main text:
「<論点名>」

Sub text:
「<短い問い>」

Visual:
<論点を象徴するアイコンや簡単な図解。小さく表示しても分かる構図にする>

Style:
Use the common “SNS反応まっぷ civic-tech infographic style”.
Text must be large, accurate, and readable at small thumbnail size.

Avoid:
Do not include long sentences. Do not add random labels.
```

## 9. WebP変換基準

生成PNGをページ用に変換する場合の目安。

```bash
cwebp -q 82 -resize 900 900 input.png -o docs/images/<topic>-infographic-<issue>.webp
cwebp -q 82 -resize 768 768 input.png -o docs/images/<topic>-vote-<issue>.webp
```

目標:

- 個別論点画像: 100〜130KB前後まで
- 投票ボタン画像: 100KB以下
- 文字が潰れる場合は `q 86` まで上げてもよい

## 10. 命名ルール

```text
docs/images/<topic>-infographic-<issue>.webp
docs/images/<topic>-vote-<issue>.webp
docs/images/<topic>-hero.webp
docs/images/<topic>-ogp.webp
```

例:

```text
docs/images/fukushuto-infographic-teigi.webp
docs/images/fukushuto-vote-kouhochi.webp
docs/images/koshitsu-infographic-kouseki.webp
```

## 11. テーマ別差し替え項目

新しいテーマで必ず決めるもの:

- テーマ名
- 読者に最初に理解してほしい中核メッセージ
- 主要論点 3〜7個
- 各論点の短い問い
- 各論点の象徴アイコン
- 避けるべき固有表現

例:

```text
Theme:
高齢者免許返納

Core message:
事故防止だけでなく、移動手段、地域交通、家族負担、一律規制の是非を考える論点である。

Issue cards:
「安全」 「事故をどう防ぐ？」
「移動手段」 「返納後にどう暮らす？」
「家族負担」 「誰が支える？」
「一律規制」 「年齢だけで決める？」
```

## 12. 品質チェック

生成後に確認すること:

- 日本語テキストが読める
- 画像内の結論が一方に偏りすぎていない
- 政治家・政党・公式ロゴに見えるものがない
- 文字量が多すぎない
- スマホ幅でカード表示しても要点が分かる
- 既存ページの色・余白・角丸と馴染む
- WebP化後も文字が潰れていない
