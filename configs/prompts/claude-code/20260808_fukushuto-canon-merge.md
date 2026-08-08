# 副首都 — 未統合の308件を正典へ入れ、ビルダーを新設する — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

> **賛否のラベルは3値のまま変えない。** 変えると読者投票が壊れる（後述）。
> 4値への統一は、8月下旬に全テーマまとめて行う。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `DATA_REFRESH.md`（データ更新）/ `LOOP.md` ⓪（作業場所の確保）
- データ台帳: `DATA_SHEET.md` / 課題一覧: `TASK_BOARD.md` の**課題40**

## なぜこの作業をするか

**公開ページが、持っているデータの半分以下しか使っていない。**

2026-07-26 に収集した308件が、「世論の潮目」ウィジェットを作るためだけに使われ、
**累積正典に統合されないまま**残っている。`THEMES.yaml` の `collect_delta: 308` には
記録されているため、台帳では追加済みに見える。

| | 実際に持っている | ページが使っている |
|---|---|---|
| 収集 | **563件** | 255件 |
| 意見 | **約500件** | 229件 |
| 賛否ラベル | **あり**（3値） | **なし**（数値2軸のみ） |

同じ形の取り残しが他の4テーマにもある（課題40）。**このセッションはその1本目で、
残り4本の雛形になる。** 手順が使いにくければ、完了報告でそう書くこと。

## このテーマの状態

| 項目 | 値 |
|---|---|
| 現在の正典 | `social-samples/fukushuto_2d_classified.json`（255件・**2D方式**） |
| 統合すべきファイル | `social-samples/fukushuto_hermes_prev_20260714_v2.json`（292件）<br>`social-samples/fukushuto_hermes_cur_20260726_v2.json`（308件） |
| 論点体系 | 両者とも同じ7論点（定義・中身／都構想・維新／候補地／防災・災害／費用・財源／優先順位／その他） |
| 賛否 | Hermes側は3値（法案反対 / 法案賛成・推進 / 中立・情報）。**2D正典には無い** |
| ページ生成 | `page_update_mode: manual`（**再生成できない**） |
| 投票 | `fukushuto-issue-stance-v1` = **21**（7論点 × 3立場） |
| 収集期限 | 2026-08-11（前倒しで今日実施） |

### 重複関係（確認済み）

- 正典255件は `hermes_prev_20260714_v2`（292件）に**完全に含まれる**
- `hermes_cur_20260726_v2`（308件）は正典と**1件も重複しない**
- Hermes 2本を統合すると **600件ユニーク・意見541件**

## やること（4つ）

1. 収集する（予定どおり）
2. **正典を Hermes 方式へ統合する**（255件の2D正典を退役させる）← 本命
3. `build_fukushuto_arena.py` を新設し、`manual` から脱する
4. `main_issue` 未分類2件を解消する

**賛否は3値のまま。** 4値化はしない。

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git fetch origin && git worktree add ../isa-wt-fukushuto -b task/fukushuto-canon-merge origin/main
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

> **末尾の `origin/main` を省かないこと。** 省くと共有ツリーの現在のブランチから
> 枝分かれし、他人の変更を巻き込んだPRになる。

### 2. 非公開の正典データを復元する

**これをしないと検査で落ちる。** 不足していても `git status` には出ない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まる。

```bash
cd ../isa-wt-fukushuto && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。

### 3. 作業前の状態を記録する

```bash
python3 -c "
import json,collections,re
def ids(rows):
    out=set()
    for r in rows:
        t=str(r.get('tweet_id') or ''); u=str(r.get('url') or '')
        m=re.search(r'/status/(\d+)',u); out.add(t or (m.group(1) if m else u))
    out.discard(''); return out
canon=json.load(open('social-samples/fukushuto_2d_classified.json'))
prev=json.load(open('social-samples/fukushuto_hermes_prev_20260714_v2.json'))
cur=json.load(open('social-samples/fukushuto_hermes_cur_20260726_v2.json'))
print('正典',len(canon),'prev',len(prev),'cur',len(cur))
print('prev∩正典',len(ids(prev)&ids(canon)),'cur∩正典',len(ids(cur)&ids(canon)),'prev∩cur',len(ids(prev)&ids(cur)))
allh={}
for d in (prev,cur):
    for r in d: allh[(r.get('tweet_id') or r.get('url'))]=r
op=[r for r in allh.values() if (r.get('classification') or r).get('is_opinion')]
print('統合後', len(allh), '意見', len(op))
print('論点', collections.Counter((r.get('classification') or r).get('main_issue') for r in op).most_common())
print('賛否', collections.Counter((r.get('classification') or r).get('stance') for r in op).most_common())
"
```

成功の形: `正典255 prev292 cur308` / `prev∩正典255 cur∩正典0 prev∩cur0` / `統合後600 意見541`。
**ここが違っていたら先に報告して止まる。**

### 4. 収集する

```bash
python3 scripts/refresh_topic.py --topic fukushuto --date 2026-08-08 --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

**`--date` には実際に収集した日を渡す。** この文書の日付をそのまま使わない。
**`--promote` は付けない**（このテーマはまだ adapter ではない）。

> `taxonomy_continuity` が「正典に main_issue が無い」で止まる可能性がある。
> 2D正典は `main_issue` を直下に持つので通るはずだが、止まったら
> **手順5（正典の入れ替え）を先に済ませてから収集をやり直す。**

### 5. 正典を Hermes 方式へ統合する（本命）

新しい正典を作る。ファイル名は `social-samples/fukushuto_hermes_classified.json`
（他テーマの命名に合わせる）。

中身の作り方:

1. `hermes_prev_20260714_v2` と `hermes_cur_20260726_v2` を、投稿ID（`tweet_id`、無ければ
   URL内のstatus ID）で重複排除して結合する
2. 手順4で収集した新規分（Hermes分類済み）を足す
3. 各レコードは `classification` の下に
   `is_relevant` / `is_opinion` / `main_issue` / `stance` / `intensity` / `summary` /
   `confidence` / `article_usable` / `risk` を持たせる（他テーマと同じ形）
4. `THEMES.yaml` の `sample_file` を新しいファイルへ向ける
5. **旧2D正典は消さず** `social-samples/fukushuto_2d_classified_v1_2d_only.json` として
   残す（自転車・高齢者と同じ扱い）

**`main_issue` が空のレコードが2件ある。** 分類器で埋めるか、`その他` に寄せる。
**黙って落とさない。** 件数が合わなくなる原因が分からなくなる。

確認コマンド:

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/fukushuto_hermes_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数',len(d),'判定なし',sum(1 for x in c if x.get('is_opinion') is None))
print('main_issue 空',sum(1 for x in c if not x.get('main_issue')))
print('意見',sum(1 for x in c if x.get('is_opinion')))
print('論点',collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
print('賛否',collections.Counter(x.get('stance') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `判定なし 0` / `main_issue 空 0`。

### 6. 生成スクリプトを新設する

新規ファイル: `scripts/build_fukushuto_arena.py`
**手本**: `scripts/build_koshitsu_arena.py` と `scripts/build_elderly_arena.py`

設計の条件:

- 入力は新しい正典**だけ**
- `classification.is_opinion` が `True` のものに絞る
- **`is_opinion` を持たないレコードがあればエラーで止める**（静かに除外しない）
- `classification.main_issue` を**そのまま**セクターに使う。
  ページ内の正規表現でラベルを作らない
- SM_RAW（マップの点）・論点カード・スタンス集計・詳細データをまとめて作り直す
- `--check` を付ける（書き換えず差分の有無だけ見る）
- **「SNS投稿の収集方法」の本文は書かない。** そこは `configs/theme-seo.json` を
  `apply_theme_trust.py` が書く。両方が書くと1回の昇格で再生成不能になる
  （`build_elderly_arena.py` / `build_constitutional_arena.py` に対処済みの実例あり）

```bash
python3 scripts/build_fukushuto_arena.py && python3 scripts/build_fukushuto_arena.py --check
```

成功の形: 1回目で書き換わり、**2回目の `--check` が差分なし**。

### 7. 論点カードと収集方法を合わせる

- `configs/fukushuto-reaction-map.json` の `issue_counts.basis` を `"opinion"` にする
- **`denominator_exceptions` の3件を削除する**（`issues` / `map` / `stances`）。
  `main_issue` 未分類2件は手順5で解消し、賛否は3値が入るので、例外は不要になる
- `configs/theme-seo.json` の副首都の収集方法を差し込みへ変える

```json
"収集した{total}件のうち意見と判定した{opinions}件を論点分析に表示しています。"
```

```bash
python3 scripts/sync_issue_counts.py fukushuto && python3 scripts/seo/apply_theme_trust.py && python3 scripts/sync_portal_stats.py
```

### 8. 「世論の潮目」を確認する

このテーマの潮目は、7/14分と7/26分の比較で作られている。**両方とも正典に入るので、
正典から再現できるようになる。** 現在の表示（法案反対85→78%、賛成15→22%）と
矛盾しないかを確認する。

**合わなければ無理に直さず、数字を並べて報告する。** 潮目の作り直しはこのセッションの
範囲外（`scripts/inject_tide_widget.py` は実行しないこと。課題38）。

### 9. THEMES.yaml を更新する

- `sample_file` … 新しい正典へ
- `page_update_mode` … `manual` → `adapter_candidate`
- `sample_period` … 統合後の実際の範囲へ（`unknown` から埋まるはず）
- `collect_at` … 周期ルールに従って次回を設定

### 10. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/verify_builder_rebuildability.py && python3 scripts/build_data_sheet.py && grep 副首都 DATA_SHEET.md
```

成功の形:

- unittest が `OK`
- 検査3本が exit 0（**`verify_builder_rebuildability.py` は9テーマになる**）
- `DATA_SHEET.md` の副首都の行で**意見 / 論点の合計 / 賛否の合計 / マップの点が同じ数**
- 「ずれあり」の一覧から**副首都が消えている**

### 11. 見た目を確認する

点が2倍以上に増えるので、実際に開いて確かめる。

- マップの点が重なりすぎて潰れていないか
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか

**点が増えて見づらければ、点を間引かず報告する。** 表示調整は別の判断。

### 12. コミットする

コミット対象:

- `scripts/build_fukushuto_arena.py`（新規）
- `configs/fukushuto-reaction-map.json` / `configs/theme-seo.json`
- `docs/fukushuto-reaction-map.html` / `docs/index.html`
- `THEMES.yaml` / `DATA_SHEET.md` / `TASK_BOARD.md`（課題40の副首都を完了に）
- `data/verification/fukushuto.json`（あれば）
- **`data/verification/updates/fukushuto/<日付>/`（今回の収集回サマリ）**

`social-samples/` 配下は非公開なのでコミット対象に入らない。
**作業ツリーを片付ける前に次で何も出ないことを確認する。**

```bash
git status --short data/verification/
```

push して main へPRを出す。

### 13. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-fukushuto
```

---

## 制約・注意

- **賛否を4値にしない。3値のまま。** 選択肢数が 21（7論点×3立場）から変わると、
  読者投票の `choiceIdx` の意味がずれ、Supabase Edge Function の再デプロイと
  既存票の破棄が必要になる。4値化は8月下旬に全テーマまとめて行うので、
  **ここで先に壊さない**
- **論点は7つのまま。** 同じ理由
- **`scripts/inject_tide_widget.py` を実行しない**（課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 旧2D正典も消さず改名して残す
- **`git checkout -- <ディレクトリ>` を使わない**
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 完了報告に含めること

1. 作業前と作業後の「収集 / 意見 / 論点の合計 / 賛否の合計 / マップの点」
2. 統合後の論点と賛否の内訳
3. `main_issue` 未分類2件をどう処理したか
4. `denominator_exceptions` を3件とも削除できたか
5. 潮目の数字が現在の表示と矛盾しなかったか（合わない場合は数字を並べて）
6. 手順11で見た目に問題がなかったか
7. **この手順が残り4テーマ（自転車・高齢者・高市・あだ名・辺野古）の雛形として
   使えそうか。使いにくかった箇所があれば具体的に**
8. オーナーへの依頼事項があれば1つだけ
