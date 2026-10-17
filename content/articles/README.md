# content/articles — サイト内記事の原稿

検索される疑問1つに1ページで答える記事の原稿（課題51）。HTMLは生成器が作る。

```
content/articles/{テーマID}/{slug}.md   … 原稿（公開する記事）
content/articles/drafts/                 … 置き場所が決まる前の下書き（生成しない）
docs/articles/{slug}.html                … 生成物。手で直さない
docs/articles/index.html                 … 記事一覧（生成物）
```

- 生成: `python3 scripts/build_articles.py`（`--check` で作り直した結果との一致を確認。CIにも入っている）
- 原稿の書き方（差し込み・図・使える記法）: `scripts/build_articles.py` の冒頭と、既存の原稿を見る
  - SNSの件数は `{{issue:論点名:立場名}}` などの差し込みで書く。手で数字を書かない
  - 本文で件数の大小を言い切ったら、原稿の `asserts` に書く。データ更新で入れ替わると生成が止まる
- サイトマップには生成器の一覧（`build_articles.article_pages()`）から自動で載る。
  記事を足したら `python3 scripts/seo/generate_seo_assets.py --site-url https://sns-reaction-map.jp/` を流す
- 公開は CEO 事前承認が必須（`company/COMPANY.md` 権限の原則）
- 文体は `WRITING_VOICE.md` と `.claude/skills/yomiyasu/`。保存前に
  `python3 scripts/review_with_yomiyasu.py <原稿> --medium seo --strict` と、生成後に
  `python3 scripts/review_with_yomiyasu.py docs/articles/<slug>.html --medium website --strict`
- 記事どうし・テーマページとの文の使い回しは `scripts/verify_page_originality.py` が止める
