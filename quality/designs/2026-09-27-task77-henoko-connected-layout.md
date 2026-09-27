# 課題77・辺野古テーマ連動レイアウト候補（2026-09-27）

## 状態

工程1〜5の候補を作成。`docs/henoko-student-accident-reaction-map.html` はこのブランチ上で有効化したが、mainへのマージ・本番公開はしていない。工程6はオーナー確認待ち。

辺野古ページには、論点別に公開してよい代表X投稿の台帳がない。そのため、投稿URL・投稿本文・投稿IDは生成せず、読書面には「投稿台帳がないため理由と投稿を推測で結びつけない」と明記した。既存の集計値、投票定義、潮目ウィジェット、静的本文・印刷用の旧節は保持している。

## 内容の接続表

| 論点 | 理由別内訳 | 資料照合 | 資料にあり投稿に見当たらないこと | 年表・確認事項 | 横断整理 |
|---|---|---|---|---|---|
| 安全管理・事故原因 | 6区分＋未読12 | school-escort / weather-advisory / unregistered-service | 4項目 | 年表全9件＋operator / alternative / briefing | safety vein＋編集部5件 |
| 政治利用・基地問題 | 4区分 | なし | なし | findings | なし |
| 報道・行政対応 | 3区分＋未読24 | なし | なし | findings / diet-nhk / prefecture-inquiry | なし |
| 追悼・被害者の尊厳 | 4区分＋未読14 | なし | なし | accident / findings | なし |
| 政治的中立性 | 5区分＋未読3 | education-finding / political-learning | なし | governor / diet-scope / diet-followup / views | なし |
| 平和教育の萎縮 | 4区分 | not-safety-only | safety vein 4項目 | notice / governor / diet-scope / briefing / views | safety vein |

年表9件と確認事項4件の接続先は、背景JSONへ未確認のissue_idsを追記せず、`scripts/henoko_connected.py`の接続表で固定した。安全論点には年表全件を残し、どの資料経緯も読書面から失わないようにした。

## 実装

- `scripts/henoko_connected.py`：有効化・接続表・冪等検査・投票定義を保つ橋渡し。
- `scripts/henoko_connected_content.py`：6論点のtemplate、理由件数、一次資料、年表、確認事項、横断整理を生成。
- `scripts/templates/henoko_connected_bridge.js`：立場変更と山の色、初期着地、hash再訪、読書面、GA4を接続。
- `docs/henoko-connected.js` / `docs/henoko-connected-page.js` / `docs/henoko-connected.css`：全体配置、3タブ、クイズ、画像拡大、モバイル・印刷を担当。
- `scripts/refresh_planet_section.py` と `scripts/refresh_adapters/henoko.py`：通常更新・潮目更新・再生成の最後に連動表示を再適用。
- `scripts/henoko_count_provenance.py` と `verify_number_provenance.py`：理由別件数、未読数、確認事項、資料側4件を正典照合。

## V01〜V12確認

| 項目 | 結果 |
|---|---|
| V01 論点・理由・資料の接続 | 合格。接続表を固定検査 |
| V02 立場・論点操作 | 合格。5モードを山と読書面へ接続 |
| V03 山の実サイズ | 合格。SVGのgetBBoxで実描画領域へ切り詰め |
| V04 即時の選択色・480ms動作 | 合格。選択色とreduced-motion分岐を実装 |
| V05 初期表示・hash再訪 | 合格。最大論点へ初期着地、論点IDを復元 |
| V06 理由別内訳 | 合格。未読分を別表示、出所検査あり |
| V07 資料3タブ | 合格。資料を読む／X投稿で語られない話／一次資料クイズ |
| V08 年表・確認事項・横断整理 | 合格。旧節の内容を読書面へ統合 |
| V09 旧節・静的・印刷 | 実装・静的検査合格。通常画面で整理し、JS無効・印刷CSSの旧節を保持。印刷実機は工程6で確認 |
| V10 GA4・キーボード | 合格。issue_view、citation_click、Esc戻り、button操作 |
| V11 票・保護要素 | 合格。投票18通り、GA/AdSense/Supabase/canonical/OGPを保持 |
| V12 生成・数値検査 | 合格。専用テスト7件、数字172件、theme検査OK |

## 検査記録

- `python3 -m unittest tests/test_henoko_connected.py -v`：7件 OK
- `python3 scripts/verify_number_provenance.py henoko-student-accident`：172件中172件を説明、NG 0
- `python3 scripts/verify_theme_page.py henoko-student-accident`：NG 0
- `node --check`：橋渡しJS・ページJS・補助JS OK
- ローカルHTTPで初期表示、読書面、資料タブ、一次資料クイズ、375px相当の折返しを目視確認。PC/320px、印刷、JS無効の実機確認は工程6に残す。

## 工程6の境界

本番公開はまだ行わない。オーナーが候補の見た目・文章・接続先を確認し、「公開して」と明示した時点で、release手順に従って工程6（merge、CI、公開URLでPC/375/320、印刷・JS無効、hash再訪）を実施する。
