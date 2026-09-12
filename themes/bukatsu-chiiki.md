# 部活動の地域移行（bukatsu-chiiki）の作業記録

`THEMES.yaml` の工程の状態（`collect` `refresh_at` など）はあちらが正典。
ここには更新のたびに書き足す経緯だけを置く。

---

2026-07-12に新規127件を収集。
2026-07-23に同一10検索語で223件を取得し、既存との重複62件を除いた新規161件を追加、累計467件。
全件をHermes方式（main_issue / stance / intensity / is_relevant / is_opinion）で再分類。
関連464件、意見389件。
2026-08-02に同じ10検索語で222件を取得し、重複63件を除いた新規159件をHermes分類（関連159件、意見130件）。
累計626件、関連623件、意見519件。
7/23追加分と8/2追加分を同一条件で比較し、移行支持が6.1pt増加、教員の働き方が8.9pt増加、感情highが8.0pt減少。
2026-08-14に同じ10検索語で250件を取得し、重複132件を除いた新規118件をHermes分類（関連117件、意見90件、分類エラー0件）。
累計850件、関連841件、意見689件。
論点は 教員の働き方212／制度・移行プロセス146／教育的意義・機会131／受け皿・指導者95／費用・家庭負担67／その他35／地域格差3、賛否は 移行支持315／慎重・反対217／条件付き・改善要求128／中立・情報29。
潮目は8/8追加分80件と8/14追加分90件の比較で、条件付き・改善要求が4.3pt増、教員の働き方が4.9pt増、感情highが3.9pt減。
注目ポイント4枚は生成側が無いため手で更新した（課題43の積み残し1）。
分類は途中1バッチがHermesの非JSON応答で落ち、分類器の --resume で96件目から再開した。
 2026-08-27定例として8/26夜に同じ10検索語から314件を取得。
重複52件を除く新規262件をkimi-k2.6で分類し、関連262件、意見239件、分類エラー0件。
累計1,216件、関連1,203件、意見993件。
論点は 教員の働き方283／制度・移行プロセス227／教育的意義・機会189／受け皿・指導者143／費用・家庭負担97／その他45／地域格差9。
賛否は 移行支持414／慎重・反対329／条件付き・改善要求206／中立・情報44。
前回意見65件と今回239件の比較で、移行支持が8.2pt増、受け皿・指導者が10.3pt増、感情highは1.4pt減。
ページと潮目表示を更新し、次回予定は2026-09-03とした。
 2026-09-02、課題54段階3として一次資料照合を実施し公開JSONへ接続（主張7件・確定投稿32件・確認者種別editorial_review）。
`scripts/build_bukatsu_process_sections.py` は他6テーマの照合生成器と違い公開HTMLへ書き込まない特殊な形（`FACT_CHECKS`/`CHECKED_AT`/`write_provenance_records()`のみを出力）。
理由は段階7で本テーマを惑星ページとして 作り直す予定があり、いま公開HTMLに事実確認セクションを差し込むと段階1で約束した「公開HTMLはバイト単位で変わらない」を破るため。
同日、独立レビューで確認済み母数（993件）と 公開母数（1139件）のズレを指摘され、9/2更新分の増分146件を同じ基準で読み足し（coach-payに2件追加）、母数を1139件へ揃えてmain公開した。
 2026-09-02、課題54段階5として地下水脈2本を抽出した（`data/verification/bukatsu-chiiki-veins.json`、確認者種別ai_assisted）。
「指導者の待遇の低さ」（慎重・反対と条件付き・改善要求が同じ懸念を共有するが中止か改善継続かで分かれる）と「移行しても教員負担が実質減らない懸念」（同様に慎重・反対と条件付き・改善要求が分かれる）の2本。
賛否の機械的な鏡像になる3本目の候補は根拠が弱く見送った。
段階6（build_planet_data.pyへの接続）はまだ未着手で公開JSON・公開HTMLへの影響なし。
 2026-09-02、独立レビューで段階4「沈んだ大陸」4件の数え方に誤りを指摘され修正した（`data/verification/bukatsu-chiiki-sunk-continents.json`）。
4件目「資格要件」は指導者の資格・経験を求める意見が5件あるのに「0件」としていた誤りを直し、東京都限定の但し書きと機械可読の検索式（`match_rule`）を追加。
`sns_count`の意味（争点そのものへの言及件数）を4件で統一した。
公開ページ・公開JSONへの接続なし。
 2026-09-02、同レビューで段階5「地下水脈」がAIの分類結果（summary）の組み替えだった指摘を受け、代表投稿12件を分類器のsummary・reasonを見ずに本文だけで読み直した（`data/verification/bukatsu-chiiki-veins.json`）。
vein-1（指導者の待遇の低さ）は変更なし、vein-2（移行しても教員負担は実質減らない懸念）は6件中3件を本文検索で差し替え、論点が4つにまたがったため`issue_id`を`issue_ids`配列に変更。
移行支持460件を含む水脈を探したが成立せず、2本のまま採用。
`curated_by`・`checked_by`を`ai_assisted`から`editorial_review`に変更し、投稿要約は`data/verification/`の規約に合わせて削除した。
段階6はまだ未着手で公開JSON・公開HTMLへの影響なし。
 2026-09-03、段階5レビュー指摘8への対応として`scripts/verify_ocean_layer.py`を新設し、沈んだ大陸・地下水脈の2ファイルを検査対象にした（件数上限・必須項目・match_rule再現性・代表投稿の正典実在・要約非混入・checked_byの公開未接続を確認）。
既存の4件・2本ともこの検査を通過。
段階6はまだ未着手。

 2026-09-09、課題63として未解決312件をA／B／Cへ仕分けた（[結果](../quality/reviews/2026-09-09-bukatsu-triage312.md)）。
作業台帳411件から確定98件・未解決312件を再現し、保存済み根拠だけで処理できる分は0件と確認した。
B（ルール決定で処理可能）142件、C（追加確認が必要）170件。Bの最大群131件は、論点に
送迎・移動の安全／公費と運営費の負担主体／子どもの安全と事故対応／活動場所の確保の受け皿が無いことによる組ごとの停止。
論点を増やすと投票の意味と1,395件の再分類に波及するため、増設せず寄せ方を明文化する案を推奨した。
312件の外側に、旧記録のみの966件と、どの記録にも無い17件が残る。原本・採用台帳・公開ページは変更していない。

 2026-09-12、課題63の再チェック方式が時間がかかりすぎる問題を調べる過程で、`data/verification/reread/bukatsu-chiiki.json`の
未読173件（現行意見）からランダム30件を抽出し、kimiの元分類を見ずにClaudeが独立に読んで比較した。
is_relevant/is_opinionは87%一致したが、main_issueは65%、**stanceは46%**しか一致しなかった。
原因は`scripts/classify_bukatsu_arena_hermes.py`のprompt（`prompt_for()`）で、main_issueには説明文があるのに
**stanceはラベル名だけを渡していた**こと、加えて2026-09-09にCEOが承認したルール7-b
（要求の無い問題指摘だけの投稿は「中立・情報」）が実際のprompt文に反映されていなかったこと。
stanceに判定順序（賛否の明示→具体的要求の有無→中立）とルール7-bを明文化したprompt（コミット`e81f86b`、main反映済み）
へ差し替えて同じ30件を再検証すると、stance一致率は70%へ改善した。
さらに2回、言い回しを調整したが（is_opinionとの混同分離、暗黙の不満の扱い）、stanceは56%・63%と上下に揺れただけで
明確な追加改善は無く、**30件という検証規模では見分けられない誤差の範囲**と判断して打ち切った。
残る不一致は今後、10%抜き取り確認（検討中の新しいチェック方式）で継続的に監視する方針。
この作業は`../isa-wt-bukatsu-check-pilot`（ブランチ`task/bukatsu-check-pilot`、mainへマージ済み・作業ツリー削除済み）で行い、
既存の正典・採用台帳・公開ページには一切触れていない。

 2026-09-12、課題63の「独立確認が不足している別群28件」に着手。対象一覧が記録に残っておらず再現できなかったため、
`data/verification/editorial-adoption-current.json`から`independently_checked=false`の部活動記録を機械的に数え直すと38件だった
（TASK_BOARDの「28件」とは数が合わないが、これが唯一再現可能な定義）。本文のみを渡し現行案を見せずにClaudeが独立に判定し、
現行案と比較した結果、24件が一致・14件が不一致だった。オーナー判断により、**一致した24件だけをadoption_status=acceptedとして
正式に確定し、不一致だった14件は採用せず台帳に一切触れていない**（保留のまま）。台帳の`counts`集計欄も再計算した。
不一致14件の判定内容は[quality/reviews/2026-09-12-bukatsu-missing-independent-38.json](../quality/reviews/2026-09-12-bukatsu-missing-independent-38.json)に
証拠として保存済み。原本（social-samples）・公開ページへの反映はまだ行っていない。
作業は`../isa-wt-bukatsu-task63-28`（ブランチ`task/bukatsu-task63-28items`、mainへマージ済み・作業ツリー削除済み）で行った。
なお着手前、`build_adoption_registry.py --check`と`verify_adoption_registry.py`が高齢者テーマのスナップショット指紋ズレで
NGだったため、オーナーが別途修正するまで台帳への書き込みを保留していた（修正確認後に本作業を実施）。

 2026-09-12、上記38件を精査し直し、**24件・14件という区分は誤りだったため訂正した。** 38件中9件には
既存の修正案（proposed）が付いており、独立確認はcurrentではなくproposedと比較すべきところを誤って
currentとだけ比較していた。さらに、不一致とした14件のうち5件（既にaccepted状態だった分）は「触れない」
という判断のせいで、独立確認で食い違いが見つかったのに台帳上は無風のacceptedのまま残ってしまっていた。
正しく仕分け直すと**確定23件・保留15件**（[quality/reviews/2026-09-12-bukatsu-missing-independent-38.json](../quality/reviews/2026-09-12-bukatsu-missing-independent-38.json)に詳細）。

保留15件は、台帳上`adoption_status=hold`に加え、共通再読台帳（`data/verification/reread/bukatsu-chiiki.json`）
へも`evidence_quality=verified`・`bucket=disputed_unresolved`として登録した。**「未確認」ではなく
「確認済みだが判定できず保留」と区別して記録できる。** 確定23件のうち1件（tweet 2086309235479265726、
論点=制度・移行プロセス）は実際にis_opinion: false→trueへ原本を修正する必要があり、適用した
（意見1,139→1,140件）。この1件に連動して、公開データJSON・DATA_SHEET・沈んだ大陸4件の母数・
下位論点（島）ファイル・採用台帳（段階D）のスナップショットをすべて揃え直した（新規1件はいずれの
沈んだ大陸にも該当しないことをmatch_ruleで確認済み）。

作業は`../isa-wt-bukatsu-apply`（ブランチ`task/bukatsu-apply-accepted`、mainへマージ済み・作業ツリー削除済み）で行った。
**`docs/bukatsu-chiiki-reaction-map.html`（公開ページ）はまだ更新していない。** 標準検査は単体テスト917件中914件OK
（2件はdocs/未更新による既知の差分、1件はcollect_at期限超過で無関係）、`build_planet_data.py`の独自性検査に合格。
公開ページへの反映はCEO承認後の`release`手順で行う。

 2026-09-12、CEO承認（`company/APPROVALS.yaml` の `approval-20260912-002`）を得て公開ページへ反映した。
その過程で**「公開済みの山なみページを、公開後に更新する手段がこのプロジェクトに存在しない」ことが判明した**
（`build_planet_page_preview.py`は旧→新の1回きりの変換専用で、既に山なみが入ったページは安全装置が拒否する。
`build_bukatsu_arena.py`／`update_bukatsu_tide.py`／`sync_issue_counts.py`はいずれも山なみ判定で件数更新を
意図的にスキップしており、2026-09-10のコード内コメントに「段階3で挿入先を設計する」と将来の宿題のまま
残っていた）。bukatsu-chiiki・elderly-license-revocationは2日前に変換されたばかりで、公開後の更新は今回が初めて。

そこで[scripts/refresh_planet_section.py](../scripts/refresh_planet_section.py)を新設した。
`PLANET_SECTION_START/END`の区間だけを最新の正典データで作り直し、区間の外（ヘッダー・フッター・投票等）は
変更しない。既存のrender_planet/split_prototype/build_section（`build_planet_page_preview.py`）をそのまま
再利用し、同じ入力で2回実行しても差分が出ないことを確認済み。今後のbukatsu-chiiki・elderly-license-revocationの
定期更新や、残り8テーマが山なみへ移った後にも使える。

実装中に3つの副作用を発見・対応した：
1. bukatsu-chiiki専用の「この論点のなかを見る」リンク（go-card）が`build_section()`自体には無く、
   `build_bukatsu()`内の後処理でのみ挿入されていた。同じ処理を再現しないと再生成のたびに消えるところだった
   （課題47と同型の欠落）
2. lead文・調査条件内のdata-methodテキストは、山なみ判定により`sync_issue_counts.py`／`build_bukatsu_arena.py`
   のどちらからも素通りされ、初回変換以来更新されていなかった。既存の`apply_lead`/`apply_note`を直接呼んで揃えた
3. 旧2Dスタンスマップ（SM_RAW）は「切り替えとして戻す予定」でデータを保持したまま表示だけ外されている。
   生成には現行分類器に無い旧専用フィールドが要るため、山なみ運用中は対象外と
   `configs/bukatsu-chiiki-reaction-map.json`の`denominator_exceptions`へ理由付きで明記した

反映後、`data/verification/bukatsu-chiiki.json`（仮名化検証データ）の再生成、トップページ
（`scripts/sync_portal_stats.py`）の同期も行った。標準検査は単体テスト917件**全件OK**
（事前から存在した無関係の1件も本反映で解消）、verify_theme_page.py／verify_number_provenance.py／
verify_top_page.py（期限超過6テーマは既知）／verify_adoption_registry.py／verify_page_originality.py
すべて合格。公開URLで実際に「意見1,140件」表示を確認済み。

作業は`../isa-wt-bukatsu-publish`（ブランチ`task/bukatsu-publish-38fix`、mainへマージ済み・作業ツリー削除済み）で行った。
