# SNS反応まっぷ 入力JSON仕様

`scripts/build_reaction_map.py` は、分類済み投稿JSONから汎用の「SNS反応まっぷ」HTMLを生成する。

## 必須形式

入力はJSON配列。

```json
[
  {
    "query": "検索語",
    "text": "投稿本文または要約前の本文",
    "url": "https://x.com/example/status/...",
    "classification": {
      "category": "批判・責任追及",
      "stance": "批判",
      "summary": "中立的な1文要約",
      "reason": "分類理由",
      "confidence": 0.86,
      "article_usable": true,
      "risk": "low"
    }
  }
]
```

## 表示に使う項目

| 項目 | 用途 |
|---|---|
| `query` | `カテゴリ × 検索クエリ` の列 |
| `text` | 代表サンプルの引用欄 |
| `url` | 投稿URLリンク |
| `classification.category` | 行カテゴリ、分類別件数 |
| `classification.stance` | `カテゴリ × スタンス` の列 |
| `classification.summary` | 代表サンプルの要旨 |
| `classification.reason` | 代表サンプルの分類理由 |
| `classification.confidence` | 代表サンプルの信頼度 |
| `classification.article_usable` | 代表サンプルの優先表示 |

## 生成コマンド

```bash
python3 scripts/build_reaction_map.py \
  --input social-samples/example_classified.json \
  --config templates/reaction-map-config.template.json \
  --output docs/example-reaction-map.html
```

## 運用ルール

- テーマごとに `configs/<topic>-reaction-map.json` を作る。
- カテゴリ名は分類スクリプトの出力と一致させる。
- 記事公開時はHTMLそのものより、PNG化した画像と要約表をSubstackへ貼る。
- 投稿本文の大量転載を避け、公開記事では「要旨 + URL」を基本にする。
