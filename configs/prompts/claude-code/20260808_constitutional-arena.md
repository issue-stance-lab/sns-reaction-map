# 憲法改正 — マップ生成スクリプトを新設し、意見のみに揃える — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

> **前提**: `20260808_constitutional-amendment-opinion.md` の完了後に実行する。
> あちらで意見判定の追加と既存646件の再分類が終わっていないと、絞り込む対象がない。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `LOOP.md` ⓪（作業場所の確保）/ データ台帳: `DATA_SHEET.md`

## なぜこの作業をするか

11テーマのページは「テーマ / 論点 / 賛否 / Xの表示（散布マップ）」で構成されている。
このうち**何件を数えているかがテーマごとに違い**、比較も検証もできない状態になっている。

オーナー判断で、**全テーマ「意見のみを数える」に統一する**ことに決まった。

このセッションは **憲法改正（`constitutional-amendment`）の1本だけ**。
これが最後の1本で、これが済むと4テーマすべてが揃う。

## このテーマの状態

- 正典: `social-samples/constitutional_amendment_hermes_arena_classified.json`（646件）
- **マップの422件は旧ページに埋め込まれた古いデータで、正典から再現できない**
  （`article_usable` の469件とも一致しない。11テーマの中でこのテーマだけが再現不可）
- 論点カードは `data/issue-counts/constitutional-amendment.json`（422件）を読んでいる
- **ページに「意見646件」と「意見422件」が両方書かれている**（読者から見える矛盾）
- 既存の `scripts/upgrade_constitutional_arena.py` は**生成済みページに再実行できない**
  （`ValueError` になる）ため使えない
- `page_update_mode: migration`

## 着手前の確認（必須）

前のセッションが終わっているかを確認する。

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/constitutional_amendment_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数',len(d),'判定なし',sum(1 for x in c if x.get('is_opinion') is None))
print('関連',sum(1 for x in c if x.get('is_relevant')),'意見',sum(1 for x in c if x.get('is_opinion')))
print('論点',collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
print('賛否',collections.Counter(x.get('stance') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `判定なし 0`。**1件でも残っていたら前のセッションが未完了なので着手しない。**
ここで出た意見件数を控える（以降すべてこの数に揃える）。

## 作業前後の数字（見込み）

| 項目 | 現在 | 作業後 |
|---|---|---|
| マップの点 | 422（旧ページ埋め込み） | 意見の件数（450〜580件の見込み） |
| 論点カード | 116 / 103 / 96 / 55 / 28 / 24（凍結ファイル） | 意見ベースの実数 |
| ページの母数表記 | 646件と422件が併存 | 1種類に統一 |

**数字が動くのは正常。** 意見判定を足した結果、母数が646から減り、賛否の比率も変わる。
劣化ではなく、他テーマと同じ数え方に揃えた結果である。

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-constitutional-arena -b task/constitutional-arena
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

### 2. 非公開の正典データを復元する

何をするか: Git管理外の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと検査で落ちる。** 不足していても `git status` には出ない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まる。

```bash
cd ../isa-wt-constitutional-arena && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

**復元した正典が、前のセッションで再分類した後のものかを必ず確認する**
（「着手前の確認」のコマンドを、復元後にもう一度実行する）。
バックアップが再分類前のものだった場合、作業がやり直しになる。

### 3. 生成スクリプトを新設する

新規ファイル: `scripts/build_constitutional_arena.py`
**手本**: `scripts/build_koshitsu_arena.py`

設計の条件:

- 入力は正典 `social-samples/constitutional_amendment_hermes_arena_classified.json` **だけ**
- `classification.is_opinion` が `True` のものに絞る
- **`is_opinion` を持たないレコードがあれば、静かに除外せずエラーで止める**
- `classification.main_issue` を**そのまま**セクターに使う。
  **ページ内の正規表現でラベルを作らない**（皇室典範でこれをやって、正典に存在しない
  擬似ラベルが2つ表示される事故になった）
- SM_RAW（マップの点）・論点カード・スタンス集計・詳細データをまとめて作り直す
- 件数を数える場所を増やさない。SM_RAW から数え上げる設計にする
- `--check` を付ける（書き換えず差分の有無だけ見る）

既存の `upgrade_constitutional_arena.py` は再実行できないので、**参考にはしても
呼び出さない**。新しいスクリプトが唯一の生成経路になる。

```bash
python3 scripts/build_constitutional_arena.py && python3 scripts/build_constitutional_arena.py --check
```

成功の形: 1回目で書き換わり、**2回目の `--check` が差分なし**（何度実行しても同じ結果）。

### 4. 論点カードを正典から数えるようにする

対象ファイル: `configs/constitutional-amendment-reaction-map.json`

- `issue_counts` に `"basis": "opinion"` を設定する
- `issue_counts.source`（`data/issue-counts/` を参照している設定）があれば削除する

そのうえで凍結ファイルを消す。

```bash
rm data/issue-counts/constitutional-amendment.json
python3 scripts/sync_issue_counts.py constitutional-amendment && python3 scripts/sync_issue_counts.py --check
```

成功の形: `--check` が差分なしで通り、カードの件数が意見ベースの実数と一致する。

> **これで TASK_BOARD 課題29 の残作業が完了する**（辺野古と憲法改正の2本が最後だった）。
> `data/issue-counts/` ディレクトリが空になったら削除し、
> TASK_BOARD の課題29を完了に更新すること。

### 5. ページ内の矛盾を解消する

このページには「意見646件」と「意見422件」が**両方書かれている**。

```bash
python3 -c "
import re
h=open('docs/constitutional-amendment-reaction-map.html').read()
print('意見◯件の出現:', re.findall(r'意見\s*([\d,]+)\s*件',h))
print('収集の表記:', re.findall(r'公開投稿\s*([\d,]+)\s*件',h))
"
```

生成スクリプトが両方を書き換えるようにし、収集件数と意見件数の**両方**が分かる形にする。

> Yahooリアルタイム検索で取得した公開投稿646件のうち、意見と判定した◯◯件を分析対象としています。

成功の形: 「意見◯件」の出現がすべて同じ数字になる。

### 6. THEMES.yaml を更新する

`page_update_mode` を `migration` から `adapter_candidate` へ上げる
（生成スクリプトはできたが、収集パイプラインの候補入出力には未対応のため）。

### 7. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/build_data_sheet.py && grep 憲法 DATA_SHEET.md
```

成功の形:

- unittest が `OK`
- 検査スクリプト2本が exit 0
- `DATA_SHEET.md` の憲法改正の行で **意見 / 論点の合計 / 賛否の合計 / マップの点が同じ数**

### 8. 見た目を確認する

ブラウザで `docs/constitutional-amendment-reaction-map.html` を開き、次を確認する。

- マップの点が偏って空白の扇形ができていないか
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか

**点が減って見栄えが悪くなっても、勝手に点を戻さない。** そのまま報告する。

### 9. コミットする

コミット対象:

- `scripts/build_constitutional_arena.py`（新規）
- `configs/constitutional-amendment-reaction-map.json`
- `docs/constitutional-amendment-reaction-map.html`
- `data/issue-counts/constitutional-amendment.json`（削除）
- `THEMES.yaml`
- `DATA_SHEET.md`
- `TASK_BOARD.md`（課題29を完了に更新）

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。
push して main へPRを出す。

### 10. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-constitutional-arena
```

---

## 制約・注意

- **論点カードの枚数（6枚）を変えない。** 数が変わると読者投票の `choiceIdx` の意味が
  ずれ、Supabase Edge Function の再デプロイが必要になる（皇室典範で実際に発生）。
  今回変わるのは**件数だけ**
- **`STANCES`（4つ）を変えない**（同じ理由）
- **`scripts/upgrade_constitutional_arena.py` を実行しない。** 生成済みページに
  再実行できず `ValueError` で落ちる
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 完了報告に含めること

1. 作業前と作業後の「マップの点 / 論点カード / 賛否 / ページの母数表記」
2. 意見件数（前のセッションの再分類結果）
3. `data/issue-counts/` を削除できたか、課題29を完了にしたか
4. ページ内の「意見◯件」が1種類に統一されたか
5. 手順8で見た目に問題がなかったか
6. **これで4テーマすべてが揃ったので、次は検査の固定
   （`20260808_denominator-check.md`）であることの確認**
7. オーナーへの依頼事項があれば1つだけ
