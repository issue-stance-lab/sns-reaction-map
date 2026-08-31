# Claudeレビュー依頼：課題57 段階2 公開データ契約

依頼日: 2026-08-31  
レビュー対象: 課題57「公開データ基盤と公開承認物の一本化」の段階2  
依頼者: 開発・データ部AI  
目的: 段階3（部活動テーマの公開JSON生成・完全照合）の実装前に、公開データ契約の重大な設計漏れを発見する。

## 背景

現在、サイトの数字は非公開の分類済み投稿、テーマ設定、検証用データ、生成器、公開HTMLなどに分散している。
課題57では、テーマごとの公開JSONと全テーマのcatalogを新設し、トップ・テーマページ・sitemap・将来の3Dが
同じ公開データを読む形へ一本化する。

公開対象は `THEMES.yaml` で `published: done` の10テーマだけ。高市テーマは非公開保全のため、
公開合計・トップ・catalog・sitemapへ含めない。

CEOは、次の方針を承認済み（`company/APPROVALS.yaml` の `approval-20260831-001`）。

- 読者向け用語を「収集した投稿」「分析対象の意見」「主要論点」「その他」に統一する
- 投稿本文、投稿ID、利用者情報、個別ハッシュ、AI信頼度、内部理由を公開JSONへ含めない
- 論点・立場のIDを表示名から自動生成せず、固定した対応表で管理する
- 一般公開、AdSense再申請、データ削除はこのレビュー対象外

## 必ず読むファイル

1. `quality/designs/public-data-foundation-rebuild.md`
2. `quality/reviews/2026-08-31-public-data-foundation-stage1-inventory.md`
3. `quality/reviews/2026-08-31-public-data-foundation-stage2-proposal.md`
4. `schemas/public-theme.schema.json`
5. `schemas/public-catalog.schema.json`
6. `configs/public-data-taxonomy.json`
7. `THEMES.yaml`
8. `company/APPROVALS.yaml`（`approval-20260831-001`）

必要に応じて、既存投票との関係を調べるため `configs/planet/bukatsu-chiiki.yaml`、
`docs/bukatsu-chiiki-reaction-map.html`、`supabase/functions/cast-vote/index.ts` を参照してよい。

## レビュー観点

### 1. 公開禁止情報

- Schemaまたは将来の生成経路から、投稿本文・投稿ID・ユーザー情報・個別ハッシュ・AI信頼度・内部理由が混入しないか
- `data/verification/` を公開データの正典にしていないか

### 2. 数字と言葉の意味

- 収集数、意見数、論点への割当数、主要論点、その他の意味が矛盾しないか
- 次の不変条件に不足がないか
  - `collected_count >= opinion_count`
  - `issue_assigned_count == opinion_count`
  - 論点別件数の合計 = `issue_assigned_count`
  - 各論点の立場別・強度別件数の合計 = 論点件数
  - その他は最大1つで、主要論点数には含めない

### 3. 固定IDと既存機能

- 10テーマの論点・立場の対応表に漏れがないか
- 表示名の変更で固定IDが変わる設計になっていないか
- 公開データIDが既存の投票 `topicId` や選択肢順を壊したり、混同したりしないか

### 4. 入力の逆流

- 公開HTML、`data/verification/`、`data/reaction_map.sqlite3`、旧ルートを次回生成の入力にしない設計になっているか
- `THEMES.yaml`、テーマ設定、非公開正典の役割分担が明確か

### 5. 実装可能性

- JSON Schemaだけで表現できない数値合計・一意性・日付整合を、専用検査器で止める必要が明記されているか
- 同じ入力から2回生成して差分0にするため、生成時刻など不安定な値を避けられているか

## 出力形式

次の形で、`quality/reviews/2026-08-31-public-data-foundation-stage2-claude-review.md` に保存してください。

```md
# 課題57 段階2 Claude独立レビュー

実施日: YYYY-MM-DD
判定: pass / revise_required

## 重大（段階3へ進めない）
- なし、または指摘と修正案

## 中（段階3の前に直す）
- なし、または指摘と修正案

## 軽微（実装時に対応）
- なし、または指摘

## 確認済み
- 確認した事実

## 総合判断
- 段階3へ進めるか。進めない場合は、必要な修正を具体的に列挙する。
```

レビューは変更提案までに留め、公開ページ・公開データ・非公開正典を変更しないでください。
