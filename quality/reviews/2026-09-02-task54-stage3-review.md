# 課題54 段階3 レビューと次工程の指示

実施日: 2026-09-02
判定: **条件付きpass。** 照合の中身は合格。マージ前に「照合の母数を1回ぶん追いつかせる」修正が要る。
対象: ブランチ `task/planet-stage3`（`b3fbb8b`、レビュー時点では main 未マージ）

**対応状況（2026-09-02 追記・本記録をmainへ入れる時点）**

- 1章（正典の欠落）: 対応済み。バックアップから復元し、共有ツリーのmainは緑に戻った
- 2章-1（増えた146意見の読み足し）: 対応済み。`coach-pay` に2件追加し確定30件→32件。
  母数を1139意見へ揃えたうえで `c9d7971` でマージ・本番反映（`68fab09` 時点で全ゲート緑）
- 2章-3（母数ズレを検出する検査）: **暫定対応。** 正式な `covered_period` は未着手のため、
  当面は `checked_on` を読んだ範囲の代わりに使い、`verify_claim_verdicts.py` が
  **警告**として一覧を出す（終了コードは変えない）。定期更新のたびに気づける状態にした
- 4章（引き継ぎ・THEMES.yaml notes）: 対応済み
- 残り（2章-2 / 2章-4 / 5章）: `TASK_BOARD.md` 課題54の「未着手（レビュー指摘）」に転記済み

この文書は当時の指示書としてそのまま残す。以降の正典は `TASK_BOARD.md` の課題54。

## 実測で確認したこと

記録の記述ではなく、実際にコマンドを走らせて確認した（すべて2026-09-02）。

- 確定した30件の投稿IDは**全件が正典に実在し、全件が意見**（`is_opinion` かつ `is_relevant`）。
  重複は1件のみで、2つの主張にまたがる投稿として妥当
- 一次資料11本すべて HTTP 200（`curl`）
- 主張と論点の対応: 5ラベルすべてが `configs/public-data-taxonomy.json` に実在し、「その他」への割り当ては無い
- ブランチ単体でのゲート: `verify_claim_verdicts`（7テーマ48主張）/ `verify_public_registry`
  2モード / `verify_theme_page bukatsu-chiiki`（993件で整合）がいずれもOK
- **mainへの試験マージ**（使い捨てツリーで実施）: `data/public/catalog.json` が衝突。
  `data/public/themes/bukatsu-chiiki.json` は自動マージされるが「新しい件数＋古い照合」の
  混成になり、**既存のどの検査にも掛からない**

## 1. 【対応済み】共有ツリーの非公開正典が1回ぶん欠けていた

段階3とは別の事故。2026-09-02の部活動データ更新（`caa9f31` / マージ `46da705`）のあと、
増えた非公開正典が共有ツリーへ戻らないまま、作業ツリー `isa-wt-bukatsu-refresh-20260902`
が削除されていた。公開JSONは意見1139件、共有ツリーの正典は8/26版（意見993件）。
`.staging/refresh/bukatsu-chiiki/20260902_120701/` も作業ツリーごと消えていた。
Gitに入っている `data/verification/updates/bukatsu-chiiki/2026-09-02/` はハッシュと分類ラベルのみで、
本文もIDも持たないため復元には使えない。

このため共有ツリーのmainで、全テスト4件・`verify_public_registry --against-private`・
`verify_number_provenance` が落ちていた。

`OPERATIONS.md` の復旧手順どおり、バックアップから戻して解消した。

```
tar -xzf /Volumes/HD-LE-B/issue-stance-private-backups/private-data-20260902T200922972051.tar.gz \
  -C . social-samples/bukatsu-chiiki_hermes_classified.json \
       social-samples/updates/bukatsu-chiiki/2026-09-02
```

戻した正典は1395件・意見1139件。`source_sha256` は
`54b31409619555de65cf5272ae1a037bbf126e1cd95f86cce4a46a1368aa9c99` で公開JSONの値と完全一致し、
別物を戻していないことを確認した。復元後のmainは全テスト367件OK、`--against-private` 10テーマ一致、
`verify_number_provenance` 11テーマNG 0件、`verify_top_page` OK。**再収集も公開の取り消しも不要。**

**再発防止（次のセッションで入れる）**: `release` スキルに、push直前に共有ツリーで
`python3 scripts/verify_public_registry.py --against-private` を回して緑を確認する手順を明記する。
非公開データを戻す手順は既にあるのに守られなかったため、文章ではなく検査の実行として書くこと。

## 2. 照合の母数が公開の母数と1回ぶんずれている（必須）

段階3は993意見（〜2026-08-26）を読んで確定した。公開済みは1139意見（〜2026-09-02）。
このままマージすると「1139意見のページに、993件時点の該当件数」が並ぶ。

**今の検査では検出できない。** `verify_claim_verdicts.py` の3か所突き合わせは
正典 `data/{theme}_claim_posts.json` / `data/verification/` / 公開JSON を比べるが、
3つとも同じ確定データから作られるため全部一致してしまう。試験マージで素通りを確認済み。

これは部活動だけではない。既存6テーマも同じ状態にある。

| テーマ | 確定日 | 公開データの期間末 |
|---|---|---|
| bike-blue-ticket | 2026-08-17 | 2026-08-24 |
| constitutional-amendment | 2026-08-20 | 2026-08-31 |
| consumption-tax-cut | 2026-08-19 | 2026-09-01 |
| elderly-license-revocation | 2026-08-21 | 2026-08-20 |
| fukushuto | 2026-08-24 | 2026-08-31 |
| koshitsu-tenpakai | 2026-08-20 | 2026-09-01 |
| bukatsu-chiiki | 2026-09-02 | 2026-09-02（照合が読んだのは08-26まで） |

### やること

1. **増えた146意見を読み足す。** 7主張それぞれの候補を洗い直し、実際にその主張を
   事実として述べている投稿だけを `data/bukatsu-chiiki_claim_posts.json` に追記する
   （`FACT_CHECK_GUIDE.md`「データを追加したときの扱い」）。願望・提案・仮定は外す。
2. **公開データ契約に「照合が対象にした期間」を持たせる。**
   `claim_verification` に `covered_period`（`{"start","end"}`）を追加し、
   `schemas/public-theme.schema.json` と `quality/designs/reaction-planet-renewal.md` 14章を更新する。
   `checked_on`（確認日）だけでは、どの範囲の投稿を読んだのかが読者に伝わらない。
   7テーマぶん埋める（既存6テーマは確定日時点の期間を入れる）。
3. **ずれたら止まる検査を足す。** `covered_period.end` がテーマの `collection_period.end` より
   前なら NG にし、テストで固定する。これが無いと定期更新のたびに再発する。
4. **既存6テーマの読み直し範囲はオーナーに確認する。** まず検査を警告として入れて一覧を出し、
   どこから読み直すかを決めるのが現実的。

## 3. マージ手順（そのままマージしない）

1. 共有ツリーの main が緑であることを確認する（`--against-private` を1回）。
2. `task/planet-stage3` の作業ツリーで `git merge main`。衝突は取り込むだけにする。
3. 生成物は手で直さず `python3 scripts/build_public_registry.py --all` で作り直す。
4. `python3 scripts/build_data_sheet.py` も回す。
5. ゲート一式（`verify_claim_verdicts` / `verify_public_registry` 2モード /
   `verify_theme_page bukatsu-chiiki` / `verify_number_provenance` / `verify_top_page` /
   `python3 -m unittest discover -s tests`）。
6. `release` スキルに従ってマージ・push。非公開正典のrsyncを飛ばさない。

## 4. 記録の更新漏れ

### 4-1. `company/HANDOFFS.yaml` が段階3のまま

`website-reaction-planet-renewal` の `next_action` が「工程表の段階3。部活動地域移行の主張5〜8件を…」
のまま。次のセッションが段階3をやり直す。`current_state` に段階3完了（主張7件・確定30件・
fact2 / gap4 / miss1・確認者 `editorial_review`）を書き、`next_action` を段階4（沈んだ大陸）へ更新する。

### 4-2. `THEMES.yaml` の notes に新設スクリプトの理由が無い

`FACT_CHECK_GUIDE.md` 手順9は「既存の生成スクリプトを共有できないかを先に検討し、
できない理由があるときだけ新設して、その理由を `THEMES.yaml` の notes に書く」と定めている。
`scripts/build_bukatsu_process_sections.py` は他6テーマと違いHTMLを書き換えない特殊な形なので、
その理由（段階7で惑星ページとして作り直すため）をnotesに1〜2文で残す。

## 5. 中身への指摘

### 5-1. 中体連の細則PDFの出典が第三者サイト（要差し替え）

`chutairen-entry`（判定 `fact`）の根拠が `https://www.fukui-jpa.com/data/saisoku061011.pdf`。
文書自体は日本中学校体育連盟の細則（令６日中体発第305号）だが、掲載元は福井県の団体サイトで
発行機関の公式掲載ではない。`FACT_CHECK_GUIDE.md` 手順5は「省庁・自治体・裁判所・国会・公的統計のみ」。
日本中学校体育連盟の公式掲載URLへ差し替える。見つからない場合は、発行機関の公開URLが
存在しないため転載を参照した旨を `note` に明記し、手順5の例外として `FACT_CHECK_GUIDE.md` に
1行足す（勝手な例外にしない）。

### 5-2. 主張と論点の結び付けが、投稿の分類論点と食い違う（段階6の前に決める）

確定30件を正典の分類と突き合わせた実測。

| 主張 | 結び付けた論点 | 実際の投稿の論点 |
|---|---|---|
| `original-deadline` | 制度 | 制度4 |
| `national-funding` | 費用・制度 | 費用2 / **教員2** / 制度2 |
| `coach-pay` | 受け皿 | 受け皿7 / **教員1** |
| `shidoin-role` | 受け皿 | **制度2** / 受け皿1 / **教員1** |
| `chutairen-entry` | 教育 | 教育2 / **制度2** |
| `club-cost-survey` | 費用 | 費用3 |
| `kyushokuchoseigaku` | 教員 | 教員1 |

「主張が何についての話か」（編集判断）と「その投稿がどの大陸に住んでいるか」（分類）は別物。
段階6で大陸を fact / gap / miss で塗ると、色のついた大陸に該当投稿が居ないという見た目の矛盾が起きる。
設計書3.3に、どちらを採るか（または両方を持つか）を1行で決めてから段階6へ進む。

### 5-3. 判定の偏り（オーナー判断）

採用7件の内訳は gap 4 / fact 2 / miss 1。9件から2件落としており、落としたのは
「令和13年度末までが期限」（fact）と「2027年度に約77%の自治体で実施」（fact）で、どちらも `fact`。
手順4の「3〜7つに絞る」の範囲内で理由も記録されているが、結果として
「SNSの言い分は資料と食い違う」側に寄って見える。
案として、`original-deadline`（gap）のカードに同じ工程表の話として
「ただし2027年度には約77%の自治体で実施見込み」（fact）を併記する。カード枚数を増やさずに、
資料が示す前向きな事実も同じ場所で見せられる。

### 5-4. 判定と表示文言の対応に検査が無い（段階7の前に）

`FACT_CHECKS` の各カードが `verdict`（fact/gap/miss）と `verdict_label`（「公表資料で確認できた」等）を
両方持つが、`verdict_label` は公開JSONにもページにも出ておらず、対応が正しいかを見る検査も無い。
段階7でページに出す前に、対応表を1か所に置いてテストで固定する。

### 5-5. 軽微

- 下書き `quality/research/bukatsu-chiiki-stage3-claims-draft.md` のBC-3は論点を
  `bukatsu-chiiki-hiyo` のみとしているが、実装は費用＋制度の2つ。記録を実装に合わせる
- `scripts/build_bukatsu_process_sections.py` はどのゲートからも実行されない
  （`verify_builder_rebuildability.py` の対象は `build_bukatsu_arena.py`）。確定データだけ直して
  再生成を忘れると `verify_claim_verdicts` が落ちるので事故にはならないが、
  `DATA_REFRESH.md` に「部活動は照合ファイルの再生成が要る」を1行足しておく

## 6. 良かったところ（維持する）

- 候補176件 → 確定30件（17%）。キーワード件数をそのまま使っていない
- 確定30件は全件が正典に実在し、全件が意見。重複IDは1件のみ
- `miss` を消していない（1件）。手順6の「空振りが人の作業の証拠」を守っている
- 公開HTMLを1バイトも変えていない。段階1の約束を守っている
- 件数1件の `kyushokuchoseigaku` を残した判断は手順4に合致（投稿が前提にしている数字を優先）
- 「その他」へ主張を結び付けていない。判定語も fact / gap / miss のみ

## 7. オーナーに決めてもらうこと

1. 2章-4 の既存6テーマの読み直し範囲
2. 5-3 のカード構成
3. 5-1 で公式URLが見つからなかった場合の扱い
4. `editorial_review`（確認者種別）の定義を設計書に明記するか。現在の定義は
   「本文を1件ずつ読んで確定」だが、誰が読んだのかが書かれていない。サイトの売りが
   「人が読んで編集した」である以上、言い方を先に固めるほうが安全

## 8. 次の1アクション

段階3の作業ツリーで main を取り込み、増えた146意見を7主張について読み足す。
そのうえで公開JSONを作り直し、ゲートを通してから `release` スキルでマージ・pushする。
