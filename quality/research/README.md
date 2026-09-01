# quality/research/ — 一次資料メモ（10テーマ）

公開中10テーマ（takaichi を除く）について、各テーマの論点ごとに一次資料を洗い出したメモ。
`FACT_CHECK_GUIDE.md` の「投稿の主張を一次資料と突き合わせる」セクションを作るときの材料。
**このメモ自体は公開ページに載せない。** 載せる前に、下の「残っている確認」を人が潰すこと。

## 作り方（2026-08-30）

- 調査したのは Hermes CLI（`hermes -z`、モデル kimi-k2.6 / OpenCode Go）。web検索とブラウザで各自が調べた
- 発注は1テーマ1プロセス、10本を並列実行。所要 約20分
- 出典に使ってよい資料を「省庁・国会会議録・e-Gov・裁判所・自治体・政党の公表資料」に限定し、
  報道・まとめサイト・解説ブログ・Wikipedia を禁止した（`FACT_CHECK_GUIDE.md` の基準）
- 出力後、全URLを curl でHTTPステータス検査した（2026-08-31 に再検査。初回の検査は
  本文の注記までURLに含めてしまい、実在するmextの2本を404と誤判定していた）

## 定期的な再確認（2026-09-01 追加）

一次資料は法改正・統計更新で古くなる。`status.yaml` にテーマごとの最終確認日を記録し、
`python3 scripts/build_admin_dashboard.py`（管理ダッシュボード）が90日（テーマによっては
短縮）を過ぎたものを自動で検知する。手順は `.claude/skills/primary-research/SKILL.md`。
**再確認したら `status.yaml` の `last_verified` を必ずその日に書き換えること。**

## テーマ別

| テーマ | ファイル | 状態 |
|---|---|---|
| 生成AIと著作権 | ai-copyright-primary-sources.md | 再発注ずみ・URL全通 |
| 自転車の青切符 | bike-blue-ticket-primary-sources.md | 取り直しずみ・URL全通 |
| 部活動の地域移行 | bukatsu-chiiki-primary-sources.md | 403が2本／本文が「推定」と自認したURLが2本（実在は確認） |
| 憲法改正論議 | constitutional-amendment-primary-sources.md | 取り直しずみ・会議録は詳細URL・URL全通 |
| 高齢者免許返納 | elderly-license-revocation-primary-sources.md | URL全通 |
| 学校でのあだ名禁止 | school-nickname-ban-primary-sources.md | 再発注ずみ・URL全通 |
| 辺野古高校生死亡事故 | henoko-student-accident-primary-sources.md | URL全通 |
| 副首都構想 | fukushuto-primary-sources.md | 取り直しずみ・会議録は詳細URL・URL全通 |
| 皇室典範改正 | koshitsu-tenpakai-primary-sources.md | URL全通 |
| 消費税減税 | consumption-tax-cut-primary-sources.md | URL全通 |

## 残っている確認（ページに載せる前に必ず）

1. **自転車の404を2本潰す。** 該当ファイルの冒頭に警告を入れてある。正しいURLを探すか、その資料を落とす
2. **国会会議録のURLがトップページ（`https://kokkai.ndl.go.jp/`）のままの箇所を、
   会議録の詳細URL（`#/detail?minId=...`）へ差し替える。** 発言番号だけでは読者が原文へ行けない。
   再発注したテーマは詳細URLで返ってきているので、同じ指示で個別に取り直せる。
   副首都も 2026-08-31 に国会会議録API（`/api/meeting_list`）で issueID を取る手順を渡して取り直し、
   会議録3本が詳細URLになった。会議録を出典にするときはこの手順を発注文に必ず入れること
3. **引用文の原文照合。** メモの「確かめられる事実」は Hermes の読み取りで、原文と1字ずつ照合していない。
   憲法改正ページで過去にやったように、会議録APIで発言番号まで突き合わせること


## 2026-08-31（続き）自転車の404を解消

国交省GOOD CYCLE JAPANの2URLが404だった原因は、Hermesが `/bicycleuse/` から始まる推測URLを
書いていたこと（正しいパスは `/road/bicycleuse/`）。この作業は「機械的な照合」ではなく
「正しいURLをもう一度探す」作業なので、opencode（`opencode-go/qwen3.7-max`、hermesとは別枠の
クォータ）にURL特定だけを発注し、返ってきたURLを自分でcurlして200・本文一致を確認した。
計画本体PDF（`assets/pdf/3rd_plan.pdf`）と目標1のページ（`plan/action1/`）も合わせて確認済み。
警察庁・内閣官房の「確認できなかったこと」2件は、URLパターンを推測しても404止まりだったため
未解決のまま残してある（空振りを消さない方針どおり）。
