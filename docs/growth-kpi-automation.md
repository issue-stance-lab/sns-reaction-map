# グロースKPI 統合取得メモ

作成日: 2026-07-08

GA4 / Search Console / Supabase の自動取得結果をまとめて、`GROWTH.yaml` に貼りやすいKPIスナップショットとして出力する。

## 現状

統合取得は自動化済み。

追加済みスクリプト:

```bash
scripts/fetch_growth_kpi.py
```

実行コマンド:

```bash
python3 scripts/fetch_growth_kpi.py
```

JSONで取得:

```bash
python3 scripts/fetch_growth_kpi.py --json
```

日付を指定:

```bash
python3 scripts/fetch_growth_kpi.py --date 2026-07-08
```

期間を指定:

```bash
python3 scripts/fetch_growth_kpi.py --ga4-days 7 --gsc-days 28
```

## 内部で呼び出すスクリプト

```text
scripts/fetch_ga4_metrics.py
scripts/fetch_gsc_metrics.py
scripts/fetch_supabase_votes.py
```

各スクリプトの詳細:

```text
docs/ga4-automation.md
docs/gsc-automation.md
docs/supabase-votes-automation.md
```

## 出力例

2026-07-08に取得確認済み:

```text
| source | metric | value |
|---|---|---:|
| GA4 | activeUsers | 13 |
| GA4 | screenPageViews | 296 |
| GA4 | pages_per_session | 6.435 |
| Supabase | votes_total | 9 |
| GSC | impressions | 4 |
| GSC | clicks | 0 |
| GSC | ctr | 0.0000 |
| GSC | position | 15.7500 |
```

`GROWTH.yaml` 貼り付け用:

```yaml
    - date: 2026-07-08
      weekly_users: 13
      pageviews: 296
      pages_per_session: 6.435
      votes_total: 9
      votes_week: null
      gsc_impressions: 4
      gsc_clicks: 0
      x_followers: null
      notes: Auto: GA4/Supabase/GSC fetched. X followers remain manual.
```

## 注意点

- `votes_week` はまだ未実装。現状は総投票数 `votes_total` のみ（`test` で始まるテスト用topicは除外）。
- `x_followers` はまだ自動取得していないため `null`。
- GA4とGSCはOAuthトークンが必要。期限切れや権限不足の場合は各メモを参照。
- Codex環境ではネットワーク接続とOAuthローカル待受のため、権限付き実行が必要になる場合がある。

## 次にやるとよいこと

以下を追加すると、週次判断にさらに使いやすくなる。

```text
votes_week の算出
GA4 pagePath別PV
GA4 utm_source=share_button 流入
GA4 related_theme_click イベント数
GSC query別 / page別 指標
```
