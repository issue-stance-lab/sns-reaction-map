# 課題77・皇室典範テーマ連動表示の品質確認

**対象**: `koshitsu-tenpakai`
**確認日**: 2026-09-27
**判定**: `ready_for_ceo` → 公開済み

## 結論

皇室典範ページを、公開済み消費税版の読み順に合わせて公開版へ移植した。立場5種・論点6種・資料照合6件・資料にしかない話4件・共通の心配1件・制度確認3件を、ページ内のIDで読書面へ接続している。年表は複数論点にまたがるため、無理な論点タグ付けはしていない。

既存の投票24選択肢、出典URL、確認日、授業・印刷導線、JavaScript無効時の静的本文は維持した。通常更新の `scripts/refresh_planet_section.py` と皇室典範専用の `scripts/build_koshitsu_arena.py` の両方から、同じ接続表示を再適用できる。

## 検査結果

| 検査 | 結果 |
|---|---|
| `python3 scripts/build_koshitsu_arena.py --check` | OK。正典再生成後も候補と一致 |
| `refresh_planet_section.refresh('koshitsu-tenpakai')` | OK。通常更新ルートの出力が候補と完全一致 |
| `python3 scripts/verify_theme_page.py koshitsu-tenpakai` | OK。6論点・立場別内訳・母数を照合 |
| `python3 scripts/verify_number_provenance.py koshitsu-tenpakai` | OK。285件の数字をすべて説明可能 |
| `python3 -m unittest tests.test_koshitsu_connected tests.test_koshitsu_adapter tests.test_koshitsu_page_candidate` | 20件 OK |
| Chromium: 320 / 375 / 1280px × 6論点 × 6状態 | 各36通り、横はみ出し0、ページエラー0 |
| 資料3タブ・資料にしかない話・一次資料クイズ | OK。クイズ6問の1→2問目遷移を確認 |
| JavaScript無効 | 旧論点カード・背景本文が表示され、ページ題名を確認 |
| スクリーンショット比較 | 同じ1280px・全体状態・第1論点で参照版と並べて確認 |

比較画像:

- [消費税・1280px](2026-09-27-task77-koshitsu/tax-layout-1280.png)
- [皇室典範・1280px](2026-09-27-task77-koshitsu/koshitsu-layout-1280.png)
- [皇室典範・375px](2026-09-27-task77-koshitsu/koshitsu-layout-375.png)
- [皇室典範・ページ全体](2026-09-27-task77-koshitsu/koshitsu-page-375.png)

## 変更範囲

- `docs/koshitsu-connected.js` / `docs/koshitsu-connected-page.js` / `docs/koshitsu-connected.css`
- `scripts/koshitsu_connected.py` / `scripts/koshitsu_connected_content.py`
- `scripts/templates/koshitsu_connected_bridge.js`
- `scripts/build_koshitsu_arena.py` / `scripts/refresh_planet_section.py`
- `data/verification/koshitsu-tenpakai-background.json`（制度確認3項目へ論点IDを付与）
- `docs/koshitsu-tenpakai-reaction-map.html`（候補を有効化）
- 皇室典範専用の接続テストとブラウザー回帰テスト

## 公開記録

オーナーの「公開して」を受け、最新mainへ取り込み後、公開前の投票・数字・差分検査、CI、本番URLの表示・選択動作・トップページを確認した。
