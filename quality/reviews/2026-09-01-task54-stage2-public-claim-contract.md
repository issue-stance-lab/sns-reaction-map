# 課題54 段階2：照合データの公開契約

実施日: 2026-09-01  
判定: pass

## 実施内容

公開テーマJSONに `claim_verification` を追加した。

- 照合済み6テーマは、主張、`fact` / `gap` / `miss`、照合結果、一次資料URL、確認済み投稿数、確認日、確認者種別を持つ。
- 未実施4テーマは `not_started`、日付・確認者・主張は空として出力する。空欄の照合済みと区別できる。
- 投稿ID・投稿本文・AIの信頼度や内部理由は公開JSONへ出さない。

## 検査結果

- `python3 scripts/build_public_registry.py --all`: 公開10テーマとcatalogを再生成
- `python3 scripts/verify_public_registry.py --against-private`: 非公開正典との完全一致
- `python3 scripts/verify_public_registry.py --public-only`: Schemaと公開JSON内の整合
- 関連17テスト: 成功

## 次工程

部活動地域移行の一次資料照合を実施し、`not_started` を照合済みの記録へ置き換える（段階3）。
