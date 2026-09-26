# 課題77・自転車青切符 連動表示候補の品質確認

確認日: 2026-09-25。判定: 承認待ち候補。公開・push・main反映は未実施。

候補識別子（SHA-256）: HTML `06f80f7eda981d908fac23675ada2940bc063038fb2134dceb26e79518ff9156`、CSS `de678bc9793212ea2a2ff4d6dd6fb6a685b9713cbdb56b1d14219f15031e6d23`、配置JS `3fe17e43ce9d47aef2bdb7ad2567a6401c84077a17ce96cd0148f51f69202057` / `dc090476a240d9b7f348be49c469c2f53559afd1fc231192a814b0a7df61dacd`。

## 実施した検査

| 区分 | 結果 |
|---|---|
| 接続・冪等性 | `python3 -m unittest tests/test_bike_blue_ticket_connected.py -v`、6件 OK |
| 数値出所 | `python3 scripts/verify_number_provenance.py bike-blue-ticket`、315/315 OK |
| ページ検査 | `python3 scripts/verify_theme_page.py bike-blue-ticket`、全項目 OK |
| Chromium / WebKit | `tests/test_bike_blue_ticket_connected_browser.cjs`で1280/375/320px、初期着地・6論点・読書面・資料4件・クイズ3択・横スクロール・JSエラーを確認。JavaScript無効時の静的本文も確認 |
| レイアウト | 横スクロールなし。山→論点一覧→読書面の順。PC4列・スマホ2列、資料欄PC左右・スマホ上下 |
| 保護範囲 | 投票定義、GA4/AdSense/canonical/OGP、既存の静的本文を保持 |
| 見本 | `.staging/task77-bike-connected/desktop-full.png`、`desktop-reading.png`、`mobile-full.png`、`mobile-reading.png` |

## 残っている確認

自転車の実更新adapterを既存の更新回で通したところ、移植とは無関係に
`build_bike_process_sections.py`が未再読8件（反対188件中、割当済み180件）で停止した。
未再読データを推測で補わず、`data/bike-blue-ticket_opposition_reread.json`への編集部確認後に、通常更新の冪等性を再実行する。

したがって現在は、工程1〜5相当の候補提示まで。工程6（承認・公開・本番URL確認）へは進めていない。
