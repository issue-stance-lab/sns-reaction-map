# 課題77 高齢者免許返納・連動表示の内容契約と画面移植計画

記録日: 2026-09-26。参照版は公開済みの消費税減税の連動表示。対象は `elderly-license-revocation-reaction-map.html`。

## 工程1: 内容の接続表

件数・割合・確認日はページ内の `PLANET_DATA` を唯一の表示元にする。投票の保存番号は山の表示順と分離し、既存の `vote_issue_order` を維持する。

| 論点ID・名称 | 再読状態・理由ID | 理由別X投稿 | 制度・照合・資料側項目 | 図解 | 確認日 | 投票順 |
|---|---|---|---|---|---|---|
| `elderly-license-revocation-safety` 義務化・事故防止 | 再読済み。A〜H、未読52件 | A〜Hを各1件、`configs/elderly-license-reason-posts.json` から表示 | 主張 `increase` `rate`。資料側 `sc-1` `sc-3` | `gizuka-v2` | 主張2026-08-18、資料側2026-09-12、再読は更新台帳の値 | 1 |
| `elderly-license-revocation-mobility-rights` 地方の足・移動権 | 再読済み。A〜G、未読6件 | A〜Gを各1件 | 主張 `transit`。資料側の論点紐付けなし | `chiho-v2` | 主張2026-08-18、再読は更新台帳の値 | 2 |
| `elderly-license-revocation-assessment` 適性検査強化 | 未再読 | 理由別投稿は作らない。論点別の既存代表投稿は重複表示しない | 主張 `renewal` `skilltest` | `tekisei-v2` | 主張2026-08-18 | 3 |
| `elderly-license-revocation-alternative-transport` 代替交通整備 | 未再読 | 理由別投稿は作らない | 主張 `transit`。資料側 `sc-2` | `infra-v2` | 主張2026-08-18、資料側2026-09-12 | 4 |
| `elderly-license-revocation-voluntary-return` 自主返納支援 | 未再読 | 理由別投稿は作らない | 主張 `benefit` `legal`。資料側 `sc-4` | `jishu-v2` | 主張2026-08-18、資料側2026-09-12 | 5 |
| `elderly-license-revocation-other` その他 | 未再読 | 理由別投稿は作らない | 対応する主張・資料側項目なし | `sonota-v2` | なし | 6 |

再読データが存在するのは2論点だけである。未再読4論点を空欄のままにするのは欠落ではなく、AI分類を人の再読結果として見せないための仕様である。理由別投稿は再読項目と同じ `bucket` の投稿から1件を選び、要旨と元URLだけを公開する。

## 画面差分表（V01〜V12）

| ID | 高齢者免許での実装先 | 判定条件 |
|---|---|---|
| V01 | `docs/elderly-connected.js`、`docs/elderly-connected-page.js` | 冒頭の短い制度現状→立場・山・論点→読書面→年表・投稿比較→投票・授業の順にする |
| V02 | `docs/elderly-connected.js`、`docs/elderly-connected.css` | 4立場の操作を `#modes` へ集約し、PC4列・スマホ2列＋「すべて」全幅にする |
| V03 | `docs/elderly-connected.css`、`scripts/templates/elderly_connected_bridge.js` | 山の表示枠は通常210px・狭幅180px。非表示の海面下演出をviewBoxから除外する |
| V04 | `docs/elderly-connected.css` | 6論点をPC4列・スマホ2列のボタン格子にし、論点名と件数を別行にする |
| V05 | `scripts/templates/elderly_connected_bridge.js` | 選択立場の色1色、選択中0.9・他0.23、0件は点で残す |
| V06 | `scripts/elderly_connected_content.py`、`docs/elderly-connected.css` | 理由・投稿と主張・資料をPC左右、スマホ上下の読書面に置き、図解を小さな入口から開ける |
| V07 | `configs/elderly-license-reason-posts.json`、`scripts/elderly_connected_content.py` | 再読済み2論点だけ、理由IDに対応する要旨・Xリンクを表示する。未再読4論点は理由別投稿なしと明示する |
| V08 | `docs/elderly-connected-page.js` | 論点側の資料と、全体の「資料を読む／x投稿で語られない話／一次資料クイズ」を同じ資料欄に統合する |
| V09 | `docs/elderly-connected-page.js` | 旧 `#ocean`・`#issue-cards`・`#quiz` は通常画面で重複表示せず、新しい読書面・資料タブへ移す。出典リンクは保持する |
| V10 | `docs/elderly-connected-page.js`、`docs/elderly-connected.css` | 背景の長文は山の前から後へ移し、現状要約を山の前に残す。年表は日付タブにする |
| V11 | `scripts/templates/elderly_connected_bridge.js` | 立場変更は480msで補間し、連打時は最後の選択へ収束。初期着地・hashchange・キーボード・reduced motionを確認する |
| V12 | `scripts/refresh_planet_section.py`、`scripts/elderly_connected.py` | 通常更新後も連動表示を再適用。JS無効・印刷・授業印刷・投票18通り・GA4/OGP/Supabase保護を確認する |

## 旧セクションの移設先

| 旧要素 | 処置 | 新しい表示先・保持 |
|---|---|---|
| `#bukatsu-background` | 山の後へ移動。冒頭の現状だけを要約カードにする | 全5年表・本文・出典・確認日を保持。年表は日付タブ |
| `#fallback` | JavaScript無効・印刷用に保持。通常画面では新しい山と重複させない | 6論点の図解、件数、論点リンクを保持 |
| `#issue-cards` | 通常画面では非表示 | 再読済みの理由別投稿を読書面へ移し、既存の論点別投稿は重複させない |
| `#ocean` | 通常画面では非表示 | 4項目を論点読書面の資料側へ、同じ本文・出典・確認日で移す |
| `#quiz` | 資料3タブのクイズへ移動 | 主張7問、回答・結果・根拠を保持 |
| `#editorial` | 折りたたむ | 横断整理5件と2026-09-11の確認日を保持 |
| 潮目ウィジェット | 山の後段で保持 | 前回・今回の収集期間と「世論全体ではない」注意書きを保持 |
| `#vote-section`、授業節、関連テーマ、詳細データ、編集分析 | 位置を後段に残す | 投票のtopic・固定番号、授業リンク、計測、OGPを変更しない |

## 工程2以降の設計判断

- 画面の署名は、交通安全の緑・条件付きの黄・反対の紫・中立の灰を使った既存の4色と、道路標識のように「選択→確認」へ視線を誘導する角丸の小さなデータパネルに置く。新しい色や画像は追加しない。
- 高齢者テーマは4立場・6論点で消費税の7論点・5立場とは異なるため、列数と初期論点だけをデータから調整し、固定値を移植しない。
- 工程5では消費税と高齢者を1280/375/320pxで初期状態・立場選択後・論点選択後・資料タブ・後段まで同じ幅で比較する。機能表と外観表を分け、未確認を残したまま公開判断へ進めない。
