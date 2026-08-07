# SNS反応のOllama分類

作成日: 2026-06-14

## 目的

Yahooリアルタイム検索などで収集したSNS反応を、キーワードではなくOllamaで文脈分類する。

キーワード分類では、例えば「虚偽答弁」という語が入っているだけで批判側に誤分類されることがある。Ollama分類では、投稿全体の文脈を読ませて、擁護・批判・比較・未確認などへ振り分ける。

## スクリプト

```text
scripts/classify_social_reactions_ollama.py
```

## 入力形式

JSON配列。最低限 `text` が必要。

```json
[
  {
    "query": "高市 中傷動画 -rt",
    "text": "投稿本文",
    "url": "https://x.com/...",
    "tweet_id": "..."
  }
]
```

## 分類カテゴリ

| カテゴリ | 内容 |
| --- | --- |
| 高市氏批判・責任追及 | 高市氏、陣営、秘書の責任や説明責任を問う |
| 高市氏擁護・報道批判 | 高市氏本人の関与を否定、文春/共同/メディア/野党を批判 |
| 玉木氏比較・説明責任 | 玉木氏も松井氏関連で説明すべき、同じではないかと見る |
| 玉木氏擁護・貰い事故 | 玉木氏を同列視すべきでない、巻き込まれと見る |
| サナエトークン関連 | サナエトークン、暗号資産、補償、金融庁等 |
| 松井健氏を軸にした拡張 | 松井氏を起点に他政治家、団体、人物へ広げる |
| ネット選挙・透明性問題 | 政治動画、AI、外注、発信主体、広告、拡散の透明性を問題視 |
| 未確認・陰謀寄り | 根拠不明の断定、外国勢力、陰謀、売国など |
| その他・分類保留 | 明確に分類できない |

## 使い方

### 1. Ollamaを起動

別ターミナルで実行する。

```bash
ollama serve
```

モデルがなければ取得する。

```bash
ollama pull qwen2.5:7b
```

### 2. dry-run

```bash
python3 scripts/classify_social_reactions_ollama.py \
  --input social-samples/takaichi_realtime_samples.json \
  --output social-samples/test.json \
  --limit 1 \
  --dry-run
```

### 3. まず10件でテスト

```bash
python3 scripts/classify_social_reactions_ollama.py \
  --input social-samples/takaichi_realtime_samples.json \
  --output social-samples/takaichi_realtime_ollama_classified_test.json \
  --markdown social-samples/takaichi_realtime_ollama_classified_test.md \
  --limit 10 \
  --model qwen2.5:7b
```

### 4. 全件分類

```bash
python3 scripts/classify_social_reactions_ollama.py \
  --input social-samples/takaichi_realtime_samples.json \
  --output social-samples/takaichi_realtime_ollama_classified.json \
  --markdown social-samples/takaichi_realtime_ollama_classified.md \
  --model qwen2.5:7b
```

## 出力

JSONには各投稿へ `classification` が付く。

```json
{
  "text": "投稿本文",
  "url": "https://x.com/...",
  "classification": {
    "category": "高市氏擁護・報道批判",
    "stance": "擁護",
    "summary": "文春報道を疑い、高市氏本人の関与を否定する主張",
    "reason": "投稿は文春記事の捏造性と松井氏の否定証言を強調している",
    "confidence": 0.86,
    "article_usable": true,
    "risk": "low"
  }
}
```

Markdownはカテゴリ別に並び替えた閲覧用ファイルになる。

## 注意

- Ollama分類も誤る可能性がある。代表投稿として記事に使うものは必ず人間が確認する。
- 件数を世論比率として扱わない。
- 攻撃的表現や根拠不明の断定は、記事本文では要約して扱う。
- `article_usable: true` は「代表意見として使いやすい」という意味であり、事実性の保証ではない。

## 構造化分類 v2

辺野古事故のように、記事見出し・引用元・投稿者本人の主張が混ざるテーマでは、単純な `category` / `stance` だけでは誤分類が起きやすい。

今後の複雑なSNS反応分類では、次の軸を分ける。

| フィールド | 役割 |
| --- | --- |
| `topic_target` | 大きな話題。例: 辺野古高校生死亡事故 |
| `actor_target` | 評価対象になっている行為主体。例: 文科省判断、学校・引率 |
| `criticized_target` | 実際に批判されている対象 |
| `target` | UI互換用の主対象 |
| `stance_to_target` | 主対象への態度 |
| `issue` | 主論点 |
| `quote_direction` | 旧互換用の引用方向 |
| `stance_to_quoted_author` | 引用元の人物・媒体への態度 |
| `stance_to_quoted_claim` | 引用元が示す主張内容への態度 |
| `confidence_level` | `high` / `medium` / `low` |
| `alternate_categories` | 第2候補以下の分類 |

特に重要なのは、`stance_to_quoted_author` と `stance_to_quoted_claim` を分けること。

例:

```json
{
  "category": "文科省判断支持・政治的中立性違反を指摘",
  "topic_target": "辺野古高校生死亡事故",
  "actor_target": "文科省判断",
  "criticized_target": "抗議声明側",
  "target": "文科省判断",
  "stance_to_target": "評価する",
  "issue": "政治的中立性",
  "quote_direction": "引用元に反対",
  "stance_to_quoted_author": "反対",
  "stance_to_quoted_claim": "反対",
  "confidence": 0.88,
  "confidence_level": "high",
  "alternate_categories": [
    {
      "category": "政治利用・反基地運動批判",
      "confidence": 0.22
    }
  ]
}
```

`review_required` は最終判定ではなく、低信頼・高リスク投稿の確認用に限定する。引用元に反対しているだけで全件要確認にすると、運用が重くなりすぎる。

辺野古向けの実装:

```bash
python3 scripts/classify_henoko_structured_ollama_batch.py \
  --input social-samples/henoko/henoko_realtime_samples_expanded.json \
  --output social-samples/henoko/henoko_structured_v2.json \
  --markdown social-samples/henoko/henoko_structured_v2.md \
  --model qwen2.5:7b \
  --batch-size 3 \
  --timeout 220 \
  --sleep 0.2
```

このスクリプトは、OllamaのJSON出力が崩れた場合にバッチを1件ずつ再試行する。明確なルール一致がある場合は、カテゴリとスタンスの整合補正も行う。
