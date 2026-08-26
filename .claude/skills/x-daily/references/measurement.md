# X投稿の記録・計測・同期

投稿実施後に読む。候補検索中には実行しない。

## content/x/posts.mdへ記録する

リプライ実績表の列を次の8列から変更しない。

`# ｜ リプライ先 ｜ テーマ ｜ タイプ ｜ 元投稿views ｜ 自リプライ表示 ｜ 元投稿の返信数 ｜ 元投稿からの経過`

管理画面の集計が列名に依存している。新しい分析項目は行の備考か `content/x/weekly-reviews.md` に書く。
列を変える場合は `scripts/admin_dashboard/collect.py` と `tests/test_admin_dashboard.py` も同時に直す。

投稿直後の `自リプライ表示` は `未計測（投稿直後）` とし、数値を入れない。備考へ次を記録する。

- 自投稿URL、返信先URL、投稿時刻
- 目的、対象者、追加価値
- 冒頭の型、具体化に使った要素、本文構造、締め方
- 投稿文、X換算、画像の有無と理由
- 候補選定時の元投稿指標

週ごとに変える文章要素を決めた場合は、その投稿が対象かどうかも備考に書く。
全要素を毎回変えず、冒頭、具体化、構造、締め方などから1つに限る。

## 24〜48時間後に計測する

```bash
# 24時間以上たった未計測投稿を一覧する。成功時はJSON、対象なしは []
python3 scripts/x_post_views.py pending --json

# 取得した表示・いいね・リポストを記録する。成功時は「1件を記録しました」
python3 scripts/x_post_views.py apply \
  --view <投稿ID>=<表示回数>,<いいね>,<リポスト> \
  --measured-at <YYYY-MM-DDTHH:MM:SS+09:00>

# 自分の投稿に付いた返信を一覧する。なければその旨を表示する
python3 scripts/x_post_views.py replies
```

ログイン済みブラウザで `https://x.com/sns_hannou_ma/with_replies` または自投稿URLを開き、
URLの投稿IDと一致する記事の `[role="group"]` から表示、いいね、リポストを読む。親投稿の数字を使わない。

公開APIで返信数、いいね、投稿時刻、画像は取れるが表示回数は取れない。

```bash
curl -s "https://cdn.syndication.twimg.com/tweet-result?id=<投稿ID>&token=a"
```

計測日時または投稿後経過時間を必ず併記する。投稿直後値と24〜48時間後値を混ぜて比較しない。

## 会話を確認する

`replies` で返信が見つかった場合は内容を読む。人物評価や挑発には乗らず、検証可能な論点へ戻せる場合だけ
返信案を作る。会話の続きには画像を再添付しない。`### 会話フォロー YYYY-MM-DD` に記録する。

## THEMES.yamlとトップを同期する

その日に触れたテーマの `x_posted_at` を実際の日付へ更新する。続いて実行する。

```bash
python3 scripts/sync_portal_stats.py
python3 scripts/verify_top_page.py
```

検査が失敗した場合はコミットせず、原因を直して再実行する。
