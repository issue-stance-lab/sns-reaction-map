# 数える対象を「意見のみ」に統一する — 2026-08-08

このファイルは**5つのセッション分**の指示をまとめたものです。
**1セッションにつき1つの章だけ**を貼って実行してください。上から順に行います。

---

## 全体の目的（全セッション共通・必ず読む）

11テーマのページは「テーマ / 論点 / 賛否 / Xの表示（散布マップ）」で構成されています。
このうち**何件を数えているかがテーマごとに違い**、比較も検証もできない状態です。

| 現状 | テーマ |
|---|---|
| 意見のみを数えている（正しい形） | 消費税・部活動・生成AI・高市・あだ名・副首都 |
| 論点と賛否は意見のみ、**マップだけ全件** | 皇室典範・高齢者免許 |
| ページが正典の**一部だけ**を使っている | 憲法改正・辺野古 |

**これから全テーマを「意見のみを数える」に統一します。**

決めたルールは3行です。

1. 数えるのは「意見」だけ。収集件数と意見件数の両方をページに出す
2. 論点・賛否・マップの点は、同じ意見の集合を数える。3つの合計は必ず一致する
3. 賛否は4つ（賛成 / 反対 / 条件付き / 中立）。賛否で切れないテーマは賛否を出さない

このファイルが扱うのは **1と2** です。3は別途。

### テーマごとの原因（診断済み）

| テーマ | マップの点 | 出所 | 直し方 |
|---|---|---|---|
| 憲法改正 | 422 | 旧ページに埋め込まれた古いデータ。**正典から再現できない** | 生成スクリプトを新設 |
| 辺野古 | 265 | 正典を `article_usable` で絞ったもの。**再現できる** | 絞り込み条件を `is_opinion` に変える |
| 皇室典範 | 347 | 正典の全件 | 生成スクリプトで意見のみに絞る |
| 高齢者免許 | 211 | 正典の全件。しかも論点の割り当てが旧分類のまま | 生成スクリプトを新設 |

### 全セッション共通の作業ツリー手順

各セッションの冒頭で必ず行います。ブランチ名だけ章ごとに変えてください。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-{章の名前} -b task/{章のブランチ名}
```

```bash
cd ../isa-wt-{章の名前} && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まります。

### 全セッション共通の注意

- **`STANCES`（賛否の選択肢）と論点カードの枚数を変えない。** 選択肢の数が変わると
  読者投票の `choiceIdx` の意味がずれ、Supabase Edge Function の再デプロイが必要になります
  （皇室典範で実際に発生）。今回は**件数だけ**が変わります
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合があります（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見えます（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

### 各セッションの終わり方（共通）

```bash
python3 scripts/build_data_sheet.py && python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py
```

成功の形: `DATA_SHEET.md` で担当テーマの**意見・論点の合計・賛否の合計・マップの点が
すべて同じ数**になり、テストと検査2本が exit 0。

通ったらコミットして push、main へPRを出す。作業ツリーを消す前に、そのツリーにしかない
非公開ファイルを共有ツリーへ複製し、バックアップを取り直す。

### 完了報告に含めること（共通）

1. 作業前と作業後の「意見 / 論点の合計 / 賛否の合計 / マップの点」の4つの数字
2. 減った件数と、それが何だったか（ニュース共有が外れたのか等）
3. 検査で落ちた項目があればその内容（隠さず書く）
4. オーナーへの依頼事項があれば1つだけ

---
---

# 第1章: 辺野古 — 絞り込み条件を意見に変える

ブランチ: `task/henoko-opinion-only` / 作業ツリー: `../isa-wt-henoko`

## このテーマの状態

- 正典: `social-samples/henoko/henoko_hermes_arena_classified.json`（363件）
- **意見判定を持っていない**（`is_relevant` / `is_opinion` が無い）
- マップは `scripts/build_henoko_arena.mjs` が生成。`article_usable === true` の265件に
  絞っている
- 論点カードは `data/issue-counts/henoko-student-accident.json`（265件）を読んでいる
- `page_update_mode: adapter_candidate`

`article_usable` は「記事の代表例として安全に使えるか」を表す値で、**意見かどうかとは
別の基準**です。これをマップの絞り込みに使っているのが今の状態です。

## 手順

### 1. 分類器に意見判定と「その他」を足す

対象: `scripts/classify_henoko_arena_hermes.py`
手本: `scripts/classify_bukatsu_arena_hermes.py`（同じ Hermes 方式で意見判定を持っている）

- `ISSUES` に `"その他"` を追加する（**広げる方向なので既存データと衝突しない**）
- `STANCES` は変えない
- プロンプトに判定ルールを足す
  - `is_relevant`: 辺野古の高校生死亡事故、文科省の判断、平和教育、追悼、報道対応に
    関係すれば `true`
  - `is_opinion`: 投稿者自身の評価・主張・懸念・追悼の意思が読み取れる場合だけ `true`
  - ニュース共有・見出しの転載だけなら `is_relevant=true` / `is_opinion=false` /
    `stance` は「中立・情報共有」
  - 無関係なら `is_relevant=false` / `is_opinion=false` / `main_issue` は「その他」
- `parse_response()` に後処理を足す（`classify_bukatsu_arena_hermes.py` の87〜95行目と同じ）
  - `bool()` で正規化 / `is_relevant` が false なら `is_opinion` も false /
    `is_opinion` が false なら `stance` を「中立・情報共有」へ

### 2. 既存363件を分類し直す

実行前に必ずバックアップを取る。

```bash
cp social-samples/henoko/henoko_hermes_arena_classified.json /tmp/henoko_before.json
```

確認コマンド:

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/henoko/henoko_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数',len(d),'判定なし',sum(1 for x in c if x.get('is_opinion') is None))
print('関連',sum(1 for x in c if x.get('is_relevant')),'意見',sum(1 for x in c if x.get('is_opinion')))
print(collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `判定なし 0`。

> **このテーマは意見が少なく出る可能性が高い。** 6月の事故で、7/26の追加収集では
> 意見投稿が6件しかありませんでした。意見が150件を下回っても異常ではありません。
> **数字が小さいことを理由に判定を甘くしないでください。**

### 3. マップの絞り込みを意見に変える

対象: `scripts/build_henoko_arena.mjs`

```javascript
.filter((row) => row.classification?.article_usable === true)
```

これを `is_opinion === true` に変える。`article_usable` は代表投稿の選定にだけ使う。

### 4. 論点カードを正典から数えるようにする

`configs/henoko-student-accident-reaction-map.json` の `issue_counts` に
`"basis": "opinion"` を設定し、`issue_counts.source`（`data/issue-counts/` 参照）があれば
削除する。そのうえで凍結ファイル `data/issue-counts/henoko-student-accident.json` を消す。

```bash
python3 scripts/sync_issue_counts.py henoko-student-accident
```

成功の形: 論点カードの件数が、手順2で出した意見ベースの内訳と一致する。

### 5. 検証データを作り直す

```bash
python3 -c "
from pathlib import Path
from scripts.verification_data import write_verification_file
write_verification_file(Path('social-samples/henoko/henoko_hermes_arena_classified.json'), Path('data/verification/henoko-student-accident.json'))
print('done')
"
```

### 6. 共通の終わり方へ

## この章の注意

- 「賛否」は最多が「論点を切り分ける」214件で、**賛否として機能していません**。
  これは既知の別問題（ルール3行目）です。**この章では触らない**でください。
  賛否の表示を変えるのは別セッションです
- 論点カードの枚数（6枚）を変えない

---
---

# 第2章: 皇室典範 — マップを意見のみに絞る

ブランチ: `task/koshitsu-opinion-only` / 作業ツリー: `../isa-wt-koshitsu`

## このテーマの状態

- 正典: `social-samples/koshitsu-tenpakai_hermes_cur_20260726.json`（347件、意見283件）
- 意見判定はすでに持っている
- マップも論点カードも**全件347件**を数えている（`issue_counts.basis: "all"`）
- 生成スクリプト `scripts/build_koshitsu_arena.py` がある（再実行可能・`--check` あり）
- `page_update_mode: adapter`

**4テーマの中で最も素直に直せます。** 分類のやり直しは不要で、絞り込みを1か所足すだけです。

## 手順

### 1. 生成スクリプトを意見のみにする

対象: `scripts/build_koshitsu_arena.py`

正典を読み込んだ直後に `classification.is_opinion` が `true` のものだけを残すよう変更する。
`build_insight_stats()` が「分析対象の投稿 347件（うち意見は283件）」という表示を作っている
ので、**収集件数と意見件数の両方を出す形は維持**したうえで、SM_RAW・論点カード・
スタンス集計・詳細データの母数を意見283件に変える。

期待される内訳（意見283件）:

```
男系vs女系93 / 旧宮家養子縁組66 / 立法手続き・民主主義47 / 女性天皇・女系天皇33 / その他30 / 愛子さま・皇族の地位14
改正反対（男系維持）165 / 改正賛成（女系容認）70 / 中立・情報48
```

### 2. 論点カードの分母を変える

`configs/koshitsu-tenpakai-reaction-map.json` の `issue_counts.basis` を
`"all"` から `"opinion"` に変える。

```bash
python3 scripts/build_koshitsu_arena.py && python3 scripts/sync_issue_counts.py koshitsu-tenpakai
```

### 3. 冪等性を確認する

```bash
python3 scripts/build_koshitsu_arena.py --check
```

成功の形: 2回目の実行で差分ゼロ（exit 0）。

### 4. 共通の終わり方へ

## この章の注意

- **論点カードは5枚のまま**（「その他」はカードにしない）。枚数を変えると投票が壊れます
- 件数が 104→93 のように減ります。これは正常です

---
---

# 第3章: 高齢者免許 — マップ生成スクリプトを新設する

ブランチ: `task/elderly-opinion-only` / 作業ツリー: `../isa-wt-elderly`

## このテーマの状態

- 正典: `social-samples/elderly-license_2d_classified.json`（211件、意見146件）
- 意見判定はすでに持っている
- 論点カードは正典から生成されている（2026-08-07に対応済み）が `basis: "all"`
- **マップ（SM_RAW）は211件の全件で、しかも論点の割り当てが旧分類のまま**
  （139 / 24 / 20 / 9 / 7 / 12。正典は 95 / 14 / 19 / 10 / 9 / 64）
- 生成スクリプトが**無い**（`page_update_mode: manual`）

## 既存の発注書がある

`configs/prompts/codex/20260807_elderly-bike-arena.md` に
`build_elderly_arena.py` / `build_bike_arena.py` の新設が発注済みです。
**まずこれを読んで、内容が今回の方針と合っているか確認してください。**
合っていれば流用し、合っていなければ今回の方針（意見のみ）を優先します。

## 手順

### 1. 生成スクリプトを新設する

`scripts/build_elderly_arena.py` を作る。手本は `scripts/build_koshitsu_arena.py`
（正典だけを読んで SM_RAW・論点カード・スタンス集計・詳細データを作り直す。`--check` あり）。

- 入力は正典 `social-samples/elderly-license_2d_classified.json` **だけ**
- `classification.is_opinion` が `true` の146件に絞る
- `classification.main_issue` をそのままセクターに使う（**ページ内の正規表現で
  ラベルを作らない**。皇室典範で事故になっています）

期待される内訳（意見146件）:

```
義務化・事故防止95 / 適性検査強化15 / 地方の足・移動権14 / 代替交通整備10 / 自主返納支援6 / その他6
義務化賛成85 / 条件付き賛成30 / 義務化反対17 / 中立・情報14
```

### 2. 論点カードの分母を変える

`configs/elderly-license-revocation-reaction-map.json` の `issue_counts.basis` を
`"all"` から `"opinion"` に変える。

### 3. 手書きの件数を消す

このページには**自動生成の件数とは別に、手書きの件数が見出しに残っています**
（`<span class="issue-count">139件</span>` など6か所）。データを更新しても動かないので、
生成スクリプトが書き換える形にするか、削除して自動生成側に一本化してください。

```bash
python3 -c "
import re
h=open('docs/elderly-license-revocation-reaction-map.html').read()
print('手書き:', re.findall(r'class=\"issue-count\">(\d+)件',h))
print('自動生成:', re.findall(r'explainer-count[^>]*>(\d+)件',h))
"
```

成功の形: 作業後、2つのリストが一致する（または手書き側が消えている）。

### 4. THEMES.yaml を更新する

`page_update_mode` を `manual` から `adapter_candidate` へ上げる
（生成スクリプトはできたが、収集パイプラインの候補入出力には未対応のため）。

### 5. 共通の終わり方へ

## この章の注意

- 論点カードの枚数（6枚）を変えない
- **自転車の青切符も同じ発注書に含まれています。** ただし自転車は211件と違い、
  正典181件が全て意見判定 `true` なので、全件＝意見で数字は変わりません。
  同じPRで `basis` を `"opinion"` に揃えておくと、以後の検査が単純になります

---
---

# 第4章: 憲法改正 — マップ生成スクリプトを新設する

ブランチ: `task/constitutional-arena` / 作業ツリー: `../isa-wt-constitutional-arena`

## 前提: 先に別セッションが必要

**この章は `20260808_constitutional-amendment-opinion.md` の完了後に実行します。**
あちらで意見判定の追加と既存646件の再分類が終わっていないと、絞り込む対象がありません。
着手前に次で確認してください。

```bash
python3 -c "
import json
d=json.load(open('social-samples/constitutional_amendment_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('判定なし',sum(1 for x in c if x.get('is_opinion') is None),'意見',sum(1 for x in c if x.get('is_opinion')))
"
```

成功の形: `判定なし 0`。1件でも残っていたら前のセッションが未完了なので着手しない。

## このテーマの状態

- 正典: `social-samples/constitutional_amendment_hermes_arena_classified.json`（646件）
- **マップの422件は旧ページに埋め込まれた古いデータで、正典から再現できません**
  （`article_usable` の469件とも一致しない）
- 論点カードは `data/issue-counts/constitutional-amendment.json`（422件）を読んでいる
- 既存の `upgrade_constitutional_arena.py` は**生成済みページに再実行できない**
  （`ValueError` になる）ため使えません
- `page_update_mode: migration`

## 手順

### 1. 生成スクリプトを新設する

`scripts/build_constitutional_arena.py` を作る。手本は `scripts/build_koshitsu_arena.py`。

- 入力は正典**だけ**
- `classification.is_opinion` が `true` のものに絞る
- SM_RAW・論点カード・スタンス集計・詳細データを作り直す
- `--check` を付ける（2回目の実行で差分ゼロを確認できるように）

### 2. 論点カードを正典から数えるようにする

`configs/constitutional-amendment-reaction-map.json` の `issue_counts` に
`"basis": "opinion"` を設定し、`issue_counts.source` があれば削除する。
そのうえで凍結ファイル `data/issue-counts/constitutional-amendment.json` を消す。

**この2ファイルが消えると TASK_BOARD 課題29 の残作業が完了します**（辺野古と憲法改正の
2本が最後でした）。TASK_BOARD の該当箇所を更新してください。

### 3. ページ内の矛盾を解消する

このページには「意見646件」と「意見422件」が**両方書かれています**。
生成スクリプトが両方を書き換えるようにし、実際の意見件数に統一してください。

```bash
python3 -c "
import re
h=open('docs/constitutional-amendment-reaction-map.html').read()
print(re.findall(r'意見\s*([\d,]+)\s*件',h))
"
```

成功の形: 作業後、出てくる数字が1種類だけになる。

### 4. THEMES.yaml を更新する

`page_update_mode` を `migration` から `adapter_candidate` へ上げる。

### 5. 共通の終わり方へ

## この章の注意

- 論点カードの枚数（6枚）を変えない
- 意見判定を足した結果、母数が646から減ります（他テーマの実績から450〜580件の見込み）。
  賛否の比率も動きます。**これは劣化ではなく、他テーマと同じ数え方に揃えた結果です**

---
---

# 第5章: 検査を追加して固定する

ブランチ: `task/denominator-check` / 作業ツリー: `../isa-wt-check`

## 前提: 第1〜4章がすべて完了していること

```bash
python3 scripts/build_data_sheet.py && cat DATA_SHEET.md
```

成功の形: 全11テーマで「意見 / 論点の合計 / 賛否の合計 / マップの点」が同じ数。
1つでもずれていたら、その章に戻る。

## なぜ最後にやるか

検査を先に入れると、直していないテーマが全部NGになって作業が進められません。
**直し終えてから、二度と壊れないように固定します。**

## 手順

### 1. `verify_theme_page.py` に検査を足す

現在の検査は `<article class="explainer-card">` の内側しか見ていません。次を追加します。

- **意見件数 = 論点カードの件数合計 = マップの点の数 = 賛否区分の件数合計**
  （一致しない場合は、その差分と理由が設定に明記されていることを条件にする）
- **ページ全体**にハードコードされた件数が残っていないこと
  （現在は `explainer-card` の内側だけを見ているため、見出しの手書き件数を見逃します。
  これが4テーマで古い数字が残っていた原因です）
- 「最大勢力」などの強調表示が、実際の最大値を指していること
  （自転車の青切符では16件の論点に付いていました）

### 2. `build_data_sheet.py --check` をテストに組み込む

`tests/` に、`DATA_SHEET.md` が正典と一致していることを確認するテストを追加する。
これでデータを更新して台帳を作り直し忘れると、テストが落ちます。

### 3. 確認する

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py
```

成功の形: 全部 exit 0。

### 4. わざと壊して、検査が効くことを確かめる

いずれかのページの件数を手で1つ書き換えて、`verify_theme_page.py` が**NGを出すこと**を
確認する。確認したら元に戻す。

**この確認を省かないでください。** 今回の問題は「検査があるのに素通りしていた」ことが
原因でした。検査を足しただけでは、効いているかどうか分かりません。

### 5. 共通の終わり方へ

## この章の完了報告に追加すること

- わざと壊したときに検査が何と言ったか（実際の出力）
