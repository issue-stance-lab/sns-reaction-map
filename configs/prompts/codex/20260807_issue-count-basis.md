## タスク: 論点カード件数の集計基準（basis）の定義と統一

### 出典
- `issue_card_counts.py` の `basis` フィールド (`all` vs `opinion`)
- テーマ設定 `configs/{theme}-reaction-map.json`

---

### 背景・目的
`configs/{theme}-reaction-map.json` の `issue_counts.basis` は、論点カードに表示する件数を集計する際の対象レコード範囲を定義する。
- `"all"`: 正典ファイル内の `main_issue` を持つすべてのレコード（ニュース共有や中立等を含む）
- `"opinion"`: 正典ファイル内で `is_opinion == true` かつ `main_issue` を持つレコードのみ

全テーマにおいて集計基準 `basis` と正典スキーマ、ページ上の解説・注意書きとの矛盾が生じないよう、明確な決定ルールを整理・統一し、検証を自動化する。

---

### やること

1. **各テーマの `configs/{theme}-reaction-map.json` における `basis` の点検**
   - 各テーマの正典データにおける `is_opinion` の有無・割合の確認
   - カード表示件数とページ本文の件数表示（「全○件 / 意見○件」）の整合確認

2. **`issue_card_counts.py` および `sync_issue_counts.py` の検証・改修**
   - `basis` の指定通りに正確に集計されることをユニットテストで保証
   - 不整合があるテーマの設定調整

3. **`verify_theme_page.py` の検証強化**
   - カード件数と `basis` の集計結果が常に100%合致することを保証

---

### 完了条件
- [ ] 全テーマの `configs/{theme}-reaction-map.json` で `issue_counts.basis` が明確に定義されている
- [ ] `python3 scripts/sync_issue_counts.py` で全テーマが正しく同期される
- [ ] `python3 scripts/verify_theme_page.py` が全テーマで exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
- [ ] `tests/test_verification_data.py` または関連テストがパスする
