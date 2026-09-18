# 課題69: koshitsu-tenpakai候補統合方式の発見経緯（2026-09-18、`tasks/task-69.md`より切り出し）

`tasks/task-69.md`が400行を超えたため、決着済みの調査記録をこちらへ切り出した
（2026-09-19）。この後の展開（候補統合方式の廃止・標準adapter経路への接続）は
`tasks/task-69.md`本体の「2026-09-18 koshitsu-tenpakai: 候補統合方式を廃止し、
標準adapter経路へ接続・本番反映まで完了（6テーマ目）」を参照。

## 2026-09-18 koshitsu-tenpakai: 収集は完了・公開はkoshitsu固有の監査ゲートで停止（要オーナー判断）

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
