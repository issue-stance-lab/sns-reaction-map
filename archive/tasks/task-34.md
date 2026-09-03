# 課題34: ページ更新スクリプトが再実行できないテーマの整備

**状態**: **完了**（11テーマ全件がadapter。henokoの候補input/output対応も2026-08-18に完了し、
`THEMES.yaml` の `page_update_mode` は全テーマ `adapter` で確認済み）
**発見**: 2026-08-02、adapter 昇格判定の実測時

**概要**: データ更新を自動化するには「同じ入力で2回実行しても差分が出ない」ページ更新スクリプトが要る。全11テーマで実測し、`THEMES.yaml` の `page_update_mode` に記録した。

| 区分 | テーマ | 状態 |
|---|---|---|
| adapter（11） | ai-copyright / bukatsu-chiiki / elderly-license-revocation / takaichi / koshitsu-tenpakai / bike-blue-ticket / school-nickname-ban / constitutional-amendment / fukushuto / consumption-tax-cut / henoko-student-accident | staging候補の入出力に対応。変更候補の2回目実行で差分ゼロ |
| adapter_candidate（0） | — | 2026-08-18 にhenokoが昇格して解消 |
| migration（0） | — | 2026-08-18 に消費税減税が昇格して解消 |
| manual（0） | — | 2026-08-17 に自転車青切符が昇格して解消 |

**やること**: なし。全11テーマがadapterになったため課題34は完了。次にpage_update_modeを見るのは新テーマ追加時（`new-topic` スキル）だけでよい

**2026-08-18 消費税減税**: `build_consumption_tax_page.py` は副首都ページをテンプレートに読む一度きりの生成器だった。候補input/outputを足し、テンプレートの既定を自分自身の公開ページへ変更。2回目で差分が出ていたのは回遊カードのスクリプトの追記・`.side.mid` の追記・潮目前後の空行の3か所。**投票は「論点の番号×立場の番号」で保存されるため、件数順の並びが入れ替わると過去の投票の意味が変わる**（8/3分を足した時点で実際に入れ替わり、adapterの投票互換性検査が止めた）。公開後は並びを固定する。調査条件（取得元・期間・件数）は昇格後に `finalize` が貼り直す。滞留していた3回分は1回ずつ公開できない（途中の状態が collect_at 期限超過で必ず落ちる）ため、`refresh_topic.py` に `--include-wave` を足して保管済み更新回を1つの候補へ畳み込んだ。**同じ滞留は他テーマでも起きるので、次からはこのフラグを使う。**
**注意**: ビルダーを直したら必ず同じ入力で2回実行し、2回目に差分が出ないことを確認してから `page_update_mode` を上げる

**2026-08-02 共通ランナー対応**: `scripts/refresh_topic.py --topic` に、全11テーマ共通の疎通確認・収集・重複排除・10件試験分類・全件分類・集合検査・更新回保存・バックアップを集約した。migration / manual / adapter_candidate も公開せずstaging止まりで予定どおり収集できる。ページ処理は `scripts/refresh_adapters/` に分離し、takaichi は候補ページ・arena data・潮目を2回生成して差分ゼロ、投票topicIdと15選択肢の互換性を検査する。

**2026-08-14 高齢者免許返納**: `build_elderly_arena.py` を候補input/output対応にし、専用adapterでページ・潮目を2回生成して差分ゼロ、投票topicId・18選択肢・GA4/AdSense/OGPを保護する。保存済み110件の収集履歴は書き換えず、現在の正典と再照合して重複18件を除いた92件（意見45件）を公開。累積364件・意見233件になった。

**2026-08-17 学校あだ名**: `scripts/build_nickname_arena.py` を新設し、一度きりの移行用
`upgrade_nickname_arena.js`（実行のたびに空行が1行増え、SEO meta を374件時代へ巻き戻す）を
`archive/scripts/` へ退けた。移行前の公開ページとアリーナの点を正典からバイト単位で
再現できることを確認してから差し替えている。専用adapterがページとアリーナの点の2ファイルを
2回生成して差分ゼロ、投票 topicId と18選択肢、GA4／AdSense／OGPを保護する。投票ボタンの
件数は毎回変わるので指紋から外した。潮目も更新回から作る形へ移した（課題38の②）。
8月17日収集の46件（意見24件）を公開し、累積420件・意見87件になった。

**横展開のゲート**: 少なくとも保全先の決定、既存データの初回バックアップ、復元確認が終わるまで、他テーマの定期更新を開始しない。
