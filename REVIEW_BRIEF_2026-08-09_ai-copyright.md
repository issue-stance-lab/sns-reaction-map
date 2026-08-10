# レビュー依頼 — 2026-08-09 の作業（PR #58 / #59）

このファイルをレビュー担当のセッションに渡す。作業内容と、特に見てほしい点をまとめてある。
作業ツリーは片付け済みなので、レビューは新しい worktree を作って行うこと。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git fetch origin && git worktree add ../isa-wt-review -b task/review-20260809 origin/task/issue-count-single-source
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。
このブランチは #58 と #59 の両方を含む（#59 は #58 の上に積んである）。

非公開の正典が無いと検査が落ちるので、続けて復元する。

```bash
cd ../isa-wt-review && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json
```

成功の形: 無言で終わる。確認は `python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"` が `欠落: []` を返すこと。

---

## PR #58 — 生成AIと著作権のデータ補充と公開更新

https://github.com/issue-stance-lab/sns-reaction-map/pull/58
ブランチ `task/ai-copyright-refresh-20260809`（`origin/main` から分岐）

発注書 `configs/prompts/claude-code/20260810_ai-copyright-refresh.md` の実行。

### 結果

| 項目 | 作業前 | 作業後 |
|---|---|---|
| 収集 | 1,606 | 2,015 |
| 意見 | 1,082 | 1,347 |
| 論点の合計 | 1,082 | 1,347 |
| 賛否の合計 | 1,082 | 1,347 |
| マップの点 | 1,082 | 1,347 |

収集468件 → 重複59件を除外して新規409件、うち意見265件。分類エラー0件。

- 最大論点「学習データ・無断利用」281→340件、順位の入れ替わりなし
- 2位と3位が入れ替わり（利用者モラル 232→307 が 法制度 230→270 を抜いた）
- 賛否は 規制支持 612→776（57%→58%）/ 推進支持 277→328 / 中立 193→243
- 次回 `collect_at` / `refresh_at` は 2026-08-16（新規意見265件 ≥ 50 のため7日周期）

### 発注書から意図的に変えた点（レビューで妥当性を見てほしい）

1. **実行日が1日前倒し。** 発注書は 2026-08-10 付だが、実行日は 2026-08-09。
   `--date 2026-08-09` を渡した（発注書のルール「`--date` には実際に収集した日を渡す」に従った）。
   ブランチ名も `20260809` にしてある。
2. **school-nickname-ban の `collect_at` を 8/16 → 8/17 に動かした。**
   ai-copyright の次回が 8/16 になり重なったため（発注書 手順6「重なるなら1日ずらす」）。
   公開を伴わない migration テーマの側を動かした。
3. **副首都（fukushuto）のSEO日付を直した。** 下記のとおり。

### 1回目の `--promote` が失敗した件

`validate_theme_seo.py` で止まった。原因は ai-copyright ではなく **fukushuto**。

```
FAILED: 1 validation error(s)
- fukushuto-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

2026-08-08 の副首都の正典統合（commit 2a9aad0）で `THEMES.yaml` の `updated_at` だけ
2026-08-08 に進み、`configs/theme-seo.json` の `dateModified` が 2026-07-26 のまま残っていた。
**origin/main の時点で既にこの状態**で、ai-copyright に限らず全テーマの `--promote` を
巻き添えで止める状態だった。日付3行を台帳に合わせて直した（commit 97e2b9e）。

公開側は仕組みどおり昇格前へ自動で戻っていた（`docs/` に差分なし）。
その後 `--resume --run-id 20260809_095306` で収集からやり直さずに昇格だけ再実行し、
`status: promoted` になった。

### 収集方法の文を直した（発注書 手順7）

`configs/theme-seo.json` の生成AIの収集方法が意見件数しか出していなかったので、
収集件数も出すように変えた。

> 収集した2,015件のうち、意見と判定した1,347件を論点分析に表示しています。

### コミット

| コミット | 内容 |
|---|---|
| 97e2b9e | 副首都の最終更新日を台帳に合わせる |
| a07602b | 2026-08-09 の収集回を保存する |
| bcc0960 | 2026-08-09 の収集を公開へ昇格する |

---

## PR #59 — 論点の件数を1か所からしか出せないようにする

https://github.com/issue-stance-lab/sns-reaction-map/pull/59
ブランチ `task/issue-count-single-source`（`task/ai-copyright-refresh-20260809` から分岐）

**#58 の公開後にブラウザで見て見つけた問題への対応。** オーナーの指示で着手した。

### 見つかった問題

テーマページには論点の件数が**4か所**に出るのに、更新していたのは論点カードだけだった。
生成AIのページでは、論点ナビ・論点セクションの見出し・アリーナのセクターが
2026-07-22 に捨てた旧2D分類の数字（126件）を表示し続け、
**同じ論点に「126件」と「340件」が並んでいた。**

アリーナは扇の広さをこの数字から計算している（`span = usable * iss.n / total`）ため、
点は 1,347件ぶん打たれているのに扇の形は古い395件ぶんの比率、という状態だった。

origin/main の時点で既に壊れていた（当時は 126 対 281）。今回の更新で差が広がった。
既存の検査はどれも気づけなかった（件数の網羅検査はトップページにしか掛かっていない）。

### 直した数字

| テーマ | 直前 | 直後 |
|---|---|---|
| 生成AIと著作権 | 126 / 79 / 73 / 46 / 40 / 31 | 340 / 270 / 307 / 190 / 54 / 82 |
| 高市文春問題 | 97 / 59 / 31 / 19 / 17 | 171 / 84 / 57 / 26 / 21 |
| 自転車の青切符（ナビ） | 36 / 27 / 26 / 11 / 11 | 38 / 29 / 14 / 14 / 18 |
| 自転車の青切符（アリーナ） | 37 / 33 / 14 / 16 / 19 | 38 / 29 / 14 / 14 / 18 |

**自転車は最大の論点が「免許制要求」から「取締り強化賛成」へ入れ替わっていた。**
数字だけ直すと「議論の中心」の見出しと中身が食い違うので、文章も書き直した。

> 危険な自転車に青切符は当然ではないか — 歩道の暴走や信号無視の実害を挙げ、取締りの強化を支持する声が最も集まりました。

辺野古・あだ名は数字が合っていたが、同じ仕組みの管理下に入れて再発を防いだ。

### 設計

`scripts/sync_issue_counts.py` に4か所すべての書き換えを寄せ、
`configs/{テーマ}-reaction-map.json` の `issue_counts.sync` でテーマごとに有効化する。

| 指定 | 対象 |
|---|---|
| `headings` | `<article id="{anchor}">` 内の `<span class="issue-count">N件</span>` |
| `nav` | `<nav class="quadrant-nav"><a href="#{anchor}">ラベル N</a>` |
| `conclusion` | 「議論の中心」の `<span class="conclusion-count"><b>N</b>件</span>` |
| `arena` | アリーナのセクター配列 `const ISSUES=[{k:'ラベル', n:N}]` |

ページ側のidがカードのslugと違うテーマがあるので、違う場合だけ `anchor` を書く。
アリーナの表示名が分類ラベルと違うテーマがあるので `arena_label` を持つ
（データ「技術競争・推進」／表示「技術競争・AI推進」）。

**ビルダがその場所を書くテーマ（副首都・消費税・皇室・憲法改正・高齢者）は
`sync` に入れていない。** 「1つの文の書き手は1つ」を保つため。

### 再発防止

- 「議論の中心」に指定した論点が最大でなくなったら、**数字を書き換えず失敗する。**
  見出しの文章は人が書いているので、数字だけ差し替えると中身と食い違うため
- `tests/test_issue_count_sync.py`（5件）が全テーマのずれを検出する

---

## 実行済みの検査（両PR適用後の状態）

| 検査 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests -q` | OK（101→106件） |
| `python3 scripts/sync_issue_counts.py --check` | exit 0（2回流して差分なし） |
| `python3 scripts/verify_theme_page.py` | 11テーマ NG 0件 |
| `python3 scripts/verify_top_page.py` | exit 0 |
| `python3 scripts/verify_builder_rebuildability.py` | 9テーマ NG 0件 |
| `python3 scripts/build_ai_copyright_arena.py --check` | 差分なし |
| `python3 scripts/seo/validate_theme_seo.py` | OK |
| `python3 scripts/build_data_sheet.py` | 「ずれあり」は高市の1件のみ（増えていない） |

ブラウザ確認: 生成AI・高市・自転車の3ページで件数が全か所揃っていること、
375px で横スクロールが出ないこと、コンソールエラーが無いこと、
投票完了後に「Xでシェア」「投票をやり直す」が出ることを確認した。
トップページの更新バーは「2026年8月9日（生成AIと著作権に409件追加）」。

まとめて流すなら次の1本。

```bash
python3 -m unittest discover -s tests -q && python3 scripts/sync_issue_counts.py --check && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/verify_builder_rebuildability.py && python3 scripts/seo/validate_theme_seo.py && echo "ALL OK"
```

成功の形: 最後に `ALL OK` が出る。途中で止まったらそこが問題。

---

## 特に見てほしい点

1. **`apply_arena` の正規表現がアリーナのセクター配列だけを捉えているか。**
   `{k:'…', n:数字}` にマッチする。他の場所に同じ形のJSがあると巻き込む。
   `scripts/sync_issue_counts.py` の `apply_arena`
2. **`apply_headings` のセクション範囲の切り出し。**
   `id="{anchor}"` から次の `class="issue-block"` までを1セクションとみなしている。
   最後のセクションはページ末尾までを範囲にしている。この前提が全テーマで成り立つか
3. **`anchor` / `arena_label` の対応づけが正しいか。**
   高市（`chusho`→`issue-accountability`、`hikaku`→`issue-comparison`）、
   自転車（`menkyo`→`issue-mensyo`、`shado`→`issue-sharido`、`rule`→`issue-ambiguity`）、
   辺野古（4件）が手で書いた対応。ずれると別の論点の数字が入る
4. **自転車の「議論の中心」の書き直しが、データの実態と合っているか。**
   最多は「取締り強化賛成」38件。文章は私が書いた
5. **school-nickname-ban の期限を 8/16 → 8/17 に動かした判断。**
   ai-copyright と重なったための移動だが、8/15 には既に3テーマ
   （副首都・憲法改正・部活動）が重なっている。そちらは触っていない
6. **`verify_builder_rebuildability.py` を `refresh_topic.py` の昇格処理に
   組み込むべきか。** 今回は手で流した。ただし今日の1回目のように
   他テーマの不整合で公開が丸ごと止まる副作用がある。
   先に「検査対象を担当テーマだけに絞る」を入れてからにすべきだと考えている

## 触っていない既知の未解決点

- `sample_period` が `unknown`（2,015件中339件に取得日が無い）。課題28
- 高市の1件差（意見360 / マップ359）。`main_issue: その他` の1件が表示対象5論点に
  含まれないため。別テーマの話
- `scripts/inject_tide_widget.py` は実行していない（TASK_BOARD 課題38）

## マージ順

**#58 → #59 の順。** #59 は #58 の上に積んであるので、#58 をマージすると
#59 の宛先は自動で main に切り替わる。

```bash
gh pr merge 58 --merge && gh pr merge 59 --merge
```

成功の形: 2つとも `Merged` と表示され、`gh pr list` に残らない。
