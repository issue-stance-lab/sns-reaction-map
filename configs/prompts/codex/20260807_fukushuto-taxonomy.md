## タスク: 副首都構想の論点体系を統一する

### 出典
TASK_BOARD.md 課題29・課題34 / 2026-08-07 の全テーマ点検

### 目的
分類プログラムと公開ページで論点の切り口が別々になっている。このままでは
8/11 の収集で taxonomy 検査に止められ、データを追加できない。

### 背景（調査済み・再調査不要）
2026-07-26 のコミット 3f28799 で分類器を新設した際、公開ページの論点定義を
参照せずに書き起こしたため、以下のように分岐した。ai-copyright と同じ原因。

- 公開ページ側（正典255件・カード・アリーナ・投票）: 定義・中身／費用・財源／
  候補地／優先順位／防災・災害／都構想・維新／その他（7論点）
- 分類器 `classify_fukushuto_arena_hermes.py`: 副首都法案の是非／大阪・関西中心の問題／
  財政・実現可能性／首都機能分散の必要性／中立・情報（5論点）

名前のゆらぎではなく切り口そのものが違うため、どちらを正とするかは編集判断になる。

### やること
1. どちらの論点体系を採るかを決める。判断材料は「正典255件を分類器の5論点へ
   割り当て直したとき、どの論点に何件入るか」を試験分類20件で見てから決める
2. `scripts/fukushuto_taxonomy.py` を新設し、論点・立場・アリーナ座標の対応を1か所に定義する
   （`scripts/ai_copyright_taxonomy.py` と `scripts/bukatsu_taxonomy.py` が手本）
3. 分類器がそのモジュールを参照するようにする。プロンプトの論点メニューも定義から生成する
4. 公開ページ側を採る場合: 分類器だけを直せば完了。投票・カード・アリーナは無変更
5. 分類器側を採る場合: 正典255件の再分類、カード定義の書き換え、アリーナの再生成、
   投票の topicId を v2 へ（Edge Function に選択肢数を追加して再デプロイ、旧票は切り離す）
6. `tests/test_fukushuto_taxonomy.py` を追加し、分類器・カード定義・ページの投票キー・
   Edge Function の選択肢数が一致することを検査する

### やらないこと
- データの追加収集（8/11 の予定に任せる）
- 他テーマの論点体系（別発注）
- 解説文の書き直し（論点名が変わる場合の最小限の追随を除く）

### 制約（必ず守る）
- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/fukushuto-taxonomy`。main 直接コミット禁止
- 数値をハードコードしない。THEMES.yaml か実データから導出する
- 投票の選択肢の並び・数を変える場合は、必ず topicId のバージョンを上げ、
  Edge Function の再デプロイまでを一組で行う

### 完了条件
- [ ] `scripts/refresh_topic.py` の `taxonomy_continuity` が fukushuto で compatible を返す
- [ ] `tests/test_fukushuto_taxonomy.py` が通る
- [ ] `python3 scripts/verify_theme_page.py fukushuto` が exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
- [ ] 投票を変更した場合、Edge Function 再デプロイ後に実際に投票が記録されることを確認

### 完了報告に必ず含めること
1. `git diff --stat`
2. どちらの論点体系を採ったかと、その判断根拠（試験分類20件の内訳）
3. `verify_theme_page.py` と `verify_top_page.py` の出力をそのまま貼る
4. 投票の topicId と選択肢数（変更の有無）
5. 判断に迷った点
