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
