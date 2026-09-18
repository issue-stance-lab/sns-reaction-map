# 課題69: 定期データ更新の通常運用の型を確立する

**状態**: 進行中
**担当**: 開発・データ部（収集・表示更新）／編集部（本文確認）
**関連**: 54（山なみ移行本体。完了・一般公開承認済み）/ 63（Xデータの定期収集整備。過去データの品質洗い出しが中心で、この追い込み読みは「担当範囲外」と明記済みのため本課題へ引き継いだ）

## 何を解決するか

課題54（山なみリニューアル）を最優先していたため、8テーマの定期収集が1〜8日超過したまま止まっていた。課題54完了・CEO承認（2026-09-15、`approval-20260915-001`）を受け、定期収集を再開する。

複数テーマを同時に段取りしようとすると、テーマごとに違う詰まりどころに同時対応することになり収拾がつかなくなる（過去に副首都・憲法改正の並行作業で分岐が生じた前例あり）。そのため、**「部活動の地域移行」1テーマだけに絞り、収集→編集再読→表示更新→公開までを一気通貫で実施し、そこで得た手順を「今後どのテーマでも使う標準手順」として`DATA_REFRESH.md`へ固定する**。残り7テーマは、この型を1つずつ当てはめて消化していく。

部活動の地域移行を最初の実例に選んだ理由: 止まっている日数（6日）に加え、編集再読（本文を人が実際に確認する作業）の余裕が2論点とも上限40%まで残り2件相当しかなく、最も切迫していたため。

## 方針

`DATA_REFRESH.md`に2026-09-15付で追記する「定期更新セッションの進め方」「読み込み確認のやり方」に従う。要点:
- 収集（正典への保存まで）と、サイト表示の更新は別工程として扱う。独自性検査（`independence_gate`）は`refresh_topic.py`の収集処理には組み込まれておらず、山なみ区画の表示更新（`refresh_planet_section.py --for-docs`）でだけ効く
- 収集した直後に`verify_reread_headroom.py`でその場の影響を確認する
- 読み込み確認は対象件数÷25件を並列数の目安にし、自動分類スクリプトへの置き換えを禁止、完了後に論点ごと10件以上を抜き取って本文と記録の一致を確認する（消費税減税の使い回し要約の再発防止）

## 実施記録

### 2026-09-15〜16 部活動の地域移行・辺野古高校生死亡事故（1〜2テーマ目）を完了

詳細は[quality/reviews/2026-09-15-task69-bukatsu-henoko-details.md](../quality/reviews/2026-09-15-task69-bukatsu-henoko-details.md)
に切り出した（400行上限のため、2026-09-18）。要点:
- 部活動: 新規223件（意見179件）→正典1,618件。読み込み確認166件。ここで
  「定期更新1回分の実務手順」（`DATA_REFRESH.md`）を確立
- 辺野古: 新規80件（意見72件、API拒否1件除外）→正典552件・意見430件。
  辺野古専用の過剰な指紋チェックを撤去（[[project_henoko_guard_bug]]）
- 両テーマとも本番反映済み。マージ時の`docs/index.html`・`data-backup-status.json`
  衝突は「手で書き換えず`sync_portal_stats.py`／`backup_private_data.py`で
  作り直す」で解消——以後の同型衝突もこの手順が前例になった

### 2026-09-17 fukushuto（3テーマ目）で収集完了、公開候補作成が既存バグで停止

詳細は[quality/reviews/2026-09-17-task69-fukushuto-details.md](../quality/reviews/2026-09-17-task69-fukushuto-details.md)
に切り出した（400行上限のため、2026-09-18）。要点:
- 新規291件（意見229件）→累積正典1,733件・意見1,452件
- 山なみ変換で消えた一次資料照合セクション（FACT_CHECK）を復元。6件の不具合を
  発見・解消して`--apply-promotion`成功、本番反映済み（`a5d9256`）
- 持ち越しで「koshitsu/bike/constitutionalもFACT_CHECK系マーカー0件」と記録したが、
  **2026-09-18に誤りと判明**（koshitsu標準化の節を参照。各テーマ固有のマーカー名
  ではなくfukushuto固有の文字列で検索した誤検知と推測）

### 2026-09-17 fukushutoページの構成をオーナー指示で起承転結型に再編（本番反映済み）

本番反映後、オーナーから「内容に統一感がない、起承転結にしたい」との指摘。診断した
ところ、同じ情報が複数箇所で重複していた（事実整理2回・6論点の説明が2〜3箇所・
数字の再掲）のが原因と判明。オーナー承認のうえ以下へ再編し、mainへ反映済み
（`b3491fe`、作業ツリー`../isa-wt-fukushuto-narrative`は削除済み）。

- 起: 「背景・経緯」と「必要性・制度・場所を分けて確認」を1セクションへ統合
- 承: 山なみはそのまま。論点解説カード（6枚・図解画像）を削除し、画像は各論点の
  詳細パネル（fallback側・実際の操作画面側drawPanel()の両方）へ移設
- 転: 「一次資料照合コーナー」を最後尾から山なみ直後へ前倒し
- 結: 投票＋編集・分析情報はそのまま。スタンス集計（3統計、山なみと数字が重複）は削除

**このテーマ固有の教訓（他の山なみテーマにも起きうる）**: 画像を含む対話的な
可視化部分（山なみ本体・詳細パネル・`drawPanel()`のJS）は`build_planet_page_preview.py`
（10テーマ共通）が`refresh_verified_planet()`のたびに丸ごと作り直すため、そこへ
直接書き込んだ変更は次回の定期更新で消える。一次資料照合コーナーと同じ「後付けの
補完処理」方式（`apply_landing_images()`、`refresh_verified_planet()`の直後に必ず
呼ぶ）で解決した。共通コード（`build_planet_page_preview.py`）自体には手を入れて
いない。あわせて、JS文字列の途中に`src="images/…-'+var+'"`のような未完成パスを
書くと`validate_theme_seo.py`の参照チェックが誤検知することも判明（パスは先に
1つの変数へ組み立ててから埋め込むこと）。

koshitsu-tenpakai・bike-blue-ticket・constitutional-amendmentの定期更新に着手する
際、これらのテーマにも同種の「画像・カード・集計の重複」がないか、着手前に一度
ページ構成を確認する価値がある（今回のような重複はfukushuto固有の可能性が高いが
未確認）。

### 2026-09-18 koshitsu-tenpakai（4テーマ目）着手前の確認で、上記「FACT_CHECKマーカー0件」が3テーマとも誤りと判明

作業ツリー（`../isa-wt-task69-koshitsu`）で着手する前に、上記持ち越し課題の前提
（bike-blue-ticket・constitutional-amendment・koshitsu-tenpakaiもFACT_CHECK系
マーカーが0件）を実機で確認したところ、**3テーマとも該当マーカーは最初から存在し、
一度も欠落していなかった**。

- koshitsu-tenpakai: `KOSHITSU_AUDIT_START/END`が現行ページに存在（1461/1463行）。
  `refresh_adapters/koshitsu.py`の`_run_process_sections`が呼ぶ
  `build_koshitsu_process_sections.py`も存在し、正常に動く経路
- bike-blue-ticket: `PROCESS_SECTIONS_START/END`が存在（1856/1956行）。
  `git log -S`で2026-08-16の導入以来、削除された履歴なし
- constitutional-amendment: `CLAIM_AUDIT_START/END`が存在（2464/2493行）。
  `git log -S`で2026-08-20の導入以来、削除された履歴なし
- koshitsu-tenpakaiは2026-09-15の候補統合（`aba5a18`、課題54側の作業）で
  この山なみページ自体が作られており、fukushutoの調査（2026-09-17）時点でも
  マーカーは既に存在していたはず。それでも「0件」と記録されたのは、おそらく
  各テーマ固有のマーカー名（`KOSHITSU_AUDIT`/`PROCESS_SECTIONS`/`CLAIM_AUDIT`）
  ではなく、fukushuto固有の`FACT_CHECK`という文字列で検索した誤検知と推測される
  （3テーマとも実際のマーカー名がFACT_CHECKとは異なる）

**教訓**: 「他テーマも同じ壊れ方をしているはず」という推測は、そのテーマの実際の
マーカー名で個別に確認するまで確定させない（[[feedback_verify_against_precedent]]
と同じ考え方）。この訂正により、①FACT_CHECK復元は3テーマとも不要と判明。
残る②〜④（apply_public_countsの山なみ分岐漏れ・正典先行差し替え・
number_provenance同期漏れ）は山なみ共通アーキテクチャの論点であり、
個別マーカーの有無とは独立に確認が必要。

### 2026-09-18 koshitsu-tenpakai: 収集は完了・公開はkoshitsu固有の監査ゲートで停止（要オーナー判断）

koshitsu-tenpakai専用の候補統合方式（`koshitsu_production.py`、正典の
未監査変更を検出すると意図的に公開を拒否する設計）を発見し、オーナーへ次の
方針を確認する持ち越しとした経緯。詳細は
[quality/reviews/2026-09-18-task69-koshitsu-audit-gate-details.md](../quality/reviews/2026-09-18-task69-koshitsu-audit-gate-details.md)
に切り出した（400行上限のため、2026-09-19）。この後の展開は次の項目を参照。

### 2026-09-18 consumption-tax-cut（5テーマ目）を収集から本番反映まで実施

**収集**: 新規624件（意見532件）を取得、累積正典4,386件・意見3,890件へ統合。
次回収集は9/24。

**山なみ変換後、初のページ生成で不具合発見・修正（5件目の同型不具合）**:
`build_consumption_tax_page.py`が9/14の山なみ形式への切り替え（`4b973a4`）で
無くなった旧セクション（「6つの論点とXの声」「この争点の背景」）を書き換える
前提のまま残っており、`html.index()`が例外で止まっていた。同じ内容は山なみの
論点別パネルと投票セクションの導入文に統合済みと確認し、該当ブロックとその
専用検証（temp-bar-wrap基準）を削除して解消（`54d4888`）。

**4論点795件の編集再読**: 対象範囲・効果・給付比較・事業者負担の4論点で、
独自性検査の上限（40%）に対し合計795件（今回分＋以前からの積み残し）が
未読だった。bukatsu-chiikiで確立した並列読み込み手順（対象件数÷25件を
並列数の目安に）をそのまま適用し、33バッチ・新規サブエージェントで
既存区分（bucket）へ割り当て。完了後、機械検査（件数・ID集合・重複・
区分の妥当性）に加え、バケット分布が偏った2バッチを本文まで戻して
個別確認、論点ごと12件以上の抜き取りも実施し、全て正しい割り当てと確認した。

**本番反映**: `--apply-promotion`は成功したが、正典を事前に候補へ手動差し替えた
ため`collect_delta`が0になる自己招来の事象が発生（fukushuto・koshitsuと同型）。
実際の新規件数624件へ手で修正し`sync_portal_stats.py`で作り直した。マージ時に
`company/data-backup-status.json`・`docs/index.html`で衝突（別セッションの
X投稿日次記録との重複、bukatsu-chiiki等と同型）。オーナー確認のうえ
`sync_portal_stats.py`／`backup_private_data.py`で作り直して解消。マージ後の
`verify_adoption_registry.py`もmain側の変更で台帳が古くなっておりNGだったため
`build_adoption_registry.py`で作り直した。標準検査（4種）・`unittest`970件・
`run_public_checks.py`いずれも最終的にNG0件。公開サイトで件数・トップページの
「+624件」表示を確認済み。作業ツリー（`../isa-wt-task69-consumptiontax`）は
反映後に削除済み。

**残り課題（持ち越し）**: bike-blue-ticket・constitutional-amendmentも
`refresh_adapters/*.py`が専用の`*_process_sections.py`を自動実行する構成だが、
2026-09-18の確認でFACT_CHECK系マーカーは最初から存在していたと判明済み
（上記koshitsu-tenpakaiの訂正記録を参照）。この2テーマの定期更新に着手する際は
「マーカー消失」ではなく、apply_public_countsの山なみ分岐漏れ・正典先行差し替え・
number_provenance同期漏れの3点を個別に確認すること。

### 2026-09-18 consumption-tax-cutをfukushutoと同じ起承転結型へ再編（本番反映済み）

オーナー指摘（「副首都と同じであっちいったりこっちいったりする」）で確認したところ、
副首都の9/17再編前と同じ3種類の重複と判明し、承認のうえ再編した
（`517972f`、作業ツリー`../isa-wt-ctc-narrative`は削除済み）。

- 承: 「6つの論点」解説カード6枚（山なみの論点別パネルと内容重複）を削除し
  画像は各論点パネルへ移設
- 転: 一次資料照合（最後尾＝97%地点にあった）を山なみ直後へ前倒し
- 結: スタンス集計（山なみの凡例と数字が重複）を削除

**fukushutoとの違い**: consumption-tax-cutは`build_consumption_tax_page.py`
（テキスト系）と`refresh_planet_section.py`（PLANET_SECTION）が分業しており、
論点画像の後付け補完（`_inject_ctc_landing_images()`）は後者のTOPIC_ENRICHへ
置いた。一次資料照合は前者側で「マーカーがどこにあっても毎回
PLANET_SECTION_END直後へ動かす」方式にした。標準検査4種・unittest 970件・
`run_public_checks.py`はNG0件、ブラウザでも確認済み。

**残り課題**: 残る3テーマにも同種の重複がないか、着手前に確認する価値がある。

### 2026-09-18 consumption-tax-cut: 投票結果が旧アリーナ地図（空白）へ自動スクロールする不具合を解消

オーナー報告「論点をタップすると前のマップが出てきます」を調査。9/14の山なみ切り替え
（`4b973a4`）で旧アリーナ（`stance-map-section`、canvas散布図）の描画スクリプトが
削除されたのに、HTMLの器とSM_RAWだけが残存し、投票後は毎回この空の器へ自動
スクロールしていた（`6ff0878`）。同じ切り替えを受けたfukushuto・bukatsu-chiiki・
koshitsu-tenpakaiは器ごと撤去済みと確認し、同じ形に揃えて削除
（`getElementById`は元からnullガード済み）。SM_RAWは`build_consumption_tax_page.py`が
毎回検査する対象のため残した。標準検査・unittest 970件・`run_public_checks.py`はNG0件。

### 2026-09-18 koshitsu-tenpakai: 候補統合方式を廃止し、標準adapter経路へ接続・本番反映まで完了（6テーマ目）

オーナーへ「候補統合方式を続けるか、他9テーマと同じ標準の型へ繋ぎ直すか」を確認し、
繋ぎ直しの承認を得た。実施内容は`feef38a`（作業ツリー`../isa-wt-task69-koshitsu`）。

**分かったこと（着手前の想定より深刻だった）**: koshitsu_production.pyは正典が
承認済み候補と一致するかを検査するだけで、**山なみ本体を正典データから作り直す
機能自体を持っていなかった**（2026-09-13に一度だけ作った固定プロトタイプを
毎回貼り直すだけ）。`build_koshitsu_arena.py`自身の`build()`もPLANET_SECTION
判定でこの経路へ委譲するだけで、他9テーマが使う`build_planet_page_preview.py`
（`bpd.build()`・`independence_gate()`・`render_planet()`等）には一度も
繋がっていなかった。

**実施**:
1. `build_koshitsu_arena.py`に`refresh_verified_planet()`（fukushuto等と同型、
   `bpd.build(THEME)`→`independence_gate`→`render_planet`→PLANET_SECTION差し替え）
   を追加し、`build()`・`--public-counts-only`の両方でkoshitsu_production.pyへの
   委譲を置き換えた
2. `apply_koshitsu_extras()`を新設。共通ジェネレータが知らない皇室典範専用の
   3箇所（軸の注記「色は今回案全体への評価です」・論点ジャンプリンク6件・
   「詳細データ」の論点×評価テーブル）を、再生成のたびに差し戻す。3件目の
   詳細データテーブルは`--prepare-promotion`を実際に走らせて初めて発覚した
   （山なみ区画の外にあり件数を持つ箇所、[[reference_planet_regen_wipes_hand_edits]]
   と同型）。公開JSON（`data/public/themes/koshitsu-tenpakai.json`）から
   論点×評価の集計表を作り直す`build_koshitsu_detail_table()`を新設して対応
3. `refresh_adapters/koshitsu.py`の`build()`から冗長な二重分岐を削除し、
   他テーマと同じ`_run_builder→_run_process_sections→_apply_tide`経路へ統一

**実機検証**: `--resume --prepare-promotion`を実行し`status: prepared`まで到達
（2回目、詳細データテーブル修正後）。副産物として、山なみ変換後の共通コード側
修正2件（副首都で発見・修正済みのCSSバグ）が皇室典範の公開ページには未反映
だったことも判明（同じ入力でも再生成のたびに差分が出続ける形で残っていた）。

**独自性検査（軽量版）で実際に必要だった作業**: `independence_gate`が
「語られていない争点」2件（`koshitsu-tenpakai-adoption-age`・`-birth-pressure`、
`data/verification/koshitsu-tenpakai-sunk-continents.json`）の母数(sns_base)が
旧意見数1245のままだとNG。新規280件（意見）を候補語で再検索し、既存の一致条件
（一次資料の論点に直接触れているか）と照らして新規の一致が無いことを確認した
うえで母数を1525へ更新。**全280件の個別監査は不要で、他9テーマと同じ軽量な
再読ルールで足りた**——これが今回オーナーへ確認した本題への回答。

**apply-promotion時に新たなNG33件（number_provenance）を発見・解消**:
標準経路へ繋いだことで初めて効くようになった検査が、他に2種類の見落としを
検出した。①`exclude_selectors`が旧2項目（review-note・article-trust-observations）
のままで、他9テーマ共通の基準セット（`note`・`findings`・`sunk`・`#planet-data`）が
未反映（「本文確認後に追加された投稿N件」の注記6箇所・coverage_note内の
一次監査由来の数字が該当）。②山なみ本体の外にあるのに件数を持つ箇所が
2箇所（ヒーローの`<p class="lead">`・`#issue-cards`の論点別バッジ6件）、
2026-09-13当時の値のまま取り残されていた。`apply_koshitsu_hero_lead()`・
`apply_koshitsu_issue_card_counts()`を新設して解消（`6c5cd47`）。

**本番反映**: 完了。`--apply-promotion`成功（`status: promoted`、正典1,950件・
意見1,525件）。マージ時に`TASK_BOARD.md`・`company/data-assets.json`・
`company/data-backup-status.json`・`data/public/catalog.json`・
`data/verification/adoption/registry.json`・`docs/index.html`・本ファイルで
衝突（consumption-tax-cutの同日反映と同型）。台帳・登録簿類は手で行を
書き換えず`build_adoption_registry.py`・`data_asset_inventory.py`・
`sync_portal_stats.py`で作り直し、文書は両セッションの記述を残す形で解消。
標準検査4種・`unittest`970件（`test_published_page_matches_canonical`含め
全通過）・`run_public_checks.py`いずれも最終的にNG0件。次回収集は9/25。
作業ツリー（`../isa-wt-task69-koshitsu`）は反映後に削除予定。

**残り課題**: bike-blue-ticket・constitutional-amendmentは、koshitsuと同じ
「候補統合方式」ではなく標準adapter経路を最初から使っているため今回の
繋ぎ替え作業は不要。ただし山なみ本体の外にあるのに件数を持つ箇所
（ヒーローのlead・詳細データ表・カード件数バッジ等）は個別に存在しうるため、
着手時に`verify_number_provenance.py`で必ず確認すること。

### 2026-09-18 koshitsu-tenpakai: オーナー指摘でヒーロー内「議論の中心」を追加（本番反映済み）

公開後、オーナーが実際の画面を見て「他のテーマにはある『議論の中心』が無い」と指摘
（fukushutoのスクリーンショット添付）。他の山なみテーマ（bukatsu-chiiki・fukushuto・
constitutional-amendment・consumption-tax-cut）はヒーロー直下に最大論点の要約
「議論の中心」を持つが、皇室典範の2026-09-13候補には最初から含まれておらず、
現行ページとの差分比較（both-sides-missing）では気づけなかった項目だった。

`configs/koshitsu-tenpakai-reaction-map.json`のarena.issue_blocks全5件に
conclusion（headline/detail）を追加。文言は各論点の理由内訳（islands）で最も多い
カテゴリを根拠にした。`apply_koshitsu_conclusion()`を新設し、公開JSONの最大論点に
対応するconclusionをヒーローのlead直後へ差し込む（初回挿入・以後の差し替え両対応、
最大論点が入れ替わっても壊れないよう5論点分すべて用意）。

**確認方法**: ローカルの/tmpに直接置くと画像・フォントが読み込めず見た目が壊れて
見えた（[[feedback_artifact_standalone_page_preview]]と同型の罠）。作業ツリーの
`docs/`配下に一時ファイルを置いて自作サーバーで配信し、実際のアセットが読み込まれる
状態でオーナーと一緒にスクリーンショットを確認してから公開した。

標準検査4種・unittest 970件・run_public_checksいずれもNG0件、本番反映後にブラウザで
実ページを確認済み。作業ツリー（`../isa-wt-koshitsu-conclusion`）は削除済み。

**教訓**: 差分ベースの点検（現行ページと再生成結果を比較）は「両方に無い要素」を
検出できない。他テーマとの横並び比較（画面を直接見比べる）でしか見つからない
見落としがある。bike-blue-ticket・constitutional-amendmentの着手前にも、
他4テーマとページ構成を横並びで確認する価値がある。

### 2026-09-18 koshitsu-tenpakai: オーナー指摘「あっちこっち行っていそう」で起承転結型へ再編（本番反映済み）

オーナーが「皇室典範テーマもどうもあっち行ったりこっち行ったりしていそう」と指摘
（fukushuto・consumption-tax-cutで既に直した「構成が行ったり来たりする」問題と同種の
懸念）。fukushutoの現行構成と直接比較し、2つの問題を確認した。

1. 「論点ごとの図解とX投稿」が山（対話パネル）とは別セクションになっており、
   山を押しても図解は出ず、ジャンプリンクで画面下まで飛ばす構造だった
   （fukushutoが再編前に持っていた重複と同型）。
2. 一次資料照合（koshitsu-audit）が資料系セクション群（クイズ・資料にあるのに・
   編集部横断整理）から離れ、投票の後ろに取り残されていた。

対応: ①論点の図解画像を各論点の詳細パネル（`extras-{id}`、山を押したときにJSが
`innerHTML`で読み込む唯一の場所）へ差し戻す`apply_koshitsu_landing_images()`を新設
（6論点中3論点は詳細パネル自体が無かったため新設）。②モーダル拡大表示のクリック
判定を、静的な`querySelectorAll+forEach`からイベント委譲（`closest()`）へ変更
——動的に挿入した画像はページ読み込み時に存在しないため静的判定では反応しない
（fukushutoの同じ修正と同型）。③koshitsu-auditセクションをissue-cardsより前
（`PLANET_SECTION_END`直後）へ移動し、資料系4セクションが連続するよう並べ替えた。
④issue-cardsから重複した画像を削除、見出しを「論点ごとの図解とX投稿」→
「論点ごとのX投稿」に変更（位置は変えていない）。

**作業中の訂正**: セクション移動の際、`#ocean`・`#editorial`もPLANET_SECTION外だと
誤認し、koshitsu-auditを両者の間へ移動しようとしたが、実際はどちらもPLANET_SECTION内
（山なみジェネレータが毎回まるごと作り直す領域）だった。`build_koshitsu_arena.py
--check`の冪等性検査（「landing-panelが6件必要なのに0件」）が本番反映前に検出、
`html.index()`で実位置を確認してから正しい位置（PLANET_SECTION_END直後）へ
やり直した。詳細は[[reference_planet_regen_wipes_hand_edits]]に追記済み。

標準検査4種・unittest 970件・run_public_checksいずれもNG0件、ブラウザで
山クリック→画像表示→モーダル拡大まで実地確認済み。作業は
`task/koshitsu-narrative-restructure`ブランチへコミット済み（`23d453b`）、
mainへのマージ・本番反映はこれから。

### 2026-09-18〜19 constitutional-amendment（7テーマ目）を収集から本番反映まで実施

期限超過テーマの再確認（管理ダッシュボード）で、bike-blue-ticketは9/12に課題63側で
既に収集・反映済み（次回9/26、超過なし）だが、constitutional-amendmentは9/12が
期限で6日超過のまま止まっていたと判明。「期限が早く来ていた方から」の基準で
constitutional-amendmentから着手した。

**収集**: 新規223件（意見199件）を取得、既存正典（1,556件）と統合し累積正典
1,779件・意見1,568件へ。taxonomy整合・分類エラーとも0件、モデルはkimi-k2.6固定。

**`--prepare-promotion`が独自性検査で停止（koshitsu-tenpakaiと同型の軽量な再読で解消）**:
「語られていない争点」2件（`constitutional-amendment-challenge`・
`-emergency-review`、`data/verification/constitutional-amendment-sunk-continents.json`）
の母数(sns_base)が旧意見数1369のままだとNG。新規199件（意見）を同じ条件語
（訴訟|裁判|異議／緊急集会）で再検索したところ、「challenge」側は新規一致0件、
「emergency-review」側は2件が候補に挙がったが、いずれも「参議院の緊急集会」という
制度の存在・要否への一般的な言及で、一次資料（第54条第3項の事後審査手続き）には
触れておらず不一致。新規の一致なし、母数のみ1568へ更新。`verify_reread_headroom.py`
も「上限に近づいている論点はありません」を確認済みで、全199件の個別監査は不要だった。

**`--apply-promotion`でnumber_provenanceのNG3件を発見・解消**:
`configs/constitutional-amendment-reaction-map.json`の`number_provenance.exclude_selectors`
に`note`が無く、独自性検査の進捗を示す「本文確認後に追加された投稿N件は、本文確認の
対象外です」（7論点中3論点分）が「説明できない数字」として`verify_number_provenance.py`
に拾われていた。henoko-student-accidentで既に踏んだのと同型の見落とし
（他5山なみテーマ中4テーマは`note`を既に持つ）。`note`を追加して解消。

**本番反映**: `--apply-promotion`成功（`status: promoted`、`collect_delta`も223で
自己招来の0件事故なし——正典の事前候補差し替えをしなかったため）。標準検査4種・
unittest 970件・run_public_checksいずれもNG0件。ブラウザで実ページを確認
（意見数・議論の中心・海面より下の2件の母数表示・論点の一覧7件・地下水脈・
資料クイズ・代表投稿の埋め込み、すべて正常）。

マージ時に`company/data-backup-status.json`で衝突（別セッションの
koshitsu起承転結再編の反映と同日に重なったため、bukatsu-chiiki等と同型）。
手で行を書き換えず、マージ完了後に`backup_private_data.py`でマージ後のmain
（261ファイル）を対象に取り直して解消。`docs/index.html`は今回は衝突なく自動統合。

マージ後のmain検査は`verify_top_page.py`の素の実行で「collect_at 期限超過:
ai-copyright・elderly-license-revocation・school-nickname-ban」のNGが出たが、
これは今回のテーマと無関係の既知の状態（課題69が対象とする期限超過テーマ群の
一部が未着手のまま）で、`--allow-overdue-collect`（`--apply-promotion`が内部で
使うのと同じフラグ）で確認するとNG0件。push・公開反映・トップページの合計値も
ブラウザ越しに確認済み。作業ツリー（`../isa-wt-task69-constitutional`）は
反映後に削除済み。次回収集は9/25。

**残り課題**: bike-blue-ticketのみ。次回収集予定9/26で現時点では期限超過なし
（前回9/12に課題63側で収集・反映済み）。着手時は他6テーマとのページ構成の
横並び比較（画像・カード・集計の重複、[[feedback_narrative_coherence_preference]]）と
`verify_number_provenance.py`（`exclude_selectors`の`note`漏れ等）を先に確認すると
同じ発見の繰り返しを避けられる。起承転結の再構成をbike-blue-ticketにも適用するかは
オーナー判断待ち。

### 2026-09-19 constitutional-amendment: オーナー指示で図解カードを起承転結型へ再編（本番反映済み）

オーナー指示「図解カードをまとめて起承転結型に再編して」を受け着手。他5山なみ
テーマの再編コミットを先に読み、fukushuto/consumption-tax-cutの「解説カードごと
削除」方式をそのまま当てはめようとしたところ、憲法改正論議だけは各カードに
編集部選定の代表投稿2件（`FEATURED_POSTS`、`add_featured_posts()`が正典との
sha256照合込みで管理）が同居しており、他2テーマには無い固有の価値だと判明
（[[feedback_verify_against_precedent]]どおり、前例を鵜呑みにせず実際の構造を
確認して助かった）。カードごと削除は代表投稿の消失につながるため見送り、
koshitsu-tenpakaiの「画像だけ論点パネルへ移設し、代表投稿は残す」方式を採用。

`build_constitutional_arena.py`に`apply_landing_images()`を新設し、画像を
フォールバック側6パネル＋drawPanel()側JSの両方へ差し戻す（fukushutoの
apply_landing_imagesと同型）。旧カードは画像・説明文・賛否一言を削除し見出しを
「論点ごとのX投稿」へ変更。モーダルのクリック判定は静的forEachからイベント委譲
（`closest('.explainer-card[data-img]')`)へ変更し、動的挿入画像でも反応するようにした
（fukushuto・koshitsuと同型）。CSSは`#explainer-section`スコープの`.explainer-card`
関連3ルールを無スコープ化し、論点パネル側の画像にも同じ見た目を適用した。

標準検査4種・unittest 970件・run_public_checks.pyいずれもNG0件。ローカルサーバーで
実機確認: 山を押す→論点パネルに図解表示→タップで拡大モーダル→Escで閉じる、を
デスクトップ・モバイル幅の両方で確認。「論点ごとのX投稿」側はdata-img属性が無く
モーダルが反応しないことも確認済み。マージ・push・CI（デプロイ・公開ファイルの
検査）とも成功、公開ページ・トップページの反映も確認済み。作業ツリー
（`../isa-wt-constitutional-narrative`）は反映後に削除済み。今回はデータ収集を
伴わないため`THEMES.yaml`の日付・件数系フィールドは変更していない。

これで6テーマ中5テーマ（fukushuto・consumption-tax-cut・koshitsu-tenpakai・
constitutional-amendment、bukatsu-chiiki/henokoは元から重複なし）が起承転結型へ
揃った。残るbike-blue-ticketも着手時に同種の重複がないか確認する価値がある。
