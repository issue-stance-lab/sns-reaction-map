# 部活動の地域移行（bukatsu-chiiki）データ補充＋公開更新 — 2026-08-09

このファイルをそのまま新しいセッションに貼って実行する。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `DATA_REFRESH.md`（データ更新の手順）/ `LOOP.md` ⓪（作業場所の確保）
- テーマ台帳: `THEMES.yaml`

## タスク

テーマ `bukatsu-chiiki`（部活動の地域移行）の `collect_at` / `refresh_at` が **2026-08-09（今日）** を迎えた。
`scripts/refresh_topic.py --promote` で **公開ページの更新まで** 行う。

このテーマは `page_update_mode: adapter` なので `--promote` を付けられる。
前回（2026-08-08）の憲法改正とはここが違う。

---

## ⚠️ 先に直すもの2つ（どちらも未対応だと失敗するか、間違った結果が出る）

**この2つを終えてコミットしてから収集に進むこと。**

### A. `validate_theme_seo.py` が落ちている（TASK_BOARD 課題37）

`--promote` は最後に `validate_theme_seo.py` を実行し、**失敗すると公開物をすべて昇格前へ巻き戻す。**
現在この検査は落ちているので、**直さない限り今回の公開更新は必ず失敗する。**

```bash
python3 scripts/seo/validate_theme_seo.py
```

いまの結果（失敗する状態）:

```
FAILED: 1 validation error(s)
- ai-copyright-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

原因は調査済み。`docs/ai-copyright-reaction-map.html` の JSON-LD `dateModified` が `2026-07-26` のまま、
`THEMES.yaml` の `updated_at` は `2026-08-07`。commit `5b6b870`（生成AIと著作権を正典1本に統一し、adapter へ昇格）で
ページを作り直して台帳を 08-07 にした際、ページ側のSEO日付だけ更新し漏れている。

**私の判断: ページの `dateModified` を `2026-08-07` に直すのが正しい**（ページの中身は実際に 08-07 に作り直されているため）。
ただし着手前に、ai-copyright の公開ページが本当に 08-07 の内容かを確認してから直すこと。

成功の形: `validate_theme_seo.py` が exit 0（`FAILED` の行が出ない）。

### B. 部活動adapterの「前回更新回」が2回前を指している

`scripts/refresh_bukatsu_pilot.py` の33行目に、比較対象の前回更新回が**日付べた書き**で入っている。

```python
PREVIOUS_DATE = "2026-07-23"
```

そして310〜312行目に「前回更新回は161件のはず」という件数チェックがある。

正典の日付別件数は次のとおりで、**いま前回にあたるのは 2026-08-02 の159件。**

| 収集日 | 件数 |
|---|---|
| 2026-06-27 | 179 |
| 2026-07-12 | 127 |
| 2026-07-23 | 161 ← いまここを指している |
| 2026-08-02 | 159 ← 本来の「前回」 |

**危険なのは、直さなくてもエラーにならないこと。** 7/23の161件は正典に残っているので件数チェックは通ってしまい、
「世論の潮目」ウィジェットが *7月23日 → 8月9日* という、8/2をまたいだ比較を表示する。
公開中のページはいま *7月23日 → 8月2日* なので、更新後に前回側が動かないという不自然な状態になる。

**やること**: `PREVIOUS_DATE` を `"2026-08-02"` に、件数チェック `161` を `159` に変える（2箇所）。
`scripts/refresh_adapters/bukatsu.py` は定数を import しているだけなので、そちらの変更は不要。
テストにこの数字のべた書きは無いので、テスト側の修正も不要（確認済み）。

**この定数は毎回の更新で書き換えが必要になる作りです。** 今回は言われたとおり直せばよいが、
「毎回手で直す前提の定数」であることは完了報告に書いて、オーナーの判断を仰ぐこと。

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-bukatsu -b task/bukatsu-refresh-20260809 origin/main
```

成功の形: `Preparing worktree` と新しいブランチ名が出る。**`origin/main` を起点にすること**（共有ツリーの現在のブランチは main より遅れている）。

### 2. 非公開の正典データを復元する

Git管理外の本文付きデータをバックアップから展開する。**これをしないと検査で落ちる。** 不足していても `git status` には出ない。

```bash
cd ../isa-wt-bukatsu && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`。1本でも名前が出たら先に進まない。

### 3. 収集ツールを動かせるようにする

```bash
cp -R ../issue-stance-aggregator/node_modules .
```

成功の形: 無言で終わる。省くと収集が `Cannot find package 'playwright'` で止まる。

### 4. 事前修正AとBを行い、コミットする

上の「先に直すもの2つ」を実施し、`validate_theme_seo.py` が exit 0 になることを確認してからコミットする。

**`--promote` は公開対象ファイルに未コミット差分があると、その場で止まる**（`THEMES.yaml` / `configs/theme-seo.json` / `docs/index.html` / `docs/sitemap.xml` / `docs/robots.txt`）。
巻き戻しを確実にするためにも、収集前に作業ツリーをきれいな状態にしておくこと。

### 5. 収集・分類・公開更新を実行する

何をするか: 収集 → 重複判定 → 分類 → 検査 → 更新回保存 → バックアップ → **候補ページを2回生成して冪等性を確認** → 全検査合格なら公開物を一括昇格 → 再バックアップ。

```bash
python3 scripts/refresh_topic.py --topic bukatsu-chiiki --date 2026-08-09 --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --promote
```

成功の形: 最後まで走り切り、`report.json` の `status` が `promoted` になる。
昇格時に以下が自動で更新される（手作業は不要）:

- 累積正典 `social-samples/bukatsu-chiiki_hermes_classified.json`
- 公開ページ `docs/bukatsu-chiiki-reaction-map.html`（潮目ウィジェット・論点件数を含む）
- `THEMES.yaml` の `updated_at` / `collect_delta` / `sample_period` / `refresh_at`
- `configs/theme-seo.json`、トップ `docs/index.html`、`docs/sitemap.xml`
- 検査4本（`verify_theme_page` / `verify_top_page` / `validate_theme_seo`）

**途中で落ちた場合は自動で昇格前へ巻き戻る。** 巻き戻ったあと、公開ページとトップが元に戻っているかを
`git status` で必ず目視確認すること。落ちた原因を直さずに再実行しない。

### 6. 結果を確認する

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py bukatsu-chiiki && python3 scripts/verify_top_page.py
```

成功の形: unittest が `OK`、2つの検査がどちらも exit 0。

加えて、公開ページを目で確認する:

- 「世論の潮目」の期間表示が **8月2日 → 8月9日** になっているか（7月23日が残っていたら手順Bの修正が効いていない）
- トップの `hero-total-samples` が全テーマの合計と合っているか
- 375px幅で横スクロールが出ないか
- コンソールエラーが出ないか

### 7. 次回 refresh_at が周期ルールどおりか確認する

| 今回の新規意見 | 次回 |
|---|---|
| 50件以上 | 今回だけ7日後 |
| 20〜49件 | 14日後（既定） |
| 20件未満が2回連続 | 28日後 |
| 0件が2回連続 | `collect_mode: event-driven` にして空欄 |

このテーマの分類器は `is_opinion` を出力するので、判定に使われるのは「意見と判定された件数」です
（憲法改正で問題になった件は 2026-08-08 の PR #34 で修正済み）。

**参考**: `data/verification/updates/bukatsu-chiiki/2026-08-02/` には `report.json` が無く、
周期判定は「前回の記録なし」として動きます。今回は結果に影響しませんが、
2回連続の判定が効かない状態なので、気づいた事実として完了報告に書くこと。

### 8. コミットして PR を出す

`social-samples/updates/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。
`main` へPRを出してマージする。

### 9. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-bukatsu
```

---

## 制約・注意

- **`scripts/inject_tide_widget.py` を実行しない。** 引数を取らず全8テーマのHTMLを書き換え、adapter方式のテーマ（ai-copyright / takaichi）を古いデータへ黙って巻き戻す（TASK_BOARD 課題38）。潮目の更新は adapter が行う。
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）。
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけをパス指定で。
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない。
- main への直接コミット禁止。
- バックアップが失敗したら更新回を確定せず、`collect_at` も進めない。**期限を手で進めない。**

## 参考: このテーマの現状

| 項目 | 値 |
|---|---|
| タイトル | 部活動の地域移行 |
| 正典 | `social-samples/bukatsu-chiiki_hermes_classified.json`（626件） |
| 収集設定 | `configs/topics/bukatsu-chiiki-v2.yaml`（検索語10本） |
| 公開ページ | `docs/bukatsu-chiiki-reaction-map.html` |
| adapter | `scripts/refresh_adapters/bukatsu.py` →`scripts/refresh_bukatsu_pilot.py` |
| 前回更新 | 2026-08-02（222件取得・重複63件・新規159件） |
| 取得期間 | 2026-06-27〜2026-08-02 |
| 分類 | Hermes方式（main_issue / stance / intensity / is_relevant / is_opinion） |

## 完了報告に含めること

1. 収集件数 / 重複除外後の新規件数 / 意見と判定された件数 / 分類エラー率
2. 次回 `collect_at` `refresh_at` の日付と、その根拠になった周期ルール
3. 公開ページの潮目ウィジェットが 8月2日 → 8月9日 になっているか（目視結果）
4. 検査で落ちた項目があればその内容（隠さず書く）
5. **手順Bの「毎回手で直す定数」をどうするか**のオーナー向け提案（選択肢と「私ならこれ」を添えて1つ）
