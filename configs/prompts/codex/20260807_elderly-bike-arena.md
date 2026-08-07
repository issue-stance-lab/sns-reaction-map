## タスク: 高齢者免許返納と自転車青切符のアリーナを正典から生成する

### 出典
TASK_BOARD.md 課題34 / 2026-08-07 の高齢者免許返納の再分類レビュー

### 目的
論点カードの件数は正典から出るようになったが、アリーナ（散布図）の点データは
古い割り当てのまま。同じページの中で、図の点の数とカードの数字が食い違っている。

### 背景（調査済み・再調査不要）
高齢者免許返納の現状（自転車青切符も同じ構造になる見込み）:

| 論点 | アリーナの点 | 論点カードの件数 |
|---|---|---|
| 義務化・事故防止 | 139 | 95 |
| 地方の足・移動権 | 24 | 14 |
| 適性検査強化 | 20 | 19 |
| 代替交通整備 | 9 | 10 |
| 自主返納支援 | 7 | 9 |
| その他 | 12 | 64 |

- アリーナの点は `docs/elderly-license-revocation-reaction-map.html` の `SM_RAW`（211点）に直書き
- 生成スクリプトが存在しないため、データを更新しても点が古いまま残る
- 手本は `scripts/build_koshitsu_arena.py`（正典だけを読み、SM_RAW・セクター・件数・
  insight・詳細データを丸ごと作り直す。`--check` で差分検査、staging 用の
  `--input` / `--html-template` / `--output-html` に対応）

### やること（1テーマずつ。まず高齢者免許返納）
1. `scripts/build_{theme}_arena.py` を新設する。`build_koshitsu_arena.py` を手本に、
   正典（`THEMES.yaml` の `sample_file`）だけを読んで次を生成する
   - SM_RAW（アリーナの点）
   - アリーナのセクター（論点の並びは `scripts/{theme}_taxonomy.py` から読む）
   - 論点カードの件数、insight、公開件数、詳細データの表
2. アリーナの座標の意味を `scripts/{theme}_taxonomy.py` に定義する
   （`scripts/ai_copyright_taxonomy.py` の `STANCE_X` / `INTENSITY_E` が手本。
   現行の点の x の符号と色の対応を壊さないこと）
3. `--check` / `--input` / `--html-template` / `--output-html` を実装する
4. `scripts/refresh_adapters/{theme}.py` を追加し、候補ページを2回生成して差分ゼロを確認、
   投票定義と保護タグの個数が変わらないことを検査してから公開対象を返す
5. `configs/refresh-pipeline.yaml` に `adapter` を登録し、`THEMES.yaml` の
   `page_update_mode` を `adapter` へ、`refresh_at` を設定する
6. `tests/test_{theme}_adapter.py` を追加する（`tests/test_koshitsu_adapter.py` が手本）

### やらないこと
- 投票の選択肢の変更（現行の topicId と選択肢数を維持する）
- 解説文の書き直し
- データの追加収集
- 2テーマを同時に進めること

### 制約（必ず守る）
- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/{theme}-arena`。main 直接コミット禁止。**専用の git worktree で作業する**
- 論点・立場・座標は taxonomy モジュールからのみ読む。ラベルを直書きしない
- 数値をハードコードしない。すべて正典から導出する
- 同じ入力で2回実行して差分が出ないことを確認するまで `page_update_mode` を上げない

### 完了条件
- [ ] `python3 scripts/build_{theme}_arena.py --check` が exit 0
- [ ] 同じ入力で2回実行して差分ゼロ
- [ ] アリーナの点の数と論点カードの件数が一致する
- [ ] 投票の topicId と選択肢数が変わっていない
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
- [ ] `tests/test_{theme}_adapter.py` が通る
- [ ] `THEMES.yaml` の `page_update_mode` が `adapter` になっている

### 完了報告に必ず含めること
1. `git diff --stat`
2. 変更前後のアリーナの点数・論点別内訳の対照表
3. 2回実行して差分ゼロだったことの実行ログ
4. 投票の topicId と選択肢数（変更がないこと）
5. `verify_theme_page.py` / `verify_top_page.py` の出力をそのまま貼る
6. 判断に迷った点
