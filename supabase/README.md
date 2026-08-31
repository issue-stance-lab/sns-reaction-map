# Supabase投票機能のセットアップ

## 1. DBマイグレーション

Supabase CLIをリンク済みの場合:

```bash
supabase db push
```

CLIを使わない場合は、DashboardのSQL Editorで `data/supabase_schema.sql` を実行します。

## 2. Edge Functionのシークレット

32文字以上のランダムな値を作り、Edge Functionだけに設定します。

```bash
supabase secrets set VOTE_HASH_SECRET="ランダムな秘密値"
supabase secrets set VOTE_ALLOWED_ORIGINS="https://sns-reaction-map.jp,https://issue-stance-lab.github.io"
```

## 3. Edge Functionの公開

投票者はログインしないため、JWT検証を無効にして公開します。許可origin、topic ID、選択肢範囲、24時間重複はFunction内で検証されます。

```bash
supabase functions deploy cast-vote --no-verify-jwt
```

## 4. 公開クライアント設定

`docs/vote-config.js` にProject URLとPublishable keyを設定します。Secret keyまたはService Role keyは設定しません。

```js
window.SNS_VOTE_CONFIG = Object.freeze({
  supabaseUrl: "https://PROJECT_REF.supabase.co",
  publishableKey: "sb_publishable_..."
});
```

両方が空の間は、全テーマがlocalStorageモードで動作します。

## 5. 疎通確認

1. テーマページで投票し、投票結果画面が表示されること
2. Edge Function logsにエラーがないこと
3. `votes` に `topic_id` と `choice_idx` が1件追加されること
4. 同じ接続元から24時間以内に再投票すると `duplicate: true` が返ること
5. ブラウザから `votes` テーブルを直接SELECT/INSERTできないこと
