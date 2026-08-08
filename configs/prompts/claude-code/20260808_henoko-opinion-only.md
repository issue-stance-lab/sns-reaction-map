# 辺野古 — 意見判定を追加し、マップの絞り込みを意見に変える — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `LOOP.md` ⓪（作業場所の確保）/ データ台帳: `DATA_SHEET.md`

## なぜこの作業をするか

11テーマのページは「テーマ / 論点 / 賛否 / Xの表示（散布マップ）」で構成されている。
このうち**何件を数えているかがテーマごとに違い**、比較も検証もできない状態になっている。

オーナー判断で、**全テーマ「意見のみを数える」に統一する**ことに決まった。
ニュースのURL共有など「意見と判定されなかった投稿」を、論点・賛否・マップから外す。

このセッションは **辺野古（`henoko-student-accident`）の1本だけ**。

## このテーマの状態

- 正典: `social-samples/henoko/henoko_hermes_arena_classified.json`（363件）
- **意見判定を持っていない**（`is_relevant` / `is_opinion` が無い）
- マップは `scripts/build_henoko_arena.mjs` が生成。`article_usable === true` の
  **265件**に絞っている
- 論点カードは `data/issue-counts/henoko-student-accident.json`（265件）を読んでいる
- `page_update_mode: adapter_candidate`

`article_usable` は「記事の代表例として安全に使えるか」を表す値で、
**意見かどうかとは別の基準**である。これをマップの絞り込みに使っているのが今の状態。

## 作業前後の数字（見込み）

| 項目 | 現在 | 作業後 |
|---|---|---|
| 正典 | 363件（意見判定なし） | 363件（意見判定あり） |
| マップの点 | 265（`article_usable` 由来） | 意見の件数 |
| 論点カード | 53 / 75 / 25 / 21 / 21 / 70（凍結ファイル由来） | 意見ベースの実数 |

**このテーマは意見が少なく出る可能性が高い。** 6月の事故で、7/26の追加収集では
意見投稿が6件しかなかった。意見が150件を下回っても異常ではない。
**数字が小さいことを理由に判定を甘くしないこと。**

---

## 手順

### 1. 作業ツリーを用意する

何をするか: 他セッションとファイルを取り合わないよう、専用の作業用コピーを作る。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git fetch origin && git worktree add ../isa-wt-henoko -b task/henoko-opinion-only origin/main
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

> **末尾の `origin/main` を省かないこと。** 省くと共有ツリーの現在のブランチから
> 枝分かれする。共有ツリーは他セッションの作業中で、main より遅れていたり
> 無関係なコミットが載っていたりする（2026-08-08 の皇室典範では、30コミット遅れ・
> 7コミット先行の状態だった）。そのままPRを出すと他人の変更を巻き込む。

### 2. 非公開の正典データを復元する

何をするか: Git管理外の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと検査で落ちる。** 不足していても `git status` には出ない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まる。

```bash
cd ../isa-wt-henoko && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 作業前の状態を記録する

何をするか: 変更前の数字を控えておく。あとで「本当に意図どおり動いたか」を確かめるため。

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/henoko/henoko_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数', len(d))
print('article_usable', sum(1 for x in c if x.get('article_usable') is True))
print('意見判定を持つ', sum(1 for x in c if x.get('is_opinion') is not None))
print('論点', collections.Counter(x.get('main_issue') for x in c).most_common())
print('賛否', collections.Counter(x.get('stance') for x in c).most_common())
"
```

成功の形: 総数363 / article_usable 265 / 意見判定を持つ 0。
ここが違っていたら、**先に報告して止まる**。別セッションが先に触っている可能性がある。

### 4. 分類器に意見判定と「その他」を足す

対象ファイル: `scripts/classify_henoko_arena_hermes.py`
**手本**: `scripts/classify_bukatsu_arena_hermes.py`（同じ Hermes 方式で意見判定を持っている）

#### 4-1. `ISSUES` に「その他」を追加する

```python
ISSUES = {
    "安全管理・事故原因",
    "報道・行政対応",
    "政治的中立性",
    "政治利用・基地問題",
    "追悼・被害者の尊厳",
    "平和教育の萎縮",
    "その他",          # 追加
}
```

**なぜ**: 現在は逃げ道がなく、分類できない投稿が既存6論点のどれかに押し込まれている。
**広げる方向の変更なので、既存データのラベルと衝突しない。**

`STANCES` は**変えない**。

#### 4-2. プロンプトに判定ルールを足す

- `is_relevant`: 辺野古の高校生死亡事故、文科省の判断、平和教育、追悼、報道対応に
  関係すれば `true`
- `is_opinion`: 投稿者自身の評価・主張・懸念・追悼の意思が読み取れる場合だけ `true`
- ニュース共有・見出しの転載・告知だけなら `is_relevant=true` / `is_opinion=false` /
  `stance` は「中立・情報共有」
- 無関係なら `is_relevant=false` / `is_opinion=false` / `main_issue` は「その他」/
  `stance` は「中立・情報共有」

出力例（JSON）にも `is_relevant` と `is_opinion` を含めること。

#### 4-3. `parse_response()` に後処理を足す

`classify_bukatsu_arena_hermes.py` の87〜95行目と同じ整合処理を入れる。

- `is_relevant` / `is_opinion` を `bool()` で正規化する
- `is_relevant` が false なら `is_opinion` も強制的に false にする
- `is_opinion` が false なら `stance` を「中立・情報共有」に寄せる

**成功の形**:

```bash
python3 -c "import runpy; v=runpy.run_path('scripts/classify_henoko_arena_hermes.py'); print(sorted(v['ISSUES']), sorted(v['STANCES']))"
```

が7論点・4スタンスを表示する。

### 5. 既存363件を分類し直す

実行前に必ずバックアップを取る。

```bash
cp social-samples/henoko/henoko_hermes_arena_classified.json /tmp/henoko_before.json
```

分類スクリプトの引数は `--help` で確認する。

確認コマンド:

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/henoko/henoko_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数',len(d),'判定なし',sum(1 for x in c if x.get('is_opinion') is None))
print('関連',sum(1 for x in c if x.get('is_relevant')),'意見',sum(1 for x in c if x.get('is_opinion')))
print('論点',collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
print('賛否',collections.Counter(x.get('stance') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `判定なし 0`。ここで出た意見件数を控えておく（以降すべてこの数に揃う）。

### 6. マップの絞り込みを意見に変える

対象ファイル: `scripts/build_henoko_arena.mjs`

現在この行で絞っている。

```javascript
.filter((row) => row.classification?.article_usable === true)
```

これを `is_opinion === true` に変える。`article_usable` は代表投稿の選定にだけ使う値なので、
マップの母数には使わない。変更理由をファイル冒頭のコメントに1行残す。

```bash
node scripts/build_henoko_arena.mjs && node scripts/build_henoko_arena.mjs
```

成功の形: 2回実行しても `docs/henoko-arena-data.js` の中身が同じ（何度実行しても
同じ結果になる）。点の数が手順5の意見件数と一致する。

### 7. 論点カードを正典から数えるようにする

対象ファイル: `configs/henoko-student-accident-reaction-map.json`

- `issue_counts` に `"basis": "opinion"` を設定する
- `issue_counts.source`（`data/issue-counts/` を参照している設定）があれば削除する

そのうえで凍結ファイルを消す。

```bash
rm data/issue-counts/henoko-student-accident.json
python3 scripts/sync_issue_counts.py henoko-student-accident && python3 scripts/sync_issue_counts.py --check
```

成功の形: `--check` が差分なしで通り、カードの件数が手順5の意見ベースの内訳と一致する。

> **これは TASK_BOARD 課題29 の残作業の1本。** もう1本は憲法改正で、そちらが済むと
> `data/issue-counts/` ディレクトリごと不要になる。課題29の該当箇所を更新すること。

### 8. ページ本文の説明文を直す

ページに件数の説明文がある。マップと論点が意見のみになったので、実際と食い違う。

```bash
grep -n "363件\|265件\|意見" docs/henoko-student-accident-reaction-map.html | head -20
```

収集件数と意見件数の**両方**が分かる形に書き換える。

> Yahooリアルタイム検索で取得した公開投稿363件のうち、意見と判定した◯◯件を分析対象としています。

成功の形: 片方の数字だけが単独で出てくる箇所が無くなり、両方がセットで説明されている。

### 9. 検証データを作り直す

```bash
python3 -c "
from pathlib import Path
from scripts.verification_data import write_verification_file
write_verification_file(Path('social-samples/henoko/henoko_hermes_arena_classified.json'), Path('data/verification/henoko-student-accident.json'))
print('done')
"
```

### 10. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/build_data_sheet.py && grep 辺野古 DATA_SHEET.md
```

成功の形:

- unittest が `OK`
- 検査スクリプト2本が exit 0
- `DATA_SHEET.md` の辺野古の行で **意見 / 論点の合計 / 賛否の合計 / マップの点が同じ数**

### 11. 見た目を確認する

点が減るので、マップがスカスカに見えないか実際に開いて確かめる。

ブラウザで `docs/henoko-student-accident-reaction-map.html` を開き、次を確認する。

- マップの点が偏って空白の扇形ができていないか
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか

**点が減って見栄えが悪くなっても、勝手に点を戻さない。** そのまま報告する。

### 12. コミットする

コミット対象:

- `scripts/classify_henoko_arena_hermes.py`
- `scripts/build_henoko_arena.mjs`
- `configs/henoko-student-accident-reaction-map.json`
- `docs/henoko-arena-data.js`
- `docs/henoko-student-accident-reaction-map.html`
- `data/verification/henoko-student-accident.json`
- `data/issue-counts/henoko-student-accident.json`（削除）
- `DATA_SHEET.md`
- `TASK_BOARD.md`（課題29の更新）

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。
push して main へPRを出す。

### 13. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-henoko
```

---

## 制約・注意

- **「賛否」の表示には触らない。** このテーマは最多が「論点を切り分ける」214件で、
  賛否として機能していない。これは既知の別問題で、**別セッションで扱う**。
  今回は件数の数え方だけを直す
- **論点カードの枚数（6枚）を変えない。** 数が変わると読者投票の `choiceIdx` の意味が
  ずれ、Supabase Edge Function の再デプロイが必要になる（皇室典範で実際に発生）。
  今回変わるのは**件数だけ**
- **`STANCES` を変えない**（同じ理由）
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 完了報告に含めること

1. 作業前と作業後の「総数 / 意見 / 論点の合計 / 賛否の合計 / マップの点」
2. 意見と判定されなかった件数と、その中身の傾向（ニュース共有が多いのか等）
3. 手順3の事前確認が想定どおりだったか
4. 手順11で見た目に問題がなかったか
5. 検査で落ちた項目があればその内容（隠さず書く）
6. オーナーへの依頼事項があれば1つだけ
