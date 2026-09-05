# 課題54 段階9-A: 「教員の働き方」の読み直し（別セッション用の指示文）

この1枚だけで作業できるように書いてある。**課題54の他の文書を読む必要はない。**

## 何のための作業か

部活動ページを公開するには、生成器 `scripts/build_planet_data.py` が持っている
**独自性の検査**を通す必要がある。いまはここで止まっている。

```
独自性の検査に不合格:
  - 「教員の働き方」の未読が236件（全323件の4割超）
```

この検査は「中身が薄いテーマの公開ページを出さない」ためのもので、
**論点の投稿を人（編集部AI）が1件ずつ本文で読み直した割合**を見ている。
検査を迂回する `--prototype` があるが、それは試作用で公開には使えない。

**もう1つ、検査より大事な理由がある。**「教員の働き方」でこれまで読み直したのは
**移行に慎重・反対の側の87件だけ**で、**賛成側（移行支持）182件は1件も読んでいない。**
片側だけを深く読んだ状態は、「どちらが正しいかを一方的に決めない」という
会社の行動原則（`company/COMPANY.md`）と正面からぶつかる。
数を満たすためではなく、**この偏りを直すための作業**として進めてほしい。

## 対象（実測値・2026-09-06 時点）

| | 件数 |
|---|---|
| 「教員の働き方」全体 | 323 |
| 読み直し済み | 87（すべて移行支持以外） |
| **未読** | **236** |
| └ 移行支持 | **182** ← 必須の対象 |
| └ 慎重・反対 | 25 |
| └ 条件付き・改善要求 | 24 |
| └ 中立・情報 | 5 |

- **必須**: 移行支持182件を読む。これで未読が54件になり、検査（4割＝129件以下）を通る
- **できれば**: 残り54件も読む。全323件が読了になり、`coverage` を `full` にできる

## 対象を手元に出すコマンド

作業ツリーの中で実行する（`social-samples/` は git に入らないので、共有ツリーから
`rsync -a ../issue-stance-aggregator/social-samples/ social-samples/` で先に持ってくること）。

```bash
python3 - <<'PY'
import json
rows = json.load(open('social-samples/bukatsu-chiiki_hermes_classified.json'))
read = {x['tweet_id'] for x in json.load(open('data/bukatsu-chiiki_teacher-reread.json'))['items']}
target = [r for r in rows
          if (r['classification'].get('main_issue') or '') == '教員の働き方'
          and r['classification'].get('is_opinion') is not False
          and r['classification'].get('stance') == '移行支持'
          and r['tweet_id'] not in read]
json.dump(target, open('/tmp/reread-target.json', 'w'), ensure_ascii=False, indent=1)
print(len(target), '件を /tmp/reread-target.json へ出した')
PY
```

成功の形: `182 件を /tmp/reread-target.json へ出した` と表示される。

## やること

1. **1件ずつ `text`（投稿の本文）を読む。** `classification.summary` や `reason` は
   AIが付けた要約なので、**それだけを見て分類しない**。本文を読む
2. **賛成側の言い分を、意味のまとまりへ分ける。** いくつに分けるかは決めうちにしない。
   読んでから決める。既存の区分（A〜F）は反対側のものなので、**そのまま使わない**。
   新しい記号（G, H, I …）を続けて振る
3. 区分ごとの件数を数える

### 分け方の目安（縛りではない）

反対側は「移しても負担は減らない」「直すべきは制度と待遇」のように、
**何に反対しているか**で割れた。賛成側は「**何に期待しているか**」で割れる可能性が高い。
ただしこれは仮説なので、本文を読んだ結果と違えば読んだほうを採る。

## 成果物

`data/bukatsu-chiiki_teacher-reread.json` を更新する。**既存の中身は消さない。**

```jsonc
{
  "theme": "bukatsu-chiiki",
  "scope": "…（賛成側を読んだことが分かるように書き足す）",
  "population": { "教員の働き方_全体": 323, "移行支持": 182, "再読対象": 269 },
  "read_at": "2026-09-06",          // 実際に読んだ日
  "method": "…（既存の文をそのまま残し、今回の分を追記）",
  "buckets": {
    "A": { "label": "…", "count": 17 },   // 既存6件はそのまま
    "…": {},
    "G": { "label": "（賛成側の新しい区分）", "count": 0 },
    "H": { "label": "…", "count": 0 }
  },
  "derived": { },                    // 既存を残す。新しい示唆があれば足す
  "items": [                         // 既存87件の後ろに、今回読んだ分を足す
    { "tweet_id": "…", "url": "…", "stance": "移行支持",
      "bucket": "G", "bucket_label": "…", "summary": "…", "risk": "low" }
  ]
}
```

**`buckets` の合計＝`items` の件数**になっていること。生成器はこの合計を
「読み直した件数」として使う。

## 完了の確かめ方

```bash
python3 scripts/build_planet_data.py --topic bukatsu-chiiki
```

成功の形: **「独自性の検査に不合格」が出ず**、`wrote quality/prototypes/…` まで進む。
（`--prototype` を付けてはいけない。付けると検査を素通りする）

続けてこの2つも通す。

```bash
python3 -m unittest discover -s tests
python3 scripts/verify_theme_page.py bukatsu-chiiki
```

成功の形: `OK` と `NG 0件`。

## やってはいけないこと

- **キーワード抽出で件数を出さない。** 実測で3〜4割多く出る（既存の `method` に記録がある）
- **AIの `summary` だけで分類しない。** 本文を読む
- **既存の87件を作り直さない。** 読み直した日も方法も違うものが混ざる
- **`--prototype` で検査を迂回しない。** 公開できないページができるだけ
- **共有ツリーで作業しない。** `git worktree add ../isa-wt-<名前> -b task/<名前> main` で
  専用の作業用コピーを作る（他セッションのファイルが消える事故が実際に起きている）

## 終わったら

`tasks/task-54.md` の段階9-Aの行に、読んだ件数・区分の数・所要を追記する。
本番反映は `release` スキルに従う（マージとpushはAIが実行する）。
