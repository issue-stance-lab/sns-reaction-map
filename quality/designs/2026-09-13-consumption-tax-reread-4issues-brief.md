# 課題54: 消費税減税「編集再読」1,019件の読む作業（別セッション用の指示文）

この1枚だけで作業できる。**他の文書を読む必要はない。**
これは**読む作業と、その結果をファイルに保存するところまで**の指示。
このテーマは山なみ形式への切り替え自体（`configs/planet/consumption-tax-cut.yaml`の
作成、投票・ページ構成の移行）がまだ手つかずで、それは**この作業の後の別工程**になる。

## 何のための作業か

山なみページを本番に出すには、生成器 `scripts/build_planet_data.py` の
**独自性の検査**（`independence_gate`）を通す必要がある。「編集部が投稿の中身を
実際に読んで確認した」論点が、意見全体の50%以上あることを機械で確かめる仕組み。
条件は2つ。

1. 読み直し済みの論点の合計が、意見全体の**50%以上**（消費税減税は意見3,358件の半分＝**1,679件以上**）
2. 読み直した論点は、**読み飛ばし＋読了後に増えた分の合計が4割まで**（＝各論点60%読めば登録できる。
   2026-09-13にオーナー判断で基準を緩和。副首都の時点では「収集停止中は実質100%」だったが、
   収集中テーマ（部活動等）と同じ基準に統一した。詳細は`tasks/task-54.md`2026-09-13の記録）

**2026-09-13時点、消費税減税はどの論点も0%（未着手）。** 独立監査等の使い回せる読了実績も無い
（`quality/reviews/`に消費税減税の本文レベル監査記録なし）ので、下記件数はほぼそのまま
新規に読む必要がある。

## 読む対象（2026-09-13 計算。最少コストの組み合わせ、60%基準）

消費税減税は7論点。全部を読む必要はない。合計1,679件（50%）を超える組み合わせのうち、
60%読了で必要件数が最小になる4論点を選んだ（総当たりで計算済み）。

| 論点 | 意見数 | 60%ライン（読む件数） |
|---|---:|---:|
| 減税の対象範囲 | 761 | **457** |
| 減税の効果 | 625 | **375** |
| 給付など他策との比較 | 219 | **132** |
| 事業者の実務負担 | 91 | **55** |
| **合計** | **1,696**（意見全体の50.5%） | **1,019** |

対象外（読まなくてよい）: 公約と政治不信（1,198件・最大論点だが読む量が最も割高）、財源と社会保障（416件）、その他（48件）。

## 対象を手元に出すコマンド

作業ツリー（`git worktree add ../isa-wt-consumption-reread -b task/consumption-reread main`
で専用コピーを作ってから）の中で実行する。`social-samples/`はgitに入らないので、先に
`rsync -a ../issue-stance-aggregator/social-samples/consumption-tax-cut_hermes_arena_classified.json social-samples/`
で持ってくること。

```bash
python3 - <<'PY'
import json

canon = json.load(open('social-samples/consumption-tax-cut_hermes_arena_classified.json'))
TARGET = ['減税の対象範囲', '減税の効果', '給付など他策との比較', '事業者の実務負担']

fresh = []
for rec in canon:
    c = rec.get('classification') or {}
    if c.get('is_opinion') is not True or c.get('main_issue') not in TARGET:
        continue
    fresh.append({'tweet_id': rec.get('tweet_id'), 'url': rec.get('url'), 'text': rec.get('text'),
                  'main_issue': c.get('main_issue'), 'stance': c.get('stance')})

json.dump(fresh, open('/tmp/consumption-fresh-read.json', 'w'), ensure_ascii=False, indent=1)
print(f'対象4論点の全件（読む候補）: {len(fresh)}件 → /tmp/consumption-fresh-read.json')
from collections import Counter
per = Counter(x['main_issue'] for x in fresh)
for k in TARGET:
    print(f'  {k}: {per[k]}件')
PY
```

成功の形: `対象4論点の全件（読む候補）: 1696件` と、論点ごとの内訳（761/625/219/91）。

**この1,696件のうち、論点ごとに60%（上表）を読めばよい。残り4割は「まだ読んでいない分」
として残してよい。** どの投稿を読むかを恣意的に選ばない（賛成側だけ・反対側だけを避けて
読み終えることのないよう、リストの順に読むか、無作為に選ぶ）。

## やること

1. **1件ずつ `text`（投稿の本文）を読む。** `classification.summary`等のAI要約だけで分類しない
2. 論点ごとに**意味のまとまり（バケット）**へ分ける。いくつに分けるかは決めうちにしない
3. 下記「分け方の目安」はヒント。読んだ結果と違えば読んだほうを採る
4. **強い言葉や極端な例だけを拾わない。** 静かな言い分のほうが多い
5. 各論点で、上表の件数（457/375/132/55）に達したら、その論点の読了作業は終えてよい
   （残りは次のステップの成果物に含めない＝「まだ読んでいない分」として自動的に扱われる）

### 分け方の目安（縛りではない。既存ページの論点説明から拾った仮説）

| 論点 | 目安となる割れ方 |
|---|---|
| 減税の対象範囲 | 「食料品だけでは不十分・一律であるべき」／「対象を広げるとインボイス・財源の問題が大きくなる」／「範囲より手続き・時期への不満」 |
| 減税の効果 | 「物価高対策として効果がある・生活が楽になる」／「財源なき減税は国債増発・インフレ加速を招く」／「効果は限定的・他の政策のほうが有効」 |
| 給付など他策との比較 | 「給付より減税のほうが分かりやすい・早い」／「所得連動給付のほうが的を絞れる」／「両方の是非を比較する中立的な言及」 |
| 事業者の実務負担 | 「レジ改修・インボイス対応の現場負担が大きい」／「免税事業者制度そのものへの批判（減税とは別の不満）」／「負担は大きいが減税自体には賛成」 |

## 成果物

`data/consumption-tax-cut_4issues-reread.json` を新しく作る（既存の
`configs/consumption-tax-cut-reaction-map.json`の論点カードのslug — hani/kouka/kyufu/jigyosha —
をそのまま使う。将来`configs/planet/consumption-tax-cut.yaml`ができたとき、
`sub_issues`からこのファイルをそのまま参照できるようにするため）。

```jsonc
{
  "theme": "consumption-tax-cut",
  "scope": "対象範囲・効果・給付比較・事業者負担の4論点、60%読了（残り4割は未読のまま）",
  "population": { "意見全体": 3358, "4論点合計": 1696 },
  "read_at": "（実際に読み終えた日。例: 2026-09-20）",
  "method": "編集部が本文を1件ずつ読み、区分へ分類した。キーワード抽出は使っていない",
  "hani": {
    "buckets": { "A": { "label": "…", "count": 0 } },
    "items": [
      { "tweet_id": "…", "url": "…", "stance": "…", "bucket": "A", "bucket_label": "…",
        "summary": "…", "text_sha256": "…" }
    ]
  },
  "kouka": { "buckets": {}, "items": [] },
  "kyufu": { "buckets": {}, "items": [] },
  "jigyosha": { "buckets": {}, "items": [] }
}
```

- 論点1つ＝1つの上位キー（`hani`=対象範囲 / `kouka`=効果 / `kyufu`=給付比較 / `jigyosha`=事業者負担）
- 各論点内で **`buckets`の合計 = `items`の件数**（読んだ件数と一致すること。上表の457/375/132/55と
  ぴったり一致する必要はないが、大きくずれていたら数え間違いを疑う）
- `items[].tweet_id`は論点内で重複禁止、`text_sha256`は`text`のsha256（`hashlib.sha256(text.encode()).hexdigest()`）
- **`summary`欄に本文をそのまま流用しない。** ハイライト用の`START`/`END`のような内部マークアップを
  混入させない（2026-09-13、副首都の別セッション作業で発生。本文の要約を自分の言葉で書く）
- バケットのラベルは**日本語として読んで意味が通るか、書いたあとに読み返して確認する**
  （2026-09-13、副首都の別セッション作業で簡体字混入・誤字が見つかった）

## 完了の確かめ方

`configs/planet/consumption-tax-cut.yaml`がまだ無いので、本物の`independence_gate`は
この段階では動かせない（config作成は次の工程）。代わりにこれを回す。

```bash
python3 - <<'PY'
import json, hashlib
from collections import Counter

canon = {r['tweet_id']: r for r in json.load(open('social-samples/consumption-tax-cut_hermes_arena_classified.json'))}
d = json.load(open('data/consumption-tax-cut_4issues-reread.json'))
TARGET = {'hani': ('減税の対象範囲', 457), 'kouka': ('減税の効果', 375),
          'kyufu': ('給付など他策との比較', 132), 'jigyosha': ('事業者の実務負担', 55)}

totals = Counter()
for r in canon.values():
    c = r.get('classification') or {}
    if c.get('is_opinion') is True:
        totals[c.get('main_issue')] += 1

ok = True
reread_n = 0
for key, (label, need) in TARGET.items():
    sec = d.get(key, {})
    items = sec.get('items', [])
    bsum = sum(b['count'] for b in sec.get('buckets', {}).values())
    ids = [x['tweet_id'] for x in items]
    dup = len(ids) != len(set(ids))
    bad_hash = sum(1 for x in items
                   if x.get('text_sha256') != hashlib.sha256((canon.get(x['tweet_id'], {}).get('text') or '').encode()).hexdigest())
    read = len(items)
    total = totals[label]
    unread = total - read
    status = 'OK' if (read >= need and bsum == read and not dup and bad_hash == 0) else 'NG'
    if status == 'NG':
        ok = False
    print(f"{label:12s} 読了{read:4d}/目標{need:4d} 全{total:4d} 未読{unread:4d}({unread/total:.0%}) "
          f"bucket合計={bsum} 重複={dup} 指紋不一致={bad_hash}  {status}")
    if status == 'OK':
        reread_n += total

share = 100 * reread_n / 3358
print(f"\n合計{reread_n}件 / 意見全体3358件 = {share:.1f}%（50%以上が必要）")
print('判定:', '通る見込み' if ok and share >= 50 else 'NG')
PY
```

成功の形: 4論点すべて`OK`、最後の行が**`判定: 通る見込み`**になること
（`text_sha256`が current の本文と一致しない場合、後で正典が更新された可能性があるので、
その投稿を読み直すか除外する）。

**注意**: これは「本物の`independence_gate`」ではなく、そのための簡易な事前確認。
`configs/planet/consumption-tax-cut.yaml`を作って`sub_issues`を接続した後、
必ず本物の検査（`build_planet_data.py`経由）で最終確認すること
（`quality/designs/2026-09-13-fukushuto-reread-5issues-brief.md`の「完了の確かめ方」が実例）。

## やってはいけないこと

- **キーワード抽出や機械分類の要約だけで区分を決めない。** 本文を読む
- **賛成側・反対側のどちらかだけを読んで4割に達したことにしない。** 読む順を恣意的に選ばない
- **60%ちょうどで止めて、他の論点を一切読まない、という極端な効率化をしない。** 数え間違いの
  余地を考えると、目標より1〜2割多めに読んでおくと安全
- **共有ツリーで作業しない。** 専用の作業用コピー（worktree）を作る
- **本番ページ（`docs/consumption-tax-cut-reaction-map.html`）を直接編集しない。** このテーマは
  まだ旧形式のままで、山なみへの切り替えは別工程
- **subagentに大量データ（200件以上）を一度に渡して「1件ずつ読んで分類せよ」と指示しない。**
  600秒の制限で不可能なため、自動分類スクリプトに置き換えられ「読んでいない不良品」になる。
  1セッションあたり20〜30件が現実的な上限。それを超える場合は分割投入か、人間作業への委譲を検討する
- **「完了しました」と「正しく完了しました」を混同しない。** subagentの報告は「ファイルが書かれた」
  だけであり、内容品質を保証しない。必ず内容サンプルを人間が確認する

## 終わったら（次のステップ）

1. `tasks/task-54.md`に、読んだ件数・所要・完了確認の結果を追記する
2. **山なみ形式への切り替え自体はまだ行われていない。** `configs/planet/consumption-tax-cut.yaml`の
   新規作成（`configs/planet/fukushuto.yaml`を土台に、stances・issues・vote_issue_order・
   geometryを消費税減税用に書き換える）と、`sub_issues`への接続が必要
   （`quality/designs/2026-09-13-fukushuto-reread-5issues-brief.md`の「仕組みへつなぐ」節が実例）
3. 接続後、本物の`independence_gate`で最終確認し、標準4検査を実行する
4. 本番反映（マージ・push・公開確認）は`release`スキルに従う
