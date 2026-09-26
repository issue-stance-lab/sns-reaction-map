# 課題77・自転車青切符の連動表示移植候補

記録日: 2026-09-25。対象: `bike-blue-ticket`。状態: 承認待ち候補（工程1〜5相当）。
公開ページ・投票・本番データはこの候補から変更していない。

## 内容の接続表

件数・立場・論点の正本はページ内 `PLANET_DATA`、制度メモは
`data/verification/bike-blue-ticket-background.json`、資料照合と資料側の項目は既存の
検証データを使う。理由別の投稿ID台帳はないため、架空の理由別投稿を作らず、既存の論点別代表投稿2件を
「論点全体の代表例」として表示し、その制約を読書面に明記した。

| 論点 | 再読・理由 | 代表投稿 | 制度確認 | 資料照合 / 資料側 | 図解 |
|---|---|---|---|---|---|
| `bike-blue-ticket-other` その他 | reread・5理由 | `issue-bike-blue-ticket-other` の既存2件 | `taisho`, `unyou`, `basho`, `menkyo` | 全体資料 `sc-3` | `sonota-v2` |
| `bike-blue-ticket-enforcement-support` 取締り強化賛成 | reread・16理由 | 既存2件 | `taisho`, `unyou` | `sc-2` | `torishimari-v2` |
| `bike-blue-ticket-infrastructure-first` インフラ整備優先 | reread・7理由 | 既存2件 | `basho` | `sc-4` | `infra-v2` |
| `bike-blue-ticket-rule-ambiguity` ルール曖昧・不信 | reread・5理由 | 既存2件 | `taisho`, `unyou`, `basho`, `menkyo` | `sc-1` | `ambiguity-v3` |
| `bike-blue-ticket-license-requirement` 免許制要求 | reread・9理由 | 既存2件 | `taisho`, `menkyo` | なし | `menkyo-v2` |
| `bike-blue-ticket-road-safety` 車道走行への不安 | reread・9理由 | 既存2件 | `basho` | なし | `sharido-v2` |

`sc-3` は特定論点へ帰属できないため、その他の読書面に「全体に関わる資料」として置き、横断タブにも同じ本文・出典・確認日で出す。
「資料にあり、収集投稿で見つからなかった」は、X全体に存在しないという意味ではない。

## 画面差分 V01〜V12

| ID | 候補での実装・判定 | 根拠 |
|---|---|---|
| V01 | 合格候補。現状カード→山・立場→論点4列→読書面→背景・潮目→後段の順に再配置 | `docs/bike-blue-ticket-connected-page.js`、スクリーンショット |
| V02 | 合格候補。立場操作を山上部へ集約し、立場3区分＋「すべて」をPC4列、狭幅2列＋全幅にした | `docs/bike-blue-ticket-connected.css` |
| V03 | 合格候補。山の表示高はPC210px、狭幅180px。海面下装飾を隠し、viewBoxを描画範囲へ補正 | `bike_blue_ticket_connected_bridge.js`、DOM寸法検査 |
| V04 | 合格候補。論点はPC4列、狭幅2列。論点名と件数を別行にした | `docs/bike-blue-ticket-connected.css` |
| V05 | 合格候補。選択立場の色・押下状態・選択山0.9/非選択0.23を同期 | Playwrightの立場切替検査 |
| V06 | 合格候補。PC左右、スマホ上下。理由・代表投稿・制度・資料・図解を同じ読書面へ接続 | 6論点×全立場の操作検査 |
| V07 | 仕様差を明記。理由別投稿IDがないため、論点全体の代表2件＋元リンクを表示 | 接続表・画面注記。架空の所属は作成していない |
| V08 | 合格候補。資料を読む／x投稿で語られない話／一次資料クイズの3タブ | Playwrightで4資料・3択を確認 |
| V09 | 合格候補。`#issue-cards`、`#ocean`、`#bukatsu-check`は通常画面で非表示、新読書面へ統合 | computed style検査、印刷CSSは旧本文を保持 |
| V10 | 合格候補。1280/375/320pxで横スクロールなし、山→論点→本文の順 | Playwright寸法検査・比較画像 |
| V11 | 合格候補。480ms変形、動きを減らす設定、キーボードの図解モーダルを確認 | bridge.js・Chromium検査 |
| V12 | 合格候補。静的テンプレート、JavaScript無効時の既存本文、投票・GA/AdSense/canonical/OGPを保持 | 保護タグ検査・既存ページ構造検査 |

## 更新・公開の境界

- `refresh_planet_section.py`の通常山更新経路と`refresh_adapters/bike.py`の候補生成の両方で、連動表示を最後に再適用する。
- 同じ入力への連動表示再適用、接続表、6論点の代表投稿2件、数値出所315件を検査した。
- bike adapter全体の実更新試験は、既存の未再読8件（188件中180件割当済み）で
  `build_bike_process_sections.py`が止まった。今回の移植コードの失敗ではないが、通常更新の工程5の完了条件として残す。
- オーナーが候補を確認して「公開して」と明示するまでは、mainへの反映、push、本番公開、公開後観察への移行は行わない。
