# 課題77 — あだ名テーマ移植の内容・画面契約

記録日: 2026-09-27。対象: `school-nickname-ban`。

目的は、あだ名テーマの旧「山・論点カード・資料・クイズ」を、消費税の完成版と同じ読み順へ組み替えること。件数・立場・論点・既存リンクは正本から再生成し、理由・資料・年表はテーマ固有の確認日を保つ。

## 内容の接続表

| 論点ID | 件数 / 再読 | 理由ID | 投稿の出所 | 制度・資料の接続 | 図解 | 確認日 |
|---|---:|---|---|---|---|---|
| `school-nickname-ban-uniform-rule` 一律禁止の実効性 | 36 / 36中8未再読 | `group-5`〜`group-7` | 再読台帳の `post_key` → 正典投稿ハッシュ、各理由2件まで | `constitution` `rule-reason`、`school-nickname-ban-vein-safety`、`scope` `reason` `revision`、年表3件、資料のみ3件 | 旧 `fb-*` の画像 | 再読 2026-09-12 / 資料 2026-09-12・2026-09-20 |
| `school-nickname-ban-psychological-safety` いじめ・心理的安全 | 29 / 29中5未再読 | `group-1`〜`group-4` | 同上 | `unwanted-name`、`school-nickname-ban-vein-safety`、`voice` | 同上 | 同上 |
| `school-nickname-ban-naming-culture` 親しさ・呼称文化 | 13 / 13中1未再読 | `group-8` `group-9` | 同上 | `school-nickname-ban-vein-safety` | 同上 | 同上 |
| `school-nickname-ban-school-practice` 学校運用・現場体験 | 12 / 全件再読 | `group-11` `group-10` | 同上 | `national-rule`、`scope` `revision`、資料のみ `sc-4` | 同上 | 同上 |
| `school-nickname-ban-gender-consideration` さん付け・ジェンダー配慮 | 6 / 全件再読 | `group-12` | 同上 | `rule-reason`、`reason` | 同上 | 同上 |
| `school-nickname-ban-individual-choice` 本人意思・柔軟運用 | 4 / 4中1未再読 | `group-13` | 同上 | `unwanted-name`、`voice` | 同上 | 同上 |

理由の件数・表示名は `PLANET_DATA.issues[].sub`、所属投稿は `data/school-nickname-ban_issues-reread.json`、要旨とURLは `social-samples/school-nickname-ban_hermes_arena_classified.json` から作る。投稿本文の全文は転載せず、要旨と元投稿へのリンクを残す。

## 画面差分表 V01〜V12

| ID | あだ名テーマでの実装 | 判定 |
|---|---|---|
| V01 | 短い現状確認 → 立場/山/論点 → 論点読書面 → 制度年表・潮目 → 投票・授業・編集情報の順。長い背景は山の後へ移動 | 実装済み。ブラウザー確認済み |
| V02 | 立場バーと立場ボタンを山の直前へ集約。論点ボタンはPC4列、375/320pxは2列 | 実装済み。3幅確認済み |
| V03 | 山の実表示210px、狭幅180px。海面下装飾を非表示、0%は基準線上の点。立場切替は480ms、reduced motionは即時 | 実装済み。DOM寸法・動作確認済み |
| V04 | 論点名と件数・割合を別行で表示。選択中は濃紺/白文字、0件もボタンを残す | 実装済み。全6論点・全表示モードを確認済み |
| V05 | 選択立場の色で山を再描画、選択山0.9・他0.23。パネル件数は選択立場、理由・投稿・資料は論点全体と明記 | 実装済み。立場切替確認済み |
| V06 | 理由・投稿と制度・資料を同じ論点パネルへ。PC左右、スマホ上下。図解は小さな入口から開く | 実装済み。375/320px確認済み |
| V07 | 再読済み理由を開くと、その理由の代表投稿2件までの要旨・Xリンク・カード。未再読は空状態を明記 | 実装済み。理由IDと投稿ハッシュを照合済み |
| V08 | 「資料を読む / x投稿で語られない話 / 一次資料クイズ・4問」を資料欄へ集約。一次資料のみの4項目は横断タブで重複を避ける | 実装済み。4項目・4問を確認済み |
| V09 | `#issue-cards` と `#ocean` は通常表示から移設、`#bukatsu-check` は資料欄、`#quiz` は資料タブ、編集・図の見かたは折りたたみ | 実装済み。旧節の対応を下表に記録 |
| V10 | 紙面色は既存の白/濃紺を基準に、確認・資料の境界を薄い青灰色で整理。長い出典名は折返し | 実装済み。3幅で横はみ出し0px |
| V11 | 論点クリック、全表示モード、立場切替、理由開閉、資料3タブ、キーボード/戻りリンクを確認 | 実装済み。Chromium/WebKitで確認済み |
| V12 | JavaScript無効時は旧 `#fallback` と `#issue-cards` を読める状態で維持。印刷・授業・投票・GA4/AdSense/Supabase/OGPタグは変更しない | 実装済み。JS無効と保護タグを確認。公開前の本番確認は未実施 |

## 旧セクションの処置

| 旧要素 | 処置 | 保持するもの |
|---|---|---|
| `#stance-glance` / `#modes` | 山直前へ集約し、実操作は `#modes` の1組へ | 4立場・件数・色・閲覧状態 |
| `#bukatsu-background` | 山の後へ移動。短い制度確認を上部、詳細は折りたたみ、年表は日付タブ | 定義、3時点、出典、確認日 |
| `#bukatsu-check` | 関連論点の資料欄へ接続。通常画面では旧独立カードを非表示 | 4項目、問い、根拠リンク |
| `#fallback` | JavaScript無効・印刷用の静的本文として維持 | 全6論点、図解、既存資料・リンク |
| `#issue-cards` | 論点別読書面へ代表投稿を移し、通常画面の旧一覧は非表示 | 既存の論点別投稿2件、要旨、URL |
| `#ocean` | 共通の心配を関連3論点へ、資料のみ4項目を資料3タブへ | `vein`、資料本文、出典、確認日 |
| `#quiz` | 資料欄のクイズタブへ移動 | 4主張、判定、根拠、論点接続 |
| `#editorial` / `#meta` | 後段の折りたたみへ移動 | 編集整理、図の見かた、既存本文 |
| 潮目・投票・授業・編集/分析・訂正・関連テーマ | 既存IDと順序を保ち、山の下の読み順へ接続 | 期間、母数、保存番号、授業印刷、計測・訂正リンク |

## 更新と検査

- `scripts/build_nickname_arena.py --connected-layout` で初回有効化。以後は接続目印を検出して、PLANET_SECTION再生成後にも橋渡しJS・CSS・読書面を再適用する。
- 同じ入力でHTMLを再生成しても差分が出ないこと、既存の投票指紋・保護タグが変わらないことを検査する。
- `tests/test_school_nickname_connected.py`、Chromium/WebKitの `tests/test_school_nickname_connected_browser.cjs` で、6論点・全表示モード・理由・資料4項目・クイズ4問・3幅・JavaScript無効を確認する。
- 本番URLの表示確認、オーナー承認、マージ・公開は未実施。候補は公開前レビューへ回す。
