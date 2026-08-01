## タスク: 既存5トピックのYahoo検索データを再収集・追加マージ

### 目的

既存トピックのSNS投稿データを再収集し、分類件数を増やしてコンテンツのボリュームと信頼性を向上させる。

### 対象トピック（優先順）

1. `ai-copyright` — 生成AIと著作権問題（現在475件）
2. `school-nickname-ban` — 学校でのあだ名禁止（現在201件）
3. `takaichi-reaction-map-standard` — 高市文春問題（現在183件）
4. `henoko-student-accident` — 辺野古高校生死亡事故（現在311件）
5. `constitutional-amendment` — 憲法改正論議

### 作業手順（各トピックごと）

#### Step 1: 既存configの確認
```bash
cat configs/topics/{slug}.yaml
```
既存のクエリと分類ルールを確認する。

#### Step 2: 再収集
```bash
node scripts/fetch_yahoo_realtime_node.mjs \
  --query "既存クエリ1" \
  --query "既存クエリ2" \
  ... \
  --dedupe \
  --output social-samples/{slug}_samples_refresh.json \
  --markdown social-samples/{slug}_samples_refresh.md
```
- 既存のYAMLにあるクエリをそのまま使う
- 出力ファイル名は `_refresh` サフィックスをつけて既存データを上書きしない

#### Step 3: 既存データとマージ
```bash
python3 -c "
import json
old = json.load(open('social-samples/{slug}_samples.json'))
new = json.load(open('social-samples/{slug}_samples_refresh.json'))
seen = set()
merged = []
for item in old + new:
    key = item.get('text', '')[:80]
    if key not in seen:
        seen.add(key)
        merged.append(item)
json.dump(merged, open('social-samples/{slug}_samples_merged.json', 'w'), ensure_ascii=False, indent=2)
print(f'Old: {len(old)}, New: {len(new)}, Merged(deduped): {len(merged)}')
"
```

#### Step 4: 再分類
```bash
python3 scripts/classify_unified.py \
  --topic {slug} \
  --input social-samples/{slug}_samples_merged.json \
  --output social-samples/{slug}_classified.json \
  --markdown social-samples/{slug}_classified.md \
  --model qwen2.5:7b \
  --batch-size 3 \
  --timeout 180 \
  --avoid-hold
```

#### Step 5: 分類結果チェック
分類率30%以上ならOK。

#### Step 6: HTML再生成
```bash
python3 scripts/build_reaction_map.py \
  --config configs/{slug}-reaction-map.json \
  --input social-samples/{slug}_classified.json \
  --output docs/{slug}-reaction-map.html
```

#### Step 7: 旧ポータルのプレビュー（必要な場合のみ）

現行トップページは再生成しない。旧ポータルを確認する場合も、
`docs/index.html` 以外のプレビュー出力先を明示する。

```bash
python3 scripts/build_site_portal.py --output /tmp/sns-reaction-portal-preview.html
```

### 完了条件
- 全5トピックの再収集・マージ・再分類・HTML再生成が完了
- 各トピックの件数が増加していること
- git commit & push まで行う

### 注意
- Ollamaが起動していることを確認してから分類を実行（`ollama list`）
- 分類に時間がかかる場合は `--limit` で段階的にテスト
- 既存のSupabase接続情報（supabaseUrl, supabaseAnonKey）がHTML再生成で消えないよう注意。build_reaction_map.py のテンプレートに含まれていない場合は手動で再設定が必要
- AI_HANDOFF.md の「新トピック追加手順」セクションに詳細な運用ノウハウあり
