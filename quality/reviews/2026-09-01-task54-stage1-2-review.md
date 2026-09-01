# 課題54 段階1・2 レビューと修正

実施日: 2026-09-01  
判定: pass（指摘6件を修正のうえ）  
対象: `task54: unify claim verdict vocabulary` / `task54: add public claim verification contract`

## 実測で確認したこと

記録の記述ではなく、実際にコマンドを走らせて確認した。

- 判定語の統一: 6テーマ41主張すべてが `fact` / `gap` / `miss`（fact 19・gap 14・miss 8）
- 公開ページが変わっていないこと: `verify_theme_page.py` の再生成可能性が11テーマでNG 0件。
  憲法改正の日本語表示（「原典にある」等）は生成時に戻るため、公開HTMLは変わらない
- 件数の一致: 6テーマ248件が、確定データ・`data/verification/`・公開JSONの3か所で一致
- 決定的生成: `build_public_registry.py --all` の2回実行で差分0
- 非公開正典との完全一致、Schema・不変条件検査、全テスト

## 指摘と修正

### 1. 主張が論点（大陸）へ結びついていなかった（要対応）

設計書3.3の地形は論点単位で実像／ずれ／蜃気楼を塗り分けるが、公開JSONの主張は論点への
参照を持っていなかった。このままでは段階6で色を決められず、段階3で作る部活動の主張も
後から結び直しになる。41主張すべてに `issue_ids` を持たせた。

「その他」への割り当ては禁止した（分類限界の受け皿であって、照合結果の受け皿ではない）。
1つの主張が複数論点にまたがることは許す。主張が1つも無い論点は「未照合」とし、色を付けない。
論点1つに複数の主張が付いたときの決め方は段階6で決める（設計書14章に明記）。

### 2. 設計書14章と公開Schemaが矛盾していた（要対応）

14章は「該当投稿IDを持つ」、Schemaは「投稿IDを含めない」。実装側が正しいため、14章を
「公開JSONは件数だけを持ち、投稿IDの正典は `data/{theme}_claim_posts.json`」へ改めた。

### 3. 一次資料が0件でも検査を通った

`fact` / `gap` の主張に一次資料0件を禁止した。0件でよいのは `miss`（資料に見当たらないこと
自体が結論）だけ。現に副首都の `cost_ai_estimate` が該当し、これは妥当な0件である。

### 4. 確認者種別が1値しかなかった

`ai_assisted` を追加した。段階3で実際に読むのはAIであるため、着手前に値を用意した。
`ai_assisted` を「人が確認」と表示しない規則を設計書14章に書いた。

### 5. 件数の出所が2経路あった

ページは `data/{theme}_claim_posts.json`、公開JSONは `data/verification/` を読む。
片方だけ更新すると同じサイトの2か所で違う数字が出る（AdSense3回目の不承認と同じ壊れ方）。
3か所を突き合わせる検査を `verify_claim_verdicts.py` に足し、テストで固定した。

### 6. 憲法の確定データに旧判定語が残っていた（5の検査で発見）

`data/constitutional-amendment_claim_posts.json` の10件が「原典にある」等のままだった。
段階1の取りこぼし。3語へ統一し、旧語彙の再混入も検査で止める。

## 検査結果（修正後）

- `verify_claim_verdicts.py`: 41主張・件数一致・旧語彙なし
- `verify_public_registry.py --public-only` / `--against-private`: いずれもOK
- `verify_theme_page.py`: 11テーマ NG 0件（再生成可能性を含む）
- `verify_number_provenance.py`: 11テーマ NG 0件
- 全テスト、2回生成の差分0

## 段階3へ引き継ぐこと

段階3（部活動の一次資料照合）には着手していない。主張を作るときは、最初から
`issues`（論点）と一次資料を持たせること。`data/bukatsu-chiiki_claim_posts.json` を
作った時点で、`CLAIM_AUDIT_SOURCES` と `verify_claim_verdicts.SOURCES` の両方へ登録する
（テストが6テーマ41主張で固定してあるため、更新しないと落ちる）。
