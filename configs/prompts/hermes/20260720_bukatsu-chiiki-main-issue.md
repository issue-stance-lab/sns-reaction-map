# bukatsu-chiiki main_issue 分類（OpenCode Go API版）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- テーマ台帳: THEMES.yaml を参照
- 本タスクの対象テーマ: bukatsu-chiiki（部活動の地域移行）
- ブランチ: `task/bukatsu-chiiki-main-issue`（作成すること）

## 背景

部活動の地域移行テーマは2D分類（245件、stance_transfer / stance_priority）が完了している。
次のステップとして「論点アリーナ」形式を追加するため、各投稿が以下6論点のどれを
主に論じているかを `main_issue` フィールドとして付与する。

論点一覧:
- 費用・家庭負担（月会費・経済格差）
- 受け皿・指導者（人材不足・報酬）
- 教員の働き方（残業・強制参加解消）
- 教育的意義・機会（子どもの成長・文化継承）
- 地域格差（都市vs地方・自治体差）
- 制度・移行プロセス（国の方針・移行スピード）

## あなたのタスク

### 0. ブランチ作成

```bash
git checkout -b task/bukatsu-chiiki-main-issue
```

### 1. 環境確認

```bash
grep OPENCODEGO_API_KEY .env
```

### 2. テスト実行（20件）

```bash
python3 scripts/classify_main_issue_bukatsu_chiiki.py --test
```

**テスト合格基準:**
- エラー率 20%以下
- 6論点のうち少なくとも3論点以上に分布していること
- 費用・家庭負担 と 受け皿・指導者 が各1件以上あること（データ上多い論点のため）

### 3. スポットチェック（テスト後）

以下のパターンを手動確認（各1件以上）:

| 投稿パターン | 期待される main_issue |
|---|---|
| 「月8000円×3人、年28万。家計がヒィヒィ」 | 費用・家庭負担 |
| 「報酬が安いから指導者が集まらない」 | 受け皿・指導者 |
| 「教員が土日も部活に駆り出されるのはブラック」 | 教員の働き方 |
| 「地域移行で夢を奪われる子がいる」 | 教育的意義・機会 |
| 「地方では受け皿となるクラブが存在しない」 | 地域格差 |
| 「移行スピードが速すぎる」 | 制度・移行プロセス |

明らかな誤分類が20%以上あれば報告して停止すること。

### 4. 全量実行

テスト合格後:

```bash
python3 scripts/classify_main_issue_bukatsu_chiiki.py
```

### 5. 結果の検証

```python
python3 -c "
import json
from collections import Counter
from pathlib import Path
data = json.load(open('social-samples/bukatsu-chiiki_2d_classified.json'))
total = len(data)
with_issue = sum(1 for x in data if x.get('main_issue'))
errors = sum(1 for x in data if x.get('is_opinion') and not x.get('main_issue'))
print(f'総数: {total}件  main_issue付与: {with_issue}件  未付与（エラー）: {errors}件')

VALID = ['費用・家庭負担','受け皿・指導者','教員の働き方','教育的意義・機会','地域格差','制度・移行プロセス','その他']
dist = Counter(x.get('main_issue') for x in data if x.get('main_issue'))
print('\n=== main_issue 分布 ===')
for k in VALID:
    bar = '█' * dist.get(k, 0)
    print(f'  {k:>12}: {dist.get(k, 0):>3}  {bar}')
"
```

**合格基準:**
- エラー率（未付与）15%以下
- 「その他」が全体の30%以下
- 費用・家庭負担 と 受け皿・指導者 がそれぞれ15件以上

### 6. コミット＆報告

```bash
git add social-samples/bukatsu-chiiki_2d_classified.json scripts/classify_main_issue_bukatsu_chiiki.py
git commit -m "feat: bukatsu-chiiki main_issue 分類完了（OpenCode Go、245件）"
```

## 報告フォーマット

完了時に以下を報告:

```
## bukatsu-chiiki main_issue 分類 完了報告

- 元データ: 245件
- main_issue付与: XXX件 / 未付与（エラー）: XXX件
- エラー率: X.X%
- main_issue 分布:
  費用・家庭負担:    XX件
  受け皿・指導者:    XX件
  教員の働き方:      XX件
  教育的意義・機会:  XX件
  地域格差:          XX件
  制度・移行プロセス: XX件
  その他:            XX件
- スポットチェック: OK / NG（詳細）
- コミット: (ハッシュ)
```
