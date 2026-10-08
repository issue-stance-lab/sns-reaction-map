# 部活動の地域移行 作業記録（2026-09-09〜2026-09-12）

`themes/bukatsu-chiiki.md` が300行の上限（`verify_themes_yaml.py`）を超えたため、2026-10-08にこの区間を切り出した。内容は元の記録のまま。

---

 2026-09-09、課題63として未解決312件をA／B／Cへ仕分けた（[結果](../../quality/reviews/2026-09-09-bukatsu-triage312.md)）。
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
不一致14件の判定内容は[quality/reviews/2026-09-12-bukatsu-missing-independent-38.json](../../quality/reviews/2026-09-12-bukatsu-missing-independent-38.json)に
証拠として保存済み。原本（social-samples）・公開ページへの反映はまだ行っていない。
作業は`../isa-wt-bukatsu-task63-28`（ブランチ`task/bukatsu-task63-28items`、mainへマージ済み・作業ツリー削除済み）で行った。
なお着手前、`build_adoption_registry.py --check`と`verify_adoption_registry.py`が高齢者テーマのスナップショット指紋ズレで
NGだったため、オーナーが別途修正するまで台帳への書き込みを保留していた（修正確認後に本作業を実施）。

 2026-09-12、上記38件を精査し直し、**24件・14件という区分は誤りだったため訂正した。** 38件中9件には
既存の修正案（proposed）が付いており、独立確認はcurrentではなくproposedと比較すべきところを誤って
currentとだけ比較していた。さらに、不一致とした14件のうち5件（既にaccepted状態だった分）は「触れない」
という判断のせいで、独立確認で食い違いが見つかったのに台帳上は無風のacceptedのまま残ってしまっていた。
正しく仕分け直すと**確定23件・保留15件**（[quality/reviews/2026-09-12-bukatsu-missing-independent-38.json](../../quality/reviews/2026-09-12-bukatsu-missing-independent-38.json)に詳細）。

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

そこで[scripts/refresh_planet_section.py](../../scripts/refresh_planet_section.py)を新設した。
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
