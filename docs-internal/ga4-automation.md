# GA4指標 自動取得メモ

作成日: 2026-07-08

このプロジェクトでは、Google Analytics Data APIを使ってGA4指標を自動取得できる。
次回以降のAIは、まずこのファイルを確認すること。

## 現状

GA4取得はOAuth方式で自動化済み。

2026-07-26以降、すべてのレポートは公開ホスト
`issue-stance-lab.github.io` のみに絞って取得する。`localhost` と
`127.0.0.1` の開発アクセスはKPIへ含めない。

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

別の公開ホストへ移行した場合:

```bash
python3 scripts/fetch_ga4_metrics.py \
  --days 7 \
  --host-name "YOUR_PRODUCTION_HOST"
```

通常運用では `.env` の `GA4_HOST_NAME`、次に `GSC_SITE_URL` のホスト名を
自動使用する。どちらも未設定の場合は
`issue-stance-lab.github.io` を使用する。

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
utm_source=x のX投稿流入を utm_campaign（post_YYYYMMDD）別に集計（2026-08-17 追加）
```

X投稿流入は `## X post traffic (utm_source=x)` の見出しで出る。`utm_campaign` は
X_POSTING_GUIDE.md §4 のとおり投稿日なので、行がそのまま「どの投稿から何人来たか」になる。
0行（`(no sessions)`）は「投稿からのクリックが記録されていない」という結果であって、
取得失敗ではない。

2026-07-26に公開ホスト限定で取得確認済み:

```text
activeUsers: 10
screenPageViews: 163
sessions: 48
eventCount: 403
related_theme_click: 0
share_button sessions: 0
```

## 必要な.env設定

`.env` に以下が必要。

```bash
GA4_PROPERTY_ID="数字のGA4プロパティID"
GOOGLE_OAUTH_CLIENT_SECRET="/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/secrets/ga4-oauth-client.json"
GA4_HOST_NAME="issue-stance-lab.github.io"
```

注意:

- `GA4_PROPERTY_ID` は `G-K10S4YCZFH` ではない。
- `GA4_PROPERTY_ID` はGA4管理画面にある数字だけのプロパティID。
- `GA4_HOST_NAME` はGA4へ記録された公開サイトのホスト名。プロトコルやパスは付けない。
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
外部 + 本番環境（2026-08-10 に「テスト中」から切り替え）
```

利用者:

```text
politicstokyo@gmail.com
```

Google Cloud Console の該当ページ:

```text
https://console.cloud.google.com/auth/audience?project=project-4b0fbab9-87a9-4ef1-999
```

ユーザーの種類は「外部」であること。「内部」にすると、以下のエラーでブロックされる。

```text
403: org_internal
issue-stance-ga4-local-reader は組織内でのみ利用可能です
```

## 「テスト中」に戻してはいけない

**「テスト中」のアプリのリフレッシュトークンは、Googleの仕様で7日後に強制的に無効化される。**

2026-07-18・07-26・08-09 の3回、取得が止まったのはこれが原因。毎回「トークンを作り直す」
対処をしていたが、原因が公開ステータスだったため1週間で再発していた。
2026-07-26〜08-10 の15日間、KPIのスナップショットが1件も取れていない。

「本番環境」に切り替えた 2026-08-10 以降、この期限は無い。**Audience の画面にある
「テストに戻る」ボタンを押さないこと。** 押すと7日ごとの失効が復活する。

なお、切り替えただけでは足りない。**切り替え前に発行済みのトークンは「テスト中」の
条件で発行されているため、7日で切れる。** 切り替えたあとに一度だけ認証を取り直す必要が
ある（2026-08-10 に実施済み）。

## 「このアプリは Google で確認されていません」は正常

本番環境に切り替えても、この警告画面は毎回出る。消すには Google の審査（verification）が
必要で、GA4・Search Console のスコープは「機密スコープ」に分類されているため審査対象になる。

**審査は不要。** 利用者が開発者本人1人だけなら、警告を通過すれば使える。

通過手順:

```text
左下の「詳細」
→ issue-stance-ga4-local-reader（安全ではないページ）に移動
→ 続行
```

「安全ではないページ」の遷移先は `127.0.0.1`（このMacの中）で、外部には出ない。

## 認証をやり直す手順

トークンが壊れた・スコープを増やしたときだけ。定期的にやる必要はない。

```bash
mv secrets/ga4-oauth-token.json secrets/ga4-oauth-token.old-$(date +%Y%m%d).json
python3 scripts/fetch_ga4_metrics.py --days 7
```

表示されたURLをブラウザで開いて許可すると、`secrets/ga4-oauth-token.json` が再生成される。
成功していれば、指標の表が出る。画面の流れは下の「初回認証手順」と同じ。

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
