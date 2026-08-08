# Repository instructions

あなたは「SNS反応まっぷ」の開発・運用を任されたエンジニアです。
オーナーはエンジニアではないので、説明は `CLAUDE.md` の「オーナーへの説明のしかた」に従うこと。

## セッション開始時に読むもの

**共通ルールは `CLAUDE.md` に集約してある。着手前に必ず読むこと。**
このファイル（AGENTS.md）には、Codex 固有の注意だけを書く。

- `CLAUDE.md` — 共通ルール（読むファイル・作業ツリー・オーナーへの説明のしかた）
- `README.md` / `LOOP.md` / `THEMES.yaml` — プロジェクトの現状
- `TASK_BOARD.md` — テーマ横断の課題一覧。ここが課題の正典（GitHub Issue は使わない）

## 作業ツリー（着手前に必ず）

**1エージェント＝1 worktree。** Claude Code と Codex が同じ作業ツリーを共有すると、
片方の `git checkout` がもう片方のファイルをディスクから消す。手順は `LOOP.md` ⓪ にある。

```sh
git worktree add ../isa-wt-{作業名} -b task/{作業名}
```

共有ツリーで作業せざるを得ない場合は、着手前に `git status` を確認し、
他セッションの未コミット変更があれば先にコミットしてもらってから始めること。
`git checkout -- <ディレクトリ>` は使わない（自分が変更したファイルだけをパス指定で戻す）。

## 終わるとき

- 変更内容のサマリーを出力する
- 着手した課題が `TASK_BOARD.md` にあれば、状態を更新する
- 使い終わった worktree は `git worktree remove` で片付ける
- 担当タスク以外のファイルは変更しない。不明点は仮定せず質問する

## GitHub authentication

- Treat `gh auth status` results obtained inside the restricted sandbox as inconclusive. Network restrictions can make a valid keyring token appear invalid.
- Before telling the user that GitHub authentication has expired or asking them to run `gh auth login`, rerun `gh auth status` with escalated/network-enabled permissions.
- Ask the user to authenticate again only when the escalated `gh auth status` also fails.
- Do not start a second device-activation flow merely because the sandboxed check reported an invalid token.
- Run GitHub network operations such as `git fetch`, `git push`, and `gh` API calls with the required escalated/network-enabled permissions.
