# 課題63: 公開ファイル検査が非公開正典を読んで失敗する

**状態**: 完了（2026-09-06、`task/public-checks-failure` ブランチ）
**優先度**: 高（`main` の GitHub Actions が常に失敗する）
**判断待ち**: main への取り込みは CEO 承認待ち
**関連テーマ**: 公開前検査、課題62

## 原因

GitHub Actions の「公開ファイルの検査」は、投稿本文を含む非公開正典
`social-samples/` が無い状態で動く。課題62の変更により `tests/test_planet_data.py` が
部活動テーマの非公開正典を読むようになったが、`scripts/run_public_checks.py`
の除外一覧への追加が漏れていた。そのため、同じ `FileNotFoundError` で18件がエラーになった。

## 対応

`PRIVATE_DATA_TESTS` に `test_planet_data` を追加し、なぜ除外するかを一覧に記録した。
対象テストは手元の非公開正典がある環境で引き続き実行する。

## 確認結果

- `python3 scripts/run_public_checks.py`: 370件、失敗0（非公開データ無し）
- `python3 -m unittest tests.test_planet_data -v`: 56件、失敗0（非公開データあり）

公開ページと公開データは変更していない。
