# GA4指標 自動取得メモ

作成日: 2026-07-08

このプロジェクトでは、Google Analytics Data APIを使ってGA4指標を自動取得できる。
次回以降のAIは、まずこのファイルを確認すること。

## 現状

GA4取得はOAuth方式で自動化済み。

追加済みスクリプト:

```bash
scripts/fetch_ga4_metrics.py
```

実行コマンド:

```bash
python3 scripts/fetch_ga4_metrics.py --days 7
```

JSONで取得:

```bash
python3 scripts/fetch_ga4_metrics.py --days 7 --json
```

詳細指標を取得:

```bash
python3 scripts/fetch_ga4_metrics.py --days 7 --details
```

詳細指標をJSONで取得:

```bash
python3 scripts/fetch_ga4_metrics.py --days 7 --details --json
```

## 取得できる指標

現在のスクリプトは、指定期間の以下を取得する。

```text
activeUsers
screenPageViews
sessions
eventCount
```

`--details` を付けると、以下も取得する。

```text
pagePath別 screenPageViews / activeUsers
related_theme_click の eventCount
utm_source=share_button 相当の sessionSource=share_button 流入
```

2026-07-08に過去7日で取得確認済み:

```text
activeUsers: 13
screenPageViews: 296
sessions: 46
eventCount: 605
related_theme_click: 0
share_button sessions: 0
```

## 必要な.env設定

`.env` に以下が必要。

```bash
GA4_PROPERTY_ID="数字のGA4プロパティID"
GOOGLE_OAUTH_CLIENT_SECRET="/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/secrets/ga4-oauth-client.json"
```

注意:

- `GA4_PROPERTY_ID` は `G-K10S4YCZFH` ではない。
- `GA4_PROPERTY_ID` はGA4管理画面にある数字だけのプロパティID。
- OAuthクライアントJSONの中身をチャットに貼らない。
- `secrets/` はGit管理しない。

設定確認:

```bash
awk -F= '/^GA4_PROPERTY_ID|^GOOGLE_OAUTH_CLIENT_SECRET/{ print $1 " is set" }' .env
```

期待値:

```text
GA4_PROPERTY_ID is set
GOOGLE_OAUTH_CLIENT_SECRET is set
```

## 保存済みファイル

OAuthクライアントJSON:

```text
secrets/ga4-oauth-client.json
```

初回認証後のOAuthトークン:

```text
secrets/ga4-oauth-token.json
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
Google Analytics Data API
analyticsdata.googleapis.com
```

サービスアカウントも作成済みだが、JSONキー作成は組織ポリシーでブロックされた。

エラー:

```text
iam.disableServiceAccountKeyCreation
```

そのため、サービスアカウントJSONキー方式ではなく、OAuthクライアント方式を採用した。

## OAuth設定

OAuthクライアント:

```text
issue-stance-ga4-local-reader
```

アプリの公開範囲:

```text
外部 + テスト中
```

テストユーザー:

```text
politicstokyo@gmail.com
```

この設定にしないと、以下のエラーでブロックされる。

```text
403: org_internal
issue-stance-ga4-local-reader は組織内でのみ利用可能です
```

## 初回認証手順

初回実行:

```bash
python3 scripts/fetch_ga4_metrics.py --days 7
```

ターミナルに以下が出る。

```text
Open this URL and approve access:
https://accounts.google.com/o/oauth2/auth?...
Waiting for browser authorization callback...
```

表示されたURLをChromeで開き、`politicstokyo@gmail.com` で許可する。

未確認アプリ警告が出た場合:

```text
詳細
→ issue-stance-ga4-local-reader に移動
→ 許可
```

成功するとブラウザに以下が表示される。

```text
GA4 authorization complete. You can close this tab.
```

その後、`secrets/ga4-oauth-token.json` が作成される。

## よくある失敗

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
python3 scripts/fetch_ga4_metrics.py --days 7
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
python3 scripts/fetch_ga4_metrics.py --days 7 --json
```

今後拡張するなら、以下の取得を追加する。

```text
sessionMedium / campaign などの流入内訳
pagePathの正規化（/sns-reaction-map/ありなしの統合）
イベント別一覧
```
