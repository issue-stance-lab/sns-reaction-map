---
name: taxonomy-migration
description: 論点体系（main_issue のラベル集合）を変えたあと、既存の収集データを再分類して、ページ・スクリプト・テストの参照をすべて揃え直すための手順。「論点を増やした／切り口を変えた」「同じページの中で論点の数が食い違っている」「潮目ウィジェットだけ古い論点のまま」「既存データを再分類して」「分類器と公開ページの論点がずれている」といった作業では必ずこのスキルを読むこと。新旧2つの論点体系が1画面に同時表示される事故は fukushuto と ai-copyright で実際に起きており、途中で放置すると1ヶ月単位で気づかれない。新規収集を伴う定期更新は対象外で、そちらは DATA_REFRESH.md を見ること。
---

# 論点体系の移行

## この作業は何か

あるテーマの論点（`main_issue`）の分け方を変えたとき、**過去に集めた投稿は古い分け方のまま**残る。
分類器の定義を直しただけでは、ページに出ている数字は古い体系のままなので、
1つの画面にアリーナ・カードは新体系、グラフだけ旧体系、という二重表示が生まれる。

この二重表示は**検査では検出されない**。件数の整合テストは新旧どちらの体系でも通るからだ。
気づくのは人間が画面を見たときだけで、fukushuto では2026-07-26から08-08まで公開されたままだった。

やることは「分類器を直す」ではなく「**旧ラベルを参照している箇所を全部なくす**」。
そこを取り違えると必ず取りこぼす。

## 進め方

### ⓪ 作業場所を用意する

専用の worktree（作業用のコピー）を作り、`origin/main` を取り込んでから始める。
この作業は分類に数十分かかるので、その間に共有ツリーが別セッションに動かされると成果物が消える。

```sh
git worktree add .worktrees/<テーマ> task/<テーマ>
cd .worktrees/<テーマ> && git merge origin/main
```

### ① 旧ラベルの参照箇所を洗い出す

**直す対象を先に確定させる。** 後から見つかると、承認をもらった数字が変わってやり直しになる。

```sh
grep -rn "<旧ラベル1>\|<旧ラベル2>" --include="*.py" --include="*.json" \
  --include="*.html" --include="*.yaml" . | grep -v node_modules | grep -v social-samples
```

出てきた箇所を「実際に使っている定義」と「経緯を説明しているコメント」に仕分ける。
コメントは歴史の記録なので消さない。消すのは定義のほうだけ。

典型的な参照先は次の5つ。テーマによって増減する。

- `scripts/<テーマ>_taxonomy.py` — 唯一の定義。ここが正典
- `scripts/inject_tide_widget.py` の `THEMES` — 潮目ウィジェットの `issue_labels`
- `docs/<テーマ>-reaction-map.html` — 生成物。直接編集せず再生成する
- `configs/<テーマ>-reaction-map.json` — 論点カードの件数
- `supabase/functions/cast-vote/index.ts` — 投票の選択肢数

### ② 変更前の数字を記録する

あとで対照表を作るために、**先に**現状を控える。検証スクリプトのベースラインも取る。

```sh
python3 scripts/verify_theme_page.py <テーマ> ; echo "exit=$?"
python3 scripts/verify_top_page.py ; echo "exit=$?"
python3 -m unittest discover -s tests -p "test_<テーマ>*"
```

着手前に落ちている検査があれば、それは自分のせいではない。記録して切り分けておく。
ここを省くと、後で出たエラーが自分の変更のせいか環境のせいか分からなくなり、
無関係な調査に時間を使う。実際 2026-08-08 は、非公開ファイル未復元によるテスト失敗を
自分の変更の疑いから調べ直すことになった。

### ③ 10件で試験分類する

全件を流す前に必ず小さく試す。1件あたり5〜6秒かかるので、300件なら30分。
プロンプトの綴りミスで30分を捨てないために、ここは省かない。

```sh
python3 scripts/classify_<テーマ>_arena_hermes.py \
  --input social-samples/<更新回ファイル>.json \
  --output social-samples/<更新回ファイル>_v2.json \
  --limit 12
```

出力の `main_issue` が**新体系のラベルだけ**になっているか確認する。
1つでも体系外が出たら、プロンプト側（`ISSUE_DEFS` の説明文）を直してからやり直す。

### ④ 更新回ごとに再分類する

**元のファイルは絶対に書き換えない。** `_v2` のように別名で保存する。
更新回のファイルは「そのとき何を集めたか」の記録であって、上書きすると再現できなくなる。

`--limit` で作った途中結果は `--resume` でそのまま続けられるので、③の12件は無駄にならない。

```sh
python3 scripts/classify_<テーマ>_arena_hermes.py \
  --input social-samples/<更新回ファイル>.json \
  --output social-samples/<更新回ファイル>_v2.json \
  --markdown social-samples/<更新回ファイル>_v2.md \
  --resume
```

**比較する更新回は全部やる。** 潮目ウィジェットは2回分を並べるので、片方だけ新体系にすると
グラフのラベルが噛み合わず全部0%になる。

長時間かかるので裏で流すことになるが、**終わったら即コミットする**。
未追跡（git に登録されていない）のまま置いた分類結果は、worktree の掃除で消える。
実際に fukushuto では中間成果物が1ヶ月放置され、危うく「不要ファイル」として消されかけた。

### ⑤ 対照表を作る（ここが山場）

同梱のスクリプトで、変更前と変更後の数字を並べる。

```sh
python3 .claude/skills/taxonomy-migration/scripts/compare_tide_numbers.py \
  --slug <テーマ> \
  --new-prev social-samples/<前回>_v2.json \
  --new-cur  social-samples/<今回>_v2.json
```

`--new-issues` を省くと `scripts/<テーマ>_taxonomy.py` の `ISSUE_ORDER` から「その他」を除いて使う。

**立場（stance）の数字も必ず並べる。** 論点だけ直すつもりでも、再分類は同じ投稿の賛否も
判定し直すため、立場の割合も動く。fukushuto では292件中29件で賛否の判定が変わった。
「立場は変わらないはず」と書かれた指示書を受け取っても、実測して確かめる。
これを黙って進めると、オーナーは知らないうちに公開数字が変わったことになる。

### ⑥ 数字の変化について承認をもらう ⛔

**ここで必ず止まる。公開ページにはまだ触れない。**

グラフの数字が変わることは、オーナーにとって「サイトの主張が変わる」ことと同じ意味を持つ。
技術的に正しいかどうかとは別の判断なので、勝手に決めない。

報告に含めるもの:

- 論点モードと立場モードの両方の対照表（変更前 → 変更後）
- 母数の変化（論点と立場では絞り込み条件が違うので母数も別々に出す）
- 数字が動いた理由を一言（＝AIが同じ投稿を仕分け直したため。世論が変わったのではない）

最後の一言を省かない。「反対が7ポイント減った」を世論の変化と読まれると、
サイトの説明そのものが誤りになる。

### ⑦ 定義と参照側を直す

承認が出てから着手する。順番は「定義 → 参照側 → 生成物」。

1. `scripts/<テーマ>_taxonomy.py` に、廃止したラベルを `RETIRED_ISSUE_LABELS` として残す
2. `scripts/inject_tide_widget.py` の該当テーマの `prev_file` / `cur_file` / `issue_labels` を差し替える
3. 注釈テキスト（`note`）の日付と件数を実データに合わせる
4. ページを再生成する

廃止ラベルを消さずに定数として残すのは、テストが「これが出てきたら退行」と判定できるようにするため。

### ⑧ 検証する

```sh
python3 scripts/verify_theme_page.py <テーマ> ; echo "exit=$?"
python3 scripts/verify_top_page.py ; echo "exit=$?"
python3 -m unittest discover -s tests -p "test_<テーマ>*"
```

②で取ったベースラインと比べる。新しく落ちた検査だけが自分の責任範囲。

## 落とし穴

**`inject_tide_widget.py` は全テーマを書き換え、一部を古いデータへ巻き戻す。**
引数を取らず `THEMES` を全部回すうえ、`adapter` 方式のテーマは別経路（refresh_topic.py）で
更新されているため、`THEMES` に書かれた更新回のほうが古い。2026-08-08 の実行では
ai-copyright（7/26→8/3 が 7/12→7/26 へ）と takaichi（7/26→8/7 が 7/12→7/26 へ）が
公開中のページごと後退した。**実行直後に必ず確認して戻す。**

```sh
python3 scripts/inject_tide_widget.py
git status --porcelain                     # 対象テーマ以外の docs/*.html が出たら巻き戻り
git restore docs/<対象外のページ>.html
```

戻したあと、そのページに元の日付が残っていることまで見る（`grep -o '7月26日 → 8月3日'`）。
差分が出ないのが正常ではなく、**出るのが普通**だと思って臨む。

**新しい worktree では非公開ファイルを先に復元する。** `THEMES.yaml` の `sample_file` には
gitignore された非公開ファイルが5本あり、復元しないとテストが落ちる。
自分の変更のせいだと誤診しやすい。着手前に確認しておくと切り分けが要らない。

```sh
python3 -c "
import re, pathlib
t = open('THEMES.yaml', encoding='utf-8').read()
for m in re.finditer(r'sample_file: (\S+)', t):
    if not pathlib.Path(m.group(1)).exists():
        print('不足:', m.group(1))
"
```

不足していたら、本体ツリーか `DATA_REFRESH.md` のバックアップ先からコピーする。
gitignore 済みなので `git status` には出ない。

**pytest は入っていない。** テストは `python3 -m unittest discover -s tests -p "test_*"` で動かす。

**論点と立場では母数が違う。** `use_relevance_filter` が有効なテーマは
「関連あり かつ 意見投稿」だけを数えるが、`calc_pcts` は集計対象ラベルに載っている分しか
分母に入れない。「その他」を `issue_labels` から外していると論点の母数だけ変わる。
対照表では母数も並べて出す（同梱スクリプトはそうしている）。

**分類は途中で止まっても復帰できる。** `--resume` は出力ファイルの件数から再開する。
ただし**同じ出力ファイルに2つのプロセスを走らせない**。ファイルが壊れる。
再開の前に `pgrep -f classify_` で生きているプロセスがないか確かめる。

## 完了条件

- [ ] ページ内に旧ラベルが1つも残っていない
- [ ] 潮目ウィジェットのラベルが `<テーマ>_taxonomy.py` の定義と一致する
- [ ] `verify_theme_page.py <テーマ>` と `verify_top_page.py` が exit 0
- [ ] `tests/test_<テーマ>_taxonomy.py` に「ページ内に taxonomy 外の論点ラベルがない」検査がある
- [ ] 再分類の中間成果物がコミット済み（未追跡で残っていない）
- [ ] `TASK_BOARD.md` の該当課題を更新した

## 完了報告に含めること

1. `git diff --stat`
2. 変更前後の対照表（論点モード・立場モードの両方）
3. 検証スクリプトの出力をそのまま貼る
4. 試験分類10件で確認した内容
5. 判断に迷った点、確認していないこと

オーナーはエンジニアではない。専門用語には初出で一言そえ、結論を先に書く（`CLAUDE.md` 参照）。
