# 課題27: GitHubトークンを期限付きで作り直す

**状態**: 未着手
**概要**: 現在のGitHubトークン（名前: claude-code）が無期限のためセキュリティリスクあり。90日など期限付きで作り直す
**手順**: https://github.com/settings/tokens で現トークン削除 → 新規作成（repo・workflow・read:orgスコープ、90日期限）→ `gh auth logout` → `gh auth login` でトークン更新
