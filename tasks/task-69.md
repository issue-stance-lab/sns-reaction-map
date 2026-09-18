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

**収集**: 新規291件（うち意見229件）を取得。1回目は作業ツリーへの`node_modules`複製漏れで
疎通確認が失敗（`OPERATIONS.md`⓪の既知の手順を後追いで実施）、2回目は分類完了後の
バックアップ工程で`configs/persona.private.json`未復元により失敗。いずれも同じ
worktreeで`--resume`して解消し、累積正典1,733件・意見1,452件へ統合できる状態まで進んだ
（`--promote`はまだ）。次回収集は9/24。

**`--resume --prepare-promotion`で新しい不具合を発見（他テーマには無い、fukushuto含む
4テーマ共通）**: `refresh_adapters/fukushuto.py`は昇格のたびに`build_fukushuto_arena.py`と
`build_fukushuto_process_sections.py`（「投稿の主張を、国会と選管の記録に当ててみた」
一次資料照合セクション、2026-08-24追加）を連続実行するが、後者は`docs/`ページ内に
`<!-- FACT_CHECK_START/END -->`が1組必要という前提で、無いと即エラーで止まる。

2026-09-13の「副首都を山なみ形式で本番反映」（`0447912`）でページを山なみテンプレートへ
作り直した際、このfukushuto専用セクションが引き継がれず消えていた（`git show
0447912^:docs/fukushuto-reaction-map.html`には2422〜2515行に存在、現行は0件）。
山なみ変換後にfukushutoの定期更新を実行したのは今回が初めてで、これまで発覚していなかった。

`refresh_adapters/*.py`を確認したところ、昇格のたびに専用の`*_process_sections.py`を
自動実行しているのは **bike / fukushuto / constitutional / koshitsu の4テーマだけ**
（henoko・bukatsu・elderly・nicknameは該当スクリプトを持っていても昇格経路からは
呼ばない）。この4テーマの現行ページを確認したところ、**bike-blue-ticket・
constitutional-amendment・koshitsu-tenpakaiも同様にFACT_CHECK系マーカーが0件** —
同じ山なみ変換で同種のセクションが失われており、これらのテーマの定期更新を初めて
実行したときに同じ場所で止まる。現行公開ページの表示自体は壊れていない
（欠けているのは次の昇格が失敗する、という形でのみ表面化する）。

**オーナー判断（2026-09-17）**: 「復元して再開」。旧文面（2026-08-24確認当時のまま、
内容更新はせず）を山なみ後の同じ位置（スタンス集計の直後・次に読むテーマの直前）へ
復元し、`build_fukushuto_process_sections.py`で再生成した（`4ca596f`）。参照する5主張・
16投稿は現行正典に全件残存を確認済み。

**`--resume --prepare-promotion`は成功**したが、続けて発見した2件目の不具合:
`build_fukushuto_arena.py`の`apply_public_counts()`（`--public-counts-only`で
「管理対象集計」をページへ貼り直す関数）が、`<!-- PLANET_SECTION_START -->`が
ある場合に早期`return`しており、スタンス集計パネル・詳細データパネル・
「議論の中心」の3箇所が更新対象から漏れていた（0447912の山なみ変換時にこの分岐が
追加された際の見落とし。他テーマ同様、初回の定期更新でしか発覚しない類）。
この3箇所を分岐の外へ移し、両方の版で必ず更新されるよう修正した。

**3件目、今回はここで停止（編集判断待ち）**: 修正後の`--prepare-promotion`で、
今度は`build_planet_data.py`の`validate_reread_records`が
「候補地の正典ID集合と公開JSONの件数が一致しません」で停止。原因は独自性検査
（`independence_gate`）とは別の、表示用の内訳（山・立場別シェア）の話。fukushutoは
共通の再読台帳（`data/verification/reread/`）に未移行で、`候補地・防災災害・
優先順位・その他・費用財源`の5論点だけ専用ファイル（`data/fukushuto_5issues-
reread.json`、2026-09-13時点で823件を区分済み）で内訳表示している。今回の新規91件
（意見）のうちこの5論点に振り分けられた分だけ、内訳の区分（バケット）が未登録のまま
残っており、候補地51件・防災災害25件・優先順位26件・その他14件・費用財源12件、
**合計128件の本文を読んで既存区分へ割り当てる必要がある**（独自性検査自体は候補データの
ままでも合格済みで、これは合否ではなく表示の内訳精度の問題）。「都構想・維新」
「定義・中身」の2論点はもともと区分表示を持たない「未再読」扱いのため対象外。

**128件の編集再読**: 5論点それぞれについて並列で読み（新規サブエージェント5体、
既存区分（バケット）へ割り当てるだけで新しい区分は作らない条件）、件数・ID集合・
summary重複・不正区分の機械検査に加え、いくつかは実際の投稿本文と区分の対応も
抜き取り確認した。5論点合計は823件→951件（`885cb15`）。

**4件目**: 上記を反映して`--prepare-promotion`を再実行しても同じ「候補地」エラーが
再発。原因は`refresh_verified_planet()`（`build_planet_data.bpd.build(THEME)`）が
`--input`の候補を無視し、`THEMES.yaml`が指す**実際の正典ファイルを直接読む**設計
だったため。`DATA_REFRESH.md`「山なみテーマは、正典だけを先に候補データへ置き換える」
の指示はこのための手順と判明——正典（`social-samples/fukushuto_hermes_classified.json`）
とpublic JSON（`build_public_registry.py --topic fukushuto`）を候補の内容へ実際に
差し替えてから`--prepare-promotion`をやり直し、`status: prepared`まで到達した。

**5件目**: `--apply-promotion`で`verify_number_provenance.py`がNG6件
（`issue-count-fukushuto-{slug}`という論点解説カードの件数span）。
`sync_issue_counts.py`は`<!-- PLANET_SECTION_START -->`があるページを
「explainer-cardごと無い」前提で同期対象から外すが、fukushutoは山なみ導入後も
この解説カード群（画像・説明文・批判/対案の一言つき）を残しており、件数だけが
同期されないまま取り残されていた。`apply_public_counts()`に、正典データから
直接この6spanを更新する処理を追加して解消（`29063eb`）。

**6件目（自己招来）**: 修正後の`--apply-promotion`は成功したが、`THEMES.yaml`の
`collect_delta`が`0`になっていた。原因は自分自身の手順——4件目の対応で正典を
事前に手動で候補へ差し替えたため、`refresh_topic.py`が`--resume`時に取り直す
raw.jsonと現行正典のdiffが0件になった（正典に既に入っていたため「新規」が
無くなった）。実際の追加意見数（229）へ手で修正し、`sync_portal_stats.py`で
トップページの「+229件」表示を作り直した。**教訓**: 山なみテーマの正典事前差し替えは
`--apply-promotion`の直前1回に留め、直後に`collect_delta`が動いていないか確認すること。

**本番反映**: 完了（2026-09-17、`a5d9256`でmainへマージ、衝突なし）。マージ後の
main検査（`verify_theme_page.py`・`verify_number_provenance.py`・
`unittest discover`・`run_public_checks.py`）は最終的に全てNG0件。公開サイトで
実ページの件数・一次資料照合セクション・論点解説カード・トップページの「+229件」
表示を確認済み。作業ツリー（`../isa-wt-task69-fukushuto`）は反映後に削除済み。

**残り課題（持ち越し）**: koshitsu-tenpakai・bike-blue-ticket・constitutional-amendment
も`refresh_adapters/*.py`が昇格のたびに専用の`*_process_sections.py`を自動実行する
同型構成で、現行ページのFACT_CHECK系マーカーが0件（3件目の発見時点で確認済み）。
この3テーマの定期更新に着手するときは、fukushutoで踏んだ手順
（①FACT_CHECK復元 → ②apply_public_countsの山なみ分岐に漏れが無いか確認 →
③正典を先に候補へ差し替えてから独自性検査・prepare-promotion → ④論点解説カード等
「山なみ区画の外だが件数を持つ」箇所の同期漏れがないかverify_number_provenance.py
で確認）を先に想定してから着手すると同じ発見の繰り返しを避けられる。ただし
2件目・5件目の不具合は「山なみ形式である」ことだけが条件で他テーマにも起きうる
（`apply_public_counts`の分岐構造自体は全山なみテーマ共通のため、koshitsu/bike/
constitutionalが同じ関数を使っていれば同種の見落としがないか個別に確認要）。

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

**収集**: 新規345件（意見280件）を取得、既存正典（1,605件）との重複0件。
分類モデルkimi-k2.6、taxonomy整合・分類エラーとも0件。まだ`--promote`していない
（`fc36f22`/`852838a`/`af43349`でコミット済み、正典・公開ページは未変更）。
次回収集は2026-09-25。

**分類スクリプトのバグを発見・修正**: `classify_koshitsu_arena_hermes.py`の
`STANCES`は2026-09-14の候補統合（`228bfb3`）で3択（改正反対/改正賛成/中立・情報）
から現行5択（今回案全体を支持/反対/条件付き/未表明/読み取れない）へ変わったが、
is_opinion=false等の投稿に付ける値だけ「中立・情報」のまま残り、許可リストに
存在しない値を書いていた。正典1,605件では該当ケースは全件「今回案全体は未表明」
だったため、コード・プロンプトともにそちらへ統一（`fc36f22`）。これは
「山なみ変換後、初めて定期更新を実行して発覚するバグ」の別の一例（fukushutoの
FACT_CHECK消失・apply_public_counts分岐漏れと同型、[[reference_planet_regen_wipes_hand_edits]]）。

**`--prepare-promotion`が設計どおりの安全装置で停止**: koshitsu-tenpakaiは
他9テーマと違い、`refresh_adapters/koshitsu.py`が汎用の`build_planet_page_preview.py`
/`build_planet_data.py`ではなく専用の`scripts/koshitsu_production.py`
（`quality/candidates/koshitsu-tenpakai/manifest.json`でsha256を固定する
「候補統合方式」、[[reference_planetpage_rollout]]参照）へ処理を委譲している。
この`verify_inputs()`は「正典が承認候補（manifestのprivate_candidate_sha256）と
一致するか」をまず確認し（今回はパス＝正典は09-13監査版のまま無傷）、次に
「今回作った候補（正典1,605件＋新規345件＝1,950件）が正典と完全一致するか」を
確認して**意図的に**`ValueError('皇室の更新候補に未監査の変更があります')`で
止まる。バグではなく「未監査の新規データを検出したら公開経路を拒否する」という
設計そのもの。

**意味すること**: koshitsu-tenpakaiは他9テーマのような「収集→独自性検査→
表示更新」を回すだけでは公開まで進めない。09-13時点で行ったのと同じ規模の
手動監査（新規280件の意見を1件ずつ読み、`quality/candidates/koshitsu-tenpakai/`
配下の全inputsスナップショットとmanifestのsha256を今回の候補に合わせて
作り直す）が必要。当時は`quality/reviews/2026-09-08-koshitsu-*`
（5系統・独立検証含む）のような複数サイクルの独立検証まで行っており、
他テーマの「対象件数÷25件を並列数の目安に」より重い、この論点（皇位継承・
皇室典範という機微な話題）向けに特別に組まれた工程と見られる。

**持ち越し**: この規模の監査を今回のサイクルでそのまま実行するか、収集済み
未公開のまま保留してオーナーに次の方針（都度フル監査を続けるか、他9テーマ同様の
標準adapter経路へ将来的に移行するか）を確認するかは、単独セッションの判断を
超えると判断し、オーナーへ報告のうえ次の一手を確認する。

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
