# 散布マップの点を「意見のみ」に揃える — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `LOOP.md` ⓪（作業場所の確保）/ データ台帳: `DATA_SHEET.md`

## なぜこの作業をするか

11テーマのうち、**数える対象（分母）が3種類に分かれている**。

| 数え方 | テーマ |
|---|---|
| 意見のみ | 消費税・部活動・生成AI・高市・あだ名・副首都・自転車 |
| **混在**（論点と賛否は意見のみ、マップの点だけ全件） | **皇室典範・高齢者免許** |
| 部分集合（正典の一部だけをページが使っている） | 憲法改正・辺野古 |

オーナー判断で、**マップの点も意見のみに揃える**ことに決まった。
ニュースのURL共有など「意見と判定されなかった投稿」をマップから外す。

## このセッションの対象

**皇室典範（`koshitsu-tenpakai`）の1本だけ。**

他3本は前提作業が終わっていないため、このセッションでは触らない。

| テーマ | 状態 | 待っているもの |
|---|---|---|
| 高齢者免許 | 未着手 | `build_elderly_arena.py` の新設（発注書 `configs/prompts/codex/20260807_elderly-bike-arena.md`） |
| 憲法改正 | 未着手 | 意見判定の追加（`20260808_constitutional-amendment-opinion.md`） |
| 辺野古 | 未着手 | 意見判定の追加（未発注） |

## 作業前後の数字（見込み）

| 項目 | 現在 | 作業後 |
|---|---|---|
| マップの点 | 347 | **283** |
| 論点カードの件数 | 104 / 74 / 54 / 40 / 17 | **93 / 66 / 47 / 33 / 14** |
| 賛否 | 改正反対165 / 賛成70 / 中立48（意見のみで既に集計） | 変わらない見込み |

**数字が減るのは正常。** ニュース共有の64件が外れるためで、劣化ではない。

---

## 手順

### 1. 作業ツリーを用意する

何をするか: 他セッションとファイルを取り合わないよう、専用の作業用コピーを作る。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-koshitsu -b task/koshitsu-arena-opinion
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

### 2. 非公開の正典データを復元する

何をするか: Git管理外の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと検査で落ちる。** 不足していても `git status` には出ない。

```bash
cd ../isa-wt-koshitsu && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 作業前の状態を記録する

何をするか: 変更前の数字を控えておく。あとで「本当に意図どおり動いたか」を確かめるため。

```bash
python3 scripts/build_koshitsu_arena.py --check && python3 -c "
import json,collections
d=json.load(open('social-samples/koshitsu-tenpakai_hermes_cur_20260726.json'))
c=[r.get('classification',{}) for r in d]
print('総数', len(d), '意見', sum(1 for x in c if x.get('is_opinion')))
print('全件の論点', collections.Counter(x.get('main_issue') for x in c).most_common())
print('意見のみ', collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `--check` が「差分なし」で通る（＝いま公開中のページはスクリプトの出力と一致している）。
ここで差分が出たら、**先にその原因を報告して止まる**。手作業でページが書き換えられている可能性がある。

### 4. ビルダーに絞り込みを入れる

対象ファイル: `scripts/build_koshitsu_arena.py`

このスクリプトは `load_canon()` で読んだレコードを唯一の入力として、
SM_RAW（マップの点）・論点カード・投票の選択肢・スタンス集計・詳細データを
まとめて作り直す。**したがって絞り込みは `load_canon()` の1か所に入れれば全部に効く。**

`load_canon()` が返す `rows` を、`classification.is_opinion` が `True` のものだけに絞る。

注意点:

- **`is_opinion` が無いレコードがあれば除外せずエラーで止める。** 静かに落とすと件数が
  合わない原因が分からなくなる
- 絞り込みを入れた理由を、スクリプト冒頭のdocstringに1行残す
- 件数を数える場所は増やさない。既存の「SM_RAW から数え上げる」設計（`build_issues()`）を
  そのまま使う

**成功の形**:

```bash
python3 scripts/build_koshitsu_arena.py --check
```

が「差分あり」を報告する（＝これから書き換わる、が正しい状態）。

### 5. ページを作り直す

```bash
python3 scripts/build_koshitsu_arena.py && python3 scripts/build_koshitsu_arena.py --check
```

成功の形: 1回目で書き換わり、**2回目の `--check` が「差分なし」**（＝何度実行しても同じ結果になる）。

### 6. 論点カードの分母も合わせる

対象ファイル: `configs/koshitsu-tenpakai-reaction-map.json`

`issue_counts.basis` が `"all"` になっている。これを `"opinion"` に変える。
マップだけ意見のみにしてカードが全件のままだと、**同じページの中で分母が2種類**になり、
今回の作業の目的に反する。

```bash
python3 scripts/sync_issue_counts.py koshitsu-tenpakai && python3 scripts/sync_issue_counts.py --check
```

成功の形: `--check` が差分なしで通る。カードの件数が 93 / 66 / 47 / 33 / 14 になる。

### 7. ページ本文の説明文を直す

ページに「分析対象となった公開投稿347件」「うち意見は283件」といった文言がある。
**マップと論点が意見のみになったので、この説明と実際が食い違う。**

該当箇所を探して、収集件数と意見件数の両方が分かる形に書き換える。

```bash
grep -n "347件\|283件" docs/koshitsu-tenpakai-reaction-map.html
```

書き換えの方針（文言は現場に合わせてよい）:

> Yahooリアルタイム検索で取得した公開投稿347件のうち、意見と判定した283件を分析対象としています。

成功の形: ページ内に「347件だけ」または「283件だけ」が単独で出てくる箇所が無くなり、
両方の数字が必ずセットで説明されている。

### 8. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/build_data_sheet.py && grep 皇室 DATA_SHEET.md
```

成功の形:

- unittest が `OK`
- 2本の検査スクリプトが exit 0
- `DATA_SHEET.md` の皇室典範の行が **意見283 / 論点283 / 賛否283 / マップ283** と4つそろう

### 9. 見た目を確認する

何をするか: 点が64個減るので、マップがスカスカに見えないか実際に開いて確かめる。

ブラウザで `docs/koshitsu-tenpakai-reaction-map.html` を開き、次を確認する。

- マップの点が偏って空白の扇形ができていないか
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか

**点が減って見栄えが悪くなった場合は、勝手に点を戻さない。** そのまま報告する。

### 10. コミットする

コミット対象:

- `scripts/build_koshitsu_arena.py`
- `configs/koshitsu-tenpakai-reaction-map.json`
- `docs/koshitsu-tenpakai-reaction-map.html`
- `DATA_SHEET.md`

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。

push して main へPRを出す。

### 11. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製する。**

```bash
git worktree remove ../isa-wt-koshitsu
```

---

## 制約・注意

- **投票の選択肢を変えない。** 論点の数（5つ）とスタンスの数（3つ）は今回いじらない。
  数が変わると読者投票の `choiceIdx` の意味がずれ、Supabase Edge Function の
  再デプロイが必要になる（このテーマで実際に発生した）。今回は**件数だけ**が変わる。
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）。
- 「世論の潮目」ウィジェットの前回値は合成データ由来で、注釈で開示済み。**今回は触らない。**
- **`social-samples/` 配下の未追跡ファイルを消さない。**
- **`git checkout -- <ディレクトリ>` を使わない。**
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない。
- main への直接コミット禁止。

## 完了報告に含めること

1. マップの点・論点カード・賛否の件数が283で一致したか
2. 手順3の `--check` が最初から差分なしで通ったか（通らなかった場合はその内容）
3. 手順9で見た目に問題がなかったか
4. 残り3テーマ（高齢者・憲法改正・辺野古）は未着手であることの確認
5. オーナーへの依頼事項があれば1つだけ
