# 憲法改正（constitutional-amendment）データ補充 — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `DATA_REFRESH.md`（データ更新の手順）/ `LOOP.md` ⓪（作業場所の確保）
- テーマ台帳: `THEMES.yaml`

## タスク

テーマ `constitutional-amendment`（憲法改正論議）の `collect_at` が **2026-08-08（今日）** を迎えた。
`scripts/refresh_topic.py` で収集・分類・更新回保存まで行う。

**このテーマは `page_update_mode: migration` なので `--promote` は付けない。**
公開ページ・累積正典・`updated_at` は変更しない。staging（更新回保存）で止める。

## 前提条件（着手前に確認）

- [ ] 外付けディスク `/Volumes/HD-LE-B` が接続されている（未接続だとバックアップ地点で必ず止まる）
- [ ] 専用の作業ツリーを作る（共有ツリーで作業しない）

## 手順

### 1. 作業ツリーを用意する

何をするか: 他セッションとファイルを取り合わないよう、専用の作業用コピーを作る。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-constitutional -b task/constitutional-refresh-20260808
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出て、`../isa-wt-constitutional` ができている。

### 2. 非公開の正典データを復元する

何をするか: Git管理外（gitignore対象）の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと収集は走っても検査で落ちる。** 不足していても `git status` には出ない。

```bash
cd ../isa-wt-constitutional && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 収集ツールを動かせるようにする

何をするか: `node_modules`（収集に使う Playwright 一式）も gitignore 対象で作業ツリーに入らないので複製する。

```bash
cp -R ../issue-stance-aggregator/node_modules .
```

成功の形: 無言で終わる。省くと収集が最初の疎通確認で `Cannot find package 'playwright'` で止まる（2026-08-08 に実際に発生）。

### 4. 収集・分類・更新回保存を実行する

何をするか: 疎通確認 → 全検索語で収集 → 重複判定 → 試験分類10件 → 全件分類 → 検査 → 更新回保存 → バックアップ＋復元検査、までを1コマンドで行う。

```bash
python3 scripts/refresh_topic.py --topic constitutional-amendment --date 2026-08-08 --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

成功の形: `social-samples/updates/constitutional-amendment/2026-08-08/` が作られ、
`data/verification/updates/` に仮名化サマリが保存され、`THEMES.yaml` の
`last_refresh_attempt_at` と次回 `collect_at` が更新される。

失敗した場合: バックアップが失敗したら更新回は確定せず `collect_at` も進まない。
**期限を手で進めない。** 失敗のまま残し、`verify_top_page.py` の期限超過NGを残す。

### 5. 次回 collect_at が周期ルールどおりか確認する

`refresh_topic.py` が自動設定するが、値が下のルールと合っているか目視で確認する。

| 今回の新規意見 | 次回 collect_at |
|---|---|
| 50件以上 | 今回だけ7日後 |
| 20〜49件 | 14日後（既定） |
| 20件未満が2回連続 | 28日後 |
| 0件が2回連続 | `collect_mode: event-driven` にして `collect_at` を空欄 |

新規0件でも「収集成功回」として履歴は残す（公開更新にはしない）。

### 6. テストを通してコミットする

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_top_page.py
```

成功の形: unittest が `OK`、`verify_top_page.py` が exit 0。

通ったら `THEMES.yaml` と `data/verification/` の差分をコミットして push、main へPRを出す。
`social-samples/updates/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。

### 7. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-constitutional
```

---

## 制約・注意

- **`--promote` を付けない。** このテーマは `migration` で、公開ページのadapterが未整備。
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ巻き戻す不具合がある（TASK_BOARD 課題38）。
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）。
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけをパス指定で。
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない。
- main への直接コミット禁止。

## 参考: このテーマの現状

| 項目 | 値 |
|---|---|
| タイトル | 憲法改正論議 |
| 正典 | `social-samples/constitutional_amendment_hermes_arena_classified.json` |
| 収集設定 | `configs/topics/constitutional.yaml`（検索語6本） |
| 公開ページ | `docs/constitutional-amendment-reaction-map.html` |
| 前回更新 | 2026-07-26（追加224件） |
| 取得期間 | 2026-06-20〜2026-07-25（課題28で確定済み） |
| 分類体系 | Hermes / kimi-k2.6、6論点・4スタンス |

## 完了報告に含めること

1. 収集件数 / 重複除外後の新規件数 / 分類エラー率
2. 次回 `collect_at` の日付と、その根拠になった周期ルール
3. 検査で落ちた項目があればその内容（隠さず書く）
4. オーナーへの依頼事項があれば1つだけ
