## タスク: 憲法改正と辺野古の件数を正典から出すようにする

### 出典
TASK_BOARD.md 課題29 の残作業

### 目的
ページのカード件数が `data/issue-counts/` の凍結ファイルから出ており、正典と
食い違ったまま。凍結ファイルはページのHTMLから1度だけ抜き出したもので、
span を手で書き換えれば検査が落ちる状態にある。

### 背景（調査済み・再調査不要）
- 憲法改正: 正典646件、分類器と論点が一致している。凍結ファイルは422件分
- 辺野古: 正典363件、分類器と論点が一致している。凍結ファイルは265件分。
  さらに正典の全363件で `is_relevant` / `is_opinion` が入っていない
- 高齢者免許返納も同じ状態だが、原因が違う（正典に論点がない）ため別発注
  `20260807_elderly-bike-main-issue.md` で扱う

正典から件数を出すと、公開中の数字が変わる。辺野古の例:
安全管理・事故原因 75 → 102、報道・行政対応 70 → 87、政治的中立性 53 → 62。

### やること（1テーマずつ。まず憲法改正）
1. 正典から論点別件数を計算し、現在の表示との差分表を作って報告する
   （数字が変わることの承認を得てから2へ進む）
2. `configs/{theme}-reaction-map.json` の `issue_counts.source` を削除する
3. `cards` の `main_issue` が正典の論点名と一致していることを確認する
4. `python3 scripts/sync_issue_counts.py {theme}` でカード件数を再注入する
5. ページの公開件数・insight・詳細データの表を正典から再計算した値に更新する
6. トップの `hero-total-samples` を再計算する
7. `data/issue-counts/{theme}.json` を削除する
8. 辺野古については、正典に `is_relevant` / `is_opinion` がないため「意見◯件」の
   表示ができない。全件基準（`basis: all`）のままにするか、再分類して意見を出すかを
   判断して報告する

### やらないこと
- アリーナの点データの再生成（別発注・課題34）
- データの追加収集
- 解説文の書き直し

### 制約（必ず守る）
- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/{theme}-issue-counts`。main 直接コミット禁止
- 数値をハードコードしない。`sync_issue_counts.py` 経由で注入する
- 手順1の差分表を報告して承認を得るまで、公開ページを変更しない

### 完了条件
- [ ] configs の `issue_counts.source` が消えている
- [ ] `data/issue-counts/{theme}.json` が削除されている
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
- [ ] トップの合計とテーマページの件数が一致する

### 完了報告に必ず含めること
1. `git diff --stat`
2. 変更前後の論点別件数の対照表
3. `verify_theme_page.py` / `verify_top_page.py` の出力をそのまま貼る
4. 辺野古の意見数表示についての判断
5. 判断に迷った点
