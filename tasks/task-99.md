# 課題99: 「クレーム監査（主張の事実確認）」の照合遅れ警告を運用に組み込む

**状態**: 進行中。運用ルール化・自動検知は実装済み。高齢者・副首都・消費税は読み直し済み
**優先度**: 中（検査は失敗していないため急ぎではないが、放置すると際限なく遅れが広がる構造）
**次にすること**: 新たな30日超の警告が出たテーマを次回定期更新で読み直す
**判断待ち**: なし（基準は決定済み）
**関連テーマ**: 全9テーマ（現時点で30日超の未対応なし）

---

## 経緯

オーナーから「主張の事実確認（クレーム監査）が9/13時点のままで、9/18までのデータに
追いついていない」という警告について調査依頼があり、2026-09-26に調査した。

### 警告の仕組み

`scripts/verify_claim_verdicts.py` の `coverage_warnings()` が出している。各テーマ
4〜8件の代表的な「主張」について、一次資料（法令・議事録等）と照らし合わせて該当する
SNS投稿を人が1件ずつ確定する作業（`data/{theme}_claim_posts.json`）に対し、

- **確認日 `checked_on`**: この照合作業を最後にした日。テーマごとのページ生成スクリプト
  （例: `scripts/build_constitutional_process_sections.py`）にリテラルとして書き込まれている
- **公開データの期間末 `collection_period.end`**: 投稿データの収集を終えた最新日。
  定期更新のたびに進む

「確認日が期間末より前」なら、「新しく増えた投稿の中にこの主張へ当てはまるものが
増えているかもしれないが、まだ人が見ていない」として警告を出す。**ただしスクリプトは
意図的に終了コードを変えない**（`return 0` のまま）。docstringに「読み直しの範囲は
オーナー判断が要るため、ここでは止めずに警告だけ出す」と明記されている。

### 9テーマ全部で構造的に発生する

定期収集のたびに期間末は進むが、確認日は人が主張を読み直した日にしか進まない。
2026-09-26時点で9テーマ全部に警告が出ていた（`python3 scripts/verify_claim_verdicts.py`
の実行結果、終了コードは0のまま）。

| テーマ | 確認日 | 期間末 | 遅れ |
|---|---|---|---|
| koshitsu-tenpakai | 2026-09-13 | 2026-09-17 | 4日 |
| constitutional-amendment | 2026-09-13 | 2026-09-18 | 5日 |
| school-nickname-ban | 2026-09-12 | 2026-09-20 | 8日 |
| henoko-student-accident | 2026-09-13 | 2026-09-23 | 10日 |
| bukatsu-chiiki | 2026-09-02 | 2026-09-21 | 19日 |
| bike-blue-ticket | 2026-08-16 | 2026-09-12 | 27日 |
| fukushuto | 2026-08-24 | 2026-09-24 | 31日 |
| elderly-license-revocation | 2026-08-18 | 2026-09-20 | 33日 |
| consumption-tax-cut | 2026-08-19 | 2026-09-24 | 36日 |

（上表は2026-09-26時点の実行結果。定例更新が進むたびに日数は変わるので、着手時に
`python3 scripts/verify_claim_verdicts.py` を再実行して最新値を使うこと）

### なぜ今までTASK_BOARDに載っていなかったか

セッション開始時に必ず実行する `python3 scripts/build_admin_dashboard.py`
（`OPERATIONS.md`「遅れの見つけ方」）の検知一覧に、この警告は入っていない。
`run_public_checks.py` 経由で `verify_claim_verdicts.py` を実行しないと見えないため、
個別テーマの作業記録（例: `themes/constitutional-amendment.md` の2026-09-25の記述）で
「他8テーマにも同時に出ている既知の遅れ」と触れられていた程度で、追跡課題化されて
いなかった。`verify_claim_verdicts.py` 内のコメントが「TASK_BOARD.md 課題54
『未着手（レビュー指摘）』を参照」と書いているが、現在の課題54は「進行中」で別内容
であり、このコメントは古い（要修正）。

詳細は調査時のメモ: [[reference_claim_verdicts_coverage_warning]]
（`/Users/studio/.claude/projects/.../memory/reference_claim_verdicts_coverage_warning.md`）。

## 実害の性質

「表示が壊れている」わけではない。主張ごとの「一致した投稿件数」
（`matched_post_count`、公開ページの「資料との照合」パネルに表示）が、実際にはもっと
投稿が増えているのに古いまま止まっている可能性がある、という性質の遅れ。新しい投稿が
既存の主張に当てはまるかどうかは人が読まないと分からないため、自動では解消できない。

`OPERATIONS.md`の「一次資料メモの再確認」（`quality/research/status.yaml`の
`last_verified`、90日ごと）とは別物。あちらは「一次資料そのものが変わっていないか」の
確認で、これは「新しく増えた投稿が既存の主張に該当するかどうか」の確認。

## 2026-09-28：30日基準の運用ルール化・自動検知を実装

オーナーが「30日以上遅れた基準で進めて」と決定したため、以下を実装した。

1. `scripts/verify_claim_verdicts.py`に`COVERAGE_WARN_DAYS = 30`定数と
   `coverage_findings()`関数を新設。既存の`coverage_warnings()`（全テーマ・遅れ日数の
   大小を問わず出す、`run_public_checks.py`向け）はそのまま維持しつつ、内部の日数計算を
   `_coverage_gaps()`へ共通化し、`coverage_warnings()`の文言にも遅れ日数を追加した。
   `coverage_findings()`は30日以上のテーマだけを`{tone: "warn", title, detail}`形式で返す
   （`verify_reread_headroom.py`の`headroom_findings()`と同じ形）
2. `scripts/admin_dashboard/actions.py`の`anomalies()`に`coverage_findings()`を
   `headroom_findings()`と同じtry/exceptパターンで接続。管理ダッシュボード
   （`build_admin_dashboard.py`）の「気になる変化」に自動で出るようになった
3. `OPERATIONS.md`「遅れの見つけ方」の検知一覧に1行追加
4. `verify_claim_verdicts.py`内の古いTASK_BOARD参照コメント（課題54を指していた）を
   課題99へ更新
5. `tests/test_claim_verdicts.py`に`test_coverage_findings_only_include_themes_over_threshold`
   を追加（29日は出ない・30日ちょうどは出る・45日は出る、をmockデータで確認）

**確認済み**: `python3 scripts/verify_claim_verdicts.py`（exit 0、30日以上3件を明示）、
`python3 scripts/build_admin_dashboard.py`で実際に3件が「気になる変化」へ出力されることを
HTML出力で確認、`tests/test_claim_verdicts.py`全6件・`tests/test_admin_dashboard.py`全87件OK。

**未実施**: fukushuto・elderly-license-revocation・consumption-tax-cutの3テーマ、
実際の主張の該当件数の読み直し自体。対象件数の見積もりもまだ。次回のそれぞれの定期更新
（課題69の型）に合わせて着手する。

## 2026-09-30：高齢者免許返納の遅れを解消

定期更新で採用した新規意見27件を既存7主張と全件照合した。「地方はバスで生活できない」に
当たる3件を追加し、主張該当投稿は46→49件になった。ほか6主張への新規追加はなかった。
`data/elderly-license-revocation_claim_posts.json`、公開検証データ、ページ生成スクリプトの確認日を
2026-09-30へ更新し、公開データの期間末へ追いついた。残る30日超の対応対象は
fukushuto・consumption-tax-cutの2テーマ。

## 2026-10-03：副首都の遅れを解消

10月3日の新規283投稿を照合し、本文確認後の新規意見226件を含む累積2,138意見に対して5主張の該当投稿を確認した。住民投票二度否決は4→10件、採決差は5→8件。附帯決議の同日実施禁止解釈は、主張を否定する2投稿を除外して2件とした。残る2主張は件数据え置き。候補manifest `26aaceb6e761d761da619b2e78d2a7edb28b7f1825bc464b73623bf980d0a2fb` に反映し、独立品質監査で `ready_for_ceo` と判定された。

同日、消費税減税も別担当が読み直したため、30日以上遅れている残件はない。

## 2026-10-03：消費税減税の遅れを解消

定期更新で追加する新規意見483件を既存6主張と全件照合した。レジ改修1件、
5兆円の必要額4件、食料品から先行する案4件を追加し、ほか3主張への追加はなかった。
別担当が483件を再監査し、初回の見落と4件を追加、誤採用は0件だった。
`data/consumption-tax-cut_claim_posts.json`、公開検証データ、ページ生成スクリプトの確認日を
2026-10-03へ更新。副首都も同日読み直したため、30日超の未対応はない。
