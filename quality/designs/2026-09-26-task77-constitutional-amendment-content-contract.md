# 課題77 — constitutional-amendment 連動表示 内容確定書

作成: 2026-09-26。課題77の[連動レイアウト移植ガイド](2026-09-22-task77-connected-layout-rollout-guide.md)に沿った工程1の確定書。対象は`constitutional-amendment`。公開URL、論点ID、既存の投票保存形式は変更しない。

## 結論

憲法改正テーマは、現在の`PLANET_DATA`・再読データ・背景確認・旧ページの代表投稿と図解を材料に、1論点1読書面へ接続できる。新設した生成器は、件数や出典を別コピーせず、ページ内データと`data/verification/constitutional-amendment-background.json`を読み直して表示する。

今回の判断は次の3点。

1. 理由別の元投稿対応表は存在しないため、V07は「理由からX投稿へ」ではなく、論点全体の既存代表投稿を表示する。理由別投稿を作って補わない。
2. `nearest_issue_id`が無い資料2件（国民投票結果への異議、参議院の緊急集会後の手続き）は、論点へ推測接続せず、資料3タブのテーマ全体一覧へ残す。
3. 年表11件は論点タグが無いため、論点面へ推測配分せず、背景の日付切替としてページ全体で表示する。制度確認4件は内容を読み、`issue_ids`を付与して論点面へ接続した。

## 論点別接続表

| 論点ID | 表示名・件数 | 再読 | 理由表示 | 代表投稿 | 資料照合 | 資料にあり投稿で未確認 | 地下水脈 | 図解 |
|---|---|---:|---:|---:|---|---|---|---|
| `constitutional-amendment-general` | 📜 改憲全般・602 | 511読了 / 91未読 | 11（未読含む） | 2 | なし | なし | `constitutional-amendment-avoid-war` | あり |
| `constitutional-amendment-article9` | 🛡️ 9条・自衛隊・316 | 284 / 32 | 12 | 2 | 2件 | なし | なし | あり |
| `constitutional-amendment-emergency` | ⚖️ 緊急事態条項・237 | 199 / 38 | 12 | 2 | 1件 | なし | なし | あり |
| `constitutional-amendment-referendum` | 🗳️ 国民投票・広告・216 | 196 / 20 | 12 | 2 | 2件 | `sc-4` | なし | あり |
| `constitutional-amendment-procedure` | 🏛️ 政党・発議手続き・132 | 118 / 14 | 7 | 2 | 1件 | `sc-3` | なし | あり |
| `constitutional-amendment-deliberation` | 💬 情報・議論の質・54 | 51 / 3 | 8 | 2 | なし | なし | なし | あり |
| `constitutional-amendment-other` | ◯ その他・11 | 10 / 1 | 5 | **未登録を明示** | なし | なし | なし | あり |

件数・理由・出典の正典は、表示についてはページ内`PLANET_DATA`、理由の元記録は`data/constitutional-amendment_issues-reread.json`、背景は`data/verification/constitutional-amendment-background.json`、公開集計の再生成確認は`data/public/themes/constitutional-amendment.json`とする。

## 旧セクションの配置と扱い

| 旧要素 | 新レイアウトでの扱い | 保存する機能 |
|---|---|---|
| `#stance-glance` | 山の直前へ移動し、`#modes`と同じ状態へ接続 | 立場の件数・選択 |
| `#planet-block` / `#modes` / `#list` / `#panel` | 中心部分として連続配置 | 立場切替、山、論点選択、深いリンク |
| `#explainer-section` | 論点面の投稿例へ読み替え、通常画面の重複表示は隠す | 既存X投稿リンク・要約・埋め込み |
| `#bukatsu-background` | 山・読書面の後段。11件を日付タブで切替 | 年表本文・出典 |
| `#bukatsu-check` | 制度確認4件を論点面の資料欄へ接続 | 本文・出典・確認日 |
| `#ocean` | 通常画面では隠し、資料3タブで4件すべてを再利用 | タグ付き2件と、未接続2件のテーマ全体表示 |
| `#editorial` / `#article-trust` / `#meta` | 後段の折りたたみへ整理 | 編集・分析情報、更新日、出典情報 |
| `#quiz` | 資料タブ「一次資料クイズ」へ移動 | 既存のクイズ操作 |
| `#vote-section` / classroom | 既存位置・保存形式を維持 | `constitutional-amendment-issue-stance-v1`、授業用印刷 |
| `#fallback` | JS無効・印刷時の本文として維持 | 図解、基本説明、読み取り可能な代替表示 |

## V01〜V12の実装対応

| 要件 | 対応 |
|---|---|
| V01 ページ順 | 立場バー→立場フィルター→山→論点一覧→読書面→背景・資料→投票の順へ接続 |
| V02〜V04 選択と4列一覧 | バー・山の状態共有、4立場、論点ボタンを既存データから生成 |
| V05 選択色 | 選択中の立場色を山へ反映。選択中`.9`、他`.23` |
| V06 読書面 | 理由・投稿・制度・資料・0件/未登録表示を同一論点面へ集約 |
| V07 投稿接続 | 論点全体の代表投稿を維持。理由別投稿データ不存在を明記 |
| V08 資料3タブ | `資料を読む`・`x投稿で語られない話`・`一次資料クイズ`を実装 |
| V09 旧要素 | 通常画面の重複を隠し、読書面・資料タブ・折りたたみへ統合 |
| V10 密度・余白 | 既存の図解・投稿・資料を同じ読書クラスタにまとめるCSSを追加 |
| V11 操作性 | 480ms補間、reduced motion、キーボードフォーカス、深いリンクを維持 |
| V12 異常系 | JS無効/失敗・印刷・授業印刷のfallbackと、投票・保護タグを維持 |

## 変更前の比較基準

- HEAD: `7214dc20`（作業開始時）
- `docs/constitutional-amendment-reaction-map.html`: 309,686 bytes、SHA-256 `9589c5d1d2e8f9ea78b21a3d96413546581827d31b28e272f1a296113bf786ec`
- 収集1,779件、意見1,568件、収集期間2026-06-20〜2026-09-18、更新2026-09-20
- 表示立場: 改正推進、慎重・反対、手続き重視、中立の4種
- 投票: `constitutional-amendment-issue-stance-v1`、24通り。順序と保存式は変更しない

## 次の確認

工程2〜5の実装・自動検証・ブラウザ確認を行い、公開前にオーナー確認を取る。公開反映はこの作業の範囲に含めない。
