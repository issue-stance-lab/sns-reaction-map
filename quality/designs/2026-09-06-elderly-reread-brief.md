# 課題54 段階10-2a: 高齢者の免許返納「読む作業」（別セッション用の指示文）

この1枚だけで作業できる。**他の文書を読む必要はない。**
これは**読む作業だけ**の指示で、ページ作りはこのあと別に行う。

## 何のための作業か

高齢者の免許返納ページを新しい形にするには、生成器 `scripts/build_planet_data.py` の
**独自性の検査**を通す必要がある。検査は「中身が薄いテーマの公開ページを出さない」ためのもので、
**投稿を人（編集部）が1件ずつ本文で読み直した割合**を見る。

条件は2つ。

1. **読み直し済みの論点の合計が、意見全体の50%以上**（このテーマでは353件の半分＝**177件以上**）
2. **読み直した論点は、未読が4割以下**であること

**このテーマには読み直しデータが1件も無い。**ゼロから読む。

**機械の分類（Hermes / kimi-k2.6）では代用できない。**あれは収集直後に
「関係あるか・意見か・どの論点か・賛成か反対か」を振り分ける工程で、
この作業は**その先で、人が本文を読んで意味のまとまりに分け直す**もの。
「集めて数えただけではない」ことがこのサイトの価値なので、ここを機械に戻すと意味が消える。

## 読む対象（2026-09-06 実測）

意見353件。論点ごとの内訳と、立場の偏りは次のとおり。

| 論点 | 件数 | 立場の内訳 |
|---|---|---|
| **義務化・事故防止** | **221** | 義務化賛成175・条件付き37・**反対5**・中立4 |
| 適性検査強化 | 51 | 条件付き31・賛成10・反対5・中立5 |
| **地方の足・移動権** | **29** | **反対20**・条件付き3・中立6 |
| その他 | 20 | ほぼ中立・情報 |
| 自主返納支援 | 16 | 中立12 |
| 代替交通整備 | 16 | 反対6・中立6 |

### 読むもの

- **必須：義務化・事故防止 221件。** これ1つで50%の壁（177件）を越える。
  最低ラインは133件（未読を4割＝88件以下にする）だが、**221件すべて読むこと**。
  133件で止めると、次の収集で数件増えるだけで条件を割る
- **強く推奨：地方の足・移動権 29件。**

**合計250件。**

### なぜ「地方の足・移動権」も読むのか

**義務化・事故防止は、79%が義務化賛成**（221件中175件）。ここだけ読むと、
**賛成側だけを深く読んだ状態**になる。いっぽう**反対の声は「地方の足・移動権」に
集中している**（29件中20件が反対）。

同じ失敗を部活動でやっている。あちらは反対側87件だけを読み、賛成側182件が
手つかずのまま公開しようとして止まった。**片側だけを深く読む状態は、
「どちらが正しいかを一方的に決めない」という会社の行動原則（`company/COMPANY.md`）と
正面からぶつかる。**数を満たすためではなく、**この偏りを最初から作らないため**に29件を足す。

## 対象を手元に出すコマンド

作業ツリーの中で実行する。`social-samples/` は git に入らないので、先に
`rsync -a ../issue-stance-aggregator/social-samples/ social-samples/` で持ってくること。

```bash
python3 - <<'PY'
import json
rows = json.load(open('social-samples/elderly-license_2d_classified.json'))
def opinion(r):
    c = r.get('classification') or {}
    return c.get('is_relevant') is not False and c.get('is_opinion') is not False
target = [r for r in rows if opinion(r)
          and r['classification']['main_issue'] in ('義務化・事故防止', '地方の足・移動権')]
json.dump(target, open('/tmp/elderly-target.json', 'w'), ensure_ascii=False, indent=1)
print(len(target), '件を /tmp/elderly-target.json へ出した')
PY
```

成功の形: `250 件を /tmp/elderly-target.json へ出した`

## やること

1. **1件ずつ `text`（投稿の本文）を読む。**
   `classification.summary` や `reason` はAIが付けた要約なので、**それだけで分類しない**
2. **意味のまとまりへ分ける。** いくつに分けるかは決めうちにしない。読んでから決める。
   **2つの論点は別々に分ける**（賛成側の言い分と、地方の足の言い分は性質が違う）
3. 区分ごとの件数を数える

### 分け方の目安（縛りではない）

賛成側は「**何を恐れているか**」で割れる可能性が高い（事故の被害・加害の責任・
自分の親のこと など）。地方の足の側は「**何が無いと困るか**」で割れる可能性が高い。
ただしこれは仮説なので、本文を読んだ結果と違えば読んだほうを採る。

**強い言葉や極端な例だけを拾わない。**多いのは静かな言い分のほうで、
そこを落とすと「声の大きさを社会の総意として扱わない」に反する。

## 成果物

`data/elderly-license_issues-reread.json` を新しく作る。

```jsonc
{
  "theme": "elderly-license-revocation",
  "scope": "main_issue が「義務化・事故防止」221件と「地方の足・移動権」29件の全件",
  "population": { "意見全体": 353, "義務化・事故防止": 221, "地方の足・移動権": 29 },
  "read_at": "2026-09-06",
  "method": "編集部が本文を1件ずつ読み、区分へ再分類した。キーワード抽出による件数は使っていない",
  "buckets": {
    "義務化・事故防止": { "A": { "label": "…", "count": 0 }, "B": { "label": "…", "count": 0 } },
    "地方の足・移動権": { "A": { "label": "…", "count": 0 } }
  },
  "items": [
    { "tweet_id": "…", "url": "…", "main_issue": "義務化・事故防止", "stance": "義務化賛成",
      "bucket": "A", "bucket_label": "…", "summary": "…", "risk": "low" }
  ]
}
```

- **論点ごとに `buckets` を分ける。**あとでページ作りの担当が
  `configs/planet/` から論点ごとに読み出す
- **各論点の区分の合計＝その論点の `items` の件数**になっていること

## 完了の確かめ方

設定ファイル `configs/planet/elderly-license-revocation.yaml` がまだ無いので、
本番の検査（`build_planet_data.py`）はこの段階では動かない。**代わりにこれを回す。**

```bash
python3 - <<'PY'
import json, collections, pathlib
rows = json.load(open('social-samples/elderly-license_2d_classified.json'))
op = [r for r in rows
      if (r.get('classification') or {}).get('is_relevant') is not False
      and (r.get('classification') or {}).get('is_opinion') is not False]
total = len(op)
per = collections.Counter(r['classification']['main_issue'] for r in op)
p = pathlib.Path('data/elderly-license_issues-reread.json')
read = {x['tweet_id'] for x in json.load(open(p))['items']} if p.exists() else set()
covered = 0
print(f"{'論点':<14}{'全体':>5}{'読了':>5}{'未読':>5}{'未読率':>7}  4割条件")
for k, v in per.most_common():
    d = sum(1 for r in op if r['classification']['main_issue'] == k and r['tweet_id'] in read)
    un = v - d
    ok = d > 0 and un <= 0.4 * v
    if ok: covered += v
    print(f"{k:<14}{v:>5}{d:>5}{un:>5}{100*un/v:>6.0f}%  {'○' if ok else '×'}")
need = -(-total // 2)
print(f"\n意見{total}件 / 50%の壁 {need}件 / いま覆えている {covered}件")
print("判定:", "通る" if covered >= need else f"あと{need-covered}件ぶんの論点が要る")
PY
```

成功の形: **義務化・事故防止と地方の足・移動権の両方が「○」**になり、
最後の行が **`判定: 通る`** になる。

（いま実行すると全部×で `あと177件ぶんの論点が要る` と出る。それが作業前の姿）

## やってはいけないこと

- **キーワード抽出で件数を出さない。**実測で3〜4割多く出る
- **AIの `summary` だけで分類しない。**本文を読む
- **義務化・事故防止だけ読んで終わりにしない。**検査は通るが、賛成側だけを
  深く読んだページになる
- **「その他」20件を読もうとしない。**区分できないものの集まりで、読んでも論点にならない
- **共有ツリーで作業しない。**`git worktree add ../isa-wt-<名前> -b task/<名前> main` で
  専用の作業用コピーを作る

## 終わったら

`tasks/task-54.md` に、読んだ件数・区分の数・所要を追記する。
そのあとページ作りに進む（設定ファイル・経緯の台帳・アダプタ）。
自転車の手順書 `quality/designs/2026-09-06-bike-rollout-brief.md` が、その部分の見本になる。
本番反映は `release` スキルに従う（マージとpushはAIが実行する）。
