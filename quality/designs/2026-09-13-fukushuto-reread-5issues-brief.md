# 課題54: 副首都「編集再読」513件の読む作業（別セッション用の指示文）

この1枚だけで作業できる。**他の文書を読む必要はない。**
これは**読む作業と、その結果を仕組みへつなぐところまで**の指示。
つないだ後、山なみページを本番へ出す作業（`release` スキル）は別途行う。

## 何のための作業か

副首都のページを新しい形（山なみ）で本番に出すには、生成器
`scripts/build_planet_data.py` の**独自性の検査**（`independence_gate`）を通す必要がある。
検査は「中身が薄いテーマの公開ページを出さない」ためのもので、
**投稿を人（編集部）が1件ずつ本文で読み直した割合**を見る。条件は2つ。

1. 読み直し済みの論点の合計が、意見全体の**50%以上**（副首都は意見1,452件の半分＝**726件以上**）
2. 読み直した論点は、**読み飛ばしが0件**であること（`grown_count`＝読了後に増えた投稿は4割まで許容）

**2026-09-13時点、副首都はどの論点も0%（未着手）。**

### 見積もりを1回間違えた。ここが今回いちばん重要

最初は「各論点60%読めば条件2を満たす」と見積もったが、**副首都には当てはまらない。**
理由は、副首都の投稿収集が**既に終了している**（2026-07-14〜08-31、追加収集は課題54・63待ちで
止めている）こと。条件2の「読了後に増えた4割まで許容」は、**読んだあとに新しく届いた投稿**の
猶予枠であって、部活動のように収集が今も続いているテーマにしか効かない。副首都は新しい投稿が
届かないので、読んでいない分はそのまま「読み飛ばし」（0件でないと不合格）になる。

**つまり副首都で論点を1つ「読了済み」にするには、その論点をほぼ全件（100%）読む必要がある。**
実例は `data/bukatsu-chiiki_teacher-reread.json`（`教員の働き方`論点、323件中323件読了、
読み飛ばし0・増分0）で確認済み。60%だけ読んで登録した論点は、読んでいない残り40%が
即座に「読み飛ばし」として引っかかり、生成が止まる。

## 読む対象（2026-09-13 実測。最少コストの組み合わせ）

副首都は7論点。**全部を100%読む必要はない**。合計726件（50%）を超える組み合わせのうち、
追加で読む件数が最小になる5論点を選んだ（総当たりで計算済み。都構想・維新・定義・中身は対象外）。

| 論点 | 意見数 | 既に監査済み | 新規に読む | 選んだ理由 |
|---|---:|---:|---:|---|
| 候補地 | 303 | 106 | **197** | |
| 防災・災害 | 215 | 86 | **129** | |
| 優先順位 | 140 | 53 | **87** | |
| その他 | 96 | 38 | **58** | 安全側の余白（下記参照） |
| 費用・財源 | 69 | 27 | **42** | |
| **合計** | **823** | **310** | **513** | 意見1,452件の56.7% |

**「その他」を含めた理由**: 候補地・防災災害・優先順位・費用財源の4論点だけだと合計727件
（50.1%）で、条件1をわずかに超えるだけになる。今後の分類修正1件で50%を割る危険がある
（bukatsu-chiikiの2論点が実際に上限40%の目前まで来ている前例が今回のセッションである）。
**「その他」を足して56.7%まで余白を作る。**

**既に監査済みの310件は、独立監査（`quality/reviews/2026-09-13-fukushuto-missing-independent-134.json`
と`-428.json`）で本文を読んで判定済み。** これは新規に読まなくてよい。区分（バケット）へ
割り振るだけでよい（下記「やること」の2番）。

## 対象を手元に出すコマンド

作業ツリー（`git worktree add ../isa-wt-fukushuto-reread -b task/fukushuto-reread main` で
専用コピーを作ってから）の中で実行する。`social-samples/`はgitに入らないので、先に
`rsync -a ../issue-stance-aggregator/social-samples/fukushuto_hermes_classified.json social-samples/`
で持ってくること。

```bash
python3 - <<'PY'
import json, sys
sys.path.insert(0, 'scripts')
from verification_data import record_id_hash

canon = json.load(open('social-samples/fukushuto_hermes_classified.json'))
audit = {}
for f in ('quality/reviews/2026-09-13-fukushuto-missing-independent-134.json',
          'quality/reviews/2026-09-13-fukushuto-missing-independent-428.json'):
    for r in json.load(open(f))['records']:
        audit[r['record_id_hash']] = r

TARGET = ['候補地', '防災・災害', '優先順位', 'その他', '費用・財源']
already, fresh = [], []
for rec in canon:
    c = rec.get('classification') or {}
    if c.get('is_opinion') is not True or c.get('main_issue') not in TARGET:
        continue
    key = record_id_hash(rec)
    row = {'tweet_id': rec.get('tweet_id'), 'url': rec.get('url'), 'text': rec.get('text'),
           'main_issue': c.get('main_issue'), 'stance': c.get('stance'), 'record_id_hash': key}
    if key in audit:
        row['prior_independent_reason'] = audit[key].get('independent_reason')
        already.append(row)
    else:
        fresh.append(row)

json.dump(already, open('/tmp/fukushuto-already-audited.json', 'w'), ensure_ascii=False, indent=1)
json.dump(fresh, open('/tmp/fukushuto-fresh-read.json', 'w'), ensure_ascii=False, indent=1)
print(f'既監査（区分付けのみ）: {len(already)}件 → /tmp/fukushuto-already-audited.json')
print(f'新規に読む: {len(fresh)}件 → /tmp/fukushuto-fresh-read.json')
PY
```

成功の形: `既監査（区分付けのみ）: 310件` / `新規に読む: 513件`

## やること

### 1. 新規513件を読む（`/tmp/fukushuto-fresh-read.json`）

- **1件ずつ `text`（投稿の本文）を読む。** `classification.summary`等のAI要約だけで分類しない
- 論点ごとに**意味のまとまり（バケット）**へ分ける。いくつに分けるかは決めうちにしない
- 下記「分け方の目安」はヒント。読んだ結果と違えば読んだほうを採る
- **強い言葉や極端な例だけを拾わない。** 静かな言い分のほうが多い

### 2. 既監査310件に区分（バケット）を付ける（`/tmp/fukushuto-already-audited.json`）

本文の再読み直しは不要。`prior_independent_reason`（独立監査時の判定理由）を手がかりに、
1で作ったバケットのどれに当たるかを機械的に割り振る。**判断に迷う件だけ本文を確認する。**

### 分け方の目安（縛りではない。ページの既存文言から拾った仮説）

| 論点 | 目安となる割れ方 |
|---|---|
| 候補地 | 「大阪は南海トラフで不適」批判 ／ 「日本海側・遠隔地（新潟・福岡・北海道等）を推す」 ／ 「首都を先に定義すべき」原則論 |
| 防災・災害 | 「南海トラフ連動で大阪は共倒れ」反対 ／ 「東京一極集中こそ最大リスク」賛成 |
| 優先順位 | 「物価高対策が先」批判 ／ 「構想自体は重要だが抱き合わせに疑問」 |
| 費用・財源 | 「総額・財源不明のまま進めるな」批判 ／ 「大型事業で最初から全費用確定の方が珍しい」擁護 |
| その他 | 選挙・党派対立への言及／制度全般への懸念／その他雑多（無理に細分化しない） |

## 成果物

`data/fukushuto_5issues-reread.json` を新しく作る（5論点を1ファイルにまとめる。
bukatsu-chiikiの `cost-receiver-reread.json` が複数論点1ファイルの実例）。

```jsonc
{
  "theme": "fukushuto",
  "scope": "候補地・防災災害・優先順位・その他・費用財源の5論点、意見823件全件",
  "population": { "意見全体": 1452, "5論点合計": 823 },
  "read_at": "（実際に読み終えた日。例: 2026-09-14）",
  "method": "独立監査（2026-09-13）で本文を読んで判定済みの310件はその記録から区分を付与。残り513件は編集部が本文を1件ずつ新規に読み、区分へ分類した。キーワード抽出は使っていない",
  "candidate_site": {
    "buckets": { "A": { "label": "…", "count": 0 } },
    "items": [
      { "tweet_id": "…", "url": "…", "stance": "…", "bucket": "A", "bucket_label": "…",
        "summary": "…", "text_sha256": "…" }
    ]
  },
  "disaster_prep": { "buckets": {}, "items": [] },
  "priority": { "buckets": {}, "items": [] },
  "other": { "buckets": {}, "items": [] },
  "cost_funding": { "buckets": {}, "items": [] }
}
```

- 論点1つ＝1つの上位キー（`candidate_site`=候補地 / `disaster_prep`=防災・災害 /
  `priority`=優先順位 / `other`=その他 / `cost_funding`=費用・財源）
- 各論点内で **`buckets`の合計 = `items`の件数 = その論点の全件数**（下表と一致すること）
- `items[].tweet_id`は論点内で重複禁止、`text_sha256`は`text`のsha256（後で本文が変わったら検出するため）
- 候補地303／防災・災害215／優先順位140／その他96／費用・財源69 —— **この件数ちょうどに
  一致しないと次のステップの検査で止まる**（読み漏れ・数え間違いのサイン）

## 仕組みへつなぐ

`configs/planet/fukushuto.yaml` の `sub_issues: {}` を、次で置き換える。

```yaml
sub_issues:
  候補地:
    file: data/fukushuto_5issues-reread.json
    path: [candidate_site, buckets]
    coverage: full
    coverage_note: 独立監査の再読記録と追加の本文読み直しを合わせて全件読了
  防災・災害:
    file: data/fukushuto_5issues-reread.json
    path: [disaster_prep, buckets]
    coverage: full
    coverage_note: 独立監査の再読記録と追加の本文読み直しを合わせて全件読了
  優先順位:
    file: data/fukushuto_5issues-reread.json
    path: [priority, buckets]
    coverage: full
    coverage_note: 独立監査の再読記録と追加の本文読み直しを合わせて全件読了
  その他:
    file: data/fukushuto_5issues-reread.json
    path: [other, buckets]
    coverage: full
    coverage_note: 独立監査の再読記録と追加の本文読み直しを合わせて全件読了
  費用・財源:
    file: data/fukushuto_5issues-reread.json
    path: [cost_funding, buckets]
    coverage: full
    coverage_note: 独立監査の再読記録と追加の本文読み直しを合わせて全件読了
```

`reread_registry`（ファイル冒頭1行目）は`false`のままでよい。共通台帳
（`data/verification/reread/fukushuto.json`）は無くても上のsub_issuesだけで検査は通る
（無い場合は検査自体が省略される仕組み。他テーマとの体裁を揃えたければ後日別途作ってもよいが、
本番反映の必須条件ではない）。

## 完了の確かめ方

**本物の検査をそのまま使う。**（elderly-license時代と違い、fukushutoは設定ファイルが
既にあるので、簡易チェッカーを別途作らずこれで確認できる。）

```bash
python3 - <<'PY'
import sys, yaml
sys.path.insert(0, 'scripts')
import build_planet_data as bpd
data = bpd.build('fukushuto')
cfg = yaml.safe_load(open('configs/planet/fukushuto.yaml').read())
failures = bpd.independence_gate(data, cfg)
if failures:
    for f in failures: print('NG:', f)
else:
    print('判定: 通る')
PY
```

成功の形: **`判定: 通る`**（2026-09-13時点で実行すると
`NG: 編集部が読み直した論点が意見の0%しかない（50%以上必要）` と出る。それが作業前の姿）

エラーが出たら典型的な原因はこれ:
- `「◯◯」の正典ID集合と公開JSONの件数が一致しません` → その論点の`items`件数が
  上の表の件数と違う（読み漏れ・重複・対象外論点の混入）
- `「◯◯」の区分件数が再読IDの実数と一致しません` → `buckets`の`count`と`items`の実数がずれている
- `「◯◯」に読み飛ばしがN件あります` → その論点を100%読めていない（このテーマは4割の猶予が使えない、上記参照）

## やってはいけないこと

- **キーワード抽出や機械分類の要約だけで区分を決めない。** 本文を読む（既監査分は`独立監査の判定理由`を手がかりにしてよい）
- **「その他」だけ読み飛ばして5論点から外す。** 50%条件の余白がなくなり、次の分類修正1件で不合格に戻る
- **60%程度で「読了済み」として登録しない。** このテーマは読み飛ばし0件が必須で、部活動の感覚は通用しない
- **共有ツリーで作業しない。** 専用の作業用コピー（worktree）を作る
- **`docs/fukushuto-reaction-map.html`を直接編集しない。** 次のステップの生成器が書き換える

## 終わったら（次のステップ）

1. `tasks/task-54.md`に、読んだ件数・所要・完了確認の結果を追記する
2. 判定が「通る」になったら、山なみページを実際に生成する:
   ```bash
   python3 scripts/build_planet_page_preview.py --topic fukushuto --for-docs --out docs/fukushuto-reaction-map.html
   ```
   （入力は差し替え前のgit履歴のコミットから取る。一度差し替え済みのページはこのスクリプトへ
   再入力できない。差し替え前の`docs/fukushuto-reaction-map.html`を退避してから実行するか、
   `git show <差し替え前コミット>:docs/fukushuto-reaction-map.html`で復元してから使うこと）
3. 標準4検査（`verify_theme_page.py`／`verify_number_provenance.py`／`verify_top_page.py`／
   `python3 -m unittest discover -s tests`）を実際に走らせる
4. `data/public/themes/fukushuto.json`を`build_public_registry.py --topic fukushuto`で作り直す
5. 本番反映（マージ・push・公開確認・片付け）は`release`スキルに従う。マージとpushはAIが実行する
