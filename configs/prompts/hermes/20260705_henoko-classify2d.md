# henoko-student-accident 2D分類（OpenCode Go API版）

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのワーカーAIです。

- リポジトリ: issue-stance-aggregator
- テーマ台帳: THEMES.yaml を参照
- 本タスクの対象テーマ: henoko-student-accident（辺野古高校生死亡事故）
- ブランチ: `task/henoko-classify2d`（作成済み・チェックアウト済み）

## 背景

辺野古沖カヌー体験学習中の高校生死亡事故をめぐるSNS投稿の2D分類を行う。
1D分類（classify）は済んでいるが、2Dスタンスマップ用の2軸スコアがまだない。

Ollama gemma4版で先行実行したが、**stance_focus軸（関心の焦点）に系統的誤分類**が発生した:
- 「教育基本法」「政治的中立性」に言及する政策議論の投稿57件が「事故・追悼中心」に誤判定
- stance_focus分布が事故寄り253件 vs 政治寄り24件と極端に偏っている
- 元データに12種33件の重複投稿が存在

そのため、OpenCode Go API版スクリプト `scripts/classify_2d_henoko.py` を新規作成済み。
重複除去ロジックも組み込み済み。

2D軸:
- **X軸 stance_mext**: 文科省判断への態度（-2 反発 〜 +2 支持）
- **Y軸 stance_focus**: 関心の焦点（-2 事故・追悼中心 〜 +2 政治・制度中心）

## あなたのタスク

### 1. 環境確認

```bash
# .env に OPENCODEGO_API_KEY があるか確認
grep OPENCODEGO_API_KEY .env
```

### 2. テスト実行（20件）

```bash
python3 scripts/classify_2d_henoko.py --test
```

**テスト合格基準:**
- エラー率 20%以下
- stance_focus軸が事故寄りに偏りすぎていないこと（「教育基本法」言及投稿がfocus > 0になっているか確認）

### 3. 全量実行

テスト合格後:

```bash
python3 scripts/classify_2d_henoko.py
```

出力先: `social-samples/henoko_student_accident_2d_classified.json`

### 4. 結果の検証

```python
python3 -c "
import json
d = json.load(open('social-samples/henoko_student_accident_2d_classified.json'))
total = len(d)
print(f'総数: {total}件')

# stance_mext distribution
from collections import Counter
mext = Counter(round(x.get('stance_mext', 0)) for x in d)
focus = Counter(round(x.get('stance_focus', 0)) for x in d)
print(f'stance_mext: {dict(sorted(mext.items()))}')
print(f'stance_focus: {dict(sorted(focus.items()))}')

# Check: 教育基本法 mention → focus should be positive
policy_posts = [x for x in d if '教育基本法' in x.get('text','') or '政治的中立' in x.get('text','')]
policy_focus_neg = sum(1 for x in policy_posts if x.get('stance_focus', 0) < 0)
print(f'教育基本法/政治的中立 言及: {len(policy_posts)}件 うちfocus<0: {policy_focus_neg}件')
"
```

**合格基準:**
- 重複除去後の件数が350-380件程度（元403件から重複33件除去）
- エラー率 15%以下
- stance_focus: 政治寄り（+1以上）が全体の15%以上あること
- 教育基本法/政治的中立に言及 → stance_focus<0 の割合が30%以下

### 5. スポットチェック（精度検証）

以下のパターンが正しく分類されているか5件以上確認:

| 投稿内容のパターン | 期待される stance_mext | 期待される stance_focus |
|---|---|---|
| 「学校が政治活動に加担」「政治的中立性違反は当然」 | +1.0〜+2.0 | +1.0〜+2.0 |
| 「平和教育を萎縮させるな」「文科省の介入は圧力」 | -1.0〜-2.0 | +0.5〜+2.0 |
| 「高校生が亡くなったのに…」「安全管理はどうなっていた」 | -0.5〜+0.5 | -1.0〜-2.0 |
| 「ご冥福をお祈りします」追悼のみ | 0.0付近 | -1.5〜-2.0 |
| 「教育基本法違反の認定に抗議声明」 | -1.0〜-2.0 | +0.5〜+2.0 |

明らかな誤分類が20%以上あれば報告して停止すること。

### 6. THEMES.yaml の更新

検証に合格したら:

```yaml
# henoko-student-accident の classify2d を更新
classify2d: done     # XXX件（重複除去後）、エラーX%
```

notesも更新:
```yaml
notes: 2D分類完了（OpenCode Go minimax-m2.7）。page_v3が次工程
```

### 7. コミット＆報告

```bash
git add scripts/classify_2d_henoko.py social-samples/henoko_student_accident_2d_classified.json THEMES.yaml
git commit -m "feat: henoko-student-accident 2D分類完了（OpenCode Go、重複除去済み）"
```

## 報告フォーマット

完了時に以下を報告:

```
## henoko-student-accident classify2d 完了報告

- 元データ: 403件 → 重複除去後: XXX件
- 有効意見: XXX件 / 非意見・エラー: XXX件
- stance_mext分布: 強反発X / やや反発X / 中立X / やや支持X / 強支持X
- stance_focus分布: 事故中心X / やや事故X / 混合X / やや政治X / 政治中心X
- 教育基本法言及→focus<0: X/X件 (X%)
- スポットチェック: OK / NG（詳細）
- コミット: (ハッシュ)
```
