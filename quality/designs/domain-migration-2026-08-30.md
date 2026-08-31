# sns-reaction-map.jp 移行設計

**2026-08-31 に破棄。** 切り替え順序・旧URLの扱い・安定後の公開データ基盤（公開専用リポジトリへの同期構成）は破棄した。
実測の結果、公開元はプロジェクトリポジトリ `issue-stance-lab/sns-reaction-map` の GitHub Pages（`docs/`）に一本化し、
`scripts/sync_public_site.py` は使わない。詳細は `TASK_BOARD.md` の課題55を参照。以下は経緯として残す。

## 決定

- 公開専用リポジトリは `issue-stance-lab/issue-stance-lab.github.io` の1つにする。
- このリポジトリの `docs/` を公開内容の正典とし、`scripts/sync_public_site.py` で公開専用リポジトリの `public/` へ同期する。
- `sns-reaction-map.jp/` をSNS反応まっぷの唯一のトップにする。旧ルート用の別トップは廃止する。
- このリポジトリは移行安定後に非公開化できる構成にする。ただし、公開サイトが参照するファイルやデプロイに必要な秘密情報の移設を確認するまでは非公開化しない。

## 公開前ゲート

1. `python3 -m unittest tests.test_domain_migration tests.test_sync_public_site -v` が通る。
2. `python3 scripts/sync_public_site.py --target ../issue-stance-lab.github.io/public --check` が差分なしになる。
3. 投票の公開クライアント設定は `vote-config.js` にだけ置き、公開専用リポジトリのActions secretsへ複製しない。
4. Supabaseの `VOTE_ALLOWED_ORIGINS` に新旧両方のオリジンを一時的に入れ、投票の読み込みと送信を確認する。
5. GitHub Organizationの設定で `sns-reaction-map.jp` の所有権をTXTレコードにより確認する。
6. 公開候補のトップ、固定ページ、全テーマページを目視確認する。
7. CEOが公開を承認する。

## 切り替え順序

1. 公開専用リポジトリへ候補版を反映し、GitHub ActionsによるPages公開を有効にする。
2. 現在の `sns-reaction-map` リポジトリからカスタムドメインを外し、Pages自体も無効にする。無効にしないと、Organizationサイト配下の `/sns-reaction-map/` が旧プロジェクトサイトとして残る。
3. 公開専用リポジトリへ `sns-reaction-map.jp` を設定する。
4. GitHubのDNS確認が通ったらHTTPSを有効にする。GitHub公式では、設定後HTTPSが利用可能になるまで最大1時間、DNS変更の伝播は最大24時間が目安。
5. `https://sns-reaction-map.jp/` と主要ページ、投票、画像、`robots.txt`、`sitemap.xml`、`ads.txt` を確認する。
6. 問題があれば、公開専用リポジトリのカスタムドメインを外し、元のリポジトリのPagesとカスタムドメインを戻してロールバックする。

DNSのAレコード4件と `www` のCNAMEは現行のGitHub Pages向け設定を維持する。リポジトリを切り替えるだけなので、通常はDNSレコードの再変更は不要。

## 旧URLの扱い

- `https://issue-stance-lab.github.io/` はOrganizationサイトのカスタムドメイン設定により新ドメインへ案内する。
- 旧 `/sns-reaction-map/*.html` には、同名の新URLへ移動する案内ページを置く。クエリ文字列とページ内位置も引き継ぐ。
- 案内ページは `noindex,follow` とし、canonicalは新URLに向ける。
- GitHub Pagesではページ単位のサーバー側301を設定できないため、canonical、サイトマップ、即時meta refreshとJavaScriptによるページ単位の案内を併用する。Googleは即時meta refreshを恒久的な転送として扱えるが、通常の301より弱い代替である。

## Search Console

1. `sns-reaction-map.jp` のドメインプロパティを追加し、XServer DomainのDNSへ指定されたTXTを登録する。
2. `https://sns-reaction-map.jp/sitemap.xml` を送信する。
3. トップ、about、主要テーマをURL検査し、canonicalが新ドメインになっていることを確認する。
4. Search Consoleの「アドレス変更」は使わない。旧サイトは `/sns-reaction-map/` というパス単位であり、この機能はドメインまたはサブドメイン単位のプロパティに限られる。また事前確認にサーバー側301を求めるため、今回のGitHub Pages構成は要件を満たさない。
5. 4週間は「ページのインデックス登録」「重複」「見つかりません」「クロール済み未登録」を週1回確認する。

## AdSense

1. サイトに `sns-reaction-map.jp` を追加する。
2. ルートの `ads.txt` と全ページのAdSenseコードを確認する。
3. サイト所有権の確認状態と、審査対象URLが新ドメインになっていることを確認する。
4. 課題15-A〜Cと品質監査が完了するまで再審査を申請しない。再申請はCEOの別承認を必要とする。

AdSense公式では、新しいサイトは「サイト」から追加し、広告コード・`ads.txt`・metaタグのいずれかで所有確認した後に審査を依頼する。今回は広告コードとルートの`ads.txt`を維持する。

## 公式資料

- [GitHub Pagesでカスタムドメインを管理する](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [GitHub Pagesのカスタムドメインについて](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages)
- [Search Consoleのアドレス変更ツール](https://support.google.com/webmasters/answer/9370220?hl=ja)
- [Google検索でURL変更を伴うサイト移転を行う](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes?hl=ja)
- [AdSenseへ新しいサイトを追加する](https://support.google.com/adsense/answer/12169212?hl=ja)

## 安定後の公開データ基盤

切り替え後2〜4週間、重大な404、投票障害、Search Consoleの急減がないことを確認してから着手する。

- 公開専用リポジトリへ置くものを生成済みHTML・画像・検証用公開ファイルに限定する。
- 元投稿本文、収集データ、運用文書、会社資料、秘密情報は公開専用リポジトリへ置かない。
- 公開物manifestと自動検査を正典化し、手作業のコピーを廃止する。
- 安定確認後、旧リポジトリの公開設定を無効化し、この開発・運用リポジトリの非公開化可否を最終確認する。
