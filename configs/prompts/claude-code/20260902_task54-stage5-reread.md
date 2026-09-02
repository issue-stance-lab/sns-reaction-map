# 課題54 段階5の読み直し — 地下水脈を「人が読んだ」状態にする — 2026-09-02

このファイルをそのまま新しいセッションに貼って実行する。
**①（段階4の修正、`20260902_task54-stage4-fix.md`）が終わってから実行する。同時に走らせない。**
両方とも `TASK_BOARD.md` の同じ段落を書き換えるので、並行するとぶつかる。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典（設計）: `quality/designs/reaction-planet-renewal.md` の **3.3**（照合レイヤー）・
  **3.3.3**（地下水脈の作り方）・**11章**（検査）・**14章**（データ契約）
- 課題: `TASK_BOARD.md` 課題54、段階5
- レビュー記録: `quality/reviews/2026-09-02-task54-stage4-5-review.md` の指摘1・2・3・4
- 直す対象: `data/verification/bukatsu-chiiki-veins.json`

## なぜこの作業をするか

**いまの地下水脈2本は、投稿の本文ではなくAI分類器が付けた要約を材料に組み立てられている。**

代表投稿12件の `summary` を正典の `classification.summary` と突き合わせたところ、
**12件中11件が一字一句同じ**で、残り1件も語尾を足しただけだった
（`2088068389046751432`: 分類器「保護者は国へ」→ veins「保護者は国へ求めるべき」）。

これが通らない理由は3つある。

1. 設計書3.3は、海面より下に「**人が一次資料を読まないと出てこない情報**だけを置く」と決めている。
   AIの分類結果を組み替えたものは、集めて分類すれば機械で再現できるので、海面より下に置く資格がない
2. 設計書3.3.3は「対立する2つ以上の立場の投稿を**編集部が読み**」と手順を指定している
3. `TASK_BOARD.md` 課題54の段階3欄に「**段階4の沈んだ大陸・段階5の地下水脈は、定義上AIに代替させない**」
   と明記されている

そして、このまま段階6へ進むと詰む。設計書3.3と11章が「`ai_assisted`（AIの下読み）を『人が確認』と
表示しない」と決めているため、**①海面下を空のまま公開する ②ルールを破って表示する** の二択になる。

**救いは、対象が小さいこと。** 代表投稿12件は全件、段階3で編集部が1件ずつ読んで確定した31件の中から
選ばれている（重なり12/12を実測）。本文を読んだ実績自体はある。足りないのは
「**水脈として成立するか**を本文で判断し直す」工程だけで、1セッション未満で終わる。

なお、いまのファイルが `curated_by` / `checked_by` を `ai_assisted` と正直に書いている点は正しい判断。
**その正直さを消して `editorial_review` に書き換えるだけの作業にはしないこと。** 実際に読んでから上げる。

## いま実際に起きていること（2026-09-02 に正典で実測済み）

### 問題1: 探索範囲が段階3の31件に閉じている（指摘2）

代表投稿12件は**全件が段階3の確定投稿（`data/bukatsu-chiiki_claim_posts.json` の31件）から**選ばれている。
段階3の31件は「7つの主張が一次資料と合うか」を確かめるために選んだ集合で、
**立場をまたいで共有された懸念を探すための集合ではない。**

その結果、**意見1139件で最大勢力の「移行支持」460件から代表投稿が1件も入っていない。**

| 立場 | 件数 | いまの水脈での採用 |
|---|---|---|
| 移行支持 | 460 | **0件** |
| 慎重・反対 | 390 | 6件 |
| 条件付き・改善要求 | 241 | 6件 |
| 中立・情報 | 48 | 0件 |

2本とも同じ「慎重・反対 対 条件付き・改善要求」の組で、`diverging_reason` も
「やめるべき か 制度を変えて続ける か」と同じ形。3.3.3が禁じる
**「賛否の機械的な鏡像」に形として近づいている。**

### 問題2: 2本目の論点IDと代表投稿の論点が合わない（指摘3）

`bukatsu-chiiki-vein-2` は `issue_id` に `bukatsu-chiiki-kyoin`（教員の働き方）を宣言しているが、
代表投稿6件の実際の分類は **教員の働き方2件 / 制度・移行プロセス2件 / 受け皿・指導者2件**。

3.3の地形は論点（大陸）単位で塗るので、このままだと段階6で
「この水脈をどの大陸の下に置くか」が決まらない。
（`vein-1` は6件すべて `bukatsu-chiiki-ukezara` で問題なし）

### 問題3: `data/verification/` に投稿の要約を入れている（指摘4）

`data/verification/README.md` は「**本文、URL、ユーザーID、tweet_id、要約は含めません**」と明記している。
同じディレクトリの先行例 `data/verification/bike-blue-ticket-reread.json` は
`"excerpt": "not_listed"` として本文を落とし、tweet_id だけを持っている。

設計書14章の地下水脈の項目にも要約は無い（固定ID・論点ID/立場・共有する懸念・分かれる理由・
両側の代表投稿ID・確認日・確認者種別）。**このリポジトリは public**（`issue-stance-lab/sns-reaction-map`）で、
個々の投稿へのAI要約が公開Gitに載っている状態になっている。

---

## 手順

### 1. 作業ツリーを用意する

①で作った `../isa-wt-planet-stage45` をそのまま使う。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/isa-wt-planet-stage45 && git status -sb | head -3
```

成功の形: `## task/planet-stage45-fix` と出て、未コミットの変更が無い。
（作業ツリーが無い場合は ① の手順1〜2をやってから戻る）

正典（`social-samples/`、Git管理外）が無ければ**ディレクトリごと**置く。
部活動の1ファイルだけではテストが16件落ちる。

```bash
rsync -a ../issue-stance-aggregator/social-samples/ social-samples/ && python3 -c "import json;d=json.load(open('social-samples/bukatsu-chiiki_hermes_classified.json'));o=[r for r in d if r['classification']['is_opinion']];print('全',len(d),'件 / 意見',len(o),'件')"
```

成功の形: `全 1395 件 / 意見 1139 件`。違ったら止めて報告する。

### 2. 12件を本文で読む（AIの要約を見ない）

**分類器の `summary` と `reason` を画面に出さずに、本文だけを読む。**
いまの水脈がAI要約の組み替えになっているので、同じ材料を見ると同じ結論に戻る。

```bash
python3 -c "
import json
c={r['tweet_id']:r for r in json.load(open('social-samples/bukatsu-chiiki_hermes_classified.json'))}
v=json.load(open('data/verification/bukatsu-chiiki-veins.json'))
for it in v['items']:
    print('='*70); print(it['id'], it['issue_id']); print('共有する懸念:', it['shared_concern'])
    for s in it['sides']:
        print('--- 立場:', s['stance_label'])
        for p in s['representative_posts']:
            r=c[p['tweet_id']]
            print(' ID', p['tweet_id'], '/ 論点', r['classification']['main_issue'])
            print('   ', r['text'].replace(chr(9),'').replace(chr(10),' '))
"
```

成功の形: 12件の本文が出る。1件ずつ読んで、次を判断する。

- その投稿は、書かれている「共有する懸念」を**本当に語っているか**
- その懸念は**具体的か**（「不安」「不信」のような抽象語で終わっていないか。3.3.3の要件）
- 立場が違う2つの側が、**同じ懸念から違う結論へ**行っているか
  （「どちらも同じことを言っている」に見えるなら、それは水脈ではない）

読んだ結果、**水脈として成立しないと判断したら、その水脈は落としてよい。**
落として2本を切ったときは、下の手順3で新しい水脈を探す。

### 3. 「移行支持」を含む組を探す

最大勢力の移行支持460件が1本も入っていないのは、探索範囲が段階3の31件だったため。
移行支持を含む水脈が1本でも作れないか探す。候補の出し方:

```bash
python3 -c "
import json
d=json.load(open('social-samples/bukatsu-chiiki_hermes_classified.json'))
o=[r for r in d if r['classification']['is_opinion']]
for r in o:
    cl=r['classification']
    if cl['main_issue']=='受け皿・指導者' and cl['stance']=='移行支持':
        print(r['tweet_id'], '|', r['text'].replace(chr(9),'').replace(chr(10),' ')[:150])
" | head -50
```

論点と立場を差し替えて何度か回す。各論点の立場別件数（2026-09-02実測）:

| 論点 | 件数 | 移行支持 | 慎重・反対 | 条件付き・改善要求 | 中立・情報 |
|---|---|---|---|---|---|
| `bukatsu-chiiki-kyoin` 教員の働き方 | 323 | 182 | 69 | 67 | 5 |
| `bukatsu-chiiki-seido` 制度・移行プロセス | 256 | 104 | 71 | 62 | 19 |
| `bukatsu-chiiki-ukezara` 受け皿・指導者 | 164 | 44 | 68 | 49 | 3 |

**見つからなければ2本のままでよい。** その場合は
「移行支持を含む組を探したが、同じ具体的な懸念を共有する組は成立しなかった」と
理由つきで記録に残す（`FACT_CHECK_GUIDE.md` の空振りの扱いと同じ。空振りは空振りのまま出す）。
**無理に3本目を作らない。**

### 4. 2本目の論点IDを直す

代表投稿の実際の論点に合わせる。やり方は2つあり、**どちらでもよい**。

- **A: 論点IDを複数持たせる。** `"issue_ids": ["bukatsu-chiiki-kyoin", "bukatsu-chiiki-seido", "bukatsu-chiiki-ukezara"]`
  にする。設計書14章は地下水脈の項目を「つなぐ論点ID**または立場**」と書いており、
  複数の大陸の下を通る水脈は metaphor としても自然
- **B: 代表投稿を1つの論点にそろえる。** 6件を `bukatsu-chiiki-kyoin` の投稿だけで組み直す

Aを採る場合、`vein-1` も同じ形（`issue_ids` の配列）に揃える。項目名が2本で違う状態にしない。

### 5. 要約を落とす

`representative_posts` から `summary` を外す。手控えが要るなら
`bike-blue-ticket-reread.json` と同じく `"excerpt": "not_listed"` を置くか、
`quality/reviews/` 側のメモに書く。**`data/verification/` に本文・要約を残さない。**

### 6. 確認者種別を上げる

**実際に本文を1件ずつ読んだ水脈だけ**、`curated_by` と `checked_by` を
`editorial_review` に変える。読んでいないものを上げない。
`method` にも、AI要約ではなく本文を読んで判断したことを書き直す
（いまの `note` にある「AIによる下読み・組み合わせ抽出」の記述は、実態に合わせて更新する）。

### 7. 記録を残す

- `TASK_BOARD.md` 課題54 の工程表「段階5」欄と、進捗の段落を更新する
  （読み直した件数、水脈の本数、移行支持を探した結果）
- `THEMES.yaml` の `bukatsu-chiiki` の notes を更新する（いまの記述は `ai_assisted` のまま）
- `quality/reviews/2026-09-02-task54-stage4-5-review.md` の指摘1〜4に「対応済み」と追記する
- `quality/reviews/2026-09-02-task54-stage5-veins.md` に読み直しの結果を追記する

### 8. 検査を足す（時間があれば。無ければ次セッションへ回してよい）

**沈んだ大陸と地下水脈の2ファイルを見る検査は、いま1つも無い**（grep実測で0件）。
設計書11章には検査項目がすでに書かれているのに、実装だけが無い状態。
このプロジェクトでは「検査にしなかったルールは別セッションで破られる」ことが繰り返し起きているので、
**いまの形を固定する最小の検査を足す。**

`scripts/verify_ocean_layer.py`（名前は任意）と `tests/test_ocean_layer.py` を新設し、最低限これを見る。

1. 沈んだ大陸は1テーマ4件以内（3.3.2）
2. 沈んだ大陸の各件に、一次資料URL・該当箇所・`sns_count`・`sns_base`・`checked_on`・`checked_by` がある（11章）
3. 沈んだ大陸の `match_rule.pattern` を実行した結果が `machine_hits` と一致する（3.3.2「機械で再現できる条件」）
4. 地下水脈は1テーマ2〜4本、各立場の代表投稿が2件以上、**その tweet_id が正典に実在する**（11章）
5. `data/verification/` のファイルに本文・要約を入れない（README の規約）
6. `checked_by` が `ai_assisted` のものを、公開契約へ載せる経路に通さない（3.3・11章）

**正典が無い環境（CI・クリーンクローン）では3と4の実在確認を飛ばす**（`social-samples/` はGit管理外）。
飛ばしたことが分かるメッセージを出すこと。黙って通さない。

時間が足りなければ、この手順8だけを `TASK_BOARD.md` 課題54の「未着手」へ**具体的に**書いて次へ回す
（「検査を足す」ではなく、上の1〜6を項目として残す）。

### 9. 検査を通す

```bash
python3 -m unittest discover -s tests 2>&1 | grep -E "^(Ran|OK \(|FAILED)" && python3 scripts/verify_claim_verdicts.py | tail -5 && git status --short docs/ data/public/ && python3 -c "import json;[json.load(open(p)) for p in ['data/verification/bukatsu-chiiki-sunk-continents.json','data/verification/bukatsu-chiiki-veins.json']];print('JSON OK')"
```

成功の形:
- `Ran 370 tests`（手順8で検査を足したならその分増える）と `OK (skipped=4)`
- `verify_claim_verdicts.py` が `OK:` 3行（末尾の警告6件は既知の別件。増えていなければよい）
- **`git status --short docs/ data/public/` が何も出さない**（公開物に触っていない証拠）
- `JSON OK`

### 10. コミットする

```bash
git add -A && git commit -m "課題54段階5: 地下水脈を本文の読み直しで作り直す"
```

**main へのマージ・pushはしない。** 本番反映は `release` スキルに従ってオーナー承認後に行う。

---

## やらないこと

- **公開ページ・公開JSON・生成スクリプトに接続しない。** それは段階6の仕事。
  `docs/` と `data/public/` に差分を出さない
- **読んでいないものを `editorial_review` に書き換えない。** それが今回直している当のもの
- **3本目を無理に作らない。** 2〜4本が設計書の範囲で、2本は範囲内
- 他テーマの地下水脈には手を出さない（段階10の仕事）

## 判断が要るとき

読み直した結果、**成立する水脈が1本以下になった**ときは、勝手に進めずオーナーに聞く。
そのときは「①1本で段階6へ進む ②範囲を広げて探し直す（追加1セッション）」の2案と、
あなたの推奨を添える。設計書3.3.3は2〜4本と決めているので、1本は仕様から外れる。

## 完了の形

1. 地下水脈2〜4本すべてが、**本文を読んだうえで** `editorial_review` になっている
2. 代表投稿の tweet_id が全件、正典に実在する（機械で確認した出力を記録に残す）
3. 各水脈の論点IDが、代表投稿の実際の論点と矛盾しない
4. `data/verification/` のファイルに投稿の要約・本文が入っていない
5. 移行支持を含む組を探した結果が、採用・不採用どちらでも記録に残っている
6. 370テストOK（検査を足したなら増える）、`docs/` と `data/public/` の差分0
