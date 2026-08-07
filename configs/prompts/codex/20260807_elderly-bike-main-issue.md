## タスク: 高齢者免許返納と自転車青切符に論点分類を入れる

### 出典
TASK_BOARD.md 課題29 / 2026-08-07 の全テーマ点検

### 目的
この2テーマは正典データに `main_issue` が入っていない。ページのカード件数は
2026-08-02 に暫定的に固めた凍結ファイルから出ており、正典から再現できない。
収集予定は 8/13（高齢者）と 8/15（自転車）。

### 背景（調査済み・再調査不要）
- 高齢者免許返納: 正典 `social-samples/elderly-license_2d_classified.json` 211件。
  `main_issue` なし。カード件数は `data/issue-counts/elderly-license-revocation.json`
  （凍結）から。`original_category` は114件しか埋まっていない
- 自転車青切符: 正典 `social-samples/bike-blue-ticket_2d_classified.json` 181件。
  `main_issue` なし。カード件数は `social-samples/bike_arena_hermes_classified.json`
  （別ファイル）から

分類器 `classify_elderly_arena_hermes.py` / `classify_bike_arena_hermes.py` は
それぞれ6論点を持っているが、正典に適用されていない。

### やること（1テーマずつ。まず高齢者免許返納）
1. `scripts/{theme}_taxonomy.py` を新設し、論点・立場・アリーナ座標を1か所に定義する
2. 分類器がそのモジュールを参照するようにする
3. 正典の全件を分類器で分類し、`main_issue` / `stance` / `is_relevant` / `is_opinion` /
   `confidence` を持つ単一スキーマの正典へ差し替える。旧ファイルは履歴として残す
4. 分類前に10件の試験分類を行い、論点の割り当てが妥当か目視で確認する
5. `configs/{theme}-reaction-map.json` の `issue_counts.source` を削除し、
   `sample_file` から件数を出すようにする。`cards` の `main_issue` を新しい論点名に合わせる
6. `python3 scripts/sync_issue_counts.py {theme}` でカード件数を再注入する
7. ページの公開件数・insight・調査条件を正典から再計算した値に更新する
8. 対応する `data/issue-counts/{theme}.json` を削除する
9. `tests/test_{theme}_taxonomy.py` を追加する

### やらないこと
- アリーナの点データ（SM_RAW）の再生成 — ページ生成プログラムの新規作成が必要で、
  別発注（課題34）にする。今回は件数の出所を正典へ一本化するところまで
- データの追加収集
- 2テーマを同時に進めること。1テーマ完了・検証・コミットしてから次へ

### 制約（必ず守る）
- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/{theme}-main-issue`。main 直接コミット禁止
- 投票の選択肢は変更しない（論点名がカードと投票で違う場合は、投票側に合わせる）
- 公開件数が変わる場合は、トップの `hero-total-samples` まで同期する
- 数値をハードコードしない

### 完了条件
- [ ] 正典の全レコードに `main_issue` がある
- [ ] configs の `issue_counts.source` が消え、件数が `sample_file` から再現できる
- [ ] `data/issue-counts/{theme}.json` が削除されている
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
- [ ] `taxonomy_continuity` が compatible を返す

### 完了報告に必ず含めること
1. `git diff --stat`
2. 分類前後の件数と論点別内訳（変更前の凍結ファイルの数字と並べる）
3. `verify_theme_page.py` / `verify_top_page.py` の出力をそのまま貼る
4. 試験分類10件で確認した内容
5. 判断に迷った点
