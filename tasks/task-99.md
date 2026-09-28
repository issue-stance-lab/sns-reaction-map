# 課題99: 「クレーム監査（主張の事実確認）」の照合遅れ警告を運用に組み込む

**状態**: 未着手（2026-09-26発見・オーナー指示で登録）
**優先度**: 中（検査は失敗していないため急ぎではないが、放置すると際限なく遅れが広がる構造）
**次にすること**: 「どのくらい遅れたら読み直すか」の基準をオーナーに決めてもらう
**判断待ち**: オーナー（読み直しの頻度・範囲の基準）
**関連テーマ**: 全9テーマ（fukushuto・elderly-license-revocation・consumption-tax-cutが30日超で最優先候補）

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

## AI推奨（未実施・オーナー判断待ち）

1. 「30日以上遅れたテーマは、そのテーマの次回定期更新（`DATA_REFRESH.md`）に合わせて
   主張の該当件数も読み直す」を運用ルールとして`OPERATIONS.md`に追記する
2. 基準が決まり次第、`scripts/admin_dashboard/render.py`の検知一覧に
   `coverage_warnings()`の結果を追加し、`build_admin_dashboard.py`で毎回自動検知させる
3. `verify_claim_verdicts.py`内の古いTASK_BOARD参照コメントを本課題番号へ差し替える

いずれも未実施。実行するかどうか・基準の数値はオーナー判断待ち。
