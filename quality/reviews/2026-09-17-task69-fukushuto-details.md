# 課題69: fukushuto（3テーマ目）の詳細記録

`tasks/task-69.md`が400行の上限に近づいたため、詳細をここへ切り出した
（2026-09-18）。索引としての要約は`tasks/task-69.md`側に残す。

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

**【2026-09-18訂正】この「bike-blue-ticket・constitutional-amendment・koshitsu-tenpakaiも
FACT_CHECK系マーカーが0件」という記録は誤りだったと判明した。** koshitsu-tenpakai着手時に
実機で確認したところ、3テーマとも該当マーカー（KOSHITSU_AUDIT/PROCESS_SECTIONS/
CLAIM_AUDIT、テーマ固有の名前）は最初から存在していた。おそらく各テーマ固有のマーカー名
ではなく、fukushuto固有の`FACT_CHECK`という文字列で検索した誤検知。詳細は
`tasks/task-69.md`の2026-09-18節（koshitsu標準化）を参照。

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

**残り課題（持ち越し、【2026-09-18訂正】済み）**: 元の記述は「koshitsu-tenpakai・
bike-blue-ticket・constitutional-amendmentもFACT_CHECK系マーカーが0件」だったが、
これは誤りと判明済み（上記訂正参照）。実際に有効な持ち越し事項は②〜④のみ:
②apply_public_countsの山なみ分岐に漏れが無いか確認 → ③正典を先に候補へ差し替えて
から独自性検査・prepare-promotion → ④論点解説カード等「山なみ区画の外だが件数を
持つ」箇所の同期漏れがないかverify_number_provenance.pyで確認。2件目・5件目の
不具合は「山なみ形式である」ことだけが条件で他テーマにも起きうる
（`apply_public_counts`の分岐構造自体は全山なみテーマ共通のため、koshitsu/bike/
constitutionalが同じ関数を使っていれば同種の見落としがないか個別に確認要）。
