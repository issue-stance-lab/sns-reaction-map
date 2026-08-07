# ai-copyright main_issue 分類（OpenCode Go API版）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- テーマ台帳: THEMES.yaml を参照
- 本タスクの対象テーマ: ai-copyright（生成AIと著作権）
- ブランチ: `task/ai-copyright-main-issue`（作成すること）

## 背景

生成AIと著作権テーマは2D分類（708件、stance_regulation / stance_beneficiary）が完了している。
次のステップとして「論点アリーナ」形式を追加するため、各投稿が以下6論点のどれを
主に論じているかを `main_issue` フィールドとして付与する。

データは2バッチで構成されている:
- **v1（旧バッチ）**: `original_category` あり、`is_opinion` なし → 309件が意見
- **v2（2026-07-12追加）**: `is_opinion=True`、`original_category` なし → 369件

main_issue対象: 合計 678件（スクリプトが自動判別）

論点一覧:
- 学習データ・無断利用（AI学習への著作物利用の合法性・パクリ論争）
- クリエイター保護・権利（表現者の生計・権利・尊厳への影響）
- 法制度・規制整備（ライセンス・許諾要件・規制立法の是非）
- 技術競争・推進（過剰規制による競争力低下・技術進歩阻害）
- 利用者モラル・倫理（クレジット表記なし・配慮欠如・個人の使い方）
- AI生成物の権利・創作性（AI出力への著作権帰属・創作性の定義）

## あなたのタスク

### 0. ブランチ作成

```bash
git checkout -b task/ai-copyright-main-issue
```

### 1. 環境確認

```bash
grep OPENCODEGO_API_KEY .env
```

### 2. テスト実行（20件）

```bash
python3 scripts/classify_main_issue_ai_copyright.py --test
```

**テスト合格基準:**
- エラー率 20%以下
- 6論点のうち少なくとも3論点以上に分布していること
- 「学習データ・無断利用」と「クリエイター保護・権利」が各1件以上あること（データ上多い論点のため）

### 3. スポットチェック（テスト後）

以下のパターンを手動確認（各1件以上）:

| 投稿パターン | 期待される main_issue |
|---|---|
| 「AI学習は漫画村と同じ。著作権侵害だ」 | 学習データ・無断利用 |
| 「イラストレーターが廃業に追い込まれている」 | クリエイター保護・権利 |
| 「政府はライセンス制度を整備すべき」 | 法制度・規制整備 |
| 「規制したら日本だけ取り残される」 | 技術競争・推進 |
| 「AI生成と隠して使う人が問題」 | 利用者モラル・倫理 |
| 「プロンプト入力だけで著作権が発生するのはおかしい」 | AI生成物の権利・創作性 |

明らかな誤分類が20%以上あれば報告して停止すること。

### 4. 全量実行

テスト合格後:

```bash
python3 scripts/classify_main_issue_ai_copyright.py
```

処理数が多いため（678件）、進捗を定期的に確認すること。

### 5. 結果の検証

```python
python3 -c "
import json
from collections import Counter
from pathlib import Path
data = json.load(open('social-samples/ai-copyright_2d_classified.json'))
total = len(data)
with_issue = sum(1 for x in data if x.get('main_issue'))
errors = sum(1 for x in data if (x.get('is_opinion') is True or (x.get('original_category') and x.get('original_category') not in ('その他・分類保留','情報共有・ニュース言及'))) and not x.get('main_issue'))
print(f'総数: {total}件  main_issue付与: {with_issue}件  未付与（エラー）: {errors}件')

VALID = ['学習データ・無断利用','クリエイター保護・権利','法制度・規制整備','技術競争・推進','利用者モラル・倫理','AI生成物の権利・創作性','その他']
dist = Counter(x.get('main_issue') for x in data if x.get('main_issue'))
print('\n=== main_issue 分布 ===')
for k in VALID:
    bar = '█' * dist.get(k, 0)
    print(f'  {k:>20}: {dist.get(k, 0):>3}  {bar}')
"
```

**合格基準:**
- エラー率（未付与）15%以下
- 「その他」が全体の30%以下
- 「学習データ・無断利用」と「クリエイター保護・権利」がそれぞれ50件以上

### 6. コミット＆報告

```bash
git add social-samples/ai-copyright_2d_classified.json scripts/classify_main_issue_ai_copyright.py
git commit -m "feat: ai-copyright main_issue 分類完了（OpenCode Go、678件対象）"
```

## 報告フォーマット

完了時に以下を報告:

```
## ai-copyright main_issue 分類 完了報告

- 元データ: 708件（main_issue対象: 678件）
- main_issue付与: XXX件 / 未付与（エラー）: XXX件
- エラー率: X.X%
- main_issue 分布:
  学習データ・無断利用:      XX件
  クリエイター保護・権利:    XX件
  法制度・規制整備:          XX件
  技術競争・推進:            XX件
  利用者モラル・倫理:        XX件
  AI生成物の権利・創作性:    XX件
  その他:                    XX件
- スポットチェック: OK / NG（詳細）
- コミット: (ハッシュ)
```

## 次ステップ（このタスク完了後）

分類完了後、ハブAIに以下を申し送ること:
- THEMES.yaml の ai-copyright に `main_issue: done` を追加依頼
- 次タスク: HTMLへの論点アリーナ追加（`task/ai-copyright-arena`）
