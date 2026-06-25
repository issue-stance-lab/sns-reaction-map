# SEO / X共有セットアップ

このプロジェクトのCodex担当範囲は、公開ページが検索エンジンとX共有で見つかりやすくなるための集客基盤です。

## 1. 公開URLが決まったら生成する

GitHub Pagesなどの公開URLが決まったら、次のコマンドで `robots.txt` と `sitemap.xml` を生成します。

```bash
python3 scripts/seo/generate_seo_assets.py \
  --site-url "https://YOUR_DOMAIN_OR_GITHUB_PAGES_URL/"
```

例:

```bash
python3 scripts/seo/generate_seo_assets.py \
  --site-url "https://example.github.io/issue-stance-aggregator/"
```

生成対象は `configs/site-cases.json` のページ一覧です。新しい反応マップやまとめUIを追加したら、同じコマンドを再実行します。

## 2. Google Search Console

公開後に Google Search Console で以下を登録します。

- プロパティ: 公開URL
- サイトマップ: `https://公開URL/sitemap.xml`
- 所有権確認: GitHub PagesならHTMLファイル確認かmetaタグ確認を使う

確認用HTMLファイルを発行した場合は `docs/` 直下に置きます。

## 3. X共有で必要なメタタグ

各公開HTMLには、最終的に以下を入れるのが目標です。

```html
<meta name="description" content="ページごとの説明文">
<link rel="canonical" href="https://公開URL/ページ.html">
<meta property="og:site_name" content="SNS反応まっぷ">
<meta property="og:type" content="article">
<meta property="og:title" content="ページタイトル">
<meta property="og:description" content="ページごとの説明文">
<meta property="og:url" content="https://公開URL/ページ.html">
<meta name="twitter:card" content="summary_large_image">
```

OGP画像が未作成の場合、スクリプトは `og:image` と `twitter:image` を出力しません。共通画像 `docs/ogp/default.png` を作成すると、自動で画像メタタグも出力されます。

公開URLが決まった後、生成済みHTMLにメタタグを一括適用する場合は次を実行します。

```bash
python3 scripts/seo/apply_meta_tags.py \
  --site-url "https://YOUR_DOMAIN_OR_GITHUB_PAGES_URL/" \
  --dry-run
```

表示された対象に問題がなければ `--dry-run` を外します。

## 4. Google Analytics

GA4の測定IDが発行できたら、次のコマンドで全HTMLへタグを追加します。

```bash
python3 scripts/seo/apply_ga_tags.py \
  --measurement-id "G-XXXXXXXXXX" \
  --dry-run
```

表示された対象に問題がなければ `--dry-run` を外します。

## 5. 現時点の注意

`sitemap.xml` のURLは絶対URLである必要があります。公開URLが未確定のまま仮URLで作ると、Google Search Console登録時に間違ったURLを送る事故につながるため、公開URL確定後に生成します。
