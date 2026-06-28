# henoko 分類設計レビュー

## 判定

小修正して可。

既存 `classify_henoko_structured_ollama_batch.py` の方向性は妥当。ただし403件への全面Ollama再分類はローカル実行で非常に重く、今回は既存403件分類をベースに、Hermes指摘の構造化フィールドを決定的ルールで付与する方針にした。

## 追加したルール

- `reaction_type` を追加し、追悼・批判・懸念・支持・反発・制度論・情報共有・未確認を分離。
- `actor_target` / `criticized_target` に、文科省、学校、教育委員会、報道機関、行政、政治家、反基地運動、基地・移設問題、なしを追加。
- 追悼だけが中心の投稿は `criticized_target: なし`。
- 事実確認・情報共有、未確認・過激表現、その他・分類保留は `article_usable: false`。
- 文科省判断支持と文科省判断反発は、本文中の評価語で分ける。
- 追悼語があっても、共産党批判・左翼批判・式典妨害・政治利用批判が中心なら追悼カテゴリに寄せない。

## カテゴリ・フィールド修正案

カテゴリは既存カテゴリを維持し、旧カテゴリ名だけ正規化した。

- `教育基本法違反視` → `文科省判断支持・政治的中立性違反を指摘`
- `事故原因・安全管理への関心` → `事故原因・再発防止への関心`

追加フィールド:

- `actor_target`
- `criticized_target`
- `target`
- `stance_to_target`
- `issue`
- `reaction_type`
- `confidence_level`
- `review_required`
- `review_reason`

## 再分類手順案

1. 最新403件の通常分類を読み込む。
2. 既存カテゴリを構造化カテゴリへ正規化する。
3. カテゴリごとに `actor_target`, `criticized_target`, `issue`, `reaction_type` を付与する。
4. 文科省判断・安全管理・追悼について本文マーカーで補正する。
5. `article_usable` と `review_required` を厳格化する。
6. HTML反応マップへ採用する。

## 採用時の注意

- `confidence_level: low` や `review_required: true` は代表投稿に出さない。
- `未確認・過激表現` は集計には残すが、本文引用は避ける。
- 安全管理、文科省判断支持、文科省判断反発、政治利用批判は近接しやすいため、記事化時は `criticized_target` を確認する。
- 今回のOllama全面再分類は速度面で未完走。将来は構造化プロンプトをさらに短くし、少量サンプル監査から再実行する。
