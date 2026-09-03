# 課題45: X運用の手の内を公開リポジトリから外す

**状態**: 未着手（第1段階のみ完了。2026-08-10、PR #80）
**きっかけ**: オーナーから「Xの情報があまり見られたくない」。調査の結果、
`docs/content/x/posts.md` が GitHub Pages でそのまま配信されており（HTTP 200 を確認）、
投稿文案とリプライ実績の表示回数がサイト訪問者から見える状態だった。
PR #80 でリポジトリ直下へ移し、サイトからは消えた。**リポジトリを直接
開いた人にはまだ見える。** これを消すのが本課題。

**前提（調査済み・作業前に読むこと）**:
- リポジトリを private にする案は使えない。Org が Free プランで、
  非公開リポジトリから Pages を配信できない → **サイトが止まる**
- 鍵・トークンの類は公開ファイルに無い（確認済み）。`G-K10S4YCZFH` は
  そもそもページに埋まる公開値。つまり漏洩ではなく「見え方」の課題
- サイト側は既に AI 利用を明記している（各テーマページに「AIを関連性・
  意見性の判定、論点・立場・表現強度の分類、要旨作成の補助に使用」）。
  **隠す対象は「AI利用」ではなく、集客のやり方とまだ小さい数字**
- CI は `.github/workflows/deploy.yml` の Pages デプロイ1本だけで、
  テストを回していない。`docs/` しかアップロードしない。
  → **Git 管理から外してもデプロイは壊れない**

**取るべき方法（移動ではなく、追跡をやめる）**:
`git rm --cached` ＋ `.gitignore` で「ファイルは今の場所に置いたまま、
Git の追跡だけ外す」。パスが変わらないので参照の書き換えが要らず、
スクリプト・テスト・Skill がそのまま動く。`social-samples/` の非公開正典と
`company/dashboard/` で既に使っている方式と同じ。

**スコープA（小・確実）— X運用の5ファイル**:
- `content/x/posts.md` / `X_POSTING_GUIDE.md` / `.claude/skills/x-daily/SKILL.md`
- `configs/prompts/claude-code/x-daily-session.md`
- `configs/prompts/codex/x-post-view-measurement.md`
- 触るコード: `scripts/x_post_views.py`、`scripts/admin_dashboard/`、
  `tests/test_admin_dashboard.py`（パスは変えないので、**新しい worktree で
  ファイルが無いときに落ちる**扱いだけ決める）

**スコープB（大・要判断）— AI運用そのもの**:
`GROWTH.yaml`（25ファイルから参照・コード6本が依存）、`creative/manga-prompts/`（28ファイル）、
`CLAUDE.md` / `AGENTS.md` / `LOOP.md` / `AI_HANDOFF.md` / `configs/prompts/` 全体。
**参照が広く、AIが手順書を読めなくなる副作用がある。** サイトが既に AI 利用を
開示している以上、費用対効果が悪い。Aを終えてから改めて判断すること。

**必ず対処すること（Aでも起きる）**:
- 追跡を外したファイルは **新しい worktree に入らない**（`git status` にも出ない）。
  LOOP.md ⓪ の復元手順に追加し、`scripts/backup_private_data.py` の対象にも入れる。
  入れ忘れると、バックアップの無いファイルが手元にだけ存在する状態になる
- 過去のコミット履歴には残る。履歴の書き換えは他セッションの worktree と
  衝突するので**やらない**方針（2026-08-10 にオーナーへ説明済み）

**完了の見分け方**: `git ls-files | grep -E "x-posts|X_POSTING"` が空。
`python3 -m unittest discover -s tests` が 184件 OK のまま。
