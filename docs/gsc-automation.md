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

デフォルト対象:

```text
https://issue-stance-lab.github.io/sns-reaction-map/
```

必要なら `.env` に以下を追加して上書きできる。

```bash
GSC_SITE_URL="https://issue-stance-lab.github.io/sns-reaction-map/"
```

Search Console APIでは、GSCに登録済みのプロパティURLと完全一致している必要がある。

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
外部 + テスト中
```

テストユーザー:

```text
politicstokyo@gmail.com
```

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
