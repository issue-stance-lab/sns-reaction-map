# SQLite DB

SNS反応まっぷ用のローカルSQLite DB。

## DBファイル

`data/reaction_map.sqlite3`

## 登録済み事例

| slug | 事例 | 投稿サンプル |
|---|---|---:|
| `takaichi-bunshun-smear-video` | 高市文春問題 SNS反応まっぷ | 183 |
| `henoko-student-accident-education-law` | 辺野古高校生死亡事故 SNS反応まっぷ | 311 |

## テーブル

| テーブル | 内容 |
|---|---|
| `issues` | 事例マスター |
| `reactions` | 取得した投稿サンプル |
| `classifications` | Ollama/編集補正後の分類 |
| `scorecards` | 論点スコアカード |
| `sources` | 参照ソース |

## 再作成コマンド

高市文春問題:

```bash
python3 scripts/import_reactions_to_sqlite.py \
  --input social-samples/takaichi_realtime_ollama_final_reclassified_editorial.json \
  --db data/reaction_map.sqlite3 \
  --reset
```

辺野古高校生死亡事故:

```bash
python3 scripts/import_reactions_to_sqlite.py \
  --input social-samples/henoko/henoko_realtime_expanded_classified_editorial.json \
  --db data/reaction_map.sqlite3 \
  --issue-slug henoko-student-accident-education-law \
  --issue-title '辺野古高校生死亡事故 SNS反応まっぷ' \
  --description '辺野古高校生死亡事故と文科省の教育基本法違反認定をめぐるSNS反応サンプル分類。拡張版311件。' \
  --source-label 'Yahooリアルタイム検索' \
  --scorecards configs/henoko-scorecards.json \
  --sources configs/henoko-sources.json \
  --replace-issue
```

## 代表SQL

分類別件数:

```sql
SELECT c.category, COUNT(*) AS count
FROM classifications c
JOIN reactions r ON r.id = c.reaction_id
JOIN issues i ON i.id = r.issue_id
WHERE i.slug = 'henoko-student-accident-education-law'
GROUP BY c.category
ORDER BY count DESC;
```

スタンス別件数:

```sql
SELECT c.stance, COUNT(*) AS count
FROM classifications c
JOIN reactions r ON r.id = c.reaction_id
GROUP BY c.stance
ORDER BY count DESC;
```

検索語 × 分類:

```sql
SELECT r.query, c.category, COUNT(*) AS count
FROM reactions r
JOIN classifications c ON c.reaction_id = r.id
GROUP BY r.query, c.category
ORDER BY r.query, count DESC;
```

記事向き代表投稿:

```sql
SELECT c.category, c.stance, c.summary, r.url
FROM reactions r
JOIN classifications c ON c.reaction_id = r.id
WHERE c.article_usable = 1
ORDER BY c.category, c.confidence DESC
LIMIT 30;
```
