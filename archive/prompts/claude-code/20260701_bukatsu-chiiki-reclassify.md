## タスク: bukatsu-chiiki（部活動の地域移行）の分類設計見直し＋再分類

### 背景

課題9（テーマ別分類設計の再構築）の一環。現在の分類データは **保留率59%**（106/180件）、confidence=0.0が49%と、分類器がほぼ判定放棄している状態。HTMLは公開済みだが、分類品質がサイトの価値を損ねている。

school-nickname-ban / henoko の再設計は完了済み。同じ手法で bukatsu-chiiki を改善する。

### 現状の問題点

1. **保留率が59%** — 「その他・分類保留」が106/180件で最多
2. **confidence=0.0が88件（49%）** — Ollamaが判定を放棄
3. **原因分析（保留投稿サンプル）**:
   - ニュースURL共有だが「地域移行」に関する意見の萌芽がある投稿まで保留になっている
   - 「提案」「考えてみました」「会社を立ち上げます」など立場が読み取れる投稿も保留
   - 分類ルールの「主観的な意見・感情・評価が含まれているものだけ」という最重要ルールが厳しすぎる
4. **カテゴリが長すぎて説明文になっている** — 「教員の長時間労働解消や持続可能性の観点から地域移行に賛成」など。分類器が一致判定しにくい

### 成功例の参考

school-nickname-ban-v2 の設計が参考になる:
- カテゴリ名を短くした（例: 「いじめ防止・心理的安全」）
- 「情報共有・立場不明」を保留とは別に設けた
- 「体験談・現場感覚」を独立カテゴリにした
- stance を「支持」「懸念」「条件付き」「体験談」「情報共有」「判断不能」に多様化

### 作業手順

#### Step 1: 保留投稿の分析（5分）

```bash
python3 -c "
import json
with open('social-samples/bukatsu-chiiki_classified.json') as f:
    data = json.load(f)
held = [d for d in data if d.get('classification',{}).get('category','') == 'その他・分類保留']
print(f'保留: {len(held)}/{len(data)}件')
for d in held:
    text = d.get('text','')[:120]
    reason = d.get('classification',{}).get('reason','')[:80]
    print(f'  {text}')
    print(f'    → {reason}')
    print()
"
```

保留投稿を全件確認し、以下を分析:
- ニュース共有だが関連性のある投稿は何割か？
- 実は立場が読み取れる投稿は何割か？
- 完全に無関係な投稿は何割か？
- 現在のカテゴリに収まらない論点パターンはあるか？

#### Step 2: 分類スキーマの再設計

`configs/topics/bukatsu-chiiki-v2.yaml` を新規作成する。

再設計の方針:
- **カテゴリ名を短くする**（15文字以内目標）
- **「情報共有・ニュース言及」カテゴリを追加** — ニュース共有でもテーマに関連していれば保留にしない
- **「現場体験・当事者報告」カテゴリを検討** — 教員・保護者・生徒の体験談
- stanceは school-nickname-ban-v2 を参考に「賛成」「反対」「条件付き」「体験談」「情報共有」「判断不能」あたりに
- classification_rules の「最重要ルール」を緩和 — 完全に無関係な投稿のみ保留にする
- few_shot_examples を実際の保留投稿から作り直す（現場感のある例に）
- avoid_hold_rules の強化

#### Step 3: 少量テスト分類（10件）

保留投稿から10件をピックアップし、新スキーマで分類テスト:

```bash
python3 scripts/classify_unified.py \
  --topic bukatsu-chiiki-v2 \
  --input /tmp/bukatsu_test_10.json \
  --output /tmp/bukatsu_test_10_result.json \
  --avoid-hold
```

保留率が30%以下になることを確認。ダメならスキーマを修正して再テスト。

#### Step 4: 全件再分類

```bash
python3 scripts/classify_unified.py \
  --topic bukatsu-chiiki-v2 \
  --input social-samples/bukatsu-chiiki_samples.json \
  --output social-samples/bukatsu-chiiki_classified_v2.json \
  --markdown social-samples/bukatsu-chiiki_classified_v2.md \
  --avoid-hold
```

#### Step 5: 品質監査

```bash
python3 -c "
import json
with open('social-samples/bukatsu-chiiki_classified_v2.json') as f:
    data = json.load(f)
total = len(data)
cats = {}; stances = {}
for d in data:
    c = d.get('classification',{})
    cats[c.get('category','?')] = cats.get(c.get('category','?'), 0) + 1
    stances[c.get('stance','?')] = stances.get(c.get('stance','?'), 0) + 1
print(f'総件数: {total}')
print(f'category分布: {dict(sorted(cats.items(), key=lambda x:-x[1]))}')
print(f'stance分布: {dict(sorted(stances.items(), key=lambda x:-x[1]))}')
held = sum(v for k,v in cats.items() if '保留' in k or '対象外' in k)
print(f'保留率: {held}/{total} ({held*100//total}%)')
"
```

**合格基準**: 保留率30%以下、category/stance矛盾なし

#### Step 6: HTML再生成

```bash
python3 scripts/build_reaction_map.py bukatsu-chiiki
```

- `configs/site-cases.json` の `classified_file` を新ファイルに更新
- GA4/AdSense/Supabase タグが維持されることを確認

#### Step 7: 監査メモ作成

`reviews/bukatsu-chiiki-v2-audit-YYYY-MM-DD.md` に:
- 旧→新の保留率比較
- カテゴリ分布
- article_usable の件数
- 代表投稿候補のサンプル確認

#### Step 8: コミット

```
git checkout -b task/9-bukatsu-chiiki-reclassify
git add configs/topics/bukatsu-chiiki-v2.yaml \
        social-samples/bukatsu-chiiki_classified_v2.json \
        social-samples/bukatsu-chiiki_classified_v2.md \
        configs/site-cases.json \
        docs/bukatsu-chiiki-reaction-map.html \
        reviews/bukatsu-chiiki-v2-audit-*.md
git commit -m "refactor: 部活動地域移行の分類設計v2 — 保留率59%→目標30%以下"
```

PRは作成せず、ブランチをpushするところまで。

### 注意事項

- 既存の `configs/topics/bukatsu-chiiki.yaml` は残す（v1として参照用）
- `social-samples/bukatsu-chiiki_classified.json`（旧データ）は上書きしない
- HTML再生成時に GA4（`G-K10S4YCZFH`）、AdSense（`ca-pub-2542211932832864`）、Supabase関連タグが消えないことを確認
- 中間ファイル（テスト用JSONなど）はコミットに含めない
