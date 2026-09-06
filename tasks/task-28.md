# 課題28: sample_period の unknown を埋める

**状態**: 進行中（期間訂正を適用・公開確認済み。全11テーマのsample_period unknownは0件となり、完了整理待ち）
## 2026-09-06：適用・公開後の現在地

著作権のUTC6/22〜9/5、高市のUTC6/13〜8/19（日本時間6/14〜8/20併記）を正典・期間台帳・既存ページへ適用し、本番の期間表示と訂正履歴を確認した。全11テーマで `sample_period: unknown` は0件。旧6/27指定の履歴を残し、出所は `recovered_fetched_at_utc` とした。課題28のunknown解消は達成しており、残るのは完了記録の整理。自転車の履歴116件の補完は課題63、全テーマの日本時間統一は別の運用整理として扱い、本課題の未解消扱いにはしない。

承認は `approval-20260906-002`、訂正対応は `correction-20260906-001`（解決済み）。[適用・公開結果](../quality/reviews/2026-09-06-repair-adoption.md) / [独立監査](../quality/reviews/2026-09-06-repair-adoption-audit.md)。以下は承認前までの経緯（小項目表の進捗は最新）。

## 2026-09-06の候補検査結果

課題63で元の取得履歴と変換処理を照合し、著作権339件・高市140件の欠損を補完した。著作権は6/22〜9/5、高市は6/13〜8/19（どちらも保存日時のUTC日付）の訂正候補を作成し、既存期間検査・統合ページ検査に合格。出所は `recovered_fetched_at_utc` とし、新たなオーナー確認済みと装わない。

著作権の旧指定6/27は当時のオーナー発言を保存し、公開前に訂正案を提示する。高市の日本時間は6/14〜8/20で、候補に注記した。共有の期間台帳は未変更。高齢者114件の履歴修復候補も統合したが、既存owner_confirmed期間は維持。自転車と全テーマの日本時間統一は別作業のまま。

[期間の根拠](../quality/reviews/2026-09-06-period-review.md) / [単一候補の検査と保全](../quality/reviews/2026-09-06-repair-steps123.md)。以下は過去の調査経緯。

**概要**: S1 で THEMES.yaml に `sample_period`（収集期間）を追加したが、一部テーマが `unknown` のまま
**2026-08-13 訂正**: 対象は**6テーマではなく4テーマ**。bukatsu-chiiki・constitutional-amendment・
school-nickname-ban・henoko-student-accident はその後に埋まっており、記述が古かった
**対象（実測4件）**: ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi
**2026-08-13 対応済み**: 公開ページの表示を「取得期間: 記録なし」から
「未記録 — 収集期間の記録を始める前に公開したテーマ」へ変更した。信頼性の表示（代表投稿の確認）の
すぐ隣に「記録なし」と並ぶのが最も印象が悪かったため、理由を書く形にした。
ラベルは `scripts/x_embed.py` の `period_label()` に集約（それまで4か所に散っていた）
**残作業**: 値そのものの復元。**収集期間の始まりは復元できない**。正典に日付フィールドが無く、
`data/verification/updates/` の記録も最新の収集回しか残っていない
（ai-copyright 2026-08-03・08-09 / bike-blue-ticket 08-10（未昇格）/ takaichi 08-07 /
elderly-license-revocation 記録なし）。推測で埋めないこと
**手順**: 各テーマの `sample_file` のレコード内タイムスタンプ、または収集時の作業ログ・git log・`social-samples/*.md` から期間を特定する。**特定できない場合は推測で埋めず `unknown` のまま残し、ページ側で「取得期間: 記録なし」と正直に表示する**
**2026-08-02 対応済み（3件）**: `sample_file` の `fetched_at` が全件そろっている constitutional-amendment（2026-06-20〜2026-07-25）/ school-nickname-ban（2026-06-22〜2026-07-12）/ henoko-student-accident（2026-06-14〜2026-06-27）を確定し、ページの「取得期間: 記録なし」も書き換えた。bukatsu-chiiki はパイロットで確定済み。
**全11テーマ再検査**: 同じ基準を既に期間が入っていたテーマにも適用した。takaichi（276件中140件欠損）/ fukushuto（255件全件欠損）も `unknown` へ戻し、koshitsu-tenpakai は正典347件が全て7/26収集なので `2026-07-26` に修正した。現在の `unknown` は ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi / fukushuto の5件。
**機械検査**: `data/verification/sample-periods.json` に総数・日付あり・欠損・最小日・最大日だけを保存し、`scripts/verify_sample_periods.py` で全11テーマを検査する。個別投稿の取得日は公開しない。
**別件（課題29の一例）**: ai-copyright は `sample_period: "2026-06-10〜2026-07-26"` と書いてあったが、`sample_file` の `fetched_at` は最新が 2026-07-12（339件は欠損）。7/26に収集した452件は `sample_file` に入っておらず別ファイルにあるため、根拠のない期間を公開し続けず `unknown`／「記録なし」へ戻した。次回更新で累積を正典へ統合した時点で確定する。

**2026-08-16 対応**: ai-copyright の収集期間はオーナー確認により `2026-06-27` と登録した。
正典には取得日欠損が339件あるため、`sample_period_source: owner_confirmed` を明示し、
自動算出値と混同しない形で検査する。

**注意**: `sample_source` は全11テーマ「Yahooリアルタイム検索」で埋まっている。検索語（クエリ）は未記録なので、A-4 で表示するなら `sample_queries` フィールドの追加も併せて検討する
