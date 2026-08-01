# TASK_BOARD — SNS反応まっぷ（テーマ横断課題のみ）

最終更新: 2026-07-05（課題6・14・20を GROWTH.yaml へ移管）

> **テーマ個別の工程状態は `THEMES.yaml` を参照してください。**
> 完了済み課題は `archive/TASK_BOARD_ARCHIVE.md` に移動しました。

---

## 運用ルール

- ハブAI（Claude Code）は毎セッション LOOP.md に従って動く
- ワーカーAIは `configs/prompts/` のプロンプトに従って作業する
- ブランチ運用: `task/{theme}-{工程}` 形式。main直接コミット禁止
- 保護タグ: GA4(`G-K10S4YCZFH`) / AdSense(`ca-pub-2542211932832864`) / Supabase / OGP

---

## アクティブ課題（テーマ横断）

### 課題13: 新規トピック継続追加
**状態**: 未着手（LOOP.md ②の優先順位5に該当）
**概要**: 2日に1本ペースで新テーマ追加。賛否が出やすいテーマ。戦争関連除外
**手順**: AI_HANDOFF.md §9 参照

### 課題15: AdSense審査対応 & 広告配置設計
**状態**: 不承認（2026-07-07、理由: 有用性の低いコンテンツ）→ 対策実装済み、再審査申請待ち
**概要**: 審査結果追跡、通過後の広告ユニット配置設計、プロジェクトアドレスへの管理権限移行
**2026-07-07 対応済み**: 全8テーマページに「この争点の背景」解説セクション追加（configs/*.json の `background` フィールド＋build_reaction_map.py 対応済みのため再ビルドでも保持される）、docs/about.html（運営者情報）新設、全フッターにリンク追加、sitemap更新
**2026-07-30 対応済み**: 問い合わせ窓口をGoogleフォームで開設（メールアドレス非公開・ログイン不要）、about.html の訂正窓口セクションと disclaimer.html の削除依頼導線をフォームにリンク。個別返信は原則行わない旨と、事実誤認の指摘・削除依頼には対応する旨を明記
**残作業**: ①git push で公開 ③コンテンツをさらに充実させ2週間程度おいてから AdSense管理画面で「審査をリクエスト」（即再申請は同理由で落ちやすい）④長期的には独自ドメイン移行を検討（github.ioサブドメインは審査上不利）

### 課題17: Googleアカウント・サービスのプロジェクトアドレス統一
**状態**: 未着手
**概要**: AdSense・GitHub Orgの管理権限をプロジェクトアドレスへ移行

### 課題18: サイトデザイン・体験の全面改善
**状態**: 大部分が課題26で実現済み。残りは配色・フォント統一とXブランドトーン統一
**スコープ**: デザインガイドライン策定、全体配色統一、モバイルファースト確認

### 課題19: パイプラインでのステータス自動更新
**状態**: 未着手
**概要**: run_pipeline.py の各Step完了時に site-cases.json の status を自動更新

### 課題27: GitHubトークンを期限付きで作り直す
**状態**: 未着手
**概要**: 現在のGitHubトークン（名前: claude-code）が無期限のためセキュリティリスクあり。90日など期限付きで作り直す
**手順**: https://github.com/settings/tokens で現トークン削除 → 新規作成（repo・workflow・read:orgスコープ、90日期限）→ `gh auth logout` → `gh auth login` でトークン更新

### 課題28: sample_period の unknown を埋める
**状態**: 未着手（`WORK_PLAN_2026-08.md` A-4 で回収）
**概要**: S1 で THEMES.yaml に `sample_period`（収集期間）を追加したが、6テーマが `unknown` のまま。A-4「調査条件の表示」で各テーマの数字の近くに取得期間を出すため、それまでに埋める必要がある
**対象（6件）**: bike-blue-ticket / bukatsu-chiiki / constitutional-amendment / elderly-license-revocation / school-nickname-ban / henoko-student-accident
**手順**: 各テーマの `sample_file` のレコード内タイムスタンプ、または収集時の作業ログ・git log・`social-samples/*.md` から期間を特定する。**特定できない場合は推測で埋めず `unknown` のまま残し、ページ側で「取得期間: 記録なし」と正直に表示する**
**注意**: `sample_source` は全11テーマ「Yahooリアルタイム検索」で埋まっている。検索語（クエリ）は未記録なので、A-4 で表示するなら `sample_queries` フィールドの追加も併せて検討する

### 課題29: ページ内件数表示と sample_file の突き合わせ
**状態**: 未着手（`WORK_PLAN_2026-08.md` A-4 で回収）
**概要**: S1 で「分類済み投稿数」をトップに出す根拠を `sample_file` の実レコード数に統一したが、THEMES.yaml のコメント記載や各テーマページ内の件数表示と食い違うテーマがある。トップとテーマページで違う数字が出ると、S1 で解消した矛盾が別の場所で再発する
**乖離の例**:

| テーマ | THEMES.yaml コメント | sample_file 実数 |
|---|---|---|
| bukatsu-chiiki | 旧2D 245件 | 467 |
| constitutional-amendment | 552件 | 646 |
| school-nickname-ban | 134件 | 374 |
| henoko-student-accident | 356件 | 363 |
| consumption-tax-cut | classify2d: n-a | 667 |

**手順**: ①各テーマページが表示している件数がどの数字か（2D分類 / Hermes論点分類 / 収集総数）を特定 ②`sample_file` の数と一致するか確認 ③一致しない場合、どちらが「分類済み投稿」の定義に合うかを決めて統一 ④`verify_top_page.py` に「トップの件数と各テーマページの件数が矛盾しない」検査を追加
**備考**: 2D分類と Hermes 論点分類で対象件数が違うのは妥当な可能性が高い。その場合はページ側の表記を「論点分類 ○件」等に変えて、何を数えた数字かを明示する

---

## 連絡メモ（AI間の申し送り）

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-27 | Antigravity | 全員 | AdSense審査通過後にプロジェクト用アドレスを「管理者」として招待し権限移行すること |
| 2026-07-01 | Antigravity | 全員 | 課題16 OGP対応完了。build_reaction_map.pyにOGP自動挿入機能を追加済み |
| 2026-08-01 | Claude | 全員 | `WORK_PLAN_2026-08.md` と `WORK_PLAN_2026-08_SESSIONS.md` を追加。8月はこの計画に従い、S1〜S5 のセッション単位で進める。発注書は `configs/prompts/codex/` に置く |
| 2026-08-01 | Claude | 全員 | S1完了。トップの数値は `THEMES.yaml` の `sample_file` の実レコード数から生成される。**数値をHTMLに直接書かないこと。** 変更後は必ず `python3 scripts/verify_top_page.py` を実行し、NG（exit 1）がないことを確認する |
