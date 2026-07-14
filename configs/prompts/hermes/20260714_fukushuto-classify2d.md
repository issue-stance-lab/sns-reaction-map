# fukushuto 2D分類（OpenCode Go API版）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- テーマ台帳: THEMES.yaml を参照
- 本タスクの対象テーマ: fukushuto（副首都法案・副首都構想）
- ブランチ: `task/fukushuto-classify2d`（作成すること）

## 背景

2026-07-14にYahooリアルタイム検索からSNS投稿292件を収集した（trend_judge: GO、スコア8/10、意見率60%）。
衆院通過が目前（翌15日見通し）の副首都法案について、以下の2軸でスタンスマップを作る。

2D軸:
- **X軸 stance_law**: 副首都法案への態度（-2 強く反対 〜 +2 強く賛成）
- **Y軸 stance_location**: 大阪を副首都候補とすることへの態度（-2 他候補地推奨 〜 +2 大阪を強く支持）

分類スクリプトは `scripts/classify_2d_fukushuto.py` として作成済み。
入力: `social-samples/fukushuto_samples.json`（292件）
出力: `social-samples/fukushuto_2d_classified.json`

## あなたのタスク

### 0. ブランチ作成

```bash
git checkout -b task/fukushuto-classify2d
```

### 1. 環境確認

```bash
grep OPENCODEGO_API_KEY .env
```

### 2. テスト実行（20件）

```bash
python3 scripts/classify_2d_fukushuto.py --test
```

**テスト合格基準:**
- エラー率 20%以下
- stance_law が賛成寄りと反対寄りの両方に分布していること（一方向に偏りすぎない）
- stance_location が 0.0（言及なし）ばかりでないこと

### 3. 全量実行

テスト合格後:

```bash
python3 scripts/classify_2d_fukushuto.py
```

### 4. 結果の検証

```python
python3 -c "
import json
from collections import Counter
d = json.load(open('social-samples/fukushuto_2d_classified.json'))
total = len(d)
opinions = sum(1 for x in d if x.get('is_opinion'))
print(f'総数: {total}件  意見: {opinions}件  非意見: {total - opinions}件')

law = Counter(round(x.get('stance_law', 0)) for x in d)
loc = Counter(round(x.get('stance_location', 0)) for x in d)
print(f'stance_law:      {dict(sorted(law.items()))}')
print(f'stance_location: {dict(sorted(loc.items()))}')

# スポットチェック: 大阪・南海トラフ言及
osaka_neg = [x for x in d if ('南海トラフ' in x.get('text','') or '近すぎ' in x.get('text','')) and x.get('stance_location',0) > 0]
print(f'南海トラフ/近すぎ言及 → location>0 の誤判定: {len(osaka_neg)}件')
"
```

**合格基準:**
- エラー率 15%以下
- stance_law: 反対側（-2〜-1）が 10件以上 / 賛成側（+1〜+2）が 10件以上
- stance_location: 0.0 が全体の50%以下（多様な地名・場所意見が分類されていること）
- 「南海トラフ」「近すぎ」言及で stance_location > 0 は 0件であること

### 5. スポットチェック（精度検証）

以下のパターンを各2件以上確認:

| 投稿パターン | 期待される stance_law | 期待される stance_location |
|---|---|---|
| 「防災のために副首都は必要」「多極成長を」 | +1.5〜+2.0 | 0.0〜+2.0 |
| 「消費税より先にやることか」「生煮え法案」 | -1.0〜-2.0 | 0.0 |
| 「大阪は東京に近い、南海トラフで共倒れ」 | 0.0〜-0.5 | -1.5〜-2.0 |
| 「副首都の定義すらない法案に賛成できない」 | -1.0〜-1.5 | 0.0 |
| 「吉村知事の悲願が実現。大阪に副首都を」 | +1.5〜+2.0 | +1.5〜+2.0 |

明らかな誤分類が20%以上あれば報告して停止すること。

### 6. THEMES.yaml の更新

検証に合格したら:

```yaml
# fukushuto の classify2d を更新
classify2d: done     # XXX件、エラーX%
```

notes も更新:
```yaml
notes: "2026-07-14のYahooリアルタイムトレンド上位「副首都」から派生。trend_judgeはGO（スコア8/10、意見率60%）。副首都法案の衆院通過直前タイミングで収集。2D分類完了（OpenCode Go minimax-m2.7）。page_v3が次工程。"
```

### 7. コミット＆報告

```bash
git add scripts/classify_2d_fukushuto.py social-samples/fukushuto_2d_classified.json THEMES.yaml
git commit -m "feat: fukushuto 2D分類完了（OpenCode Go、292件）"
```

## 報告フォーマット

完了時に以下を報告:

```
## fukushuto classify2d 完了報告

- 元データ: 292件 → 重複除去後: XXX件
- 有効意見: XXX件 / 非意見・エラー: XXX件
- stance_law 分布: 強く反対X / 慎重X / 中立X / 概ね賛成X / 強く賛成X
- stance_location 分布: 大阪絶対ダメX / 他候補推奨X / 言及なしX / 大阪でOKX / 大阪を強く支持X
- 南海トラフ/近すぎ言及 → location>0 誤判定: X件
- スポットチェック: OK / NG（詳細）
- コミット: (ハッシュ)
```
