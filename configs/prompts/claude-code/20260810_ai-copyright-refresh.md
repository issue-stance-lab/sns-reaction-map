# 生成AIと著作権 — データ補充と公開更新 — 2026-08-10

このファイルをそのまま新しいセッションに貼って実行する。

> **これは 2026-08-08 に整備した仕組み一式を、実際の公開更新で初めて通す回。**
> 途中で止まったら、無理に回避せず**そのまま報告する**。何が足りなかったかが
> 分かることのほうが、この回を通すことより価値がある。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `DATA_REFRESH.md`（データ更新の手順）/ `LOOP.md` ⓪（作業場所の確保）
- テーマ台帳: `THEMES.yaml` / データ台帳: `DATA_SHEET.md`

## タスク

テーマ `ai-copyright`（生成AIと著作権）の `collect_at` / `refresh_at` が
**2026-08-10** を迎えた。収集・分類・**公開まで**を行う。

**このテーマは `page_update_mode: adapter` なので `--promote` を付ける。**

## このテーマの現状

| 項目 | 値 |
|---|---|
| 正典 | `social-samples/ai-copyright_hermes_classified.json`（1,606件） |
| 意見 | 1,082件 |
| 論点 / 賛否 / マップの点 | すべて 1,082（**ずれなし**） |
| 論点 | 学習データ・無断利用281 / 利用者モラル・倫理232 / 法制度・規制整備230 / クリエイター保護・権利151 / その他84 / AI生成物の権利・創作性64 / 技術競争・推進40 |
| 賛否 | 規制・制限強化支持612 / 推進・活用支持277 / 中立・情報193（**3値**） |
| 前回収集 | 2026-08-03（7日前） |
| 投票 | `ai-copyright-issue-stance-v1` = **21**（7論点 × 3立場） |
| ビルダー | `scripts/build_ai_copyright_arena.py`（`--check` あり） |
| adapter | `scripts/refresh_adapters/ai_copyright.py` |

**課題40（7/26分の未統合）の対象外。** このテーマの7/26分452件は統合済み。

## 前提条件（着手前に確認）

- [ ] 外付けディスク `/Volumes/HD-LE-B` が接続されている（未接続だとバックアップ地点で必ず止まる）
- [ ] 専用の作業ツリーを `origin/main` から作る

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git fetch origin && git worktree add ../isa-wt-aicopyright -b task/ai-copyright-refresh-20260810 origin/main
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

> **末尾の `origin/main` を省かないこと。** 省くと共有ツリーの現在のブランチから
> 枝分かれし、他人の変更を巻き込んだPRになる（2026-08-08 に4回起きた）。

### 2. 非公開の正典データを復元する

**これをしないと収集は走っても検査で落ちる。** 不足していても `git status` には出ない。

```bash
cd ../isa-wt-aicopyright && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 収集ツールを動かせるようにする

`node_modules`（収集に使う Playwright 一式）も gitignore 対象で作業ツリーに入らない。

```bash
cp -R ../issue-stance-aggregator/node_modules .
```

成功の形: 無言で終わる。省くと収集が疎通確認で `Cannot find package 'playwright'` で止まる。

### 4. 作業前の状態を記録する

```bash
python3 scripts/build_data_sheet.py && python3 scripts/build_ai_copyright_arena.py --check && python3 scripts/verify_builder_rebuildability.py
```

成功の形:

- `DATA_SHEET.md` の生成AIの行が **1606 / 1082 / 1082 / 1082 / 1082**
- 「ずれあり」は**1件だけ**（高市の1件差）。生成AIは入っていない
- ビルダーの `--check` が差分なし
- 再生成可能性が **9テーマ NG 0件**

**ここで想定と違ったら、先に報告して止まる。** 何かが後退している。

### 5. 収集・分類・更新回保存・公開までを実行する

```bash
python3 scripts/refresh_topic.py --topic ai-copyright --date 2026-08-10 --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --promote
```

**`--date` には実際に収集した日を渡す。** この文書の日付をそのまま使わない。
日付がずれたまま進めると検査に掛からず、次回の期限計算が狂う。

処理内容: 疎通確認 → 全検索語で収集 → 重複判定 → 試験分類10件 → 全件分類 → 検査 →
更新回保存 → バックアップ → adapterで候補ページを2回生成して冪等性・投票互換・保護タグを検査 →
全検査合格時だけ累積正典・ページ・台帳・SEO・トップ・sitemap を一括昇格 → もう一度バックアップ。

成功の形: 昇格まで完了し、`THEMES.yaml` の `updated_at` が今日、`collect_delta` が
今回の新規件数、次回の `collect_at` / `refresh_at` が周期ルールどおりに更新される。

失敗した場合: **公開側は昇格前へ自動で戻る。** 期限を手で進めない。
失敗のまま残し、`verify_top_page.py` の期限超過NGを残す。

> **2026-08-08 に検査を増やしたので、これまで通っていた回がここで止まる可能性がある。**
> 止まったら、それは検査が仕事をしたということ。**回避せずに内容を報告する。**
> 特に次の2つは新しい:
> - 意見件数 = 論点カードの合計 = マップの点 = 賛否の合計 が一致すること
> - ページ全体に、生成スクリプトが書いた以外の件数が残っていないこと

### 6. 次回の期限が周期ルールどおりか確認する

| 今回の新規意見 | 次回 |
|---|---|
| 50件以上 | 今回だけ7日後 |
| 20〜49件 | 14日後（既定） |
| 20件未満が2回連続 | 28日後 |
| 0件が2回連続 | `collect_mode: event-driven` にして空欄 |

**同じ日に他テーマの予定が入っていないかも見る。** 現在 8/11 に2件（副首都・自転車）、
8/15 に2件（憲法改正・部活動）。重なるなら1日ずらす。

### 7. 収集方法に収集件数を足す

`configs/theme-seo.json` の生成AIの収集方法は、いま**意見件数しか出していない**。

> ページの論点分析は、収集サンプルのうち分析対象とした意見{opinions}件を表示しています。

ルールは「**収集件数と意見件数の両方をページに出す**」（`DATA_REFRESH.md`）。
`{total}` を足す。

> 収集した{total}件のうち、意見と判定した{opinions}件を論点分析に表示しています。

```bash
python3 scripts/seo/apply_theme_trust.py && python3 scripts/seo/apply_theme_trust.py
```

成功の形: 1回目で `changed=1`、**2回目が `changed=0`**。ページに2つの数字が並ぶ。

### 8. 昇格後にもう一度、再生成できるかを確かめる

**`refresh_topic.py` の昇格処理はこの検査を呼んでいない。** 手で流す。

```bash
python3 scripts/build_ai_copyright_arena.py --check && python3 scripts/verify_builder_rebuildability.py
```

成功の形: どちらも exit 0（**9テーマ NG 0件**）。

ここでNGが出たら、**昇格した結果このテーマが「1回の更新で再生成できないページ」に
なった**ということ。2026-08-08 に3テーマで起きた「1つの文に書き手が2人いる」問題なので、
ビルダー側の書き込みを外して `configs/theme-seo.json` に一本化する。

### 9. 検査とデータ台帳

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py && python3 scripts/build_data_sheet.py && grep 生成AI DATA_SHEET.md
```

成功の形:

- unittest が `OK`（現在101件）
- 検査2本が exit 0、`verify_theme_page.py` は11テーマ NG 0件
- `DATA_SHEET.md` の生成AIの行で**意見 / 論点の合計 / 賛否の合計 / マップの点が同じ数**
- 「ずれあり」が**1件のまま**（高市だけ）。生成AIが増えていない

### 10. 見た目を確認する

ブラウザで `docs/ai-copyright-reaction-map.html` を開く。

- マップの点が増えて潰れていないか
- **「最大勢力」の見出しと件数が食い違っていないか**（件数が変わると最大論点が
  入れ替わる。副首都で実際に起きた）
- 375px幅で横スクロールが出ないか
- コンソールにエラーが出ていないか
- 投票完了後に「Xでシェア」「投票をやり直す」が出るか

トップページ `docs/index.html` も開き、更新バーの日付と件数が今日の結果に合っているかを見る。

### 11. コミットする

コミット対象:

- `THEMES.yaml` / `DATA_SHEET.md`
- `docs/ai-copyright-reaction-map.html` / `docs/index.html` / `docs/sitemap.xml`
- `configs/theme-seo.json`
- `data/verification/ai-copyright.json`
- **`data/verification/updates/ai-copyright/<日付>/`（今回の更新回サマリ）**

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。

**作業ツリーを片付ける前に、次で何も出ないことを確認する。**

```bash
git status --short data/verification/
```

成功の形: 何も出ない。`??` で更新回のディレクトリが出たらコミットしていない。

push して main へPRを出す。

### 12. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-aicopyright
```

---

## 制約・注意

- **投票の選択肢を変えない。** 論点7つ・立場3つ（合計21）は今回いじらない。
  数が変わると読者投票の `choiceIdx` の意味がずれ、Supabase Edge Function の
  再デプロイと既存票の破棄が必要になる。**賛否の4値化は8月下旬に全テーマまとめて行う**
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 参考: 既知の未解決点（今回は触らない）

- `sample_period` が `unknown`（1,606件中339件に取得日が無い）。過去分の欠落で、
  新規収集分には日付が入る。課題28
- 高市の1件差（意見360 / マップ359）。`main_issue: その他` の1件が表示対象5論点に
  含まれないため。別テーマの話

## 完了報告に含めること

1. 収集件数 / 重複除外後の新規件数 / 分類エラー率
2. **作業前と作業後の「収集 / 意見 / 論点の合計 / 賛否の合計 / マップの点」**
3. 論点と賛否の内訳の変化（最大論点が入れ替わったかどうかを含む）
4. 次回 `collect_at` / `refresh_at` の日付と、根拠になった周期ルール
5. **手順5・手順8で新しい検査に引っかかったか。引っかかった場合はその出力と対処**
6. 手順10で見た目に問題がなかったか
7. `verify_builder_rebuildability.py` を昇格処理（`refresh_topic.py`）に組み込むべきだと
   思うか。今回は手で流したが、毎回忘れずに流せるとは限らない
8. オーナーへの依頼事項があれば1つだけ
