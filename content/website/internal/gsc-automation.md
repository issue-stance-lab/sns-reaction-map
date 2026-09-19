# Search Console指標 自動取得メモ

作成日: 2026-07-08

このプロジェクトでは、Google Search Console APIを使ってGSC指標を自動取得できる。
次回以降のAIは、まずこのファイルを確認すること。

## 現状

Search Console取得はOAuth方式で自動化済み。

追加済みスクリプト:

```bash
scripts/fetch_gsc_metrics.py
```

実行コマンド:

```bash
python3 scripts/fetch_gsc_metrics.py --days 28
```

JSONで取得:

```bash
python3 scripts/fetch_gsc_metrics.py --days 28 --json
```

## 取得できる指標

現在のスクリプトは、指定期間の以下を取得する。

```text
clicks
impressions
ctr
position
```

2026-07-08に過去28日で取得確認済み:

```text
site_url: https://issue-stance-lab.github.io/sns-reaction-map/
clicks: 0
impressions: 4
ctr: 0.0000
position: 15.7500
```

## 対象URL

デフォルト対象（2026-09-20更新。旧ホスト時代の記述が残っていたため訂正）:

```text
sc-domain:sns-reaction-map.jp
```

`sns-reaction-map.jp` はSearch Console上で「ドメインプロパティ」として登録されている。この種類のプロパティは、
画面上の見た目や実際のサイトURLとは違い、APIでは `sc-domain:` から始まる専用の識別子を使う。

必要なら `.env` に以下を追加して上書きできる（例: 旧ホストを見る場合。こちらは通常のURL形式の
「URLプレフィックスプロパティ」なので `sc-domain:` は付けない）。

```bash
GSC_SITE_URL="https://issue-stance-lab.github.io/sns-reaction-map/"
```

Search Console APIでは、GSCに登録済みのプロパティの識別子と完全一致している必要がある。
プロパティの種類ごとに書式が違う点に注意（下記「よくある失敗」参照）。

## 必要な.env設定

GA4自動化で作成済みのOAuthクライアントJSONを流用する。

```bash
GOOGLE_OAUTH_CLIENT_SECRET="/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/secrets/ga4-oauth-client.json"
```

注意:

- OAuthクライアントJSONの中身をチャットに貼らない。
- `secrets/` はGit管理しない。
- `GSC_SITE_URL` は必要な場合だけ設定する。

設定確認:

```bash
awk -F= '/^GOOGLE_OAUTH_CLIENT_SECRET|^GSC_SITE_URL/{ print $1 " is set" }' .env
```

## 保存済みファイル

OAuthクライアントJSON:

```text
secrets/ga4-oauth-client.json
```

初回認証後のSearch Console OAuthトークン:

```text
secrets/gsc-oauth-token.json
```

どちらも秘密情報なので、Gitに入れない。

`.gitignore` には以下を追加済み。

```text
secrets/
```

## Google Cloud側の設定

Google Cloudプロジェクト:

```text
My First Project
project-4b0fbab9-87a9-4ef1-999
```

有効化済みAPI:

```text
Google Search Console API
searchconsole.googleapis.com
```

OAuthクライアント:

```text
issue-stance-ga4-local-reader
```

OAuthアプリ設定:

```text
外部 + 本番環境（2026-08-10 に「テスト中」から切り替え）
```

利用者:

```text
politicstokyo@gmail.com
```

**「テスト中」に戻すと、リフレッシュトークンが7日ごとに強制失効する。**
経緯と対処は `content/website/internal/ga4-automation.md` の「『テスト中』に戻してはいけない」を参照。
GA4と同じOAuthクライアントを共有しているので、片方を戻すと両方が同時に壊れる。

## OAuthスコープ

Search Console取得では以下のスコープを使う。

```text
https://www.googleapis.com/auth/webmasters.readonly
```

GA4とは別スコープなので、初回だけ追加認証が必要。

## 初回認証手順

初回実行:

```bash
python3 scripts/fetch_gsc_metrics.py --days 28
```

ターミナルに以下が出る。

```text
Open this URL and approve access:
https://accounts.google.com/o/oauth2/auth?...
Waiting for browser authorization callback...
```

表示されたURLをChromeで開き、`politicstokyo@gmail.com` で許可する。

成功するとブラウザに以下が表示される。

```text
GSC authorization complete. You can close this tab.
```

その後、`secrets/gsc-oauth-token.json` が作成される。

## よくある失敗

### 認証URLの一部だけを開いた

失敗例:

```text
Required parameter is missing: response_type
Error 400: invalid_request
```

原因:

```text
Google認証URLを途中から開いている、またはURLコピーが欠けている。
```

対応:

ターミナルに出たURLを `https://accounts.google.com/o/oauth2/auth?...` から最後まで全部コピーして開く。

### 古い127.0.0.1 URLを開いた

失敗例:

```text
ERR_CONNECTION_REFUSED
```

原因:

```text
前回のOAuth待受がタイムアウト済み。毎回ポート番号が変わる。
```

対応:

```bash
python3 scripts/fetch_gsc_metrics.py --days 28
```

を再実行し、新しく出たURLだけを開く。

### サンドボックスでローカル待受が失敗

失敗例:

```text
PermissionError: [Errno 1] Operation not permitted
```

原因:

```text
OAuthコールバック用に127.0.0.1で一時サーバーを立てる必要がある。
```

対応:

Codex環境では権限付きで再実行する。

### ドメインプロパティなのに通常URLを指定した（403）

失敗例:

```text
GSC HTTP error 403: {"error": {"code": 403, "message": "User does not have sufficient
permission for site 'https://sns-reaction-map.jp/'.", ...}}
```

原因:

```text
sns-reaction-map.jp はSearch Console上で「ドメインプロパティ」として登録されている。
Search Console画面でオーナー権限（確認済み）があっても、Search Analytics APIに渡す
サイト識別子が通常のURL（https://sns-reaction-map.jp/）のままだと、Googleは
「そのURLプレフィックスのプロパティは存在しない」として403を返す。権限不足ではない。
```

対応:

```text
2026-09-20に発生・特定し、DEFAULT_SITE_URL を sc-domain:sns-reaction-map.jp に修正済み。
--site-url で上書きするときも、ドメインプロパティを指定する場合はこの書式を使う。
GSC画面の「設定 > ユーザーと権限」でオーナー/フルが付いているのにこのエラーが出たら、
まずこの書式のずれを疑う（権限を疑って再設定しても直らない）。
```

## 次にやるとよいこと

KPI記録に使う場合は、以下を実行して `GROWTH.yaml` の `kpi.snapshots` に転記する。

```bash
python3 scripts/fetch_gsc_metrics.py --days 28 --json
```

今後拡張するなら、以下の取得を追加する。

```text
query別 clicks / impressions / ctr / position
page別 clicks / impressions / ctr / position
検索クエリ上位から新規テーマ候補を抽出
```
