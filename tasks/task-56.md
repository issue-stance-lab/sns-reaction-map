# 課題56: 公開後の反映確認が index.html を誤ったパスで読んでいる


**状態**: 未着手（2026-08-31、課題55の段階2独立レビューで検出。課題55より前から存在する既存バグで、今回の移行が原因ではない）
**発見**: 2026-08-31
**優先度**: 低〜中（管理画面からの公開作業でしか発現しない。手動 `git push` では影響しない）

**概要**: `scripts/admin_dashboard/jobs.py` の `_verify_live_pages`（635行目）が、公開後にトップページが
本当に反映されたかを確認する際、`self.root / "index.html"` を読んでいる。しかし実際のトップページは
`docs/index.html` にあり、リポジトリ直下に `index.html` は無い。1行上でテーマページを読む処理は
`THEMES.yaml` の `html:` の値（`docs/...` を含む）をそのまま使っており正しい。

**やること**: 635行目を `(self.root / "docs" / "index.html").read_bytes()` に直す。

**完了条件**: 管理画面から公開を実行したとき、`_verify_live_pages` がトップページを正しく検証し、
`FileNotFoundError` で失敗しないこと。
