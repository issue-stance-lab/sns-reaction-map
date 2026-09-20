# 課題71: 海面より下（沈んだ大陸・地下水脈）のデータ品質を仕上げる

**登録日**: 2026-09-19
**状態**: 未着手
**優先度**: 中（`verify_ocean_layer.py` がCIに繋がっていないため公開は止まっていないが、
公開中の「語られていない争点」の裏付けデータが古いままの箇所がある）

## 何が起きたか

`scripts/verify_ocean_layer.py`（沈んだ大陸・地下水脈の検査）を単体実行すると、複数テーマでNGが出る
という報告を受けて調査した。原因を切り分けた結果、2種類の別々の問題だと分かった。

1. **検査スクリプト側の不具合（このセッションで修正済み）**: `koshitsu-tenpakai` は
   正規表現ではなく人が候補を読んで選ぶ新形式（`match_rule.type: "editorial_confirmation"`）を
   使っていたが、検査スクリプトがこの形式を知らず、無関係な「match_rule.pattern がありません」
   というNGを出していた。`verify_sunk_continents()` に type ごとの分岐を足し、
   `editorial_confirmation` を認識するようにした（`selected` の各ハッシュが正典に実在するかも検査する）。
   あわせて、`machine_hits` に生の tweet_id ではなく sha256 ハッシュが紛れ込んだときに
   はっきりしたエラーを出す防御も足した（次の2番の不具合を直接検出する）。
   再発防止のテストは `tests/test_ocean_layer.py` に追加済み（実データでのkoshitsu-tenpakai検査・
   全テーマのtype検査を含む）。

2. **データ側の未解決の問題（このセッションでは直していない、要判断）**:

   **(a) constitutional-amendment の「沈んだ大陸」2件が、現行の正典と照合できない。**
   `constitutional-amendment-challenge`（国民投票への異議申立手続き）と
   `constitutional-amendment-emergency-review`（参議院緊急集会の事後審査）の
   `match_rule.machine_hits` / `excluded` が sha256 ハッシュ（`record_id_hash()` 形式）で
   記録されているが、これは `type: regex` の設計（bukatsu-chiiki が実例。生の tweet_id で記録する）
   から外れている。さらに、記録されているハッシュのうち大半（challengeは6件中6件、
   emergency-reviewは6件中4件）が、現行の正典1,779件のどのレコードをハッシュ化しても
   一致しない＝現行データから再現できない状態になっている（2026-09-18に追加された最新2件は
   正しく再現できる。古い分だけがずれている）。中身が改ざんされた形跡ではなく、
   2026-09-12前後の判定以降にサンプルの重複整理か何かで対象の投稿が入れ替わった可能性が高いが、
   確証はない。`sns_count: 0` という結論自体が誤りだとは確認していない
   （現行データで同じ正規表現を再実行しても新たな一致は無い）が、**裏付けの再現性が崩れている**。

   **(b) 4テーマの「地下水脈」が実質空のプレースホルダのまま。**
   `constitutional-amendment` / `henoko-student-accident` / `koshitsu-tenpakai` /
   `school-nickname-ban` の `data/verification/{テーマ}-veins.json` は、いずれも水脈1本のみ
   （設計書3.3.3は1テーマ2〜4本必須）で、代表投稿の `tweet_id` が全側・全件 `None`（未設定）。
   `shared_concern`（共有している具体的な懸念）の文章自体は書かれているが、それを裏付ける
   実在の投稿IDが1件も埋まっていない。bukatsu-chiiki（2本、tweet_idも実在）だけが完成している。

   **2026-09-19追記**: ai-copyrightは元々`-sunk-continents.json`・`-veins.json`自体が
   存在せず（この4テーマとは別の「未着手」状態）、オーナー指示で新規作成した
   （沈んだ大陸4件・地下水脈2本、いずれも実データを検索・1件ずつ読んで確認、
   tweet_idも実在。`verify_ocean_layer.py`のai-copyright分はNG0件）。bukatsu-chiikiに
   加えて、地下水脈を1本から2〜4本へ増やす際の実例として参照できる。

   **2026-09-20追記（検査スクリプトのバグを発見・修正）**: fukushutoの「資料にしかない話」
   新設（オーナー指示）に着手した際、`scripts/verify_ocean_layer.py`の`find_theme_files()`が
   `veins_path.exists()`を必須にしており、**地下水脈(veins)を持たず沈んだ大陸(sunk-continents)
   だけを作ったテーマが検査から丸ごと抜け落ちる**バグを発見した（`build_ocean_layer()`
   （`scripts/public_registry_common.py`）は元から両方を独立に扱う設計で、この非対称は
   検査スクリプト側だけの欠陥だった）。どちらか一方だけでも対象にするよう修正し、
   `tests/test_ocean_layer.py`に再発防止テストを追加した。

   この修正により、**bike-blue-ticketの`-sunk-continents.json`も初めて検査対象になり、
   (a)と同型の新しい不一致を検出した**: `bike-blue-ticket-sc-1`の`machine_hits`に記録された
   2件のtweet_idのうち1件（`2086098880874311993`）が、現行の正典に対して同じ正規表現を
   再実行しても見つからない。elderly-license-revocationの`-sunk-continents.json`は
   同じ検査で新たにNG0件と確認できた（veins無しでも中身は正しく再現できている）。
   `bike-blue-ticket-sc-1`の不一致は今回のセッションでは調査・修正していない。次に着手する
   セッションは、(a)のconstitutional-amendment分と同じ手順（現行正典への同条件語での
   再ヒット→本文を実際に読んで除外理由を書き直す。再現できないという理由だけで
   `sns_count`を変更しない）で対応すること。

   **2026-09-20追記**: consumption-tax-cutも同じく`-sunk-continents.json`・
   `-veins.json`自体が存在しない「未着手」状態だった（オーナーから「他のテーマにはある
   『資料にしか無い話を見る』が無い」と指摘され着手）。大綱（内閣、令和8年9月15日閣議決定）
   を一次資料に、沈んだ大陸4件・地下水脈2本を新規作成。いずれも正典3890件を正規表現で
   検索した上で、ヒットした投稿を1件ずつ本文で読んで除外理由を書いた（要約・理由の
   使い回しはしていない）。`verify_ocean_layer.py`のconsumption-tax-cut分・
   `verify_adoption_registry.py`ともNG0件、標準検査4種・unittest 984件・
   `run_public_checks.py`もNG0件。ai-copyright・bukatsu-chiikiに加えて3件目の
   完成例になる。

## 対応方針の案（次のセッションへの申し送り）

(a)(b) とも、一次資料や正規表現の話ではなく「実際の投稿を読んで人が判断する」編集作業そのものなので、
このセッションでは代筆・推測での穴埋めをしていない。

- **(a)**: 現行の正典に対して同じ条件語（`訴訟|裁判|異議`／`緊急集会`）で再度ヒットを取り、
  該当する投稿本文を実際に読んで除外理由を書き直す（`checked_by: ai_assisted` のままでよい）。
  `machine_hits` は生の tweet_id 形式に揃える。再現できないという理由だけで `sns_count` を
  変更しない（本文を読んだ上で判断する）
- **(b)**: 各テーマの意見データから、対立する2立場が同じ具体的懸念を語っている箇所を
  編集部（AI可）が読み、設計書3.3.3の基準で水脈をあと1〜3本ずつ作る。または、
  「1本で足りる」と基準を見直すならオーナー確認を取り、`MIN_VEIN_COUNT` を変える

いずれも公開中のページ（海面より下のセクション）に関わる編集判断のため、
着手前に CLAUDE.md「オーナーへの説明のしかた」に沿って方針をオーナーに確認すること。

## 次にすること

優先度は中（CIを落としていない）。課題69・課題70などの優先作業が一段落してから着手する。
着手するときは、まず (a) constitutional-amendment の2件だけを直し、
`python3 scripts/verify_ocean_layer.py` で該当エラーが消えることを確認してから (b) に進む。

## 進捗

（未着手）
