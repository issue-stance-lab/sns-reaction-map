# 課題21: あだ名禁止・高齢者免許返納 — データ再分類 & HTML修正

**担当**: Hermes (Kimi K2.6)
課題管理: `TASK_BOARD.md`（課題7・課題9の延長）

## 作業の前に
- `Agent.md` と `TASK_BOARD.md` を読んでください
- 再分類はOllamaではなく、あなた（Hermes）が投稿テキストを直接読んでカテゴリを判定してください（Ollamaで一度保留になったデータのため）

## リポジトリ
https://github.com/issue-stance-lab/sns-reaction-map.git
ブランチ: `main` から `task/21-nickname-elderly-data-fix` を切って作業

## 問題の概要

保留率が高い2テーマのデータを再分類し、HTMLの半円チャート・バーチャート・ヒートマップを修正する。

---

## テーマ1: school-nickname-ban（あだ名禁止・さん付け）— 保留率66%

### 現状データ (`social-samples/school-nickname-ban_classified_v2_final.json`, 344件)
- 対象外・分類保留: 185件
- 体験談・現場感覚: 91件
- 情報共有・立場不明: 39件
- 親しさ・呼称文化への懸念: 15件
- その他・分類保留: 5件
- 一律禁止への実効性批判: 5件
- いじめ防止・心理的安全: 2件
- 柔軟運用・本人意思重視: 2件

**有効分類が24件 (7%) しかない。** 344件中229件が保留系。

### 問題 #21-1: 「対象外・分類保留」185件の大半はそもそもテーマと無関係

**重要**: 「対象外・分類保留」185件を実際に確認したところ、大半は「学校でのあだ名エピソード」（例: 「あだ名がベッタンだった」「ザビエルって呼ばれてた」）であり、**あだ名禁止政策への賛否とは無関係**。「体験談・現場感覚」91件も同様に個人の思い出話が多い。

つまり再分類だけでは解決しない。**検索クエリ自体が「あだ名 学校」のような広すぎるキーワードで、意見ではなく雑談を大量に拾っている**可能性が高い。

対応方針（以下から選択）：
- **A. 無関係データを除外し、有効データのみでHTML再構成** — 344件→有効分類のみ（数十件規模）で半円チャート等を再生成。件数は減るが正確になる
- **B. 検索クエリを見直して追加収集** — 「あだ名禁止 賛成」「さん付け 賛否」など意見が出やすいクエリでYahoo検索から追加取得し、有効データを増やす。その後HTML再生成
- **C. A+Bの両方** — まず無関係を除外、その後追加収集で補充

推奨は**C**。まず無関係データを `対象外` として確定除外し、有効データのみでHTMLを暫定更新。その後クエリ追加収集で件数を補充する。

再分類の手順：
1. 保留系229件 + 体験談91件 = 320件の投稿テキストを読む
2. 分類カテゴリは `configs/school-nickname-ban-reaction-map.json` の `category_order` を参照
3. あだ名禁止政策への賛否が読み取れるものは適切なカテゴリに再分類
4. テーマと無関係な投稿（個人のあだ名エピソード等）は「対象外・分類保留」に確定

### 問題 #21-2: 半円チャートの「その他」229件 (67%)

`docs/school-nickname-ban-reaction-map.html` の半円チャート `var data=[...]` を再分類後の件数で再構成する。

対立軸グループ（`configs/school-nickname-ban-reaction-map.json` の `conflict_axes` 参照）:
- 禁止支持 (positive): いじめ防止・心理的安全, ジェンダー配慮・さん付け支持 → 青系 `#1769d1`
- 禁止反対 (negative): 親しさ・呼称文化への懸念, 一律禁止への実効性批判 → オレンジ系 `#b54708`
- 柔軟運用 (derived): 柔軟運用・本人意思重視, 体験談・現場感覚 → ティール系 `#0f7490`
- その他: `#cbd5e1`

### 問題 #21-3: バーチャート・ヒートマップの件数更新

再分類後の件数に合わせて、分類別件数バーチャートとヒートマップも更新する。

---

## テーマ2: elderly-license-revocation（高齢者免許返納）— 保留率34%

### 現状データ (`social-samples/elderly-license-revocation_classified.json`, 183件)
- 免許返納義務化に賛成: 68件
- その他・分類保留: 63件
- 免許返納義務化に反対: 19件
- 自主返納のインセンティブ強化: 15件
- 適性検査や技術的制限の強化: 11件
- 代替移動手段や公共交通機関の整備: 7件

### 問題 #21-4: 「その他・分類保留」63件の再分類

63件の投稿テキストを読み、上記の既存カテゴリに分類できるものは再分類する。分類カテゴリは `configs/elderly-license-revocation-reaction-map.json` の `category_order` を参照。

### 問題 #21-5: 半円チャートの「未確認・過激化した反応」63件 (34%) の修正

`docs/elderly-license-revocation-reaction-map.html` の半円チャート `var data=[...]` を再分類後の件数で再構成する。

現在の半円チャートのグループ:
- 事故防止のため義務化すべき: 68件
- 適性検査や技術、インフラでカバーすべき: 33件
- 一律義務化には反対・地方の死活問題: 19件
- 未確認・過激化した反応: 63件 ← ここを減らす

### 問題 #21-6: バーチャート・ヒートマップの件数更新

再分類後の件数に合わせて更新する。

---

## 作業手順

1. `main` から `task/21-nickname-elderly-data-fix` ブランチを作成
2. `social-samples/school-nickname-ban_classified_v2_final.json` の保留320件を再分類
3. `social-samples/elderly-license-revocation_classified.json` の保留63件を再分類
4. 再分類結果をもとに各HTMLを更新:
   - 半円チャート `var data=[...]`
   - 分類別件数のバーチャート
   - ヒートマップの件数
5. コミット（タイトルに `課題21対応` を含める） & PR作成 → main へマージ

## 参考ファイル

- 正しく動作している例: `docs/ai-copyright-reaction-map.html`（保留28%で対立軸・半円チャートが正常表示）
- school-nickname-ban 設定: `configs/school-nickname-ban-reaction-map.json`
- elderly-license-revocation 設定: `configs/elderly-license-revocation-reaction-map.json`
- 分類設計の参考: `classification-design-v2.md`
