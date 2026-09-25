# 辺野古「政治利用・基地問題」追い読み（2026-09-24）

2026-09-23定期収集分で増えた本論点の未読投稿39件（読み飛ばし0・読了後増分39、
未読合計34%・上限40%）を対象に、独自性検査の上限に達する前の追い読みとして実施。

## 対象・方法

- 対象: `manage_reread_registry.py prepare --topic henoko-student-accident --issue 政治利用・基地問題`
  で固定した39件（固定対象: `.staging/reread/henoko-base-politics-target.json`）
- 方法: 39件全件、本文を1件ずつ読み、既存の分類（`is_opinion` / `main_issue` /
  `stance`）が本文の主張と整合するかを確認したうえで、テーマ固有の内訳区分
  （`politics-links` 活動団体・政党・教育機関への批判と関係／`politics-base`
  基地政策・反対運動の是非／`politics-double` 批判する側にも説明と反省を求める／
  `politics-election` 事故対応を選挙や政治家の評価につなげる）へ分類した。
  自動判定プログラムへの置き換えは行っていない。
- 対象期間の性質: 39件はいずれも2026年9月の沖縄県知事選（現職敗北）前後の投稿で、
  事故そのものより選挙・政党評価の文脈で事故を引き合いに出す内容が中心だった。

## 結果

- 39件すべて `is_opinion=true`・`main_issue=政治利用・基地問題`・
  `stance=論点を切り分ける`（文科省判断そのものへの賛否を明示した投稿は0件）で、
  既存分類との不一致・誤分類は見つからなかった。修正は0件。
- 内訳区分の新規追加内訳: `politics-election` 20件／`politics-double` 12件／
  `politics-links` 4件／`politics-base` 3件。
  （更新後の論点内訳: politics-links 33件／politics-base 6件／
  politics-double 39件／politics-election 37件、合計115件）

## 完了確認（抜き取り）

39件のうち10件（tweet_id末尾が偶数の投稿から機械的に選定）を、記録した要約・
判定理由が本文の内容と一致しているかを別途読み直し、いずれも一致を確認した。
サマリのユニーク率100%（39件で文言重複なし）、抽出マーカー（`START`/`END`等）の
残留も0件。

## 記録先

- 共通台帳: `data/verification/reread/henoko-student-accident.json`
  （`manage_reread_registry.py record` で反映）
- テーマ固有の内訳ファイル: `data/henoko-student-accident_issues-reread.json`
  （`items` へ39件追加、`buckets.政治利用・基地問題` の件数を更新）
- 機械可読の判定結果（本文なし）: `2026-09-24-henoko-base-politics-reread.json`
  （tweet_id・区分・判定理由のみ。投稿本文は含まない）

## 副産物: `resync-source` の既存バグを発見・修正

上記の記録作業中、`scripts/manage_reread_registry.py` の `resync_source` /
`initialize` が、継承元ファイルの投稿から `item['tweet_id']` を無条件に読む
実装になっており、`post_key` のみを持つ形式（辺野古・constitutional-amendment・
koshitsu-tenpakai・school-nickname-banの4テーマが該当）に対して必ず
`KeyError: 'tweet_id'` で落ちることを確認した（変更前の未変更ファイルに対して
再現、このバグは今回の変更とは無関係の既存不具合）。`resync-source` を参照する
既存テストが0件だったため、このスキーマ差異が検出されずに残っていたとみられる。

`post_key` があればそれを直接使い、無ければ `tweet_id` から導出するよう修正
（`scripts/manage_reread_registry.py`）。回帰確認として `tests/test_manage_reread_registry.py`
に4件のテストを追加: post_key形式での成功、tweet_id形式（bukatsu-chiiki等）が
従来どおり動くことの回帰確認、不一致の拒否、`initialize`のpost_key形式対応。
既存58件を含め全件成功を確認。

**他3テーマ（constitutional-amendment・koshitsu-tenpakai・school-nickname-ban）
への横展開・影響確認は未実施**（今回の作業範囲外）。それぞれの継承元ファイルで
`resync-source` を試すと同じ理由で落ちていた可能性があるが、いずれのテーマも
今回時点で `resync-source` を実行した形跡はなく、実害（公開データへの影響）は
確認していない。
