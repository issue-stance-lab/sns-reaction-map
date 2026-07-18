# 漫画コンテンツ データスキーマ

## 概要

各トピックの reaction-map ページに埋め込むショートコミック（3ページ構成）のデータ定義。
SNSの対立論点を当事者視点で視覚化し、読者の感情移入を促す。

## 配置場所

「この話題、あなたはどう感じる？」セクションの**投票ボタンの前**に配置。
体験フロー: 漫画で感情移入 → 投票 → データで全体像確認

## データ形式

`configs/<topic>-reaction-map.json` の `manga` フィールドとして追加。

```json
{
  "manga": {
    "synopsis": "漫画のあらすじ・狙い（対立構造の解説と読者にどう感じてほしいか）",
    "disclaimer": "※ この漫画はSNS上の代表的な意見をもとに構成したフィクションです",
    "characters": [
      {
        "id": "char_a",
        "name": "キャラクター名",
        "role": "立場（例：イラストレーター）",
        "age": 28,
        "stance": "賛成派 / 反対派",
        "emotion_base": {
          "fear": "何を恐れているか",
          "desire": "何を望んでいるか"
        },
        "appearance": "外見の詳細（髪型・服装・体型など、プロンプト生成に使用）",
        "character_sheet_prompt": "英語プロンプト（Step 1: キャラクターシート生成用）"
      }
    ],
    "pages": [
      {
        "page_number": 1,
        "title": "ページタイトル",
        "description": "ページの概要・演出意図（日本語）",
        "layout": "上段1コマ大 + 下段2コマ",
        "panels": [
          {
            "position": "上段・大コマ",
            "direction": "演出・状況の解説（日本語）",
            "dialogue": "セリフ（日本語）",
            "speaker": "char_a"
          }
        ],
        "image_prompt": "英語プロンプト（Step 2: ページ全体の画像生成用、セリフ描画指示を含む）"
      }
    ]
  }
}
```

## キャラクター設定ルール

- SNS論点をベースに、対立する意見を代弁する**当事者キャラクターを2名**設定
- 属性（年齢・職業・立場）と感情のベース（恐れ・望み）を含める
- 実在の個人が特定できる設定は禁止

## ページ構成（3ページ × 各2〜3コマ）

各ページは1枚の画像として生成する（参考画像のようなコマ割りレイアウト）。

| ページ | 役割 | 推奨レイアウト |
|--------|------|----------------|
| 1【導入】 | 主人公の日常と問題の発覚 | 上段1コマ大 + 下段2コマ |
| 2【対立】 | 二人の価値観がぶつかる | 上段2コマ + 下段1コマ大 |
| 3【余韻】 | 歩み寄りの兆し → オープンエンド | 上段2コマ + 下段1コマ大（ワイド） |

## 画像生成プロンプトルール

### Step 1: キャラクターシート生成（Character Lock用）

必須キーワード: `character design reference sheet, white background, multiple expressions`
三面図や多様な表情を含むキャラシートの英語プロンプトを作成。

### Step 2: 本番ページ生成

- 1プロンプトで1ページ（2〜3コマ含む）を生成
- 各コマの位置（上段/下段、大/小）を `[TOP LARGE PANEL]` 等で明示
- **漫画風の題名（1ページ目のみ）:** 1ページ目のプロンプトにのみ、漫画タイトルバナーを含める。指定方法例: `At the top of the page, a bold manga-style title banner with the Japanese text "男系か、女系か。" in large, dynamic handwritten-style lettering with a subtle background accent`。2ページ目以降にはタイトルバナーを入れない。
- 日本語フキダシの描画指示を含める
- 指定方法例: `A speech bubble containing the Japanese text "ここにセリフ"`
- **重要:** 生成時に Step 1 のキャラクターシートを参照画像として添付すること

## プロンプト出力先

`manga-prompts/<topic>-prompts.md` に独立ファイルとして出力。
Step 1 → Step 2 の順に、コピペしやすい形式で記載。

## 画像仕様

- 形式: WebP
- サイズ: 1枚100KB以下
- 保存先: `docs/images/<topic>-manga-page-{1,2,3}.webp`
- 遅延読み込み: `loading="lazy"` 必須
