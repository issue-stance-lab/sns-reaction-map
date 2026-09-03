# 課題36: 放置された作業ツリー3本

**状態**: 完了（2026-08-08。3本とも削除済み。中間成果物4件は担当ブランチへ保全）
**発見**: 2026-08-07、運用棚卸し

**概要**: `LOOP.md` ⓪ は「作業が終わったら `git worktree remove` で片付ける」と定めているが、3本残っていた。**3本ともブランチは main にマージ済み。**

| ツリー | ブランチ | 未コミット | 処置（2026-08-08） |
|---|---|---|---|
| `.claude/worktrees/agent-ae24789032b473197` | task/henoko-page-v3 | あり。`docs/henoko-student-accident-reaction-map.html` を公開版1,051行 → 142行のスタブに壊す中断状態（投票セクション・シェア・やり直しボタンが全消え）。**採用してはいけない** | 未コミット分を破棄して削除。origin/main の現行版が正 |
| `.claude/worktrees/competent-gates-92d0d7` | detached HEAD | なし | 削除。コミット 5b69733 は `claude/competent-gates-92d0d7`（ローカル・origin 両方）に残存 |
| `.worktrees/fukushuto-tide` | task/fukushuto-tide | 未追跡4件。2026-08-07 に共有ツリーの `social-samples/` へ退避済み（`fukushuto_hermes_prev_20260714_v2.json/.md`、`fukushuto_test_10.json`、`fukushuto_test_10_classified.json`） | 削除。4件は `task/fukushuto-tide` にコミットして push（3b3efef）。詳細は下記 |

**4件の正体（2026-08-08 に中身を確認）**: `configs/prompts/codex/20260807_fukushuto-tide-widget.md` の**手順1・手順2の成果物**であり、破棄してはいけないものだった。

- `fukushuto_test_10.json` / `_classified.json` — 手順2の試験分類10件。入力は旧5論点で全件「副首都法案の是非」、出力は新7論点に分散
- `fukushuto_hermes_prev_20260714_v2.json` / `.md` — 手順1の7/14分292件の再分類。旧版に対し stance が変わったのは29件

**残作業は 2026-08-08 に完了**（`task/fukushuto-tide` の `433d89c`）。7/26分308件を再分類し、対照表でオーナー承認を得たうえで潮目ウィジェットを7論点へ移行した。同一画面での二重表示は解消済み。作業手順は `.claude/skills/taxonomy-migration/` にスキルとして残した。

**なぜ放置が危険だったか**: 2026-08-07 に共有ツリーで事故が2件起きている（分類処理の参照ファイル消失、統合直後の正典1,606件が削除されかけ）。残ったツリーは同じ事故の温床になる。**今回も、未追跡ファイルを中身を見ずに「不要」と判断しかけた。中間成果物は必ず中身を確認してから処置すること。**
