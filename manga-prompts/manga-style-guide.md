# SNS反応まっぷ 漫画共通スタイルガイド

このファイルは、各テーマページで使う漫画コンテンツの作風・構成・プロンプト雛形をまとめたものです。

既存の主な参照:

- `templates/manga-content.schema.md`
- `manga-prompts/ai-copyright-prompts.md`
- `manga-prompts/fukushuto-prompts.md`
- `configs/prompts/claude-code/20260703_task24-manga-content.md`

## 1. 共通コンセプト

SNS反応まっぷの漫画は、読者を特定の立場へ誘導するためではなく、**SNS上にある代表的な視点を会話や生活場面として理解しやすくするための導入コンテンツ**です。

狙い:

- 抽象的な政策論点を、具体的な人物の不安・期待・疑問に変換する
- 対立を煽らず、どちらの立場にも理由があることを見せる
- 投票やスタンスマップを見る前後の理解を助ける
- 実在人物・団体を直接描かず、フィクションとして扱う

## 2. 基本構成

標準セット:

- キャラクターシート2枚
- 漫画ページ3枚
- 必要に応じて論点別ページ4〜7枚

標準の3ページ構成:

1. 導入: どちらかのキャラの日常と問題への気づき
2. 対立: 2キャラが出会い、価値観がぶつかる
3. 余韻: 完全な結論ではなく、読者に問いを残す

論点別構成を使う場合:

- 各ページは1論点1枚
- 1枚ごとに「何が争点か」が分かる
- 全ページで同じキャラクターを使い、視点の連続性を保つ

## 3. 作風

共通スタイル:

- Anime-inspired semi-realistic manga style
- Clean line art
- 現実的な日本の生活・学校・職場・地域の雰囲気
- 表情は分かりやすいが、過剰にコミカルにしない
- 色は柔らかく、テーマに応じたアクセントを入れる
- 説明漫画ではなく、会話と場面で論点が伝わる構図にする

避けるもの:

- 実在政治家・実在有名人の似顔絵
- 政党ロゴ、公式エンブレム
- 実在団体を攻撃する視覚表現
- 過激な怒り顔、暴力、流血、破壊描写
- 特定立場だけを愚かに見せる描き方
- 長すぎるセリフ
- 画像生成で崩れやすい細かい法律文や長文
- フキダシが多すぎるページ

## 4. キャラクター設計

原則:

- SNS分類で多い立場・代表的な懸念から2人を設計する
- 年齢、職業、地域、生活背景に必然性を持たせる
- 片方を正義、片方を悪役にしない
- どちらも「恐れ」と「望み」を持つ人物にする

キャラクター項目:

- 名前
- 年齢
- 役割・職業
- 立場
- 恐れ
- 望み
- 服装・小物
- 表情の幅
- 口調

キャラシート標準プロンプト:

```text
Character design reference sheet, white background, multiple expressions (<expression list>), full body and close-up face views.
Japanese <gender/person description>, age <age>, <hair/face>, wearing <clothing>, holding <symbolic item>.
<body/build and personality>.
Anime-inspired semi-realistic manga style, clean line art, <theme color palette>.
No real person likeness, no logos, no official emblems.
```

## 5. ページ構成

標準レイアウト:

- 縦長 `2:3`
- 3コマ構成
- 上段大コマ + 下段2コマ
- または上段2コマ + 下段大コマ

推奨:

- 1ページあたり主張は1つ
- セリフは各コマ1〜2個まで
- 最後のコマで問いまたは視点の転換を置く
- 画面内テキストは短く、読みやすく

標準ページプロンプト:

```text
A vertical manga page with 3 panels layout (<layout description>).
Anime-inspired semi-realistic manga style, clean line art, realistic Japanese <setting> atmosphere, <tone> tone.

[PANEL 1]
<scene description>
Speech bubble: "<Japanese text>"

[PANEL 2]
<scene description>
Speech bubble: "<Japanese text>"

[PANEL 3]
<scene description>
Speech bubble: "<Japanese text>"

Keep the characters consistent with the attached character reference sheets.
Make Japanese text readable and accurate.
No politicians, no party logos, no official emblems, no real person likeness.
```

## 6. ストーリー設計テンプレ

```text
Theme:
<テーマ名>

Core conflict:
<このテーマの根本対立>

Character A:
Name: <名前>
Role: <役割>
Stance: <立場>
Fear: <恐れ>
Want: <望み>

Character B:
Name: <名前>
Role: <役割>
Stance: <立場>
Fear: <恐れ>
Want: <望み>

Page 1 - 導入:
<日常場面で問題に気づく>

Page 2 - 対立:
<2人の価値観がぶつかる>

Page 3 - 余韻:
<共通する不安や未解決の問いを残す>
```

## 7. 論点別漫画テンプレ

```text
Issue:
<論点名>

Question:
<短い問い>

Story:
<この論点を会話でどう見せるか>

Panel table:
1. <上段大コマの内容> / セリフ: 「...」
2. <下段左の内容> / セリフ: 「...」
3. <下段右の内容> / セリフ: 「...」

Image prompt:
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row).
Anime-inspired semi-realistic manga style, clean line art, realistic Japanese <setting> atmosphere.
...
```

## 8. 画像サイズ・変換

生成:

- 漫画ページ: 縦長 `2:3`
- キャラシート: 正方形または横長でも可

保存:

```text
docs/images/<topic>-manga-charsheet-<name>.webp
docs/images/<topic>-manga-page-1.webp
docs/images/<topic>-manga-page-2.webp
docs/images/<topic>-manga-page-3.webp
docs/images/<topic>-manga-<issue>.webp
```

WebP変換:

```bash
cwebp -q 45 -resize 900 0 input.png -o docs/images/<topic>-manga-page-1.webp
cwebp -q 55 -resize 900 0 input.png -o docs/images/<topic>-manga-charsheet-<name>.webp
```

目標:

- 漫画ページ: 100KB前後
- キャラシート: 120KB前後
- 文字が潰れる場合は品質を上げる

## 9. HTML表示ルール

- 漫画画像には `loading="lazy"` を付ける
- 漫画セクションには注記を表示する

```text
※ この漫画はSNS上の代表的な意見をもとに構成したフィクションです。
```

- モーダル拡大で読めるようにする
- 投票導線の前後どちらに置くかはテーマごとに判断する
- インフォグラフィックを入口にするテーマでは、漫画は「代表意見の深掘り」として後段に置く

## 10. 品質チェック

- キャラクターがページ間で一貫している
- どちらか一方を極端に悪く描いていない
- セリフが短く読みやすい
- SNS上の代表意見と対応している
- 実在人物・団体への誤認を招かない
- 注記が入っている
- WebP化後も文字が読める
- ページ全体の導線と役割が重複していない
