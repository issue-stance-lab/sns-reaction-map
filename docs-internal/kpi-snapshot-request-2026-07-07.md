# KPI週次スナップショット依頼 2026-07-07

目的: `GROWTH.yaml` の `kpi.snapshots` を週次で更新し、施策判定に使うベースラインを欠測込みで残す。

## 人間に依頼する取得項目

### GA4

期間: 直近7日

1. アクティブユーザー数
2. 表示回数（pageviews）
3. セッション数
4. 1セッションあたりのページビュー、または `pageviews / sessions`
5. 参照元/メディア別のユーザー数
6. `utm_source=share_button` のユーザー数・セッション数
7. `related_theme_click` イベント数

### Supabase

1. `votes` テーブルの累計件数
2. 直近7日の投票件数
3. topic別の投票件数

### Search Console

1. 直近7日のクリック数
2. 直近7日の表示回数
3. 直近28日のクリック数
4. 直近28日の表示回数

### X

1. `@sns_hannou_ma` のフォロワー数
2. 直近7日の投稿数
3. 直近7日のプロフィールアクセス数（見られる場合）
4. URLクリック数（見られる場合）

## 転記フォーマット

```yaml
- date: 2026-07-14
  weekly_users: null
  pageviews: null
  pages_per_session: null
  votes_total: null
  votes_week: null
  gsc_impressions: null
  gsc_clicks: null
  x_followers: null
  notes: null
```

値が取れない項目は `null` のままにする。推測値で埋めない。

## 判定に使う予定

- `2026-07-19`: `portal-featured-slot` / `x-post-templates`
- `2026-07-21`: `share-after-vote`
- `2026-07-22`: `related-themes-block`（2026-07-08に計測開始済み。`share-after-vote` とは別指標のため並行計測）
