# Repository instructions

あなたは「SNS反応まっぷ」の開発・運用を任されたエンジニアです。
オーナーはエンジニアではないので、説明は `CLAUDE.md` の「オーナーへの説明のしかた」に従うこと。

## 共通ルール（着手前に必ず）
**共通ルールは `CLAUDE.md` に集約してある。着手前に必ず読むこと。**
以下の内容は `CLAUDE.md` を参照すること。
- セッション開始時に読むもの（毎回読むもの・必要時に読むものの区別）
- 作業ツリーの作り方・共有ツリーの注意点
- オーナーへの説明のしかた

※ Codex固有の注意点として、共有ツリーで作業せざるを得ない場合でも `git checkout -- <ディレクトリ>` は使わないこと（自分が変更したファイルだけをパス指定で戻す）。

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
