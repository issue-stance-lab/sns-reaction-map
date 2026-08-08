# 高齢者免許 — マップ生成スクリプトを新設し、意見のみに揃える — 2026-08-08

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

このセッションは **高齢者免許（`elderly-license-revocation`）の1本だけ**。
ついでに**自転車の青切符（`bike-blue-ticket`）の設定も同じPRで揃える**（後述）。

## このテーマの状態

- 正典: `social-samples/elderly-license_2d_classified.json`（211件、意見146件）
- 意見判定はすでに持っている（分類のやり直しは不要）
- 論点カードは正典から生成されている（2026-08-07に対応済み）が `issue_counts.basis: "all"`
- **マップ（SM_RAW）は211件の全件で、しかも論点の割り当てが旧分類のまま**

| | マップ（SM_RAW） | 正典（`classification.main_issue`） |
|---|---|---|
| 件数 | 211 | 211（うち意見146） |
| 内訳 | 139 / 24 / 20 / 9 / 7 / 12 | 95 / 14 / 19 / 10 / 9 / 64 |

- **生成スクリプトが無い**（`page_update_mode: manual`）。だから正典を再分類しても
  ページが追随しなかった
- ページの見出しには**自動生成とは別に手書きの件数**が残っている

## 既存の発注書を先に読む

`configs/prompts/codex/20260807_elderly-bike-arena.md` に
`build_elderly_arena.py` / `build_bike_arena.py` の新設が発注済み。

**着手前にこれを読み、内容が今回の方針（意見のみ）と合っているか確認すること。**
合っていれば流用する。食い違っていれば**今回の方針を優先**し、その旨を報告する。

## 作業前後の数字（見込み）

| 項目 | 現在 | 作業後 |
|---|---|---|
| マップの点 | 211（旧分類の割り当て） | **146** |
| 論点カード | 95 / 14 / 19 / 10 / 9 / 64（全件） | **95 / 15 / 14 / 10 / 6 / 6**（意見のみ） |
| 手書きの見出し件数 | 139 / 24 / 20 / 9 / 7 / 12 | 自動生成に一本化 |

意見146件の内訳（この数に揃える）:

```
義務化・事故防止95 / 適性検査強化15 / 地方の足・移動権14 / 代替交通整備10 / 自主返納支援6 / その他6
義務化賛成85 / 条件付き賛成30 / 義務化反対17 / 中立・情報14
```

**数字が減るのは正常。** ニュース共有が外れるためで、劣化ではない。

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-elderly -b task/elderly-opinion-only
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

### 2. 非公開の正典データを復元する

何をするか: Git管理外の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと検査で落ちる。** 不足していても `git status` には出ない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まる。

```bash
cd ../isa-wt-elderly && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 作業前の状態を記録する

```bash
python3 -c "
import json,collections,re
d=json.load(open('social-samples/elderly-license_2d_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数',len(d),'意見',sum(1 for x in c if x.get('is_opinion')))
print('全件の論点',collections.Counter(x.get('main_issue') for x in c).most_common())
print('意見のみ',collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
h=open('docs/elderly-license-revocation-reaction-map.html').read()
print('手書きの件数', re.findall(r'class=\"issue-count\">(\d+)件',h))
print('自動生成の件数', re.findall(r'explainer-count[^>]*>(\d+)件',h))
"
```

成功の形: 総数211 / 意見146 で、手書きと自動生成の件数リストが**食い違っている**
（これが今回直す対象）。想定と違ったら先に報告して止まる。

### 4. 生成スクリプトを新設する

新規ファイル: `scripts/build_elderly_arena.py`
**手本**: `scripts/build_koshitsu_arena.py`（正典だけを読んで SM_RAW・論点カード・
スタンス集計・詳細データを作り直す。`--check` あり）

設計の条件:

- 入力は正典 `social-samples/elderly-license_2d_classified.json` **だけ**
- `classification.is_opinion` が `True` の146件に絞る
- **`is_opinion` を持たないレコードがあれば、静かに除外せずエラーで止める**
  （落とすと件数が合わない原因が分からなくなる）
- `classification.main_issue` を**そのまま**セクターに使う。
  **ページ内の正規表現でラベルを作らない**（皇室典範でこれをやって、正典に存在しない
  擬似ラベルが2つ表示される事故になった）
- 件数を数える場所を増やさない。SM_RAW から数え上げる設計にする
- `--check` を付ける（書き換えず差分の有無だけ見る）

```bash
python3 scripts/build_elderly_arena.py && python3 scripts/build_elderly_arena.py --check
```

成功の形: 1回目で書き換わり、**2回目の `--check` が差分なし**（何度実行しても同じ結果）。
マップの点が146になる。

### 5. 論点カードの分母を変える

対象ファイル: `configs/elderly-license-revocation-reaction-map.json`

`issue_counts.basis` を `"all"` から `"opinion"` に変える。

```bash
python3 scripts/sync_issue_counts.py elderly-license-revocation && python3 scripts/sync_issue_counts.py --check
```

成功の形: `--check` が差分なしで通り、カードの件数が **95 / 15 / 14 / 10 / 6 / 6** になる。

### 6. 手書きの件数を消す

このページには**自動生成の件数とは別に、手書きの件数が見出しに残っている**
（`<span class="issue-count">139件</span>` など6か所）。データを更新しても動かないため、
今回の食い違いの原因になっていた。

生成スクリプトが書き換える形にするか、削除して自動生成側（`explainer-count`）に
一本化する。**どちらでもよいが、手で書いた数字がページに残らないようにする。**

```bash
python3 -c "
import re
h=open('docs/elderly-license-revocation-reaction-map.html').read()
print('手書き:', re.findall(r'class=\"issue-count\">(\d+)件',h))
print('自動生成:', re.findall(r'explainer-count[^>]*>(\d+)件',h))
"
```

成功の形: 2つのリストが一致する、または手書き側が空になる。

### 7. ページ本文の説明文を直す

```bash
grep -n "211件\|146件\|意見" docs/elderly-license-revocation-reaction-map.html | head -20
```

収集件数と意見件数の**両方**が分かる形に書き換える。

> Yahooリアルタイム検索で取得した公開投稿211件のうち、意見と判定した146件を分析対象としています。

成功の形: 片方の数字だけが単独で出てくる箇所が無くなり、両方がセットで説明されている。

### 8. 自転車の青切符も設定を揃える

同じ発注書に含まれているテーマ。**こちらは数字が変わらない。**
正典181件が全て意見判定 `true` なので、全件＝意見で結果は同じになる。

- `configs/bike-blue-ticket-reaction-map.json` の `issue_counts.basis` を
  `"all"` から `"opinion"` に変える
- 自転車のページにも**手書きの見出し件数**（37 / 33 / 14 / 16 / 19）が残っており、
  自動生成側（38 / 29 / 14 / 14 / 18）と食い違っている。手順6と同じ方法で一本化する
- **「最大勢力」バッジが16件の論点4（免許制）に付いている。** 実際の最大は38件の論点1
  （取締り強化賛成）。正しい位置に直す
- `build_bike_arena.py` の新設は発注書に含まれるが、**数字が変わらないため今回は任意**。
  時間があれば作る（作れば `page_update_mode` を上げられる）

```bash
python3 scripts/sync_issue_counts.py bike-blue-ticket && python3 scripts/sync_issue_counts.py --check
```

### 9. THEMES.yaml を更新する

高齢者免許の `page_update_mode` を `manual` から `adapter_candidate` へ上げる
（生成スクリプトはできたが、収集パイプラインの候補入出力には未対応のため）。
自転車も `build_bike_arena.py` を作った場合は同じく上げる。

### 10. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/build_data_sheet.py && grep -E "高齢者|自転車" DATA_SHEET.md
```

成功の形:

- unittest が `OK`
- 検査スクリプト2本が exit 0
- `DATA_SHEET.md` の高齢者免許の行が **意見146 / 論点146 / 賛否146 / マップ146**
- 自転車の行が **181 / 181 / 181 / 181**

### 11. 見た目を確認する

点が65個減るので、実際に開いて確かめる。

ブラウザで `docs/elderly-license-revocation-reaction-map.html` を開き、次を確認する。

- マップの点が偏って空白の扇形ができていないか
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか

**点が減って見栄えが悪くなっても、勝手に点を戻さない。** そのまま報告する。

### 12. コミットする

コミット対象:

- `scripts/build_elderly_arena.py`（新規）
- `configs/elderly-license-revocation-reaction-map.json`
- `configs/bike-blue-ticket-reaction-map.json`
- `docs/elderly-license-revocation-reaction-map.html`
- `docs/bike-blue-ticket-reaction-map.html`
- `THEMES.yaml`
- `DATA_SHEET.md`

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。
push して main へPRを出す。

### 13. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-elderly
```

---

## 制約・注意

- **論点カードの枚数（高齢者6枚・自転車5枚）を変えない。** 数が変わると読者投票の
  `choiceIdx` の意味がずれ、Supabase Edge Function の再デプロイが必要になる
  （皇室典範で実際に発生）。今回変わるのは**件数だけ**
- **`STANCES` を変えない**（同じ理由）
- **分類のやり直しはしない。** 両テーマとも意見判定を既に持っている。
  今回はページ側だけを直す
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 完了報告に含めること

1. 高齢者免許の作業前後の「マップの点 / 論点カード / 賛否」の件数
2. 手書きの件数をどう処理したか（生成対象にした／削除した）
3. 自転車の「最大勢力」バッジを正しい論点に移したか
4. `build_bike_arena.py` を作ったかどうか
5. 既存発注書 `20260807_elderly-bike-arena.md` と今回の方針に食い違いがあったか
6. 手順11で見た目に問題がなかったか
7. オーナーへの依頼事項があれば1つだけ
