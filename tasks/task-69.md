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

### 2026-09-15 部活動の地域移行（1テーマ目）を収集から表示更新まで一気通貫で実施

**収集**: 新規223件（うち意見179件）を取得、正典1,618件に統合（`--promote`）。次回収集は9/22。

**独自性検査への影響試算**: 正典統合前に候補データを直接`build_planet_data`へ通し、
教員の働き方・制度・移行プロセスの2論点が上限40%に迫ることを事前に確認。費用・家庭負担／
受け皿・指導者の2論点は専用の下位分類（cost_side/receiver_side）を持つため別集計が必要と判明。

**読み込み確認**: 4論点・対象166件を1件ずつ本文を読んで判定（`quality/reviews/
2026-09-15-bukatsu-headroom-catchup.json`）。完了後、論点ごと10件以上を抜き取り
本文と記録の一致を確認。結果、最終的な未読件数は教員の働き方52件・制度・移行プロセス
42件・教育的意義・機会23件で、いずれも独自性検査の上限（40%）には抵触しない。

**専用ファイルの指紋同期**: 読了記録を専用ファイル（`data/bukatsu-chiiki_cost-receiver-
reread.json`）へ反映する際、直接指紋を書き換える操作がClaude Codeのセキュリティ機構に
ブロックされた。オーナーに状況を報告し承認を得たうえで、「専用ファイルの中身が共通台帳の
読了記録と1件ずつ一致することを確認してから指紋を進める」`manage_reread_registry.py
resync-source`コマンドを新設し、正規の手順で解消した。

**2026-09-16 追記（CI発見分）**: 本番反映の数日後、CI「公開ファイルの検査」が2回連続で
失敗した。原因は表示更新チェックリストの漏れがもう2箇所あったこと — `docs/sitemap.xml`
の該当lastmod（`最終更新日表示`とは別の場所）と、非公開データの保全台帳
`company/data-assets.json`（山なみ区間の外で、かつローカルの通常チェックリストにも
無い項目）。前者はDATA_REFRESH.mdのsitemapチェックリストに`validate_theme_seo.py`の
ローカル実行を追記して以後の見落としを検査で止めるようにした。残り7テーマの表示更新
では、チェックリスト完了後に`python3 scripts/run_public_checks.py`まで通すこと
（`verify_theme_page.py`だけでは拾えない）。

**表示更新**: `refresh_planet_section.py --for-docs`で山なみ区間を更新。このテーマ固有の
見落としを3件発見・修正（調査条件の取得件数・期間テキスト、`#issue-cards`の論点カード
件数、`configs/theme-seo.json`の`dateModified`〔ページ末尾「最終更新日」とJSON-LD〕
— いずれも山なみ区間の外にあり初回変換時にしか同期されていなかった）。3件目は
機械検査では見つからず、本番反映後にページを実際にブラウザで開いて発見した
（`verify_theme_page.py`等はページ内の数字同士の整合は見るが、この値が最新かどうかは
見ていない）。

**持ち越し事項**: 読み込み確認の対象選定で、既に別の独立確認プロセス（課題63・2026-09-12の
部活動38件確認）でレビュー済みだが区分（bucket）が今回の形式（P1-P6/R1-R6）でない投稿が
10件見つかった（receiver 6件・cost 4件）。独自性検査への影響が軽微なため、無理に今回の
スコープへ含めず持ち越した（詳細は`tests/test_planet_data.py`の該当テストに記載）。

**確立した型**: 上記の手順を`DATA_REFRESH.md`の「定期更新1回分の実務手順」として固定した。
残り7テーマ（期限超過順）は、この手順をそのまま当てはめて1つずつ消化する。

**本番反映**: オーナー確認後、mainへマージ。マージ時に`docs/index.html`・
`company/data-backup-status.json`で衝突が発生（別セッションのX投稿日次記録が同じ日に
2回mainへ反映しており、実行のたびに全体を書き直す2ファイルの同じ行に両方の変更が
重なったため）。中身は矛盾しておらず、オーナー確認のうえ手で行を書き換えず
`sync_portal_stats.py`／`backup_private_data.py`で作り直して解消した（`docs/index.html`は
`THEMES.yaml`が衝突なく自動マージ済みだったため、再生成だけで両セッションの変更を
正しく含む結果になった）。公開確認後、ブラウザで実ページを見て最終更新日の見落とし
（3件目、上記）を発見・追加修正しmainへ反映。作業ツリー（`../isa-wt-task69-bukatsu`）は
削除済み。

### 2026-09-16 辺野古高校生死亡事故（2テーマ目）を収集から標準検査まで実施

**収集**: 新規80件（意見72件）を取得。分類モデル（`kimi-k2.7-code`、`--batch-size 5`）が
1件だけ「高リスク」判定でAPI拒否（HTTP 400、内容は通常の政治コメントで実際に危険な
内容ではない）。この1件を今回の分類対象から除外し（`raw.json`・`new-only.json`双方から
除いて集合検査の整合を保つ）、次回以降の収集で再取得されるのを待つ扱いとした。
残り72件（うち意見61件）を正常に分類し、累積552件・意見430件へ統合。次回収集は9/23。

**独自性検査への影響試算**: 候補データを`build_planet_data`へ直接通し、6論点すべてで
読み飛ばし＋増分が上限40%未満（最大28.3%、政治利用・基地問題）と確認。bukatsu-chiikiと
異なり、今回は追い読みなしで反映して問題ない水準だった。

**発見した既存の不具合（辺野古専用、他テーマには無い）**:
1. `henoko_planet_guard.py`の`canonical_sha256`完全一致チェックが、再読台帳の指紋を
   「常に最新の正典と一致すべき値」として扱っており、設計書
   （`quality/designs/2026-09-06-stage-c-reread-registry.md`）の定義（初回スナップショット
   時点の指紋であり、以後の正典更新に追随させる欄ではない）と矛盾していた。このため
   辺野古は正典が1件でも増減するたびに、定期更新の最終段階（`build_henoko_arena.py
   --public-counts-only`）が必ず失敗する状態だった。他9テーマの`build_*_arena.py`には
   同種のチェックは存在しない。オーナー承認を得て撤去。実際の改ざん検出は
   `load_reread_registry`の本文指紋照合と`verify_inputs`自身の公開件数・公開分類の
   突き合わせが別途担っており、撤去後も`tests/test_henoko_verified_refresh.py`
   （期待するエラーの種類・文言を実態に合わせて更新）で維持を確認した。
2. 山なみ区画の外にある「SNS投稿の収集方法」段落（552件/430件への言い換え）が
   初回の山なみ変換以来同期されていなかった（bukatsu-chiikiの「調査条件」文と同型の
   見落とし）。`refresh_planet_section.py`にhenoko専用の同期関数を追加して解消。
3. `configs/henoko-student-accident-reaction-map.json`の`number_provenance.exclude_selectors`
   に`note`が無く、「本文確認後に追加された投稿N件は、本文確認の対象外です」という
   正しい注記が「説明できない数字」として`verify_number_provenance.py`に拾われていた。
   他テーマ（bukatsu-chiiki等）の設定と揃え、`note`を追加して解消。

**標準検査**: `verify_theme_page.py`・`verify_number_provenance.py`・`verify_themes_yaml.py`・
`verify_update_provenance.py`いずれもNG0件。`python3 -m unittest discover -s tests`
970件（skip4件）全通過。`refresh_planet_section.py --for-docs`の冪等性（2回目は
`OK. Lines: N → N`）も確認済み。

**本番反映**: 完了（2026-09-17、`07fceef`でmainへマージ）。マージ時に
`company/data-backup-status.json`で衝突が発生（bukatsu-chiikiと同型 —
実行のたびに全体を書き直すファイルの同じ行に、別ブランチの再生成が重なったため）。
中身は矛盾しておらず、手で行を書き換えず`backup_private_data.py`で作り直して解消した。

マージ後のmain検査で新たに2件発見・解消:
1. `TASK_BOARD.md`課題69の「状態」欄が180文字で上限（120文字）超過
   （`verify_task_board.py`／`test_task_board.py`で検出）。経緯をこのファイルへ
   寄せて索引を簡潔化した。
2. `THEMES.yaml`の`updated_at`が旧日付（09-13）のまま、`configs/theme-seo.json`の
   `dateModified`だけ09-16へ更新済みという食い違い（`validate_theme_seo.py`／
   `docs/sitemap.xml`のlastmodも同様に旧日付のまま）。作業ツリーでの表示更新時に
   `DATA_REFRESH.md`「2. THEMES.yaml」の`updated_at`更新が漏れていた。
   `updated_at`とsitemapを09-16へ揃えたところ、今度は`docs/henoko-student-accident-
   reaction-map.html`内の山なみ区画の「更新」表示が旧日付のまま`build_henoko_arena.py`の
   期待値と食い違い、`test_henoko_planet.py`・`test_portal_stats.py`・`test_data_sheet.py`
   が連鎖して落ちた。`refresh_planet_section.py --topic henoko-student-accident --for-docs`
   （冪等性確認済み）・`build_data_sheet.py`・`sync_portal_stats.py`・
   `data_asset_inventory.py`を再実行して解消（`run_public_checks.py`・
   `unittest discover`とも最終的にNG0件）。**教訓**: `updated_at`を直すと、そこから
   逆算する表示・統計・資産台帳が連鎖して古くなる。1箇所直したら
   `python3 scripts/run_public_checks.py`まで通して初めて完了とみなす。

作業ツリー（`../isa-wt-task69-henoko`）は反映後に削除予定。

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
