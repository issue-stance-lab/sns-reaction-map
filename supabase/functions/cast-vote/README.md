# cast-vote Edge Function

匿名投票を受け付け、同一IP・同一テーマの24時間以内の重複を防ぎます。IPそのものは保存せず、Edge Function内で秘密鍵付きHMAC-SHA256へ変換します。

## デプロイ前の設定

```bash
supabase secrets set VOTE_HASH_SECRET="32文字以上のランダム値"
supabase secrets set VOTE_ALLOWED_ORIGINS="https://sns-reaction-map.jp,https://issue-stance-lab.github.io"
supabase functions deploy cast-vote --no-verify-jwt
```

`SUPABASE_URL` と `SUPABASE_SERVICE_ROLE_KEY` はホストされたEdge Functionでは標準で利用できます。`VOTE_HASH_SECRET` やService Role KeyをHTMLへ書かないでください。
