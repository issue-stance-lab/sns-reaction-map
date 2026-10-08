# 課題69: constitutional-amendment（7テーマ目）の収集から本番反映の詳細（2026-09-18〜19）

tasks/task-69.md が400行上限のため切り出した（2026-10-09）。本文は元の記述のまま。

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
