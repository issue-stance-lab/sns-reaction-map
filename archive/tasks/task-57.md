# 課題57: 公開データ基盤と公開承認物の一本化（旧15-A・課題54の前提）【完了 2026-08-31】


**状態**: **段階4完了（2026-08-31）。トップページと公開10テーマすべてを接続済み**
（部活動・あだ名禁止・消費税減税・自転車青切符・生成AIと著作権・憲法改正・高齢者免許返納・
辺野古学生事故・副首都・皇室典範）。当初は10テーマ中2テーマで「候補生成中は公開JSONに繋げない」
壁に当たり、オーナー承認により段階5を先行着手した。段階5の完了でその前提が消えたため、
最後に残ったあだ名禁止も接続した
**優先度**: **最優先の基盤作業**。課題54の3D実装より先に完了する
**正典**: `quality/designs/public-data-foundation-rebuild.md`
**対象**: 公開中の10テーマ。高市テーマは非公開保全し、公開合計・トップ・sitemapへ含めない
**前提**: 課題55の段階0〜5-2完了。4週間のSearch Console監視は並行して続け、課題57の着手を止めない

**目的**: 収集数・意見数・論点・立場・表現強度・期間・更新日をGit管理の公開データJSONへ集約し、
トップ、10テーマ、sitemap、将来の3D用データが同じ契約を読むようにする。公開HTML、旧SQLite、旧ルートを
次回生成の入力にしない。課題15-Aはこの課題へ統合し、二重管理しない

**実施順**（各段階の成功条件を満たすまで次へ進まない）:

0. 最新mainから専用worktreeを作り、非公開正典を復元し、課題管理を課題57へ統合する
1. 公開10テーマの入力・生成器・数字表示場所を棚卸しし、値ごとの正典を1つに決める
2. JSON Schema、安定した論点／立場ID、数字の不変条件、読者向け用語を確定して独立レビューとCEO確認を受ける
3. 部活で公開データ生成・完全照合を実証し、同じ生成器で残り9テーマとcatalogを作る
4. トップ、10テーマ、sitemapの公開候補を公開データへ接続し、旧数字・旧用語を除く
5. `refresh_topic.py` の候補作成と既存promotion manifestへ接続し、一部だけ古い状態で昇格できないようにする
6. 全テーマ、トップ、数字の出所、SEO、ドメイン、投票・計測・広告、全テスト、2回生成差分0を確認し独立レビューを受ける
7. 実装・検査記録を残して課題57と旧15-Aを完了し、課題54へ公開データ契約を引き渡す

**完了条件**:

- 公開10テーマの数字、論点、期間、更新日、用語が公開データJSONとcatalogから再現できる
- 「収集した投稿」「分析対象の意見」「主要論点」「その他」の意味が全ページで一致する
- トップ、10テーマ、sitemapの公開候補が同じcatalogを参照する
- 非公開正典がある完全監査と、非公開正典が無い環境での公開物再生成を区別できる
- 通常のデータ更新でも公開JSON、ページ、トップ、sitemapが同時に候補化される
- 課題54がHTMLや設計書の固定数字を読まず、公開JSONから3D用データを作れる
- 一般公開、Search Console再確認、AdSense再申請は行っていない

**対象外**: 収集データの再分類、3D実装、一般公開、AdSense再申請、既存SQLiteの削除・履歴書き換え、外部DB導入

**進捗（2026-08-31）**: 段階0を確認済み。`task/public-data-foundation` の専用worktreeを
最新main（`3f80271`）へ合わせ、バックアップ `private-data-20260831T123456320691.tar.gz` から
非公開正典を復元した。`published: done` の公開10テーマについて `sample_file` の欠落は0件。
段階1では、公開値の入力・生成器・表示場所・検証データ・旧SQLite・参考実装を棚卸しした。
公開10テーマの数値表示1,306か所を抽出し、既存の出所検査で不明0件を確認した。検証用データは
新しい公開正典にせず、トップ・テーマ・sitemapを公開JSON／catalogへ接続する方針を確定した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage1-inventory.md`。公開物は変更していない。

**段階5 実装（2026-08-31）**: `refresh_topic.py` は承認前に隔離した候補コピーで、累積正典・
公開JSON・catalog・テーマページ・トップ・sitemap・robots・テーマ台帳・SEO設定をまとめて生成し、
既存promotion manifestへ全ファイルのSHA-256を記録するようにした。承認後の
`--apply-promotion` は再生成せず、manifestで固定した候補だけを適用する。候補生成の実地確認で
22ファイルを固定できること、全unittest 327件成功を確認。収集予定日超過は `WARN` とし、
公開物の整合不良とは分けて表示する。一般公開は行っていない。

段階5単体の自動検査と実地確認は完了。独立レビューは、段階4の残りを接続した後の段階6で
公開候補全体をまとめて行う。

**段階4：消費税減税を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
論点カードを `data/public/themes/consumption-tax-cut.json` から同期するようにした。反応マップ見出しが
初版の固定文字列しか置換できず「意見612件」のまま残っていた問題を修正し、候補公開JSONの
`opinion_count=2,852` を貼り直す後工程を追加。ヒーローの収集数・意見数、議論の中心、作り方欄も
同じ公開JSONから同期する。公開ページ候補から「公開中の11テーマ」を除去した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-consumption-tax.md`。

**段階4：自転車青切符を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
論点カード、論点ナビ、議論の中心、アリーナのセクターを候補公開JSONから同期するようにした。
ヒーローの「分析対象201件」は、実際には全意見384件のうち主要5論点に入った合計だった。
候補公開JSONから「収集384件／意見384件／主要5論点201件／その他183件」と意味を分けて貼り直す。
立場を明示できた221件の編集部再読集計は別の検証データなので維持した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-bike-blue-ticket.md`。

**段階4：生成AIと著作権を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
論点カード、アリーナのセクター、詳細データの論点・立場別集計、アトラス、ヒーロー、注目ポイント、アリーナ母数を候補公開JSONから同期するようにした。
アリーナの点データは個々の投稿から作る必要があるため、従来どおり候補正典から生成し、同じ候補の集計JSONで表示歌才を確定する。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-ai-copyright.md`。

**段階4：憲法改正を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
ヒーロー、調査条件、議論の中心、注目ポイント、マップ見出し、詳細集計を候補公開JSONから貼り直す後工程を追加した。
マップの点と代表投稿は個々の投稿から作るため、候補正典から生成し、同じ候補公開JSONで集計表示を確定する。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-constitutional-amendment.md`。

**段階4：高齢者免許返納を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
ヒーロー、調査条件、議論の中心、注目ポイント、マップ見出し、詳細集計を候補公開JSONから貼り直す後工程を追加した。
マップの点と代表投稿は個々の投稿から作るため、候補正典から生成し、同じ候補公開JSONで集計表示を確定する。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-elderly-license-revocation.md`。

**段階4：辺野古学生事故を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
ヒーロー、反応マップ見出し、論点別本文、注目ポイント、詳細の論点別・立場別・クロス・強度別集計を候補公開JSONから貼り直す後工程を追加した。
公開JSONが0件を明示し仮名化検証データがその論点を省略する場合も、両方を同じ0件として比較する検査に修正した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-henoko-student-accident.md`。

**段階4：副首都を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
ヒーロー、調査条件、議論の中心、アリーナのセクター、注目ポイント、スタンス集計、詳細集計を候補公開JSONから貼り直す後工程を追加した。
候補生成で既存アダプターの事実確認データ出力先の不整合を検出・修正し、候補生成の冪等性を回復した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-fukushuto.md`。

**段階4：皇室典範を接続（2026-08-31）**: `issue_counts.basis` を `public_json` に変更し、
ヒーロー、調査条件、議論の中心、アリーナの論点順・見出し、注目ポイント、スタンス集計、詳細集計を候補公開JSONから貼り直す後工程を追加した。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-koshitsu-tenpakai.md`。

**段階6：総合検査と独立レビュー（2026-08-31）**: 設計書の10項目
（公開データSchema・完全照合／全10テーマの`verify_theme_page.py`／`verify_top_page.py`／
`verify_number_provenance.py`／SEO・sitemap検査／ドメイン移行回帰／投票・GA4・AdSense・
Supabase・OGP・topicId・選択肢順序の回帰／全unittest／2回生成差分0／`git diff --check`）を
すべて実行し成功を確認した。全unittest **353件成功**。公開経路の生成チェーン
（公開JSON→論点カード→SEO trust→トップ→SEOアセット→検証期間→データシート）を通しで2周実行し、
1周目・2周目とも差分0を実地確認（従来はテーマ単位の`--check`のみだった）。独立レビュー観点
（正典の重複・旧HTML/SQLite/旧ルートからの逆流・公開JSONへの内部情報混入・10テーマの契約適合・
既存機能の保全）はすべて重大指摘0件。公開JSON全11ファイルを走査し、投稿URL・非公開パス・
スクリプト名・@ユーザー名・ペルソナ関連語の混入0件を確認した。`collect_at`期限超過3テーマ
（ai-copyright / constitutional-amendment / fukushuto、いずれも8/30予定）はWARN表示で
exit 0（段階5で実装済みの運用警告と公開停止の分離どおり）、公開物の整合不良ではない。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage6-audit.md`。

**段階7：課題57の完了と引き継ぎ（2026-08-31）**: 実装・検査記録を`quality/reviews/`へ保存、
`TASK_BOARD.md`の課題57と旧15-Aを完了に更新、`company/HANDOFFS.yaml`の
`public-data-foundation`を`complete`にし次の作業を課題54（3D「議論の惑星」）へ変更した。
課題54へ引き渡すのは`data/public/catalog.json`・`data/public/themes/{theme}.json`・
`configs/public-data-taxonomy.json`（Schema・安定ID・立場/強度分布・監査コマンド一式）。
一般公開・Search Console再確認・AdSense再申請は実施していない（公開内容の変更は15-Bと
課題54の完了後、15-CのCEO承認でまとめて行う）。専用worktree
（`/Volumes/M2-WorkSpace/Projects/副業/isa-wt-task57-nickname`）は非公開正典の同期・
バックアップ確認後に片付ける。

**課題57は完了した。** 次は15-B（手動編集・独自価値の確認台帳整備）と課題54。

**段階4：あだ名禁止を接続し、段階4を完了（2026-08-31）**: 段階5により
「候補ツリーの中で公開JSONを作り直してから `finalize` が走る」順序が保証されたため、
見送っていた最後の1テーマを接続した。`issue_counts.basis` を `public_json` に変更し、
`build_nickname_arena.py` に `apply_public_counts()` と `--public-counts-only` を、
`refresh_adapters/nickname.py` に `finalize()` を追加。リード文・調査条件・注目ポイント・
論点カード・マップ見出し・投票とアリーナの `var issues`・論点ナビ・論点ブロックの集計・
詳細データを候補公開JSONから貼り直す。代表投稿とアリーナの点は公開JSONに入らないため
候補正典から作り続ける。**公開ページのHTMLはバイト一致（見た目は変わらない）。**
古い公開JSONで貼る事故は `source_sha256` の鮮度確認で止まることを実地確認した。
「2回生成して差分ゼロは通るのに数字だけ古い」すり抜けは、公開JSONの件数を1件増やすと
ページ5か所の数字が増えることを検査するテストで塞いだ。あわせて
`tests/test_public_data_contract.py` に全公開テーマ横断の検査を2件追加し、
①10テーマすべての `basis` が `public_json` ②10テーマすべての adapter が `finalize` を持つ
ことを固定した（1テーマでも戻すと落ちる）。全unittest 353件成功。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage4-school-nickname-ban-connected.md`。

**段階4→段階5の順序変更の判断（2026-08-31）**: 部活動（1本目）で「昇格後に正典から
数え直す後工程（finalize）があるテーマだけ、鮮度確認つきで公開JSONへ安全に繋げる」ことを
確認したが、あだ名禁止（2本目）はその後工程を持たず、候補生成そのものが正典（候補ファイル）
から直接件数を計算していたため接続を見送った（詳細は下記および
`quality/reviews/2026-08-31-public-data-foundation-stage4-school-nickname-ban.md`）。
10テーマ中2テーマで同じ制約に当たった時点で、残り8テーマも同様の壁に当たる可能性が高いと
判断し、個別テーマの接続を1つずつ進めるより、`refresh_topic.py`の候補作成パイプラインへ
`build_public_registry.py`を先に組み込む（段階5）方が手戻りが少ないとオーナーへ提案し、承認された。
段階5が完了すれば、`finalize`の有無や候補データのタイミングをテーマごとに個別調査する必要が
なくなり、残り8テーマの接続はその上に乗るだけになる見込み。

**段階4：あだ名禁止は調査のうえ接続を見送り（2026-08-31）**: `build_nickname_arena.py` の
論点別件数計算は、通常のデータ更新時に**まだ昇格していない候補ファイル**を直接読む
（`refresh_adapters/nickname.py`の`build()`が`--input`に候補を渡す）。bukatsu-chiikiと違い
「昇格確定後に正典から数え直す」専用の後工程（finalize）が無いため、ここを公開データJSONへ
繋ぐと、次回のデータ更新（このテーマの`collect_at`はまさに本日）で候補ページが新しい投稿の
件数を反映しなくなる。しかも「2回生成して差分ゼロ」の既存検査はこの不具合をすり抜ける
（2回とも同じ古い数字で一致するため）。**段階5（`refresh_topic.py`の候補作成への自動接続）が
終わるまで、このテーマの接続は見送る。** 番号→固定IDの対応表と判断の詳細は
`quality/reviews/2026-08-31-public-data-foundation-stage4-school-nickname-ban.md`。
この調査の副産物として、bukatsu-chiikiの接続に同種の鮮度リスク（昇格後にbuild_public_registry.py
の再実行を忘れると古い件数を出し続ける）があることに気づき、`source_sha256`の鮮度確認を追加した
（古ければ止まる）。段階5を残り8テーマの個別接続より前に着手候補として検討する価値がある。

**この手動再実行の指示は段階5の完了により不要になった（2026-08-31追記）**。
`prepare_public_candidate_bundle()`（`scripts/refresh_topic.py`）が `--promote` /
`--prepare-promotion` のどちらでも、隔離した候補コピーの中で `build_public_registry.py --all` を
`finalize()` の直前に必ず実行するようになったため、`source_sha256` は毎回その場で作り直された
公開JSONと一致する。bukatsu-chiikiを含む公開10テーマすべてで、通常のデータ更新（収集→分類→
`--promote`）を行うだけで公開JSONは自動的に最新化される。手動での `build_public_registry.py
--topic {theme}` 実行は、通常運用では不要（このコマンド自体は残っていて、事故調査など個別に
最新化を確認したいときに使える）。

**段階4：部活動の論点カード接続（2026-08-31）**: `configs/bukatsu-chiiki-reaction-map.json` の
`issue_counts.basis` を `public_json` に変更し、`scripts/issue_card_counts.py` に
`count_by_issue_from_public_json()` を追加。論点カード6枚とリード文の件数が
`data/public/themes/bukatsu-chiiki.json` から出るようになった（表示数字は接続前後でバイト一致、
`sync_issue_counts.py --check` で確認）。`verify_theme_page.py` の2箇所
（`verify_issue_count_source` / `verify_denominators`）を `basis: public_json` に対応させ、
bukatsu-chiikiで全項目OK、他9テーマもNG 0件を確認。番号→固定IDの対応表（`public-data-taxonomy.json`
の論点順とページ内の論点番号は**並びが違う**ことが判明）と、ビルダーのどの関数が要らなくなったかの
棚卸しを `quality/reviews/2026-08-31-public-data-foundation-stage4-bukatsu.md` に記録。
アリーナのセクター件数（`update_bukatsu_tide.py` が担当）と自転車・消費税の古い数字は未接続。
既存unittest 327件中326件成功（唯一の失敗は本作業と無関係な既存の遅れ）。

**段階4：トップページ接続（2026-08-31）**: `sync_portal_stats.py` を拡張し、`data/public/catalog.json`
（課題57の公開データ）を正典として読むようにした。トップの「収集した投稿」（旧称「分類済み投稿」）に
加えて「分析対象の意見」を新設し、10テーマのカードそれぞれに収集数・意見数・主要論点数を表示。
`verify_top_page.py` にcatalogとの一致検査を追加し、古い数字に戻すと検査が落ちることを確認した
（意見数・論点数を書き換えて検査がNGになることを実地テスト済み）。sample_fileの実件数とcatalogの
集計が一致しない場合もエラーで止まるようにした（catalog再生成忘れの検知）。既存unittest 327件中
326件成功（唯一の失敗は本作業と無関係な既存の遅れ、下記に既出）。

**段階3の実装・完全照合（2026-08-31）**: `build_public_registry.py` / `verify_public_registry.py` を実装し、
公開10テーマすべてでSchema検査・不変条件検査・非公開正典との完全照合（終了コード0/1/2）が通った。
2回生成でバイト列差分0、既存unittest 327件中326件成功（唯一の失敗は本作業と無関係な
ai-copyright/constitutional-amendment/fukushutoの収集期限超過）。10テーマ合計は収集12,792件・意見10,030件で、
段階1調査で「廃棄対象」とされた旧固定テストの値と、固定値としてではなく計算結果として一致した。
自転車青切符は`is_relevant`フィールドが存在せず`is_opinion`のみで判定する既存規則（`build_bike_arena.py`）を
踏襲。読者向け「問い」は各テーマの公開済みvote_intro/subtitleを言い換えたが未レビュー。
記録: `quality/reviews/2026-08-31-public-data-foundation-stage3-generator.md`。公開ページ・sitemap・一般公開は未変更。

**段階2の仕様案（2026-08-31）**: `schemas/public-theme.schema.json` と
`schemas/public-catalog.schema.json` を追加し、公開JSONに含める項目と禁止する内部情報を定義した。
読者向け用語は「収集した投稿／分析対象の意見／主要論点／その他」に統一する提案。不変条件7件と
固定IDの方針を `quality/reviews/2026-08-31-public-data-foundation-stage2-proposal.md` に記録した。
生成器の実装・既存テーマ設定へのID追加は、独立レビューとCEO確認の後に行う。

**CEO確認（2026-08-31）**: `approval-20260831-001` として承認を記録。10テーマの論点・立場と
固定IDの対応表を `configs/public-data-taxonomy.json` に追加した。公開ページの変更・一般公開・
AdSense再申請は含まない。次は独立レビュー後、部活動テーマの公開JSON生成・完全照合へ進む。

**独立レビュー（2026-08-31）**: Claudeレビューで重大0件、中3件、軽微2件を検出。10テーマすべての
「その他」固定ID、ID一意性・catalog合計・未知ラベル停止の検査条件、決定的なJSON・ハッシュ規則、
単一日付の変換規則を反映し、最終判定 `pass`。記録:
`quality/reviews/2026-08-31-public-data-foundation-stage2-claude-review.md`。
