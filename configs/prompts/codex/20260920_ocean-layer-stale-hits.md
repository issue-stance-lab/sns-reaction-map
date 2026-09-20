## タスク: 「沈んだ大陸」のmachine_hitsが正典と再現しなくなった2テーマを直す

### 出典
`tasks/task-71.md`「(a) constitutional-amendment の「沈んだ大陸」2件が、現行の正典と照合できない」
「2026-09-20追記（検査スクリプトのバグを発見・修正）」節。bike-blue-ticket分は本セッション
（副首都の「資料にしかない話」新設中）で新規発見。

### 目的

`data/verification/{theme}-sunk-continents.json` の `match_rule.machine_hits` に記録した
tweet_id が、現行の正典に対して同じ条件（正規表現 or 選定済みハッシュ）を再実行しても
一致しなくなっている。`python3 scripts/verify_ocean_layer.py` を実行するとNGになる
（このスクリプト自体はCIに未接続のため、公開は止まっていない）。

着手前に必ず読む: `quality/designs/reaction-planet-renewal.md` 3.3.2、
`scripts/verify_ocean_layer.py`（検査の実装）。作業ツリー（作業用のコピー）を作ってから着手する。

### 対象1: bike-blue-ticket-sc-1（regex型、tweet_idが1件だけ再現しない）

`data/verification/bike-blue-ticket-sunk-continents.json` の `bike-blue-ticket-sc-1`。
`match_rule.pattern`（`指導警告|基本的には現場`、scope: text）を
`social-samples/bike-blue-ticket_2d_classified.json` に対して再実行すると、
記録された2件のうち `2098286331302740165` は再現するが、`2086098880874311993` が再現しない。

**原因を確認済み**: `2086098880874311993` は正典に実在し、本文にも「指導警告」「基本的に」の
語がそのまま含まれている（内容は改ざんされていない）が、`classification.is_opinion` が
`None`（`True`ではない）になっている。`run_match_rule()`（`verify_ocean_layer.py`）は
`is_opinion` が真でないレコードを検索対象から除外する設計のため、本文が一致していても
ヒットしない。**いつ・なぜこのレコードの`is_opinion`が`None`になったか（分類のやり直しで
変わったのか、元からこの値だったのか）は未調査。**

**やること**:
1. `2086098880874311993` の本文を実際に読み、これが本当に「意見」として数えるべき投稿か
   （`is_opinion`が`True`であるべきか）を判断する
2. `True`であるべきなら、そのレコードの分類を直す側（正典 or 分類のやり直し）で対応する。
   `sns_count`（現在2件）はそのままでよい
3. `True`にすべきでない（実際に意見未満と判定すべき）なら、`machine_hits`から
   `2086098880874311993`を外し、`sns_count`を1件に修正する。`sns_note`の文面
   （「従来の1件は歩道の少なさを語り」の記述）も実態に合わせて書き直す
4. どちらの場合も、`checked_by`を`ai_assisted`から`editorial_review`へ更新する
   （今回の見直しで人が本文を確認するため）

### 対象2: constitutional-amendment-challenge / -emergency-review（editorial_confirmation型）

`data/verification/constitutional-amendment-sunk-continents.json`。
`match_rule.type: editorial_confirmation`（正規表現では過検出になるため、`selected`に
`record_id_hash()`形式のsha256を記録する形式）。

- `constitutional-amendment-challenge`（国民投票への異議申立手続き）: `selected`6件中6件が
  現行の正典（`social-samples/`、`constitutional_amendment_*`系）のどのレコードをハッシュ化
  しても一致しない
- `constitutional-amendment-emergency-review`（参議院緊急集会の事後審査）: `selected`6件中
  4件が同様に一致しない（2026-09-18に追加された最新2件は再現できる）

**すでに分かっていること**（`tasks/task-71.md`より。再調査不要）:
- 改ざんの形跡ではなく、2026-09-12前後の判定以降にサンプルの重複整理等で対象投稿が
  入れ替わった可能性が高い
- `sns_count: 0`という結論自体が誤りとは確認していない（現行データで同じ条件語を
  再実行しても新たな一致は無い）が、**裏付けの再現性が崩れている**

**やること**（task-71.mdの対応方針を踏襲）:
1. 現行の正典に対して同じ条件語（`訴訟|裁判|異議`／`緊急集会`）で再度ヒットを取る
2. ヒットした投稿本文を実際に1件ずつ読み、除外理由を書き直す
3. `selected`（および`evidence`）を現行正典で再現できるハッシュへ揃える
4. **再現できないという理由だけで`sns_count`を変更しない。** 本文を実際に読んだ上で
   件数を判断する
5. `checked_by`を更新する（人が読み直した場合は`editorial_review`）

### 完了の条件

- `python3 scripts/verify_ocean_layer.py` がNG 0件（対象2テーマ分。他テーマの
  「地下水脈が1本しかない」等、既存の別課題（3.3.3・veins関連）まで解消する必要はない）
- `python3 -m unittest discover -s tests` が**マージ後のmain**ですべて通る
- 標準検査（`verify_theme_page.py` / `verify_number_provenance.py` / `verify_page_originality.py`
  / `verify_builder_rebuildability.py`）がNG 0件
- 本文を実際に読んで判断したことが、コミットメッセージか`themes/{テーマ名}.md`に残っている
  （要約の使い回し・機械的な穴埋めをしていないことの記録）

### やらないこと

- `machine_hits`/`selected`が再現しないことだけを理由に、対象そのもの（`topic`・`life_impact`）
  を書き直すこと。本文を読んだ結果、事実の記述自体は変えなくてよい場合が多い
- 地下水脈（veins）が1本しかない4テーマ（constitutional-amendment / henoko-student-accident /
  koshitsu-tenpakai / school-nickname-ban）への対応。これは別課題（task-71.mdの(b)）で、
  本タスクの範囲外
