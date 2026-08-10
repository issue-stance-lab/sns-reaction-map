# 投票数 自動取得メモ

作成日: 2026-08-10

`docs/growth-kpi-automation.md` から参照されているが実体が無かったので新設した。

## 実行

```bash
python3 scripts/fetch_supabase_votes.py
```

JSONで取得:

```bash
python3 scripts/fetch_supabase_votes.py --json
```

1テーマだけ:

```bash
python3 scripts/fetch_supabase_votes.py --topic koshitsu-tenpakai-issue-stance-v2
```

2026-08-10 に取得確認済み（合計15票）。

## 取得経路

**`votes` テーブルは直接読めない。** 2026-07-31 の
`supabase/migrations/202607310001_secure_votes.sql` が

```sql
REVOKE ALL ON TABLE public.votes FROM anon, authenticated;
```

を実行し、読み取りを `public.get_vote_counts()` の中へ隠した。この関数の実行権限は
`service_role` にしか無い。

そのため、このスクリプトは**サイト本体と同じ公開の入口**から読む。

```text
GET {SUPABASE_URL}/functions/v1/cast-vote?topic_id={topic_id}
→ {"counts": {"0": 1, "5": 1}}
```

Edge Function 側が `service_role` で `get_vote_counts()` を呼び、選択肢ごとの
集計だけを返す。個票（誰がいつ入れたか）は外に出ない。

`service_role` キーをこのスクリプトに持ち込まないこと。持ち込めば投票の個票を
読める鍵が手元の平文ファイルに増える。集計しか要らないので必要ない。

## topic_id の正典

`supabase/functions/cast-vote/index.ts` の `TOPIC_CHOICES`。スクリプトはここから
読むので、二重に管理しない。ここに無い `topic_id` は Edge Function が
`invalid_topic` で弾く。

## 壊れていた期間

2026-07-31（上記migration）〜 2026-08-10。この間、
`scripts/fetch_supabase_votes.py` は

```text
Supabase HTTP error 401: permission denied for table votes
```

で落ちていた。`GROWTH.yaml` の `votes_total` が 7/26 の 12 のまま止まっていたのは
これが原因（実際は 8/10 時点で15票）。

なお 401 の本文に出る `GRANT SELECT ON public.votes TO anon;` は
**実行してはいけない。** migration が意図して剥がした権限で、実行すると
投票の個票が誰でも読める状態に戻る。

## よくある失敗

### 403 origin_not_allowed

Edge Function は `Origin` ヘッダを見て弾く。スクリプトからは `Origin` を
付けないこと（付けるなら `VOTE_ALLOWED_ORIGINS` に入っている値）。

### 合計が管理画面と合わない

`--json` の出力には票が1票も無いテーマが出てこない。合計は出ているテーマの
足し算になる。テスト用トピックは `TOPIC_CHOICES` に無いので最初から入らない。
