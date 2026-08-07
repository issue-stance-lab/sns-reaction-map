# Hermesレビュー依頼: テーマ別分類設計 v2

## 背景

Yahooリアルタイム検索で取得したSNS反応をOllamaで分類しているが、テーマによって失敗傾向が異なる。

- `school-nickname-ban` は明確な賛成/反対が出にくく、v2でも `201件中167件がその他・分類保留` になっている。
- 政治系は賛否が出やすい一方で、引用、皮肉、人物批判、政策賛否、党派批判が混ざり、単純分類では誤分類が多い。
- `constitutional` と `henoko` では構造化分類v2があり、単純分類より有望。

## レビュー対象

- `classification-design-v2.md`
- 既存トピック設定:
  - `configs/topics/school-nickname-ban.yaml`
  - `configs/topics/takaichi.yaml`
  - `configs/topics/constitutional.yaml`
  - `configs/topics/henoko.yaml`
  - `configs/topics/ai-copyright.yaml`
  - `configs/topics/bukatsu-chiiki.yaml`

## レビューしてほしいこと

1. テーマ型の分類が妥当か
   - 政治・政策論争型
   - 事故・炎上・複合対象型
   - 生活・教育・マナー型
   - 技術・権利・産業対立型
   - 制度移行・公共サービス型

2. 各テーマ型の出力フィールドが多すぎないか
   - `category`
   - `stance`
   - `issue`
   - `target` / `actor_target` / `criticized_target`
   - `stance_to_quoted_author`
   - `stance_to_quoted_claim`
   - `confidence_level`
   - `review_required`

3. UI・記事化の観点で読者に伝わりやすいか
   - 反応マップで見せるべき主軸は何か
   - 棒グラフにするべき軸、表にするべき軸、代表投稿だけでよい軸を分けてほしい

4. `school-nickname-ban` の再設計案
   - 賛成/反対ではなく論点分類を主軸にする方針が妥当か
   - 追加すべき検索クエリ案
   - カテゴリ名の改善案

5. `takaichi` の構造化v2移行案
   - 高市氏、玉木氏、松井氏、文春・共同、サナエトークン、ネット選挙透明性をどう分けるべきか
   - 人物批判、報道批判、疑惑否定、制度論を混同しないフィールド設計にできているか

## 期待する出力

以下の形式でレビュー結果を返してください。

```md
# 分類設計v2レビュー

## 総評

## 修正必須

## テーマ型ごとの指摘

### 政治・政策論争型

### 事故・炎上・複合対象型

### 生活・教育・マナー型

### 技術・権利・産業対立型

### 制度移行・公共サービス型

## トピック別の修正案

### school-nickname-ban

### takaichi

### constitutional

### henoko

### ai-copyright

### bukatsu-chiiki

## 実装優先順位
```

## 注意

- 件数は世論比率として扱わない。
- Yahooリアルタイム検索で取得できる短文SNS投稿を前提に、細かすぎる分類は避ける。
- 代表投稿に使うものは高信頼・低リスクを優先する。
- 既存HTML生成・SQLite取込への影響も考慮する。

