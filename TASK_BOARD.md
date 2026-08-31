# TASK_BOARD — SNS反応まっぷ（テーマ横断課題のみ）

最終更新: 2026-08-31（課題57 段階4を一時中断し段階5を先行着手。オーナー承認済み）

> **テーマ個別の工程状態は `THEMES.yaml` を参照してください。**
> 完了済み課題は `archive/TASK_BOARD_ARCHIVE.md` に移動しました。

---

## 運用ルール

- ハブAI（Claude Code）は毎セッション OPERATIONS.md に従って動く
- ワーカーAIは `configs/prompts/` のプロンプトに従って作業する
- ブランチ運用: `task/{theme}-{工程}` 形式。main直接コミット禁止
- 保護タグ: GA4(`G-K10S4YCZFH`) / AdSense(`ca-pub-2542211932832864`) / Supabase / OGP

---

## アクティブ課題（テーマ横断）

### 課題55: カスタムドメイン移行と公開元の一本化（課題54・15-Cの前提）

**状態**: ドメイン取得・DNS・GitHub Pages・HTTPS設定は完了。**ただし新ドメインでは投票とGA4が停止している**（2026-08-31 のレビューで実測検出。段階0で先に直す）。公開HTML内のURL移行と検索エンジン移行は未完了
**優先度**: **最優先の基盤作業**。課題54の公開実装および課題15-Cより先に完了する
**正式URL**: `https://sns-reaction-map.jp/`

**公開元（2026-08-31 確定）**: `issue-stance-lab/sns-reaction-map` の GitHub Pages（GitHub Actions公開・`.github/workflows/deploy.yml`）。
`docs/` がサイトのルートになる。旧ルートリポジトリを同一内容の第二公開元にしない。

**採用しなかった案**: `quality/designs/domain-migration-2026-08-30.md` は「公開専用リポジトリ `issue-stance-lab.github.io` から公開し、
このリポジトリのPagesを止める」設計だった。2026-08-31 に実際に行われた設定はこれと違い、プロジェクトリポジトリ側に
カスタムドメインを付けている。実測の結果**現行構成のほうが優れているため、現行構成を採用し、設計書の「切り替え順序」「旧URLの扱い」
「安定後の公開データ基盤」は破棄する**。理由は、現行構成では旧URLがパスを保ったまま本物の301転送になること（実測: 
`/sns-reaction-map/bukatsu-chiiki-reaction-map.html` → `https://sns-reaction-map.jp/bukatsu-chiiki-reaction-map.html`、`sitemap.xml` も同様）。
設計書案では GitHub Pages がページ単位の301を出せず、meta refresh による弱い代替になる。設計書の Search Console 節・AdSense 節は引き続き有効。

**実装ブランチ（未マージ・要修正）**: `task/domain-migration`（929ebc9 "Prepare custom domain migration"）。
公開HTML・configs・スクリプト・テストの書き換えは大半が実装済みで流用できる。ただし次の3点は破棄した設計に属するため**そのままマージしてはいけない**。
- `.github/workflows/deploy.yml` の削除 → 現行構成ではこれが唯一の公開経路。削除すると公開が止まる
- `scripts/sync_public_site.py` と `tests/test_sync_public_site.py` の新設 → 公開専用リポジトリへ同期する前提の道具。不要
- `tests/test_domain_migration.py` の `test_source_repository_has_no_pages_deploy_workflow` → 上と同じ前提。削除して差し替える

**Hermes/Codexレビュー反映**: 2リポジトリの存在だけでなく、数字・URL・生成物を複数箇所で手編集できることが再発の原因。正典の一元化、自動検査、承認済み生成物の固定をセットで行う

**2026-08-31 に実画面・公開URLで確認済み**:
- GitHub Pages のDNSチェック成功、HTTPS強制が有効
- `sns-reaction-map.jp` と `www.sns-reaction-map.jp` は到達でき、wwwは正式URLへ転送される
- 旧URL `https://issue-stance-lab.github.io/sns-reaction-map/` は新しい正式URLへ**パスを保ったまま301で**転送される
- ただし公開HTMLの canonical / OGP / JSON-LD、`robots.txt`、`sitemap.xml` は旧URLのまま
- 新ドメインではサイトをルート `/` で公開するため、`/sns-reaction-map/` が404になること自体は想定どおり
- 旧ルート `https://issue-stance-lab.github.io/` は200のまま生きており、中のリンクは全て新ドメインへ301する

**2026-08-31 のレビューで検出した「すでに本番で壊れているもの」**:
- **投票が新ドメインで動かない。** Supabase Edge Function の許可オリジンに新ドメインが無い。
  実測: `Origin: https://sns-reaction-map.jp` で preflight を送ると `access-control-allow-origin: https://issue-stance-lab.github.io` が返り、ブラウザが拒否する。
  実際に効いているのは**デプロイ済みの環境変数 `VOTE_ALLOWED_ORIGINS`** で、`supabase/functions/cast-vote/index.ts` の既定値を直すだけでは復旧しない
- **GA4が新ドメインで1件も計測していない。** 公開中のHTMLに `var allowedHosts = ["issue-stance-lab.github.io"];` のホスト判定が入っており、
  新ドメインでは計測タグ自体が読み込まれない。書き手は `scripts/seo/apply_ga_tags.py`。
  あわせて `scripts/fetch_ga4_metrics.py`（DEFAULT_HOST_NAME）と `scripts/fetch_gsc_metrics.py`（DEFAULT_SITE_URL）も旧ホスト固定で、数字が0のまま静かに続く

**修正範囲**:
1. 正式ドメインとベースパスを1つの設定へ集約し、生成器がそこだけを参照する
2. canonical、`og:url`、JSON-LD、絶対画像URL、robots、sitemap、404、内部リンクを一括生成・検査する
3. 公開対象10テーマ、トップ、共通ページについて、旧URL残存とリンク切れを機械検査する
4. 旧URLから対応する新URLへの転送を確認し、旧ルートリポジトリは重複コンテンツを配信しない役割に整理する
5. 公開後にSearch Consoleへ新ドメインのサイトマップを登録し、旧プロパティも移行確認のため当面残す
6. **投票（Supabase許可オリジン）とGA4計測ホストを新ドメインで復旧する**
7. **再生成で旧URLが復活する経路を塞ぐ。** `scripts/refresh_topic.py` と `scripts/refresh_bukatsu_pilot.py` の `SITE_URL`、
   `scripts/admin_dashboard/{jobs,render}.py` の `PUBLIC_BASE`、`scripts/build_bukatsu_arena.py` と `scripts/build_consumption_tax_page.py` の共有URL
8. **旧URLを埋め込む手順書を直す。** `README.md`（公開URL）、`.claude/skills/release/SKILL.md`（後述の永久ループ）、
   `.claude/skills/new-topic/SKILL.md` と `.claude/skills/new-topic/scripts/check_launch.py`（旧ルートへの追記手順）、
   `.claude/skills/note-operation/SKILL.md`（UTM URL）、`X_POSTING_GUIDE.md`
9. **旧URLを正解として固定しているテストを更新する。** `tests/test_theme_hero_assets.py`、`tests/test_image_policy.py`、`tests/test_admin_dashboard.py`
10. **公開対象外の11ページ目 `docs/takaichi-reaction-map-standard.html` の扱いを決める。**
   新ドメインで200で開けるがサイトマップには載っていない。方針は「URLだけ新ドメインへ直し、`noindex` は付けない現状維持」

**実施順**（段階をまたいで先に進まない。各段階の「成功の形」が出てから次へ）

**段階0: すでに壊れている2つを復旧する（CEO操作1つ＋先行公開の判断）**
0-1. 投票の復旧。**2026-08-31 CEO実施・確認済み。** Supabaseダッシュボード → Edge Functions → cast-vote → Secrets の
    `VOTE_ALLOWED_ORIGINS` に新ドメインを追加する。値は新旧を並べる（移行期間中は両方許可する）:
    `https://sns-reaction-map.jp,https://issue-stance-lab.github.io,http://localhost:8000,http://127.0.0.1:8000`
    成功の形: 下のコマンドで `access-control-allow-origin: https://sns-reaction-map.jp` が返る。
    ```sh
    curl -sS -X OPTIONS -H "Origin: https://sns-reaction-map.jp" -H "Access-Control-Request-Method: POST" \
      -D - -o /dev/null https://qslrlprzoucrlptnhsmi.supabase.co/functions/v1/cast-vote | grep -i access-control-allow-origin
    ```
    **2026-08-31 に実行して確認済み**（新旧どちらのOriginでも `access-control-allow-origin` が自分自身の値で返ることを確認）。
    **残作業**: 新ドメインの公開ページで実際に1票入れ、やり直しボタンまで動くことをブラウザで目視確認する（未実施）
0-2. GA4の復旧は**原則として段階3の一括公開に同梱する**（公開回数を増やさないため）。
    ただし段階3が2026-09-03 より後ろにずれる場合は、`apply_ga_tags.py` の許可ホスト1行だけを先行公開する承認案件を出す。
    判断者はCEO。計測が止まっている日数と、公開を1回増やす手間の比較で決める

**段階1: 作業ツリーを作り、実装ブランチを現行構成へ直す。2026-08-31 完了**
1-1. **完了。** `git worktree add ../isa-wt-domain-cutover -b task/domain-cutover task/domain-migration` で `929ebc9` から分岐した
    （main から作り直していない。コード側の大半は既に実装済みだったため）
1-2. **完了。** 破棄した設計に属する3点を戻した: `.github/workflows/deploy.yml` を復活、`scripts/sync_public_site.py` と
    `tests/test_sync_public_site.py` を削除、`tests/test_domain_migration.py` から
    `test_source_repository_has_no_pages_deploy_workflow` を削除
1-3. **完了。** 修正範囲 6〜10 を確認・実装した。**6・7・9・10 は `929ebc9` の時点で既に実装済みだった**
    （`cast-vote/index.ts` の既定値、GA許可ホスト、`refresh_topic.py` 等のSITE_URL、テスト、`takaichi-...standard.html` のURLはすべて新ドメイン）。
    **8（旧URLを埋め込む手順書）は未着手で今回直した**: `README.md`（公開先の説明を1リポジトリ構成へ書き換え、
    `sync_public_site.py` への言及を削除）、`.claude/skills/release/SKILL.md`（段階3-2で指示された確認コマンドの修正を先取り）、
    `.claude/skills/new-topic/SKILL.md` と `check_launch.py`（別リポジトリへの追記手順を削除。公開元一本化で不要になったため）、
    `.claude/skills/note-operation/SKILL.md`、`X_POSTING_GUIDE.md`（UTM付きURL例）
1-4. **完了。** `quality/designs/domain-migration-2026-08-30.md` の冒頭に破棄の経緯を追記した
1-5. （計画外の追加対応）新しい作業ツリーに非公開の正典データ `social-samples/` が無く、フルテストが13件エラーになったため、
    分岐元の `isa-wt-domain-migration` からrsyncで同期した。
    同期後のフルテストは1件失敗のみで、これは `929ebc9` の時点から存在する無関係な既存差分
    （`test_portal_stats.test_top_page_matches_canonical_stats`、トップページの集計値ずれ）と確認した。段階1の変更が原因ではない
    コミット: `56cb9b8`（`task/domain-cutover` ブランチ、作業ツリー `../isa-wt-domain-cutover`）

**段階2: 公開前の機械検査を足し、候補を固める。2026-08-31 完了**
2-1. **完了。** `tests/test_domain_migration.py` に4件追加した（9→10件）:
    ①公開HTMLのGA許可ホストが新ドメインであること ②`docs/CNAME` が存在し中身が `sns-reaction-map.jp` であること
    ③`scripts/` 配下に旧オリジンのURL定数が残っていないこと ④`docs/ads.txt` が存在すること。
    `docs/CNAME` はこの段階で新設した（段階4-3が確認する対象。デプロイでカスタムドメインが外れないことの検査対象にする目的）
2-2. **完了。** 検査を通した。フルテストは310件中、既存の無関係な1件のみ失敗（`test_top_page_matches_canonical_stats`、
    データ更新待ちで `929ebc9` の時点から存在）。`verify_top_page.py` と全10テーマの `verify_theme_page.py` にもNGが出たが、
    いずれも本移行と無関係と確認した：collect_at期限超過3テーマ・次回更新日の表示ズレ（today=2026-08-31になったことによる
    既存の日付ドリフト、`929ebc9` でも再現）、外部リンクチェックの一時的失敗2件（対象URLは実際は200、再実行で消えた）
2-3. **完了。** `generate_seo_assets.py` を2回連続実行し、`docs/` に差分が出ないことを確認した（既にコミット済みの内容と完全一致）
2-4. **完了。** Claudeの独立レビュー（5観点のエージェントで最大30候補→検証、8件生存）を受けた。
    **見つかった主な問題**: 廃止した「公開専用リポジトリへの同期」設計への言及が、コードでなく会社のガバナンス文書
    （`company/APPROVALS.yaml` の承認待ち案件、`company/HANDOFFS.yaml` の引き継ぎ、設計書の「公開前ゲート」節）に
    4箇所残っていた。削除済みファイル（`tests/test_sync_public_site.py`）を承認の証拠に挙げたままの箇所もあった。
    いずれも修正済み。あわせて `deploy.yml`（唯一の公開経路）の存在を検査するテストが無かったので追加した。
    残り2件は対象外として記録のみ（`scripts/admin_dashboard/jobs.py` の公開後確認が `docs/` 抜きでindex.htmlを読む
    既存バグ＝mainにも存在し本移行が原因ではない。ドメイン定数が7スクリプトに重複している設計上の改善余地）
2-5. **完了。** `company/APPROVALS.yaml` の `approval-20260830-003`（既存のpending案件。新規追加ではなく、
    廃止済み設計を書いたままだったこれを訂正して使った）に、公開候補コミット
    `77782e719f2c9e0209aba0e58823be13c0816c06`（`task/domain-cutover`、承認対象は「このSHAの `docs/` の中身」）と
    検査・レビュー結果をevidenceとして記録した。CEO承認はまだ得ていない（`status: pending` のまま）
    コミット: `bb30a35`（2-1）→ `77782e7`（2-4）→ `d7a0fe9`（2-5）→ `bc52a74`（承認案件の説明を
    非エンジニアのオーナーが判断できる粒度へ書き直し。`docs/` は変更していないので、公開候補SHAは
    `77782e719f2c9e0209aba0e58823be13c0816c06` のまま。`task/domain-cutover` ブランチ）

**段階3: CEO承認後に一度だけ公開する。2026-08-31 完了**
3-1. **完了。** CEO承認。`APPROVALS.yaml` の `approval-20260830-003` を `approved` にした
3-2. **完了。** `release` スキルでマージ・push。**マージ時に3ファイルで衝突した**
    （`TASK_BOARD.md` / `company/HANDOFFS.yaml` / `quality/designs/domain-migration-2026-08-30.md`。
    作業ブランチが8/30の古い時点から分かれていたため、この会話の中でmain側を直接更新した内容と競合した）。
    手順どおり一度中止してオーナーへ報告し、承認を得てから手作業で解決した。コード・テスト・`docs/` は無傷で衝突していない。
    マージコミット `cb50227`。`.claude/skills/release/SKILL.md` ⑥の確認コマンドは段階1で先に直してあったのでそのまま使えた。
    push: `3ea6dbd..b9e22b9`
3-3. **完了。** 承認したSHA（`77782e7`）と実際に公開されたコミットの `docs/` を比較したところ、
    `docs/index.html` に1箇所差分があった。原因は、承認後の作業ブランチが古い分岐元のままだったため、
    main側で別途進んでいたX投稿日の更新（`xpost` の日付が2箇所で08-29→08-30）が自動マージで取り込まれたこと。
    **ドメイン移行に関する内容は無傷で一致**。承認から公開までの間に競合するpushは無かった

**段階4: 本番で確かめる。2026-08-31 完了**
4-1. **完了。** 転送・メタデータ・robots・sitemap・404を本番URLで直接確認した：canonical/og:url（トップ・bukatsu-chiiki・
    ai-copyright・consumption-tax-cut・takaichi-standard）、robots.txt、sitemap.xml、旧URL→新URLの301転送、404（正しく404を返す）
4-2. **完了。** 投票のCORS preflightを本番Supabaseエンドポイントに送り、`access-control-allow-origin: https://sns-reaction-map.jp`
    を確認した。GA4のリアルタイムに実アクセスが出ることは、ブラウザでの目視確認が必要なため未実施
    （GA4計測自体の復旧は元々段階3の一括公開に同梱する予定で、今回のpushに含まれている）
4-3. **完了。** `docs/CNAME`（中身 `sns-reaction-map.jp`）がリポジトリに残っており、デプロイ後も
    `https://sns-reaction-map.jp/` がHTTPSで正しく応答することを確認した（カスタムドメイン設定は外れていない）

**段階5: 検索エンジンとAdSenseの移行**
5-1. **完了（2026-08-31）。** Search Console に `sns-reaction-map.jp` のドメインプロパティを追加し、DNS TXTレコードで所有権を確認した。
    `https://sns-reaction-map.jp/sitemap.xml` を送信し、同日「成功しました」・検出ページ数16件を確認。旧プロパティは移行確認のため当面残す。**「アドレス変更ツール」は使えない**（パス単位の移転は対象外のため）
5-2. **実施しない（CEO指示、2026-08-31）。** AdSenseへの新ドメインサイト追加・所有権確認・再審査は行わない。既存サイトの `ads.txt` 承認状態を維持する。
5-3. 4週間、週1回インデックス状況を見る。移行確認後に課題54と15-Cを進める

**完了条件**:
- 公開物の canonical / OGP / JSON-LD / robots / sitemap がすべて正式URLを示す
- 公開対象10テーマ、トップ、about等の共通ページが新ドメインのルート配下で開く
- 旧URLが対応する新URLへ転送され、新旧2か所で同じ本文を公開していない
- 旧オリジン文字列は、転送設定・移行記録など明示的な許可箇所以外の公開物で0件（`docs/takaichi-reaction-map-standard.html` を含む）
- 公開直前に承認されたコミットSHAの `docs/` と、実際に公開されたコミットSHAの `docs/` が同一である
- Search Consoleで新ドメインのサイトマップが受理される
- **新ドメインの公開ページで投票が成立する**（preflightが新ドメインを許可し、実際に1票入る）
- **新ドメインでGA4が計測される**（公開HTMLの許可ホストが新ドメインで、リアルタイムに反映される）
- **収集・更新スクリプトを再実行しても旧URLが復活しない**（`refresh_topic.py` 実行後の `sitemap.xml`・`robots.txt` が新ドメインのまま）
- **旧URLを埋め込む手順書が残っていない**（README・release・new-topic・note-operation・X_POSTING_GUIDE）
- **`docs/CNAME` がリポジトリにあり、デプロイ後もカスタムドメインが外れない**
- 上記のうち機械で見られるものが `tests/test_domain_migration.py` で検査され、検査を消さない限り再発しない

**CEO決定（2026-08-31）**: 旧ルート `issue-stance-lab.github.io` をどうするか → **(A) に決定**。
旧ルートのトップを `noindex` + 新ドメインへの案内1枚に置き換え、AdSenseの審査対象を新ドメインへ移す。
**未着手。** 旧ルートは別リポジトリ（`issue-stance-lab/issue-stance-lab.github.io`）なので、
本リポジトリの作業ツリーでは着手できない。別途そちらのリポジトリで作業する
**CEO決定（2026-08-31）**: GA4の復旧タイミング → **段階3の一括公開に同梱する**（0-2の既定どおり）。先行公開はしない

**対象外**: 3D実装、AdSense再申請そのもの、記事内容の改稿、収集データの数字修正
**状態（更新）**: **2026-08-31、段階0〜5-2が完了し `sns-reaction-map.jp` を正式URLとして本番公開した。**
CEO承認（段階3-1）→ AIがマージ・push・本番確認（段階3-2〜3-3、段階4）まで実行済み。**ここで一区切り。**
**次にすること**（優先度順。いずれも着手可能・急ぎではない）:
1. 段階5-3: 4週間、週1回Search Consoleのインデックス状況を見る
2. 旧ルート（別リポジトリ `issue-stance-lab/issue-stance-lab.github.io`）を案内ページへ置き換え（CEO決定A、未着手）
3. 新ドメインでGA4のリアルタイムに実アクセスが出ることをブラウザで目視確認する

### 課題57: 公開データ基盤と公開承認物の一本化（旧15-A・課題54の前提）

**状態**: 段階5の候補一括生成を実装後、段階4を再開（2026-08-31）。トップページ完了。テーマページは6/10
（部活動＝接続、あだ名禁止＝調査、消費税減税＝接続、自転車青切符＝接続、生成AIと著作権＝接続、憲法改正＝接続）。当初10テーマ中2テーマで「候補生成中は
公開JSONに繋げない」という同じ壁に当たったため、**オーナー承認により段階5を先行着手する**
（消費税減税を含む残り8テーマの個別接続は段階5の後に再開）
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

**次にすること（段階4）**: 残り4テーマについて、同じ候補公開JSON経路へ接続する。

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
（古ければ止まる。**bukatsu-chiikiの次回更新`refresh_at: 2026-09-03`の前に、昇格後は
`build_public_registry.py --topic bukatsu-chiiki`を手動で再実行すること**）。
段階5を残り8テーマの個別接続より前に着手候補として検討する価値がある。

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

### 課題54: 3D「議論の惑星」を中心とするWebsiteリニューアル（最重要）

**状態**: 方針承認・設計確定。実装準備中
**優先度**: **最重要**。通常の新規テーマ追加、検索記事追加、旧2Dマップの横展開より優先する
**対象**: 公開対象10テーマすべて。最初の完成基準は `bukatsu-chiiki`（部活地域移行）。対象IDは設計書に固定する
**正典**: `quality/designs/reaction-planet-renewal.md`
**独立レビュー**: `quality/reviews/2026-08-30-reaction-planet-plan.md`
**AdSense対策**: `quality/designs/planet-adsense-gates.md`（2026-08-30。生成器に独自性の検査を実装。展開順の変更提案あり）
**部活の実装構想**: `quality/designs/planet-bukatsu-chiiki.md`（2026-08-30 作成。面積・色・標高の具体値を現行正典993意見で確定）

**目的**: テーマごとに雑多な情報を縦に並べるページから、読者が議論の全体像を回し、論点へ着陸し、
理由と一次資料を読めるWebsiteへ変える。noteは論考、Xは入口、Websiteは探索できる中心商品に役割を分ける。

**変えない意味**:
- 球体全体 = 1テーマ
- 大陸・島 = 論点
- 面積 = その論点に分類された意見数
- 色 = その論点内のスタンス分布（テーマ固有ラベルを使い、単純な赤青へ固定しない）
- 標高 = AI分類から再現可能な「強い表現の割合」。正しさ・重要度・世論の熱量とは呼ばない
- 大陸の位置 = 初版では見やすさのための配置。論点同士の近さを意味しない

**読者体験**: 最初に惑星を表示し、回転（横・縦）、拡大縮小、論点への着陸、全体表示への復帰を可能にする。
着陸後は同じ画面内の読めるHTMLに、比率、代表的な理由、一次資料、編集部の整理を表示する。
3Dが動かない端末、JavaScript無効時、キーボード操作でも同じ主要内容へ到達できることを必須とする。

**実装順**:
1. 課題55を完了し、正式URLと公開元を一本化する
2. 課題57を完了し、意見数・論点数・更新日・用語の公開データ契約を一本化する
3. 部活地域移行で、共通planet-data生成器、共通3D表示、HTMLフォールバックを作る
4. 非公開の部活完成版を品質監査し、CEOが10テーマ共通仕様として承認する
5. 同じ生成器で残り9テーマへ移行し、10テーマすべてを確認台帳へ記録する
6. 10テーマ・トップ・サイトマップを総合監査し、CEO承認後に課題55で一本化した公開元へ公開する
7. 新ドメインの再クロールを確認し、品質監査とCEO承認後にだけAdSenseへ再申請する

**完了条件**:
- 10テーマすべてが1つの共通生成経路から再生成でき、同じ入力では地形が勝手に変わらない
- 公開対象10テーマを設定から機械判定でき、公開HTMLを次回生成の入力にしない
- 10テーマすべてで、地形の面積・色・標高と読者向けHTMLの数字が正典と一致する
- スマホで横スクロールせず、縦回転を含む操作、戻る操作、キーボード操作、動きの抑制設定が機能する
- WebGLまたはJavaScriptが使えなくても、論点・比率・理由・一次資料・編集整理を読める
- 既存の投票、GA4、AdSenseコード、Supabase、OGPを壊さず、公開ページに内部のAI判定理由を出さない
- 10テーマの確認台帳、独立監査、公開前レビュー、再クロール確認がそろうまでAdSenseを再申請しない

**対象外**: 初版の銀河トップ、リアルタイム更新、投稿1件ごとの3D点群、VR/WebGPU、マップ操作内や直近の広告配置。

---

### 課題13: 新規トピック継続追加
**状態**: 未着手（OPERATIONS.md「サイト改善の進め方」に該当）
**概要**: 話題が大きいもの、または CEO が関心を持つ社会問題を優先する。公開SNS投稿を収集でき、複数の価値観を整理できる論点があることを確認する。
**手順**: `.claude/skills/new-topic/SKILL.md` 参照

### 課題15: AdSense審査対応 & 広告配置設計
**状態**: **対応中（再申請保留）**。2026-08-29 に3回目も不承認（理由: 有用性の低いコンテンツ）。ads.txt は承認済み
**概要**: 審査結果追跡、通過後の広告ユニット配置設計、プロジェクトアドレスへの管理権限移行

**2026-08-29 不承認（3回目）**:
- 8/21 に申請し、8/29 に「有用性の低いコンテンツ」で不承認。支払い情報・サイトリンクの案内は
  審査理由とは別で、ads.txt は承認済み
- 8/18 のセオリコ診断は高齢者免許返納1記事を代表記事とした参考評価で、
  `issue-stance-lab.github.io` 全体の整合性を保証する検査ではなかった
- 詳細な調査記録: `quality/reviews/adsense-third-rejection-2026-08-29.md`

**今回の調査で確認した主要因**:
1. 審査対象ルートが「11テーマ・7,704件・8/14更新」、本体が「10テーマ・12,792件・8/27更新」で不一致。
   高市テーマの導線だけを8/21に削除し、ルートのテーマ数・合計・更新日は更新されていなかった
2. 消費税ページに「意見2,852件・6論点」と「意見612件・7論点」が同居。自転車ページにも
   「分析対象201件」と「意見384件」が同居しているが、既存検査はどちらも `OK` と判定した
3. `about.html` は「分類済み」を意見と判定した件数と定義しているが、トップの12,792件は
   `sample_file` の全レコード合計。読者向けの用語と自動検査の定義が一致していない
4. 代表投稿の確認台帳で `reviewed` の公開テーマは bike / koshitsu の2件。一方トップには
   全体へ適用される「人が内容を確認します」という表現がある。AIの信頼度・分類理由も本文に残る
5. サイトマップのトップ最終更新が7/7、ルートが8/13のままで、公開更新をGoogleへ伝える情報が古い。
   ルート生成器の `--check` も未知の `.conditional` 区画で停止し、2リポジトリ同期が機能していない

**再申請までの管理単位**:

| ID | 担当 | 状態 | 完了条件 |
|---|---|---|---|
| 15-A 表示・数字・公開元整合 | 開発・データ部AI | **課題57へ統合** | 課題57の完了を15-Aの完了とする。新ドメインのトップ・10テーマ・サイトマップの収集数／意見数／論点数／更新日を公開データ契約へ統一し、説明文中の古い数字も検出する |
| 15-B 手動編集・独自価値 | 編集部AI → 品質監査AI | 15-A後 | 公開対象10テーマの代表投稿・要旨・編集結論を確認台帳へ記録し、AIの信頼度・内部理由を読者向け本文から除去する |
| 15-C 公開・再クロール確認 | 開発・データ部AI → CEO | 課題55・15-A/B後 | CEO承認後に一本化した公開元へ公開し、Search Consoleで新ドメインのトップ・10テーマが最新版として取得されたことを確認する |
| 15-D AdSense再申請 | 事業部AI → CEO | **保留** | 課題55で審査対象サイトを確定し、AdSenseへ新ドメインを追加・所有権確認済みであること。そのうえで15-A〜Cの証拠を品質監査が確認し、CEOが再申請を事前承認する |

**次にすること**: 課題57を先に進める。消費税・自転車・「分類済み」の定義修正を含む15-Aは課題57で管理し、
一本化した公開元の生成器とサイトマップ生成を通常の公開検査へ接続する。課題57完了前に新しいAdSense対策記事を増やさない

**2026-08-21 対応済み（3回目の申請）**: 「投稿の主張を一次資料と突き合わせる」セクションを5テーマに実装し、
セオリコ診断の Experience NG を解消した（2026-08-18 の再診断で全12項目OK・総合「合格ライン」）。
- 実装したテーマ: bike-blue-ticket（7主張・37件）／elderly-license-revocation（7主張・38件）／
  consumption-tax-cut（6主張・72件）／constitutional-amendment（10主張・37件）／
  koshitsu-tenpakai（6主張・21件）。手順は `FACT_CHECK_GUIDE.md`
- 一次資料は省庁・国会会議録・e-Gov・政党の公表資料のみ。該当投稿はキーワード抽出のままにせず、
  候補を1件ずつ読んで確定し、`data/{テーマ}_claim_posts.json` に保存して件数をそこから数える
- 「確認できず」の行を消さない方針。空振りが残っていることが人の作業の証拠になる
- **テンプレ化を検査で止める仕組みを追加**（`scripts/verify_page_originality.py` + `tests/test_page_originality.py`）。
  手順書に「先行事例の見出しをコピーするな」と書いても守られず、2026-08-18 に自転車→高齢者で
  見出しが完全一致した。共通で当たり前の文は `configs/page-originality.json` に理由つきで登録する
- 取得期間を bike / elderly にも記載（`sample_period_source: owner_confirmed`）
**2026-08-21 時点の残り**: 一次資料との突き合わせが未実装のテーマが5つ（ai-copyright / bukatsu-chiiki / henoko-student-accident /
fukushuto / school-nickname-ban）。takaichi は 2026-08-21 に noindex / sitemap除外 / サイト導線から除外し、
検索・AdSense審査の対象外にした（データ・投票は保持。設定を戻せば復活可）。
2026-08-24 に fukushuto へ実装済み。2026-08-29 現在の未実装は4テーマだが、
15-A/Bの整合性と手動確認を先に行うため、横展開は保留する
**2026-07-07 対応済み**: 全8テーマページに「この争点の背景」解説セクション追加（configs/*.json の `background` フィールド＋build_reaction_map.py 対応済みのため再ビルドでも保持される）、docs/about.html（運営者情報）新設、全フッターにリンク追加、sitemap更新
**2026-07-30 対応済み**: 問い合わせ窓口をGoogleフォームで開設（メールアドレス非公開・ログイン不要）、about.html の訂正窓口セクションと disclaimer.html の削除依頼導線をフォームにリンク。個別返信は原則行わない旨と、事実誤認の指摘・削除依頼には対応する旨を明記
**2026-08-01 判明した本質的な問題**: AdSenseに登録されているサイトは `issue-stance-lab.github.io`（**ルートのサブドメイン全体**）であり、`/sns-reaction-map/` ではない。7/7以降の対策（背景解説・about・問い合わせ窓口）はすべて `/sns-reaction-map/` 配下で、**審査員が最初に見るルートページは見出し1つ＋リンク1本の947バイトのスタブのままだった**。「有用性の低いコンテンツ」はこれを指していた可能性が高い。所有権確認は完了済み（管理画面で緑チェック）。
**2026-08-01 対応済み**: 別リポジトリ `issue-stance-lab/issue-stance-lab.github.io` の `index.html` を実体のあるトップページに差し替え（プロジェクトの目的、収集→分類→編集の3ステップ、公開中11テーマへのリンク、編集方針5項目、運営者情報と問い合わせフォーム、privacy/disclaimer/usage へのフッターリンク、数字の前にサンプルであり世論調査ではない旨の注意書き）。同リポジトリのルートに `ads.txt` を追加（`docs/ads.txt` と同一内容。従来は `/sns-reaction-map/ads.txt` にしか無く、ルートは404で管理画面のads.txtステータスが「不明」だった）。commit `aa4d05e`
**注意**: ルートページには件数を載せていない。別リポジトリで二重管理すると課題29と同じ数字の食い違いが再発するため、件数と取得期間は各テーマページ側に一本化する方針
**2026-08-01 申請済み**: 管理画面から再審査をリクエスト。お支払いプロフィールは登録済み（住所確認PINは累計$10、支払い方法登録は$100到達後のため現時点では操作不可）
**2026-08-12 不承認（2回目）**: 理由は同じ「有用性の低いコンテンツ」。
セオリコの診断ツールにもかけ、Experience=NG / 必須ページ・Expertise・Trustworthiness=不明 が出た。
Codex にも見せ、3者の指摘を実ファイルで検証して統合した。

**2026-08-13 対応済み（フェーズA: 減点要素の除去）**:
- **公開ページに制作指示が載っていた**（8テーマ・14文）。「代表投稿は公開前に人間が確認する前提です」
  「投稿本文の転載は最小限にし…してください」など。**未完成の下書きに見えるうえ、同じページ上部の
  「人間による代表投稿の確認あり」と矛盾していた**。`constitutional-amendment` は廃止済みの Ollama
  への言及つき。設定10件・生成器4本・雛形1件から出どころも除去
  （`scripts/seo/strip_production_notes.py --check` で再発を検出）
- **`subtitle` の「編集用ビューです」**を設定3件＋雛形から除去。公開HTMLは差し替え済みだったが
  設定が古く、再ビルドで復活する状態だった
- **辺野古に旧2D分類の section が2つ丸ごと残っていた**。356件と278件が同一ページに同居。
  どちらも `display:none` で読者には見えず、クローラーだけが63KBを読んでいた。削除して176KB→112KB。
  詳細データ3表も旧仕様だったため正典から4表を再生成（`build_henoko_arena.mjs` に生成を追加）
- **X投稿の埋め込み142件が空だった**。widgets.js が読めないと出典もリンクも残らない。
  `scripts/x_embed.py` に形を集約し、生成器9本と修正スクリプトで共用
- **運用メモ10件が HTTP 200 で配信されていた**（課題46。完了・アーカイブ済み）
- **「AI分類・人間による代表投稿の確認あり」に記録が無かった**。ただし**確認自体は実際に行われていた**
  — ページの要旨を正典と突き合わせると、断定的・党派的な表現を中立化する書き換えが入っている。
  `data/review-ledger.json`（非公開）に証拠を記録し、記録のあるテーマだけ件数つきで表示するようにした
  （bike-blue-ticket / takaichi / koshitsu-tenpakai の3テーマ。残る7テーマは正典が手元に無く判定不能）
- **404ページを新設**（`scripts/build_404_page.py`）。GitHub Pages の汎用404が出ていた
- takaichi の「意見360件を表示しています」が1件ずれ（表示は359件）。`{issue_opinions}` 差し込みで修正

**2026-08-13 対応済み（フェーズB・C前半）**:
- **お問い合わせ導線が index.html と全11テーマに1件も無かった**（セオリコ「必須ページ 不明」の実体）。
  全18ファイルのフッターを6リンクで統一（運営者情報／調査・編集方法／お問い合わせ・訂正依頼／
  プライバシーポリシー／免責事項／画像制作方針）。`scripts/seo/unify_site_chrome.py --check` で検査可能
- **about.html を 1,368字 → 2,980字**。テーマ選定基準・検索語の作り方・重複除外・意見判定基準・
  分類方法・代表投稿の選定基準・AI分類の誤りの確認方法・訂正時の対応・**広告と編集の関係**を追加。
  `#operator` `#method` を新設。運営者が1人であること、「編集部」が1人の編集名義であることを明記。
  「ローカル環境で動作するAI」の誤記も修正（現行は Hermes / OpenCode Go）
- **全11テーマに「収集・分類で分かったこと」を追加**（セオリコ Experience NG への本丸）。
  report.json・THEMES.yaml の notes・検索語設定から、実際の作業ログにある事実だけを書いた。
  本文 +3,595文字。`configs/theme-seo.json` の `observations` で管理し、正典が無い環境でも
  `apply_theme_trust.py --observations-only` で更新できる
- **ルートリポジトリに robots.txt / sitemap.xml / 404.html を追加**。robots.txt はホストのルートに
  置いたものしか読まれない仕様で、`/sns-reaction-map/robots.txt` は無視されていた。sitemap も
  発見されていなかった（GSC 28日間で表示27回・クリック1件と整合）。
  ブランチ `claude/google-adsense-improvement-iot78g` に出してある（main へ push すると即公開になるため）

**検証コマンド**（すべて `OK` で終われば成功。`grep` で数えると修正後の正常な形も
拾ってしまうため、必ず下のスクリプトを使うこと）:

```sh
python3 scripts/seo/strip_production_notes.py --check   # 制作指示が残っていないか
python3 scripts/seo/add_embed_fallback.py --check       # 中身が空の埋め込みが無いか
python3 scripts/seo/unify_site_chrome.py --check        # 全ページに統一リンクが揃っているか
python3 scripts/seo/apply_review_note.py --check        # 確認表示が台帳と一致するか
python3 scripts/build_404_page.py --check               # 404がテーマ一覧と同期しているか
python3 scripts/build_review_ledger.py --check          # 台帳の再計算で内容が変わらないか
python3 scripts/verify_theme_page.py <theme>            # 出典リンクの死活を含む総合検査
python3 scripts/verify_top_page.py                      # docs/ の衛生・404の存在
```

**2026-08-13 対応済み（フェーズC後半）**:
- **一次資料が0本だったテーマをゼロにした**。7テーマに官公庁・国会の出典を2〜4本ずつ追加
  （参議院・衆議院の議案情報、首相官邸の記者会見録、文部科学省の見解、内閣官房・内閣府の資料、
  総務省の制度資料、e-Gov 法令検索）。`configs/*.json` の `background.sources` で管理し、
  `scripts/seo/apply_background_sources.py` が背景セクション末尾へ差し込む
- school-nickname-ban には「**あだ名の禁止を定めた国の規定は無い**」、takaichi には
  「事実関係の認定を行うページではない」という注記を添えた

**2026-08-13 確認済み**: 出典リンクの死活をオーナーのローカル環境で確認し、
**全40本が HTTP 200（OK 40 / NG 0 / 遮断 0 / エラー 0）**。リンク切れは無い。
確認は `python3 scripts/seo/check_source_links.py`。遠隔実行環境では組織のegressポリシーで
*.go.jp への CONNECT が 403 になり全件「遮断」と出るため、この検査はローカルで行うこと。

**2026-08-13 検証済み（オーナーのローカル環境）**: 非公開の正典が揃った環境で全検査を通した。
- 出典リンク: **全40本 HTTP 200**（OK 40 / NG 0）
- 数字の出所: **11テーマ / NG 0件**
- 再生成可能性: **9テーマ / NG 0件**
- テーマページ検査: **11テーマすべて NG 0件**
- テスト: 残る失敗は `collect_at 期限超過: elderly-license-revocation（2026-08-13）` の1件のみ。
  これは当該テーマのデータ収集予定日が来ているという運用リマインダーで、AdSense対応とは無関係

作業中に見つかり修正した、今回の作業に起因する不具合は3件。
①分析メモと確認表示の件数が数字の出所検査に引っかかった（review-note の囲みを作って
  その2か所だけを exclude_selectors で除外。領域ごと除外はしていない）
②生成器3本が review-note の囲みを落としていた
③build_constitutional_arena.py が article-trust-method を作り直す際に分析メモを落としていた

**2026-08-14 公開済み**: 2リポジトリとも main へマージ・push 済み。
- ルート `issue-stance-lab.github.io`: `aa4d05e..5f8d95d`（robots.txt / sitemap.xml / 404.html を新設）
- `sns-reaction-map`: `f6588a4..7646dc8`
- Pages のデプロイはどちらも成功（ルート run 31751029338 / テーマ側 run 31786825581）

**残作業**:
①**Search Console で再クロールを依頼する**（オーナー操作。URL検査 → インデックス登録をリクエスト、
  およびサイトマップに `sitemap.xml` を登録）。ルートに robots.txt が無かったため、
  そこで宣言していた sitemap は今まで一度も発見されていない
②Buy Me a Coffee のURLが2種類ある。`issue.stance.lab` が7ページ、`sns_hannou_map` が
  ai-copyright の1ページ。どちらが正しいかオーナーの確認が要る
③背景解説の本文増補（現状は一次資料の追加のみ。時系列・未決着の問いの明記は未着手）
④編集情報をページ冒頭へ移す（現状は可視テキストの23〜66%の位置）
⑤独自ドメイン移行は2026-08-31に実施へ変更。DNS・HTTPS設定は完了し、公開HTMLと検索エンジンの残作業は課題55で管理する
⑥再申請の判断。**反映して Google が再クロールするまで、管理画面の「問題を修正しました」に
  チェックを入れないこと**
⑦通過した場合は広告ユニットの配置設計（本課題の後半スコープ）
⑧`/sns-reaction-map/` 側だけを改善しても審査対象のルート（別リポジトリ
  `issue-stance-lab/issue-stance-lab.github.io`）には反映されない（**2026-08-30に
  公開専用リポジトリへ本体を統合する方針へ変更。`scripts/build_root_index.py` は廃止**）

**2026-08-15 修正**: ルートを「中身を厚くする」方向で作った 2026-08-14 の初版は判断を誤っていた。
審査対象はサブドメイン全体で `/sns-reaction-map/` 側も評価に入るため、ルートに要るのは分量ではなく
**重複していないことと入口として機能すること**だった。実測すると初版はポータルと6要素が重複し、
 画像0枚の劣化コピーだった。重複を削って論点別インフォグラフィックとスタンス内訳バーに差し替え、
 可視テキスト 3,645字 → 2,530字、画像 0枚 → 11枚（`8d2a39e`）。詳細は課題48。
 **ルートを短くしたのは AdSense 的には逆方向に見える変更で、これが正しいという確証は無い。**
 同じ内容が2か所にある状態よりは良いという判断。

**2026-08-16 対応**: 生成AIと著作権ページは、編集・分析情報をヒーロー直後へ移し、
一次資料に基づく「学習・出力・公開」の判断入口を追加した。部活動の地域移行ページには、
学校が担ってきた運営・費用・人材・安全の責任を誰が引き受けるかを確認する入口を追加した。
残る9テーマの移設は未着手。

**2026-08-18 対応**: 自転車青切符ページに「集め方 → 確かめ方 → 分かったこと」の3段を追加した。
中心は**確かめ方**で、投稿が事実として言っていること7つを警察庁の公表資料と1件ずつ突き合わせ、
4つで食い違い、1つは確認できずという結果をそのまま載せた（確認日を明記）。
分類結果をきれいに見せる工夫（グラフ・内訳）は「分類のみ」という指摘の反証にならず、
**一次資料に当たった記録だけが効く**という判断。手順と発注文は `FACT_CHECK_GUIDE.md` に残した。
他テーマへ広げるときは STEP2（確かめ方）から移すこと。STEP3 は結論次第で形が変わるため定型化しない。
落とし穴として、主張の該当件数を本文のキーワード抽出で数えると3〜4割水増しになる
（ポイ捨ての過料やヘルメット補助まで拾う）。必ず候補を1件ずつ読んで確定し、投稿IDを `data/` に保存する。

**2026-08-18 対応（2件目）**: 高齢者免許返納ページにSTEP2「確かめ方」を追加した。公的資料で確かめられる主張7つを、警察庁・内閣府・国土交通省の公表資料と道路交通法に突き合わせ、一致2件・食い違い4件・確認できず1件。該当投稿32件は候補を1件ずつ読んで確定し `data/elderly-license-revocation_claim_posts.json` に保存、生成は `scripts/build_elderly_process_sections.py`。「確認できず」は、地方の運行本数（バスが1日2本など）を示す全国的な公的資料が見つからなかったもので、そのまま残している。残る9テーマは未着手。

**2026-08-19 対応（3件目）**: 消費税減税ページに「その言い分、原典に当たるとどうなるか」を追加した。公の記録で当否を判定できる言い分6つを、首相官邸の会見録・国会会議録（衆院予算委の片山財務大臣答弁）・財務省・国税庁の公表資料と突き合わせ、原典どおり2件・原典とズレ3件・原典に届かず1件。該当投稿72件は候補を1件ずつ読んで確定し `data/consumption-tax-cut_claim_posts.json` に保存した。**このテーマは生成器を新設していない**（`scripts/build_consumption_tax_page.py` に組み込み、`CLAIM_AUDIT_START/END` の間だけを差し替える）。ただし通常ビルドは潮目ウィジェットを外す作り（adapterが貼り直す前提）なので、公開ページを直すときは `--claim-audit-only` を使うこと。「原典に届かず」は輸出還付金の金額で、国税庁が公表しているのは還付申告税額の合計（令和4年で7兆円超）だけで、輸出分を区分した公表値が国税庁サイトにも e-Stat にも無かったもの。オーナー判断でそのまま残している。将来予測が争点の中心のテーマでも、決定内容・金額・制度の線引きなら確かめられるという確認になった。残る8テーマは未着手。**3本できたので、次はセオリコで再診断して Experience の判定が動くかを見るのが先**（11本作ってから崩れると直す対象も11本になる）。

### 課題17: Googleアカウント・サービスのプロジェクトアドレス統一
**状態**: 未着手
**優先度**: 低
**判断待ち**: オーナー（アカウント移行の実作業は本人しかできない）
**次にすること**: AdSense管理画面でプロジェクトアドレスを管理者として招待する
**概要**: AdSense・GitHub Orgの管理権限をプロジェクトアドレスへ移行

### 課題18: サイトデザイン・体験の全面改善
**状態**: 大部分が課題26で実現済み。残りは配色・フォント統一とXブランドトーン統一
**スコープ**: デザインガイドライン策定、全体配色統一、モバイルファースト確認

### 課題19: パイプラインでのステータス自動更新
**状態**: 未着手
**概要**: run_pipeline.py の各Step完了時に site-cases.json の status を自動更新

### 課題27: GitHubトークンを期限付きで作り直す
**状態**: 未着手
**概要**: 現在のGitHubトークン（名前: claude-code）が無期限のためセキュリティリスクあり。90日など期限付きで作り直す
**手順**: https://github.com/settings/tokens で現トークン削除 → 新規作成（repo・workflow・read:orgスコープ、90日期限）→ `gh auth logout` → `gh auth login` でトークン更新

### 課題28: sample_period の unknown を埋める
**状態**: 表示は対応済み（2026-08-13）。値の復元は未着手
**概要**: S1 で THEMES.yaml に `sample_period`（収集期間）を追加したが、一部テーマが `unknown` のまま
**2026-08-13 訂正**: 対象は**6テーマではなく4テーマ**。bukatsu-chiiki・constitutional-amendment・
school-nickname-ban・henoko-student-accident はその後に埋まっており、記述が古かった
**対象（実測4件）**: ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi
**2026-08-13 対応済み**: 公開ページの表示を「取得期間: 記録なし」から
「未記録 — 収集期間の記録を始める前に公開したテーマ」へ変更した。信頼性の表示（代表投稿の確認）の
すぐ隣に「記録なし」と並ぶのが最も印象が悪かったため、理由を書く形にした。
ラベルは `scripts/x_embed.py` の `period_label()` に集約（それまで4か所に散っていた）
**残作業**: 値そのものの復元。**収集期間の始まりは復元できない**。正典に日付フィールドが無く、
`data/verification/updates/` の記録も最新の収集回しか残っていない
（ai-copyright 2026-08-03・08-09 / bike-blue-ticket 08-10（未昇格）/ takaichi 08-07 /
elderly-license-revocation 記録なし）。推測で埋めないこと
**手順**: 各テーマの `sample_file` のレコード内タイムスタンプ、または収集時の作業ログ・git log・`social-samples/*.md` から期間を特定する。**特定できない場合は推測で埋めず `unknown` のまま残し、ページ側で「取得期間: 記録なし」と正直に表示する**
**2026-08-02 対応済み（3件）**: `sample_file` の `fetched_at` が全件そろっている constitutional-amendment（2026-06-20〜2026-07-25）/ school-nickname-ban（2026-06-22〜2026-07-12）/ henoko-student-accident（2026-06-14〜2026-06-27）を確定し、ページの「取得期間: 記録なし」も書き換えた。bukatsu-chiiki はパイロットで確定済み。
**全11テーマ再検査**: 同じ基準を既に期間が入っていたテーマにも適用した。takaichi（276件中140件欠損）/ fukushuto（255件全件欠損）も `unknown` へ戻し、koshitsu-tenpakai は正典347件が全て7/26収集なので `2026-07-26` に修正した。現在の `unknown` は ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi / fukushuto の5件。
**機械検査**: `data/verification/sample-periods.json` に総数・日付あり・欠損・最小日・最大日だけを保存し、`scripts/verify_sample_periods.py` で全11テーマを検査する。個別投稿の取得日は公開しない。
**別件（課題29の一例）**: ai-copyright は `sample_period: "2026-06-10〜2026-07-26"` と書いてあったが、`sample_file` の `fetched_at` は最新が 2026-07-12（339件は欠損）。7/26に収集した452件は `sample_file` に入っておらず別ファイルにあるため、根拠のない期間を公開し続けず `unknown`／「記録なし」へ戻した。次回更新で累積を正典へ統合した時点で確定する。

**2026-08-16 対応**: ai-copyright の収集期間はオーナー確認により `2026-06-27` と登録した。
正典には取得日欠損が339件あるため、`sample_period_source: owner_confirmed` を明示し、
自動算出値と混同しない形で検査する。

**注意**: `sample_source` は全11テーマ「Yahooリアルタイム検索」で埋まっている。検索語（クエリ）は未記録なので、A-4 で表示するなら `sample_queries` フィールドの追加も併せて検討する

### 課題29: ページ内件数表示と sample_file の突き合わせ
**状態**: **完了（2026-08-08）**。全11テーマの論点件数を正典 `sample_file` から再現できる状態にし、`data/issue-counts/` を削除した
**概要**: S1 で「分類済み投稿数」をトップに出す根拠を `sample_file` の実レコード数に統一したが、THEMES.yaml のコメント記載や各テーマページ内の件数表示と食い違うテーマがある。トップとテーマページで違う数字が出ると、S1 で解消した矛盾が別の場所で再発する
**乖離の例**:

| テーマ | THEMES.yaml コメント | sample_file 実数 |
|---|---|---|
| bukatsu-chiiki | 旧2D 245件 | 467 |
| constitutional-amendment | 552件 | 646 |
| school-nickname-ban | 134件 | 374 |
| henoko-student-accident | 356件 | 363 |
| consumption-tax-cut | classify2d: n-a | 667 |

**手順**: ①各テーマページが表示している件数がどの数字か（2D分類 / Hermes論点分類 / 収集総数）を特定 ②`sample_file` の数と一致するか確認 ③一致しない場合、どちらが「分類済み投稿」の定義に合うかを決めて統一 ④`verify_top_page.py` に「トップの件数と各テーマページの件数が矛盾しない」検査を追加
**備考**: 2D分類と Hermes 論点分類で対象件数が違うのは妥当な可能性が高い。その場合はページ側の表記を「論点分類 ○件」等に変えて、何を数えた数字かを明示する

**2026-08-02（S8）に判明した、①の調査結果**

課題30の件数併記のために全11テーマの論点別件数の出所を洗ったところ、**7テーマは `sample_file` から再現できたが、4テーマは再現できるファイルがリポジトリに残っていなかった**。

| テーマ | 論点別件数の出所 | `sample_file` から再現できるか |
|---|---|---|
| ai-copyright | sample_file（全件） | ✅ 126/79/73/46/40/31 |
| bukatsu-chiiki / consumption-tax-cut / school-nickname-ban / takaichi | sample_file（`is_opinion` のみ） | ✅ |
| fukushuto | sample_file（全件） | ✅ |
| bike-blue-ticket | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |
| **constitutional-amendment** | ページ内 `const P`（422件） | ❌ sample_file は646件（旧422件の分類が残っている） |
| **henoko-student-accident** | `docs/henoko-arena-data.js`（265件） | ❌ sample_file は363件 |
| **koshitsu-tenpakai** | ページ内 `SM_RAW` + JS の `arenaIssueOf()`（268件） | ❌ sample_file は347件。しかも公開中の h3 件数は `koshitsu-tenpakai_hermes_prev_synthetic.json` 由来 |
| **elderly-license-revocation** | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |

**暫定措置**: 上記4テーマ分を `scripts/extract_arena_issue_assignment.py` でページから1度だけ取り出し、`data/issue-counts/{theme}.json` に固定した。件数併記と検査はこのファイルを読む（ページのHTMLは読まないので、spanを手で書き換えれば検査が落ちる）。

**2026-08-07 対応済み（2テーマ）**: elderly-license-revocation（211件）と bike-blue-ticket（181件）を Hermes で再分類し、結果を正典 `sample_file` の各レコードへ `classification`（main_issue / stance / intensity / summary / reason / confidence / article_usable / risk）として格納した。あわせて次を実施。

- 論点定義を `scripts/elderly_license_taxonomy.py` / `scripts/bike_blue_ticket_taxonomy.py` に切り出し、分類スクリプトと共有（`tests/test_*_taxonomy.py` で固定）
- `configs/{theme}-reaction-map.json` の `issue_counts.source` を削除し、sample_file へ戻した
- 凍結ファイル `data/issue-counts/elderly-license-revocation.json` を削除。bike が依存していた `social-samples/bike_arena_hermes_classified.json` への参照も解消（ファイル自体はGit管理外に残置）
- 再分類前の2D分類のみの正典を `social-samples/{theme}_2d_classified_v1_2d_only.json` として保存
- 再分類でラベルが動いたため、`THEMES.yaml` の `main_issue` 行の内訳も実数へ更新した（elderly 139→95 等）
- 同日に main 側で ai-copyright（7論点・1,606件）と fukushuto も単一ソース化されたため、マージ後は `tests/test_taxonomy_continuity.py` の taxonomy不一致テーマが **0件** になった

**2026-08-07 に判明した未解決点（elderly / bike）**: 論点カードの件数は正典へ揃ったが、**同じページのアリーナ散布データ `SM_RAW` のセクター `i` は旧分類のまま**で、同一ページ内に2つの内訳が並んでいる。

| テーマ | SM_RAW の件数・内訳 | 正典（`classification.main_issue`） |
|---|---|---|
| elderly-license-revocation | 211件 / 139・24・20・9・7・12 | 211件 / 95・14・19・10・9・64 |
| bike-blue-ticket | **268件** / 54・56・16・28・20・94 | 181件 / 38・29・14・14・18・68 |

bike は件数自体も食い違う（SM_RAW は収集総数268件、分類済みは181件）。`verify_theme_page.py` は SM_RAW を検査していないため exit 0 のまま通る。
**発注書**: `configs/prompts/codex/20260807_elderly-bike-arena.md`（`build_elderly_arena.py` / `build_bike_arena.py` の新設と SM_RAW 再注入、検査追加。ブランチ `task/elderly-bike-arena`）

**2026-08-08 対応済み（憲法改正）**: constitutional-amendment は646件を同一条件で再分類し、意見577件に統一した。`scripts/build_constitutional_arena.py` を新設して SM_RAW・論点別の声・スタンス・詳細表を同じ意見集合から再生成し、`issue_counts.source` と凍結ファイルを削除した。

**2026-08-08 対応済み（辺野古）**: henoko-student-accident は363件を意見性付きで再分類し、意見のみをマップと論点件数の母数に統一。`issue_counts.source` と凍結件数ファイルへの依存を解消した。

**残作業なし。** 最後の `data/issue-counts/henoko-student-accident.json` を削除し、`data/issue-counts/` ディレクトリごと不要になった。**課題29は完了。**

**2026-08-08 検査固定**: 全11テーマでマップ・論点・賛否の母数を「意見のみ」に統一。`verify_theme_page.py` に母数一致、ページ全体の管理対象外件数、最大勢力バッジ、昇格順後のビルダ再生成可能性を追加した。差分は config に件数と理由が無ければ許可しない。`DATA_SHEET.md` の再生成忘れも unittest で検出する。
**横展開の完了条件に追加（2026-08-02）**: constitutional / henoko の `data/issue-counts/` 依存は、それぞれのadapter・ビルダー整備と同時に解消する。累積正典またはGit管理する仮名化検証データから論点件数を再現できることをadapter昇格条件とし、暫定ファイルだけを残さない。

### 課題30: 論点カードの解説と実データの乖離
**状態**: 対応案②（件数の併記）を2026-08-02に全11テーマへ適用済み。①③は未着手
**発見**: 2026-08-01、部活動ページの本番確認時

**2026-08-02 対応済み（S8）**
- `configs/{theme}-reaction-map.json` に `issue_counts`（source / basis / cards）を追加。カードと分類結果のラベル対応をここで宣言する
- `scripts/issue_card_counts.py`（件数の計算）と `scripts/sync_issue_counts.py`（HTMLへの注入）を新設。`<span class="explainer-count" id="issue-count-{theme}-{slug}">N件</span>` を全11テーマ・65枚のカードに併記
- `scripts/verify_theme_page.py` に「=== 論点カード ===」3検査を追加（id付きで併記されている / 件数が分類結果と一致する / ハードコードされた件数が残っていない）
- 解説文の中に重複して書かれていた件数（ai-copyright・elderly・henoko・bike・school-nickname・takaichi の計34箇所）を削除。内訳の数字（「うち30件が反対」等）は残した
- `build_bukatsu_arena.py` / `upgrade_constitutional_arena.py` / `build_consumption_tax_page.py` は生成後に `sync_issue_counts.py` を呼ぶようにした。`upgrade_nickname_arena.js` は手動実行が必要な旨をヘッダに明記

**残り（①③、別途判断）**
- 解説文の config への移行
- 件数順の並べ替え、少数論点の「その他」への集約（部活動の地域格差2件は併記で可視化されたが、カードの大きさは他と同じまま）

**概要**: 各テーマページの「このテーマを読み解く、N つの論点」の解説カードが**手書きの固定文言**で、分類結果の件数と連動していない。件数の大小に関わらず全論点が同じ大きさで並ぶため、実データ上ごく少数の論点が主要論点のように見える。

**具体例（部活動の地域移行）**

| 論点カード | 実件数（389件中） | 紙面 |
|---|---|---|
| 教員の働き方 | 114 (29%) | カード1枚 |
| 教育的意義・機会 | 82 (21%) | カード1枚 |
| 制度・移行プロセス | 81 (21%) | カード1枚 |
| 受け皿・指導者 | 61 (16%) | カード1枚 |
| 費用・家庭負担 | 30 (8%) | カード1枚 |
| **地域格差** | **2 (0.5%)** | **カード1枚**（「都市はできるが地方は無理」と1論点として大きく扱われている） |

同じページの「詳細データ」には `地域格差 2` と正しく出ているため、**同一ページ内で扱いの重みが矛盾している**。

**根が深い点: 解説文がPythonスクリプト内にハードコードされている**

config ではなくビルドスクリプトの中に直接埋め込まれている。

```
scripts/build_bukatsu_arena.py:141   <p class="explainer-card-title">地域格差 — 「都市はできるが地方は無理」</p>
scripts/build_consumption_tax_page.py
scripts/upgrade_constitutional_arena.py
scripts/upgrade_nickname_arena.js
```

**影響範囲**: 全11テーマ（論点カードは各テーマ3〜8枚、計70枚以上）

**対応案**（横展開時に決める）
1. 解説文を `configs/*.json` に移す（コードからコンテンツを分離）
2. 各カードに**実件数を併記**する（「地域格差 **2件**」）
3. 件数順に並べる、または一定件数未満は「その他の論点」にまとめる
4. `verify_theme_page.py` に「論点カードの件数が sample_file の分類結果と一致する」検査を追加

**優先度の判断**: 件数表示自体は全て正しいため緊急性は低い。ただし「実態と表示のズレ」はS1〜S6で潰してきた問題と同じ性質のもの。生成AIと著作権への `arguments` 横展開時に、同じ構造の設計判断が必要になるため、そのタイミングで一括対応する。

**2026-08-02 追記**: 「件数の併記」は S8 で全11テーマに実装済み（`issue_counts` + `sync_issue_counts.py` + `verify_theme_page.py` の検査）。残るのは①解説文の config 移行 ②件数順の並べ替え ③少数論点の集約 の3点。いずれも設計判断が必要なため未着手。

### 課題31: 「世論の潮目」ウィジェットの合成データ残存（koshitsu のみ）
**状態**: **完了（2026-08-12）**。対応案②（実データへの差し替え）で解消した
**優先度**: 高
**判断待ち**: なし
**関連テーマ**: koshitsu-tenpakai
**次にすること**: なし
**発見**: 2026-08-02、S8-fix（koshitsu 正典統一）の完了報告時

**2026-08-12 完了**: 8/10 収集分（325件）を初めて `--promote` で昇格したことで、
潮目の比較対象が「7月26日収集分347件（＝昇格前の正典）」対「8月10日収集分325件」の
実データ同士になった。合成データ `_prev_synthetic.json` はページから参照されなくなった。
再発防止は `scripts/refresh_adapters/koshitsu.py` の `_apply_tide()` にあり、比較対象の
ファイル名に `synthetic` が含まれていると `ValueError` で昇格ごと止まる。
以下は当時の記録として残す。

**概要**: `koshitsu-tenpakai` の「世論の潮目」ウィジェットの**前回値**が、S1 で正典から除外した合成データ `koshitsu-tenpakai_hermes_prev_synthetic.json` 由来のまま残っている。

S8-fix でページ本体（アリーナ・投票・カード・集計・詳細データ）は正典347件から再生成したが、**潮目ウィジェットの比較対象だけは旧データのまま**。

**現在の表示**

```
前回収集分273件と今回収集分347件の構成比を比較します。
比較対象：7月17日収集分の2Dスタンス統計（改正成立直後326件）と
7月26日収集分のAI分類（347件）。前回は2D分類データを再構成した参考値です。
「改正賛成（女系容認）」が9.2ポイント増加
```

**問題点**

1. **合成データが出所** — 前回値は実投稿ではなく、2D分類の集計値から逆算した273件の疑似レコード（`tweet_id: synthetic_*` / `url` 空）。S1 でヒーロー件数から除外した当のデータ
2. **同一ページ内で前回値が2つある** — 本文グラフの説明は「**273件**」、注記は「**326件**」。どちらが前回の母数か読者には分からない
3. **開示が弱い** — 「2D分類データを再構成した参考値」とは書いてあるが、**合成である旨は書かれていない**。読者は実投稿の再分類だと解釈しうる
4. **「9.2ポイント増加」が合成値との比較** — 数字として意味を持たせにくい

**他10テーマは問題なし**（全て実際の収集日を比較対象にしている。確認済み）

**対応案**
1. **koshitsu のみ潮目ウィジェットを非表示にする**（最も安全・実装も軽い）
2. 前回値を実データのある時点（7/12 など）に差し替える。ただし該当データがリポジトリに存在するか要確認
3. ウィジェットは残し、開示文に「前回値は合成データから再構成したものです」と明記したうえで、273/326 の食い違いを解消する

**推奨は案1。** S1〜S8 で「根拠を1行で説明できない数字は載せない」を徹底してきた方針と整合する。ウィジェット自体は他10テーマで正常に機能しているため、機能の削除ではなく1テーマの非表示で足りる。

**該当箇所**: `docs/koshitsu-tenpakai-reaction-map.html` の `TIDE_CARD_START` 〜 `TIDE_CARD_END`

**再発防止**: 対応時に `verify_theme_page.py` へ「潮目ウィジェットの比較対象が合成データでないこと」の検査を追加する

### 課題32: OGP画像とXヘッダー画像に旧コピーとダミー数値が残存
**状態**: 進行中（2026-08-09、OGP差し替え完了・Xプロフィール反映は保留）
**発見**: 2026-08-02、X固定ポスト差し替え時

**準備済みのもの**
- 生成プロンプト: `creative/manga-prompts/site-ogp-header-prompts.md`（サイトのヒーロー準拠）
- 差し替え発注書: `configs/prompts/codex/20260802_ogp-header-replace.md`
- 新画像: 生成済み（リポジトリ未配置。パスは着手時に確認）

**2026-08-09更新**: `docs/ogp/default.png` は、A案のブランドマークと「その話題を、数ではなく問いから読む。」だけを使う画像へ差し替えた。ダミー数値、円グラフ、旧コピーは削除済み。X用ヘッダーとアイコンも `docs/images/brand/` に作成済みだが、Xプロフィールへの反映はサイト公開後に判断する。

**概要**: `docs/ogp/default.png`（2026-06-27作成）に、トップページから削除した旧コピーと根拠のない数値が入ったまま。**サイトのトップURLを共有するたびにこの画像が表示される。**

**画像に含まれている問題のある要素**

| 要素 | 問題 |
|---|---|
| 「その話題、SNSでは実はどっちが多い？」 | S2でトップから削除した旧コピー |
| 賛成42% / 保留18% / 中立20% / 反対20% | **根拠のないダミー値**。S1〜S6で潰した性質の数字 |
| 「トレンド上昇中」「12.5K」「話題沸騰中」 | 実データではない演出値 |

**なぜ緊急度が高いか**

2026-08-02にX固定ポストを「出典は公的資料。**世論調査ではありません**」に差し替えたが、同じ投稿のOGPカードが割合の円グラフを表示しており、**本文と画像が同一投稿内で矛盾している**。

`utm_campaign=profile` / `pinned` を設定して導線を整えた直後であり、**入口の画像だけが最も古い状態**になっている。

**影響範囲**

| 対象 | 現在の画像 |
|---|---|
| `docs/index.html`（トップ） | 新ブランド版 `ogp/default.png` へ差し替え済み |
| `docs/usage.html` | 新ブランド版 `ogp/default.png` を共用 |
| X プロフィールのヘッダー画像 | 新画像は作成済み。プロフィールへの反映は保留 |

テーマ別OGP（`ogp/ai-copyright.png` 等9枚）は個別テーマ用のため、内容を確認のうえ別途判断する。

**やること**
1. [完了] `docs/ogp/default.png` を作り直す（1200×630）
2. [完了] X のヘッダー画像（1500×500）とアイコン（400×400）を作る
3. [保留] サイト公開後にXプロフィールへ反映するか判断する
4. 余力があればテーマ別OGP9枚の内容も点検する

**画像プロンプト**: `creative/manga-prompts/site-ogp-header-prompts.md` に記載

### 課題33: 非公開の正典データと更新履歴の保全先を確立する
**状態**: 完了（2026-08-02。物理的に別のマシンでの再現のみ未実施）
**発見**: 2026-08-02、部活動パイロットのクリーンクローン検証時

**概要**: 本文・URL・ユーザー識別子を含む5テーマの `sample_file` と、`social-samples/updates/` の更新履歴はGit管理外で、このMacにしか存在しない。Macの故障・紛失時はページ再生成と代表投稿の再選定ができない。

**対応済み**: `data/verification/` に、ソルト無しSHA-256で仮名化した投稿IDと分類5項目だけの検証データを保存した。クリーンクローン／CIで件数・論点・意見数・投稿集合の検査は再現できるが、本文付きデータの復元はできない。

**完了条件**:
1. 公開Gitとは別の、アクセス制御された非公開ストレージを1つ正規の保全先として決める
2. 5テーマの本文付き累積正典と `social-samples/updates/` をバックアップする
3. 更新の昇格完了後に自動または1コマンドでバックアップし、失敗を検知できるようにする
4. 別マシンへの復元テストを行い、正典からページ候補を再生成できることを確認する
5. 保存期間、暗号化、アクセス権、削除手順を運用文書へ記録する

**2026-08-02 対応済み（完了条件3）**: `scripts/backup_private_data.py` を追加。`--dest` で必須の非公開 `sample_file` 5本、`social-samples/updates/`、標準化前のGit管理外raw・分類履歴をアーカイブする。必須ファイル欠落時は作成せず exit 1。同日再実行でも別run-idとなり、作成直後にSHA-256・件数の復元確認を自動実行する。実行確認は25ファイル・5,822,291バイト・復元確認 NG 0件。
**2026-08-02 追加対応**: 共通ランナー `scripts/refresh_topic.py` は、更新回履歴を確定した直後と公開昇格後の2地点でバックアップを必須実行する。バックアップ失敗時は更新回を確定せず、昇格中なら公開側を復元する。`--backup-dest` は必須で、保存先未決定のまま本収集できない。
**注意**: tar.gz自体は暗号化されない。保存先はリポジトリ外とし、暗号化・アクセス範囲はオーナー判断を運用文書へ記録する。
**2026-08-02 保存先決定・初回実行**: 正規保存先を `/Volumes/HD-LE-B/issue-stance-private-backups` に決定。個人サイトとして運用するオーナー判断により暗号化は行わない。25ファイル・5,822,291バイトを初回保存し、別コマンドで全25ファイルを展開してSHA-256・レコード件数を照合、NG 0件。アーカイブSHA-256は `a0414f05679bbb366863cfd32df669f45c80a91bc2457ac53178235bc837f1c1`。
**2026-08-02 復元確認（完了条件4）**: 作業ツリーに依存しないことを示すため、Gitのクリーンクローン（非公開 `sample_file` 5本が欠落した状態）へアーカイブを展開し、次を確認した。

1. 欠落5件 → 0件。ignore対象24ファイルと更新回履歴 `updates/bukatsu-chiiki/2026-08-02/{raw,classified}.json` が復元される
2. 復元した正典から `verification_data.py` で検証データを再生成すると、Git上の `data/verification/*.json` 5本すべてとバイト一致する
3. 復元した正典から `build_bukatsu_arena.py` + `sync_issue_counts.py` でページを再生成すると、公開版と**差分ゼロ**
4. その環境で unittest 45件 OK、全11テーマ NG 0件、`verify_top_page` / `verify_sample_periods` ともに exit 0

**Git ＋ 外付けディスクのアーカイブだけで、公開物と検証を完全に再構成できることが実証された。** 残るのは物理的に別のマシンへディスクを接続する確認のみで、データの十分性としては満たしている。
**保存期間**: 当面は全世代保持。ディスクの共有・譲渡・廃棄時はアーカイブを先に削除する。

### 課題34: ページ更新スクリプトが再実行できないテーマの整備
**状態**: **完了**（11テーマ全件がadapter。henokoの候補input/output対応も2026-08-18に完了し、
`THEMES.yaml` の `page_update_mode` は全テーマ `adapter` で確認済み）
**発見**: 2026-08-02、adapter 昇格判定の実測時

**概要**: データ更新を自動化するには「同じ入力で2回実行しても差分が出ない」ページ更新スクリプトが要る。全11テーマで実測し、`THEMES.yaml` の `page_update_mode` に記録した。

| 区分 | テーマ | 状態 |
|---|---|---|
| adapter（11） | ai-copyright / bukatsu-chiiki / elderly-license-revocation / takaichi / koshitsu-tenpakai / bike-blue-ticket / school-nickname-ban / constitutional-amendment / fukushuto / consumption-tax-cut / henoko-student-accident | staging候補の入出力に対応。変更候補の2回目実行で差分ゼロ |
| adapter_candidate（0） | — | 2026-08-18 にhenokoが昇格して解消 |
| migration（0） | — | 2026-08-18 に消費税減税が昇格して解消 |
| manual（0） | — | 2026-08-17 に自転車青切符が昇格して解消 |

**やること**: なし。全11テーマがadapterになったため課題34は完了。次にpage_update_modeを見るのは新テーマ追加時（`new-topic` スキル）だけでよい

**2026-08-18 消費税減税**: `build_consumption_tax_page.py` は副首都ページをテンプレートに読む一度きりの生成器だった。候補input/outputを足し、テンプレートの既定を自分自身の公開ページへ変更。2回目で差分が出ていたのは回遊カードのスクリプトの追記・`.side.mid` の追記・潮目前後の空行の3か所。**投票は「論点の番号×立場の番号」で保存されるため、件数順の並びが入れ替わると過去の投票の意味が変わる**（8/3分を足した時点で実際に入れ替わり、adapterの投票互換性検査が止めた）。公開後は並びを固定する。調査条件（取得元・期間・件数）は昇格後に `finalize` が貼り直す。滞留していた3回分は1回ずつ公開できない（途中の状態が collect_at 期限超過で必ず落ちる）ため、`refresh_topic.py` に `--include-wave` を足して保管済み更新回を1つの候補へ畳み込んだ。**同じ滞留は他テーマでも起きるので、次からはこのフラグを使う。**
**注意**: ビルダーを直したら必ず同じ入力で2回実行し、2回目に差分が出ないことを確認してから `page_update_mode` を上げる

**2026-08-02 共通ランナー対応**: `scripts/refresh_topic.py --topic` に、全11テーマ共通の疎通確認・収集・重複排除・10件試験分類・全件分類・集合検査・更新回保存・バックアップを集約した。migration / manual / adapter_candidate も公開せずstaging止まりで予定どおり収集できる。ページ処理は `scripts/refresh_adapters/` に分離し、takaichi は候補ページ・arena data・潮目を2回生成して差分ゼロ、投票topicIdと15選択肢の互換性を検査する。

**2026-08-14 高齢者免許返納**: `build_elderly_arena.py` を候補input/output対応にし、専用adapterでページ・潮目を2回生成して差分ゼロ、投票topicId・18選択肢・GA4/AdSense/OGPを保護する。保存済み110件の収集履歴は書き換えず、現在の正典と再照合して重複18件を除いた92件（意見45件）を公開。累積364件・意見233件になった。

**2026-08-17 学校あだ名**: `scripts/build_nickname_arena.py` を新設し、一度きりの移行用
`upgrade_nickname_arena.js`（実行のたびに空行が1行増え、SEO meta を374件時代へ巻き戻す）を
`archive/scripts/` へ退けた。移行前の公開ページとアリーナの点を正典からバイト単位で
再現できることを確認してから差し替えている。専用adapterがページとアリーナの点の2ファイルを
2回生成して差分ゼロ、投票 topicId と18選択肢、GA4／AdSense／OGPを保護する。投票ボタンの
件数は毎回変わるので指紋から外した。潮目も更新回から作る形へ移した（課題38の②）。
8月17日収集の46件（意見24件）を公開し、累積420件・意見87件になった。

**横展開のゲート**: 少なくとも保全先の決定、既存データの初回バックアップ、復元確認が終わるまで、他テーマの定期更新を開始しない。

### 課題35: デザインシステム同期の実験が宙に浮いている
**状態**: 完了（2026-08-27。フェーズ3.1で休止実験としてアーカイブ）
**優先度**: 中
**判断待ち**: なし
**次にすること**: 再利用を決めた場合だけ、アーカイブから復帰して現行サイトとの差を再検査する
**発見**: 2026-08-07、運用棚卸し

**概要**: `design-system/`（26ファイル、最終更新 2026-06-21）と、その claude.ai/design 同期まわり一式が残っているが、**`docs/` からの参照は0件**。公開サイトは一切使っていない。

| 対象 | 状態 |
|---|---|
| `design-system/` | Git管理下26ファイル。参照元は `.gitignore` と `.design-sync/` のみ |
| `.design-sync/` | 212KB。`config.json` に `projectId: 7a02f1be-4fed-4822-a2f2-4ac155424358` |
| `.ds-sync/` | **45MB**。gitignore済み。同期ツールの実行環境（node_modules含む） |
| `ds-bundle/` | 2.9MB。gitignore済み。生成物 |

**2026-08-27の処置**: オーナーのフェーズ3.1実施指示を、削除ではなく休止保存の承認として扱った。
Git管理分は `archive/design-system-experiment/`、ローカル実行環境と生成物は
`archive/local/design-sync-runtime/` へ移す。公開サイトからの参照は0件のままなので、公開物は変わらない。

**注意**: 再開時は保存済みの `sync-config/NOTES.md` と現行ツール仕様を照合する。

---

### 課題36: 放置された作業ツリー3本
**状態**: 完了（2026-08-08。3本とも削除済み。中間成果物4件は担当ブランチへ保全）
**発見**: 2026-08-07、運用棚卸し

**概要**: `LOOP.md` ⓪ は「作業が終わったら `git worktree remove` で片付ける」と定めているが、3本残っていた。**3本ともブランチは main にマージ済み。**

| ツリー | ブランチ | 未コミット | 処置（2026-08-08） |
|---|---|---|---|
| `.claude/worktrees/agent-ae24789032b473197` | task/henoko-page-v3 | あり。`docs/henoko-student-accident-reaction-map.html` を公開版1,051行 → 142行のスタブに壊す中断状態（投票セクション・シェア・やり直しボタンが全消え）。**採用してはいけない** | 未コミット分を破棄して削除。origin/main の現行版が正 |
| `.claude/worktrees/competent-gates-92d0d7` | detached HEAD | なし | 削除。コミット 5b69733 は `claude/competent-gates-92d0d7`（ローカル・origin 両方）に残存 |
| `.worktrees/fukushuto-tide` | task/fukushuto-tide | 未追跡4件。2026-08-07 に共有ツリーの `social-samples/` へ退避済み（`fukushuto_hermes_prev_20260714_v2.json/.md`、`fukushuto_test_10.json`、`fukushuto_test_10_classified.json`） | 削除。4件は `task/fukushuto-tide` にコミットして push（3b3efef）。詳細は下記 |

**4件の正体（2026-08-08 に中身を確認）**: `configs/prompts/codex/20260807_fukushuto-tide-widget.md` の**手順1・手順2の成果物**であり、破棄してはいけないものだった。

- `fukushuto_test_10.json` / `_classified.json` — 手順2の試験分類10件。入力は旧5論点で全件「副首都法案の是非」、出力は新7論点に分散
- `fukushuto_hermes_prev_20260714_v2.json` / `.md` — 手順1の7/14分292件の再分類。旧版に対し stance が変わったのは29件

**残作業は 2026-08-08 に完了**（`task/fukushuto-tide` の `433d89c`）。7/26分308件を再分類し、対照表でオーナー承認を得たうえで潮目ウィジェットを7論点へ移行した。同一画面での二重表示は解消済み。作業手順は `.claude/skills/taxonomy-migration/` にスキルとして残した。

**なぜ放置が危険だったか**: 2026-08-07 に共有ツリーで事故が2件起きている（分類処理の参照ファイル消失、統合直後の正典1,606件が削除されかけ）。残ったツリーは同じ事故の温床になる。**今回も、未追跡ファイルを中身を見ずに「不要」と判断しかけた。中間成果物は必ず中身を確認してから処置すること。**

---

### 課題37: validate_theme_seo.py が1件落ちている
**状態**: 未着手（2026-08-07 の棚卸しで検出。棚卸し前から存在する既存の不整合）
**発見**: 2026-08-07

```
FAILED: 1 validation error(s)
- ai-copyright-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

**概要**: `docs/ai-copyright-reaction-map.html` の JSON-LD `dateModified` と `THEMES.yaml` の `updated_at` がずれている。データ更新時にページ側のSEO日付を戻し忘れたと思われる。

**やること**: どちらが正しいか（最後に実際に公開更新した日）を確認して片方へ揃える。ai-copyright は `page_update_mode: adapter` なので、adapter 側で `dateModified` を更新していない可能性も調べる。

---

### 課題38: inject_tide_widget.py が公開中のページを古いデータへ巻き戻す
**状態**: 進行中（自転車青切符だけ 2026-08-17 に解消。ai-copyright / takaichi は未対応で、実行すると巻き戻る）
**発見**: 2026-08-08

**概要**: `scripts/inject_tide_widget.py` は引数を取らず、実行すると `THEMES` の全8テーマの HTML を書き換える。ところが `adapter` 方式のテーマは `refresh_topic.py` 経由で更新されており、スクリプト内の `THEMES` に書かれた更新回のほうが**古い**。そのため実行すると、公開中のページが過去のデータへ戻る。

| テーマ | 公開中 | 実行後（巻き戻り先） |
|---|---|---|
| ai-copyright | 7月26日 → 8月3日 | 7月12日 → 7月26日 |
| takaichi | 7月26日 → 8月7日 | 7月12日 → 7月26日 |

**なぜ危険か**: 1テーマの潮目を直すだけのつもりで実行すると、無関係な2テーマが黙って後退する。`git status` を見て戻さない限り、そのままコミットされて公開される。検査は通ってしまう（日付の新しさを見る検査がない）。

**やること**: 次のいずれか。①`--slug` 引数を足して対象テーマだけ書き換えられるようにする ②`adapter` 方式のテーマを `THEMES` から外し、adapter 側に一本化する ③実行前に「`THEMES` の更新回がページの現状より古くないか」を検査して止める。②が筋が良いが、adapter 側が潮目を生成できるか未確認。

**2026-08-17 自転車青切符**: ②を1テーマ分だけ実施。`THEMES` の `bike-blue-ticket` の `prev_file` / `cur_file` を `None` にして、単体実行では飛ばすようにした（`constitutional-amendment` と同じ形）。潮目は `scripts/refresh_adapters/bike.py` が更新回どうしを比較して作る。残るのは ai-copyright / takaichi / 部活動など、まだ固定ファイル名を持つテーマ。

**暫定の回避策**: 実行後に必ず `git status --porcelain` を見て、対象外の `docs/*.html` が出ていたら `git restore` する。この手順は `.claude/skills/taxonomy-migration/SKILL.md` の「落とし穴」に記載済み。
### 課題39: ポータル（本体トップ）のカウントダウンが毎日ズレる
**状態**: 完了（2026-08-10。対応1を実施）
**発見**: 2026-08-08、日付が変わった直後の検査で検出

**概要**: `docs/index.html` の更新バーに「次回更新: 8月9日（あと2日）」のように**残り日数が固定文字列で焼き込まれている**。日付が変わるたびに1日ずつズレる。

**訂正**: 当初「公開サイトに誤った日数が出続ける」と書いたが、これは誤り。残り日数を計算し直すJSは 2026-07-14 から `docs/index.html` に入っており（`update-bar-days` を書き換える即時関数）、**訪問者にはもともと正しい日数が出ていた**。焼き込まれた文字列はJSが動く前の控えで、実害は検査だけだった。

`scripts/verify_top_page.py` と `tests/test_portal_stats.py` は毎日この不一致で落ちるため、**「検査が落ちているのが平常」になって本当の異常を見逃す**危険がある。実際 2026-08-08 は、別作業の検証中にこれが混ざって原因切り分けが必要になった。

**取りうる対応（どれか1つ）**:
1. 残り日数の計算をページ内のJSに寄せ、HTMLには日付だけ焼き込む（表示は毎回正しくなる。既に `update-bar-days` という id はあるので差し替えやすい）
2. 「あと◯日」の表示自体をやめ、日付だけ出す（いちばん単純）
3. 毎日 `sync_portal_stats.py` を実行する運用にする（人手が増えるので非推奨）

**推奨**: 1。既存の id をそのまま使えて、検査も安定する。

**やったこと**（2026-08-10）: 対応1。`sync_portal_stats.py` が書き出す更新バーから残り日数を外し、`<span id="update-bar-days"></span>` を空のまま置くようにした。カッコごとJSが書くので、JSを切っている訪問者には「次回更新: 8月12日」と日付だけ出る。検査は比べる相手がなくなり、`verify_top_page.py` のNGは0件、unittest 129件も全て通る。バッジは flex なので、要素が3つから2つに減った分だけ幅が5px縮み、カッコ内の余白がなくなった（「8月12日（ あと2日 ）」→「8月12日 （あと2日）」）。

---


### 課題40: 2026-07-26 の一斉収集が5テーマで正典に統合されていない

**状態**: 進行中（6テーマ中3テーマ完了。副首都 2026-08-08 / 高市・高齢者免許 2026-08-14）
**発見**: 2026-08-08

**概要**: 2026-07-26 に全テーマで一斉収集した分が、**「世論の潮目」ウィジェットを作るためだけに使われ、累積正典に統合されないまま**残っている。THEMES.yaml の `collect_delta` には記録されているため、台帳では「追加済み」に見える。公開ページの収集件数は、この分を数えていない。

| テーマ | 7/26に収集 | 正典に未統合 | 現在の正典 | 実際に持っているデータ |
|---|---|---|---|---|
| 副首都 | 308 | ~~308~~ → 0 | 897 | 統合済み（2026-08-08） |
| 高市 | 178 | ~~140~~ → 0 | 675 | 統合済み（2026-08-14。同日の新規88件も公開） |
| 自転車の青切符 | 72 | ~~72~~ → 0 | 355 | 統合済み（2026-08-17。8/10・8/17収集回もまとめて統合） |
| 高齢者免許 | 61 | ~~61~~ → 0 | 272 | 統合済み（2026-08-14） |
| あだ名禁止 | 45 | **45** | 374 | 419 |
| 辺野古 | 39 | **39** | 363 | 402 |
| 生成AIと著作権 | 452 | 0 | 1,606 | 統合済み |
| 皇室典範 | 347 | 0 | 347 | 統合済み |

**当初の未統合は合計665件。副首都308件・高市140件・高齢者免許61件・自転車72件を統合したので、残りは84件（あだ名45・辺野古39）。** 対象テーマの notes には「◯件を追加収集しHermes分類し『世論の潮目』ウィジェットを追加」と書かれており、当時から潮目専用だった。

**なぜ問題か**: ①公開ページの収集件数が実際より少ない ②潮目ウィジェットが、正典に入っていないデータを比較対象にしている ③台帳（collect_delta）とページの数字が食い違う。読者から見えるのは①だけだが、③は今後の集計をずっと狂わせる。

**やること**: 各テーマの `collect_at` のタイミングで、収集と同時に正典へ統合する。7/26分は現行のHermes方式（`is_relevant` / `is_opinion` / `main_issue` / `stance`）で分類済みなので、論点体系が一致していれば再分類は不要。

**対象外（取り残しではないもの）**:
- `koshitsu-tenpakai_hermes_prev_synthetic.json`（273件）… **合成データ**。取得日が無く実投稿ではない。潮目の前回値として注釈付きで開示済み（課題31）
- `ai-copyright_classified_added.json` / `school-nickname-ban_classified_v2_redesign*.json` など … 2026-06 の旧スキーマ（`category` / `policy_attitude`）。現行方式と互換が無く、統合には再分類が必要。別課題として扱う

**2026-08-08 に確認した、統合の可否と作業量**

6テーマとも、7/26分のラベルが現行の分類器の `ISSUES` / `STANCES` に収まる。
**再分類は不要で、そのまま統合できる**（最悪の場合665件の再分類が必要だった）。

作業量はテーマ別ビルダーの有無で決まる。

| テーマ | 日付 | 未統合 | ビルダー | 作業 |
|---|---|---|---|---|
| 副首都 | 08-08 | 308 | 無→新設 | 発注済み（`20260808_fukushuto-canon-merge.md`）。**残り5本の雛形** |
| 自転車 | 08-11 | 72 | 無→新設 | 統合＋ビルダー新設 |
| 高齢者免許 | 08-13 | ~~61~~ | 有 | 完了（2026-08-14） |
| 高市 | 08-14 | ~~140~~ | 有 | 完了（2026-08-14） |
| あだ名禁止 | 08-16 | 45 | 無→新設 | 統合＋ビルダー新設 |
| 辺野古 | 08-18 | 39 | 有 | 統合してビルダーを流すだけ |

**オーナー判断（2026-08-08）: あだ名禁止も統合する。** 意見率17%（374件中63件）で
45件足しても意見は十数件しか増えず、ビルダー新設が必要なため費用対効果は6本中最も
悪い。それでも統合するのは、1テーマだけ例外を残すと「なぜここだけ数え方が違うのか」を
以後ずっと思い出す必要が生じるため。例外を残すコストは後から効く。

**賛否の値は変えない（3値のまま）。** 選択肢数が変わると読者投票の `choiceIdx` の
意味がずれ、Supabase Edge Function の再デプロイと既存票の破棄が必要になる。
4値への統一は8月下旬に全テーマまとめて1回で行う（分けても票のリセット回数は増えない）。

**着手順**: ~~副首都（2026-08-08 に完了）~~ → 自転車(8/11、**未着手のまま残っている**) → ~~高齢者(2026-08-14 に完了)~~ → ~~高市(2026-08-14 に完了)~~ → あだ名(8/16) → 辺野古(8/18)。各テーマの収集セッションに組み込む。**追加のセッション枠は作らない。** どのテーマも収集のために必ず触るため。

**高市・高齢者でやったこと（2026-08-14）**: どちらも `{theme}_hermes_cur_20260726.json` を
`scripts/refresh_topic.py` の `identity()`（tweet_id → URL内status ID → URL → 本文ハッシュ）で
重複判定して正典へ足しただけ。ラベルは現行 taxonomy に収まっており再分類は不要だった。
高市は重複38件を除いて140件、高齢者は重複0件で61件。**高市は収集の前に統合した**ので、
その日の収集の重複判定も統合後の全件に対して行われている。

**副首都でやったこと（残り5テーマの雛形）**:

1. 収集の**前に**正典を入れ替える。7/14分と7/26分（いずれも公開側の論点で再分類済みのv2）を投稿IDで重複排除して結合し、`{theme}_hermes_classified.json` として `sample_file` を差し替える。旧2D正典は消さず `_v1_2d_only.json` に改名して残す。**先に入れ替えると、収集の重複判定が統合後の全件に対して行われる**（後回しにすると、すでに持っている投稿を新規として数え直す）
2. そのうえで `refresh_topic.py` を実行し、更新回の分類結果を正典へ足す
3. `scripts/build_{theme}_arena.py` を作り、ページの件数・論点・賛否・マップの点を正典1本から生成する。`scripts/verify_builder_rebuildability.py` の `BUILDERS` に登録する
4. `configs/{theme}-reaction-map.json` の `denominator_exceptions` を削除する（賛否が入るので不要になる）
5. **新しい正典を `.gitignore` に足す**（本文を含むため。`social-samples/` は全体が除外されているわけではない）
6. **ページ本文に残っている順位の主張（「最多論点」「感情温度が最も高い」など）を外す。** 件数が変わると最大論点が入れ替わり、見出しと数字が食い違う（副首都では「議論の中心」が定義・中身の見出しのまま件数だけ都構想・維新の180件になった）

### 課題41: AI生成画像の制作方針と問い合わせ窓口を公開する
**状態**: 完了（2026-08-09）

**対応内容**:
- `docs/image-policy.html` を新設し、AI生成画像の用途、制作・確認工程、避ける生成指示、限界、ご指摘への対応を明記
- 全公開HTMLのフッターから「画像制作方針」へ移動できるようにし、sitemapへ登録
- 既存Googleフォームに「画像・著作権等に関するご指摘」を追加し、記載してほしい情報を案内
- Googleフォームの「その他」を選択肢の末尾へ移動
- 画像制作方針ページを「このサイトについて」「免責事項」と共通の情報ページデザインへ統一
- `tests/test_image_policy.py` で方針ページの必須内容、全公開ページの導線、sitemap登録を固定

**対応範囲**: 方針公開と受付整備のみ。既存画像の削除・差し替えは行っていない。

### 課題42: AI生成画像を用途別方針へ移行する
**状態**: 完了（2026-08-09、全11テーマのヒーロー統一完了）

**決定済みの方向**:
- 「データ編集部＋論点地図」を軸に、ネイビーと4視点カラーでサイト・OGP・Xを段階的に統一
- indexの漫画風画像は、人物漫画ではない図形・アイコンへ段階的に置換
- テーマ別ヒーローは、人物なし・画像内文字なしでAI生成を継続
- 論点インフォグラフィックは今回は現行画像を維持し、テーマヒーロー統一後の別課題とする
- テーマページの漫画本編は掲載終了
- 人物を描いた投票画像は中立アイコンへ置換

**段階別の状態**:
1. 共通ブランド・アイコン: A「編集地図」を採用し、正式SVGと各サイズの画像を書き出し済み
2. index・共通ロゴ・favicon・OGP: 完了。人物画像7枚を論点地図SVGへ差し替え、X用画像も作成済み
3. テーマ別ヒーロー: 全11テーマを人物なし・画像内文字なしの「中央の問い＋4視点」画像へ差し替え・公開完了
4. 論点インフォグラフィック: 現行維持。将来の別課題

**注意**: 本課題は画像種類ごとにさらに分割して着手する。課題41の作業に混ぜない。

### 課題43: ページ上の数字に出所を持たせる（検査の常設）

**状態**: 検査を常設化して全11テーマが通過（2026-08-09）。残りは下の「積み残し」だけ

**なぜ作ったか**: 2026-08-08〜09 の2日間で「表示される数字が合わない」が5回起きた。

| 回 | 見つかった場所 | そのときの対応 |
|---|---|---|
| 1 | 論点カードの見出しの手書き件数 | `sync_issue_counts.py` で生成 |
| 2 | `theme-seo.json` のべた書き件数 | `{total}` / `{opinions}` の差し込みへ |
| 3 | ビルダと `apply_theme_trust.py` が同じ文を書く | 書き手を1つに |
| 4 | 論点ナビ・論点セクション・アリーナのセクター | `issue_counts.sync` で生成（PR #59） |
| 5 | `sitemap.xml` の生成元にページが無い | 生成元へ追加 |

5回とも構造は同じ。**数字の正典は1つなのに、表示している場所が何か所あるかを誰も知らない。**
人が場所を列挙し、列挙した場所だけを同期する。新しい場所が見つかるたびに列挙を足す。終わらない。

**この検査が保証すること**:

> ページに出る数字は、正典から導けるか、理由付きで許可リストに登録されているかのどちらかである。
> 新しい表示場所が増えても、同期し忘れれば `scripts/verify_number_provenance.py` が落ちる。

`python3 scripts/verify_number_provenance.py`（`tests/test_number_provenance.py` からも実行）。
設定は `configs/{テーマ}-reaction-map.json` の `number_provenance`。
クロス集計・波・和差は、configs に領域を書いた場所でしか使えない。
**書いていない場所＝新しく現れた場所は、常にいちばん厳しい判定になる。**

**この検査で見つかった古い数字（今回まとめて直した）**:

| テーマ | 場所 | 直し方 |
|---|---|---|
| 部活動 | リード文 意見389件 → 599件 | `sync_issue_counts.py` の `lead` で生成 |
| 高市 | リード文 意見223件 → 359件 | 同上 |
| 高市 | 「※ SNS投稿223件をAIが分類」→ 447件 | `sync_issue_counts.py` の `note` で生成 |
| 高齢者 | 投票の選択肢の説明文（139件など） | `build_elderly_arena.py` の `sync_vote_counts` で生成 |
| 部活動 | 注目ポイント4枚（464/176/114/66件と割合） | 手で修正（生成側なし） |
| 高市 | 注目ポイント4枚と論点内スタンス分布5本 | 手で修正（生成側なし） |
| 自転車 | 注目ポイント・論点内スタンス分布・論拠本文の件数 | 手で修正（生成側なし） |
| 辺野古 | 2Dマップ「安全・追悼重視(下方向)」34件 → 78件 | 手で修正。旧2D正典の `stance_focus<0` は78件で、34件はどの規則にも当たらなかった |

**積み残し（別課題として着手する）**:

1. **注目ポイント（`insight-stats`）と論点内スタンス分布（`temp-bar-wrap`）に生成側が無い**
   テーマは部活動・高市・自転車。今回は手で直した。次のデータ更新で必ず古くなるが、
   検査が落ちるので黙って腐ることはない。`sync_issue_counts.py` に生成対象を足すのが筋
   **2026-08-14 に高市の更新でまた発生し、また手で直した**（注目ポイント4枚と分布5本。
   説明できない数字が 1 → 30 → 1 と動いた）。7日周期のテーマなので毎週これが起きる
   **同日、部活動の更新でも発生した**（注目ポイント4枚の5箇所。意見599→689件、関連724→841件、
   移行支持278→315件、教員の働き方184→212件、改善条件あり105→128件）。部活動のページ本体には
   `temp-bar-wrap` の実体が無く、直す必要があったのは `insight-stats` だけだった。
   **3テーマ目で同じ手作業が3日以内に3回**。生成側を足す判断はもう先送りしないほうがよい
2. **高齢者の詳細データ「カテゴリ × 検索クエリ／スタンス」96セル中7セルが再現できない**
   2026-07-01 の「その他・分類保留」再分類の途中状態が残っている。
   いまは `number_provenance.allow` に領域を限って登録してある。表そのものを現行論点へ
   作り直すのが本筋（生成AI・自転車・憲法改正の同じ表は旧1D正典から完全に再現できる）
   **7セル目は 2026-08-14 に判明した**（「その他・分類保留 / 免許返納 地方 生活」の4件。
   旧1D正典では2件）。それまでは正典側の別の集計とたまたま値が一致していて通っており、
   正典が増えた瞬間に露出した。この表の「再現できないセル」は今後も増える可能性がある
3. **旧2D分類の表と現行論点が同じページに併存している**（生成AI・自転車・憲法改正・高齢者）
   `taxonomy-migration` スキルの対象。今回は出所を持たせるところまで

**検査が捕まえられない数字の出方**:

- `件` も `n:` も付かない数字（`<b>103</b>` のような対戦表示、`%`、画像に焼き込まれた数字）は拾えない。
  今回の高市「批判103 VS 擁護102」も検査ではなく目視で見つけた
- 値が小さいと、別の集計とたまたま一致して通ってしまう。ラベルが添えてある数字は
  「そのラベルの集計」に限定して照合するが、ラベルの無い数字は値だけの照合になる

### 課題44: SNS反応マップの共通デザインを再設計する
**状態**: **課題54へ統合（2026-08-30）**。既存2Dは3Dが完成するまでフォールバックとして維持し、旧設計の他テーマへの横展開は停止する

**確定した設計**（試作段階の記述は破棄）:
- テーマページ = 「問いの背骨」。縦=論点、中央線=未解決の問い、左右=立場、
  中央からの距離=主張の強さ。**左右の縮尺は必ず対称にする**
- 論点ラベルは点の帯の外（行の左端）に置く。点に重ねない
- トップページ = 論点アトラス。**位置に意味を持たせない。**
  軸ラベルと中央線は置かない。立場は色と「← / ・ / →」で示す
- テーマ固有の左右軸は configs の map_axes.xAxis を使う（未設定は
  consumption-tax-cut / fukushuto / koshitsu-tenpakai の3テーマ）

**やってはいけないこと**（試作で実際に起きた失敗）:
- 全テーマ共通の左右軸を1つ置く → AI以外の8テーマで意味を成さない
- チップの位置をCSSのmarginで決める → データと無関係な位置が意味に見える
- 論点ラベルやチップをHTMLに手書きする → 論点体系を変えたとき追随しない
- ページの表示文字列を検査やビルダーの目印にする → デザイン変更で必ず壊れる
  （目印は data-arena-total のような表示に依存しない属性にする）

**残っている課題**: スマホでのCanvas内文字（実効4.7px）、高DPI未対応、
15論点で行が重なる、Canvas上の投稿点にキーボードで到達できない、
トップのアトラス34語が手書き


---
### 課題45: X運用の手の内を公開リポジトリから外す
**状態**: 未着手（第1段階のみ完了。2026-08-10、PR #80）
**きっかけ**: オーナーから「Xの情報があまり見られたくない」。調査の結果、
`docs/content/x/posts.md` が GitHub Pages でそのまま配信されており（HTTP 200 を確認）、
投稿文案とリプライ実績の表示回数がサイト訪問者から見える状態だった。
PR #80 でリポジトリ直下へ移し、サイトからは消えた。**リポジトリを直接
開いた人にはまだ見える。** これを消すのが本課題。

**前提（調査済み・作業前に読むこと）**:
- リポジトリを private にする案は使えない。Org が Free プランで、
  非公開リポジトリから Pages を配信できない → **サイトが止まる**
- 鍵・トークンの類は公開ファイルに無い（確認済み）。`G-K10S4YCZFH` は
  そもそもページに埋まる公開値。つまり漏洩ではなく「見え方」の課題
- サイト側は既に AI 利用を明記している（各テーマページに「AIを関連性・
  意見性の判定、論点・立場・表現強度の分類、要旨作成の補助に使用」）。
  **隠す対象は「AI利用」ではなく、集客のやり方とまだ小さい数字**
- CI は `.github/workflows/deploy.yml` の Pages デプロイ1本だけで、
  テストを回していない。`docs/` しかアップロードしない。
  → **Git 管理から外してもデプロイは壊れない**

**取るべき方法（移動ではなく、追跡をやめる）**:
`git rm --cached` ＋ `.gitignore` で「ファイルは今の場所に置いたまま、
Git の追跡だけ外す」。パスが変わらないので参照の書き換えが要らず、
スクリプト・テスト・Skill がそのまま動く。`social-samples/` の非公開正典と
`company/dashboard/` で既に使っている方式と同じ。

**スコープA（小・確実）— X運用の5ファイル**:
- `content/x/posts.md` / `X_POSTING_GUIDE.md` / `.claude/skills/x-daily/SKILL.md`
- `configs/prompts/claude-code/x-daily-session.md`
- `configs/prompts/codex/x-post-view-measurement.md`
- 触るコード: `scripts/x_post_views.py`、`scripts/admin_dashboard/`、
  `tests/test_admin_dashboard.py`（パスは変えないので、**新しい worktree で
  ファイルが無いときに落ちる**扱いだけ決める）

**スコープB（大・要判断）— AI運用そのもの**:
`GROWTH.yaml`（25ファイルから参照・コード6本が依存）、`creative/manga-prompts/`（28ファイル）、
`CLAUDE.md` / `AGENTS.md` / `LOOP.md` / `AI_HANDOFF.md` / `configs/prompts/` 全体。
**参照が広く、AIが手順書を読めなくなる副作用がある。** サイトが既に AI 利用を
開示している以上、費用対効果が悪い。Aを終えてから改めて判断すること。

**必ず対処すること（Aでも起きる）**:
- 追跡を外したファイルは **新しい worktree に入らない**（`git status` にも出ない）。
  LOOP.md ⓪ の復元手順に追加し、`scripts/backup_private_data.py` の対象にも入れる。
  入れ忘れると、バックアップの無いファイルが手元にだけ存在する状態になる
- 過去のコミット履歴には残る。履歴の書き換えは他セッションの worktree と
  衝突するので**やらない**方針（2026-08-10 にオーナーへ説明済み）

**完了の見分け方**: `git ls-files | grep -E "x-posts|X_POSTING"` が空。
`python3 -m unittest discover -s tests` が 184件 OK のまま。

### 課題47: 自動生成されるファイルへ手で足した文章が、公開昇格のたびに消える

**状態**: 判明した3件は対処済み（2026-08-13〜14）。同じ形の4件目がいつでも起きうる
**発見**: 2026-08-14、高市の収集セッション（`build_constitutional_arena.py` の件は別セッションが同日に独立して発見・修正しており、`12fc063` / `8dd81ae` として先に main に入っている）

**何が起きたか**: 手で足した文章が、生成側のスクリプトに上書きされて消えていた。

| 消えたもの | 上書きしていた側 | 影響 | 直したコミット |
|---|---|---|---|
| 憲法改正ページの「収集・分類で分かったこと」 | `build_constitutional_arena.py` が `article-trust-method` の div ごと作り直す | **全テーマが `--promote` できない状態だった** | `12fc063` |
| 調査条件の `review-note` の囲み | 同上 | 数字の出所検査が落ちる | `8dd81ae` |
| `docs/robots.txt` の「このファイルはクローラーに読まれていない」注意書き | `generate_seo_assets.py` が毎回まるごと書き出す | 次に触る人が同じ調査をやり直す | 本ブランチ |

**同じ日に2セッションが別々に踏んだ。** 高市の公開は `verify_theme_page.py` で止まり、
原因を調べて同じ修正に行き着いた（マージ時に競合して、先に入っていた `12fc063` を採用）。
`review-note` の囲みも、高市・高齢者のページ再生成でもう一度落ちてマージ時に戻している。

**なぜ公開が止まるのか**: `refresh_topic.py` の昇格処理は `verify_theme_page.py`（全テーマ）に
合格しないと巻き戻す。その中の再生成可能性検査が、憲法改正ページで「ビルダーの出力と
公開版が一致しない」で落ちていた。**壊れたのは憲法改正ページなのに、止まるのは全テーマの公開。**
2026-08-13 の変更以降、誰も `--promote` を実行していなかったため気づかれていなかった。

**対処**: いずれも生成側に文章を持たせた。ビルダーは既存の節を読み取って持ち越し、
robots.txt の注意書きはスクリプトの出力に含めた。

**残る危険**: 「ページを手で直す」作業は今後も起きる。手で足したものが生成側の
書き換え範囲に入っているかは、`python3 scripts/verify_theme_page.py`（引数なし）を
実行しないと分からない。**ページを手で直したセッションは、必ずこれを実行して終わること。**
テーマを指定した実行（`verify_theme_page.py {theme}`）では再生成可能性検査が走らない。

---

### 課題48: ルートと本体、トップページが2枚あり、放っておくと中身が重複していく

**状態**: 独自ドメイン移行と1リポジトリへの統合を実装中（2026-08-30、公開はCEO承認待ち）
**発見**: 2026-08-15、オーナーの指摘「面白みのないトップページ」「SNS反応まっぷを見るボタンを押すとまたトップページみたいなのが立ち上がる」

**何が問題か**: ドメインの入口が2枚あり、役割が文書化されていない。

| | `issue-stance-lab.github.io/`（ルート） | `issue-stance-lab.github.io/sns-reaction-map/`（本体） |
|---|---|---|
| リポジトリ | `issue-stance-lab/issue-stance-lab.github.io` | `issue-stance-lab/sns-reaction-map` の `docs/` |
| title | Issue Stance Lab | SNS反応まっぷ |
| sitemap | 自分1枚のみ | 17ページ |
| 投票・注目の問い・論点アトラス | なし | あり |
| X運用で使っているURL | 3回 | 18回 |

**読者にとってのトップは `/sns-reaction-map/`。ルートは AdSense と検索エンジンのための入口。**
2枚あるのは設計判断ではなく、サイトを `sns-reaction-map` リポジトリで作ったあと、
課題15（AdSense はサブドメイン全体を見る）への対応でルートを後から足した経緯による。

**実際に起きた事故**: 役割が決まっていないため、ルートに本体トップと同じ内容を書いてしまった。
2026-08-14 の初版を実測したところ、**ヒーロー・件数・工程説明・テーマ一覧・注意書き・読み方の
6要素すべてが重複**し、画像だけが無い劣化コピーになっていた。ヒーロー画像を足す案も、
ポータルが同じ絵柄を使っているため「また同じページ」になり、没にしている。

**2026-08-15 対応済み（重複の除去）**: `scripts/build_root_index.py` を作り直した（`8d2a39e`）。
- ポータルと重複する説明（3ステップ・数字の読み方・編集方針の列挙）を削除し `docs/about.html` へ寄せた
  （`#numbers` を新設）
- カード画像は**論点別インフォグラフィック**。ヒーロー画像はポータルが使っているため使わない
- 各カードに論点1のスタンス内訳バーを追加。ラベル・件数・幅はテーマページの表示をそのまま
  引き写すので、ルートで数え直さない（課題29・課題43と同じ方針）
- ポータルのフッターにルートへの導線を追加。**それまでルートへ戻るリンクが1本も無かった**
- 可視テキスト 3,645字 → 2,530字、画像 0枚 → 11枚

**バーを出していない3テーマ**: 副首都・部活動の地域移行・高齢者免許返納は
テーマページにスタンス内訳バーが無いため省いている。**共通の「賛成／反対」バーには丸めないこと。**
高市文春は「批判／擁護」、辺野古は事故の「評価」で、是非を問う争点ではない。
丸めると課題30（正典に対応が無い擬似ラベル）と同じ事故になる。

**当初の統合案（2026-08-15時点）**: サイト本体をルートへ移し、トップを1枚にする。
- 利点: 「どっちがトップか」の混乱が消える。重複が構造的に起こらなくなる
- 費用: **全17ページの URL が変わる。** 2026-08-14 にインデックス登録された3ページを含め、
  Google への登録がやり直しになる。X の過去投稿18件のリンクも旧URLを指す
- **審査の直前にやらないこと。** 通過を確認してから着手する

**2026-08-30 CEO決定**: 独自ドメイン `sns-reaction-map.jp` を取得したため、当初案を実行する。
- `issue-stance-lab/issue-stance-lab.github.io` を唯一の公開専用リポジトリにする
- 本体を新ドメインのルートへ置き、旧ルート用トップを廃止する
- このリポジトリの `docs/` を正典とし、`scripts/sync_public_site.py` で公開専用リポジトリの `public/` へ同期する
- canonical、OGP、sitemap、robotsを `https://sns-reaction-map.jp/` へ統一する
- 旧 `/sns-reaction-map/` パスには同名ページへの移行案内を置く
- Search ConsoleとAdSenseは新ドメインを追加し、安定後に公開データ基盤と非公開化を判断する

設計・公開ゲート・ロールバックは `quality/designs/domain-migration-2026-08-30.md` を正典とする。
公開専用リポジトリへの反映、カスタムドメインの付け替え、一般公開は別途CEOの最終承認後に行う。

**未確認**: 公開後の実物を見ていない。作業環境から外部サイトへ到達できないため
（`curl https://issue-stance-lab.github.io/` が 000）。反映確認はオーナーの手元で行う。

---

### 課題49: 管理画面からCodex運用セッションを起動する

**状態**: 実装完了（2026-08-29、初回の実データ運用確認待ち）
**実装内容**:
- Codex App Serverで作った読み取りセッションがCodexデスクトップアプリのタスク一覧に現れ、同じ履歴を読み直せることを実証した
- `管理画面を開く.command` から、127.0.0.1限定・起動ごとの秘密トークン付き管理画面を必要時だけ起動する
- 許可済み8操作と登録テーマIDだけを受け付け、変更作業は専用worktree・同時1件・未コミット保護で実行する
- 収集、公開候補、別セッション品質監査、CEO承認後の公開、X準備・記録・計測、GA4・Search Console・Supabase取得と解説を画面に統合した
- 公開は `--prepare-promotion` と `--apply-promotion` に分け、manifestハッシュが変われば承認候補を適用できない
- Xは投稿画面の準備までとし、実際の「ポストする」はオーナー操作のまま残した

**初回運用で確認すること**: 実データで1テーマの「収集・分類」から「公開候補を確認」までを通し、通知とログイン継続も確認する。本番公開はその候補に対するCEO承認がある場合だけ行う。

**2026-08-29 追加**: 「今日のX候補」で、検索回数、読み込んだ検索結果、重複除外後の投稿、個別確認、投稿者、候補数を件数だけ記録するようにした。各作業履歴には当時のX API単価と換算費用を保存し、管理画面には直近30日の「投稿だけ」と「投稿者情報込み」の2通りを表示する。過去の不明な検索総数は推測で補完しない。

**2026-08-29 共通化**: 実測記録を管理画面起動のセッションだけでなく、`x-daily`を使うCodex／Claudeデスクトップアプリへも拡張した。本文・URL・アカウント名を含まないローカル共通台帳へ保存し、管理画面は実行場所を問わず同じ30日集計を表示する。

---

### 課題50: AI中心の会社運営形式へ整理する

**状態**: フェーズ1〜3.1と4-A完了。フェーズ4-B（安全運用台帳と復元試験）が次

**着手日**: 2026-08-26
**目的**: 理念、目標、AI部門の責任、CEO承認範囲を明確にし、週10時間以内で運営できる構造にする。

**ロードマップの正典**: `company/ROADMAP.md`

**フェーズ1｜会社の基礎設計（完了）**:

- `company/` に理念、数値目標、承認、収支、経営判断、6部門の責任を追加
- `AI_HANDOFF.md` を旧構想から会社運営の入口へ置き換え
- `README.md` / `CLAUDE.md` / `AGENTS.md` から会社文書を参照
- `OPERATIONS.md` / `DATA_REFRESH.md` に「AIが候補作成・検査、CEOが公開を最終承認」を反映
- レビューで見つかった note 頻度、新テーマ手順、note更新承認の矛盾を修正

**フェーズ1.5｜進行中業務の引き継ぎと安定化（完了 2026-08-27）**:

1. テーマ更新、X、note第1〜4回、AdSenseを `company/HANDOFFS.yaml` へ登録する
2. 台帳間の実績日、期日、次の一手を照合する
3. Git未追跡の手順・調査・レビューを内容別に保全する
4. 実際の承認と月次収支の記録を開始する

**フェーズ2｜理念と公開品質の統一（完了 2026-08-27）**:

1. テーマ設定、OGP、タイトル、ボタン文言を棚卸しする
2. 「あなたはどっち？」、「どっちが多い？」など、二択や対立をあおる旧文言を、論点と背景が伝わる表現へ変える
3. ページ再生成・公開前検査・CEO承認後に反映する

**フェーズ3｜情報設計とフォルダ整理（完了 2026-08-27）**:

1. 現役の手順書と古い構想文書を棚卸しし、重複・矛盾するものを `archive/` へ移す
2. Website / X / note の下書き・調査・実績の置き場を媒体ごとに設計する
3. まず参照の少ない文書から移し、`docs/` / `scripts/` / `data/` / `configs/` は参照先と検査をすべて更新できるときだけ移す

**フェーズ3.1｜ルート直下の実整理（完了 2026-08-27）**:

1. デザイン・ブランド・画像プロンプト・テンプレートを `creative/` へ集約
2. Website内部資料と調査を `content/website/` へ集約
3. 管理画面を `company/dashboard/`、設計レビューを `quality/`、完了計画と休止実験を `archive/` へ移動
4. Git管理外のnote原資料とデザイン同期生成物も、大分類配下へ削除せず移す経路を定義
5. 管理画面生成、11テーマ検査、数値出所、トップページ、全259テストに合格

**フェーズ4-A｜CEO経営ホーム（完了 2026-08-27）**:

1. 管理画面に90日・1年・3年目標、承認待ち、月次収支を表示する
2. 毎日のCEO報告を「昨日の結果 / 今日の作業 / 遅れ・問題 / 承認事項」の4行で作れるようにする
3. 承認、訂正、費用の記録漏れをアラートで見つける

**フェーズ4-B｜安全運用の可視化（次）**:

4. 障害、契約、アカウント権限、バックアップ復元の台帳と検知を追加する

**フェーズ5｜収益化と成長の運用（常時並行）**:

1. AdSense の審査結果に対応し、通過後は最初の1円とページRPMを記録する
2. Xは4つの時間帯で候補を調べ、価値を足せるときだけCEO承認後に投稿する
3. noteは3日に1本を目安に無料で届け、30日後に実測と独自価値がある記事だけを500円化候補として提案する
4. 月次で収益・費用・利益と目標の差を確認し、翌月に試す施策は1つだけ決める

**フェーズ6｜拡大と法人化準備（条件到達後）**:

1. 収益源別の利益、作業量、リスクを整理する
2. アカウント、データ、契約、著作物の移管先を整理する
3. 会計、税務、契約、個人情報、広告表示を必要な時点で専門家に確認する
4. 3年目の月間収益100万円を主な目安とし、CEOが法人化の実行可否を決める

**ルートに維持する技術基盤**: `docs/` / `scripts/` / `data/` / `configs/` / `tests/` /
`social-samples/` / `supabase/`。公開・収集・検査の実行経路そのものなので、大分類の下へは移さない。

---


### 課題51: サイト内記事セクションを新設する（検索流入用）

**状態**: 未着手。`writer-seo` エージェントは作成済みだが、公開先が無いため下書きのみで待機中
**発端**: 2026-08-27、編集部にライター3名（`.claude/agents/`）を採用した際、`writer-seo` の
担当媒体「サイト内SEO記事」が**実在しない**ことが分かった。`docs/` にあるのは11本のテーマページと
法務ページだけで、`sitemap.xml` にも記事は0本。

**なぜやるか**: 90日目標に月3,000ページ表示がある（`company/GOALS.yaml`）。テーマページは
1テーマ1本しか作れず、検索語の幅を取れない。「〇〇 賛否」「〇〇 どっちが正しい」で流入する
読者向けの記事があれば、既存の投票ページへ送れる。

**決めること**:
1. URL設計（`docs/articles/{slug}.html` か、テーマ配下か）
2. HTMLテンプレート（テーマページの `topic-modern.css` を流用するか、専用にするか）
3. `index.html` からの導線と `sitemap.xml` への登録
4. 記事から投票ページへの導線の形
5. 記事の生成方法。**手書きHTMLを `docs/` へ直接置かない**
   （`verify_builder_rebuildability.py` が落ちる。課題47と同じ事故）
6. 記事に対する `verify_page_originality.py` / `verify_ai_tone.py` の掛け方

**完了条件**: 記事1本が公開され、上記6つの検査・導線がすべて通ること。
**関係する文書**: `WRITING_VOICE.md` / `.claude/agents/writer-seo.md` / `company/GOALS.yaml`

---

### 課題52: 既存11ページのAI臭をリライトで落とす

**状態**: 未着手。検査（`scripts/verify_ai_tone.py`）と baseline は 2026-08-27 に設置済み
**発端**: 公開11ページの本文1,007文を実測したところ、「いかがでしたか」の類の安っぽい定型は
**0件**だった一方、**賛否を同じ構文で並べる鏡像**が見つかった。これが読者に「AIが書いた」と
感じさせる最大の要因。

> 推進側の最も強い根拠は、〜ことです。慎重側の最も強い根拠は、〜ことです。

**baseline に登録した既存分**（`configs/ai-tone.json`。ここを0へ減らすのがこの課題）:

| テーマ | 検出 | 件数 |
|---|---|---|
| ai-copyright | 側の最も強い根拠は | 2 |
| bukatsu-chiiki | 側の最も強い根拠は / というのが◯◯側の強い主張 | 各2 |
| elderly-license-revocation | 側の最も強い根拠は / というのが◯◯側の強い主張 | 各2 |
| bike-blue-ticket | というのが◯◯側の強い主張 | 2 |
| school-nickname-ban | ではなく（密度 6.7/100文、上限5.0） | 4 |

**難しさ**: 本文は `scripts/refresh_adapters/*.py` と `configs/prompts/` の発注書から生成される。
ページのHTMLを直接直すと次のデータ更新で戻る。**発注書と adapter 側を直す必要がある**。

**手順の骨子**:
1. 該当テーマの発注書に `WRITING_VOICE.md`「1. 対称にしない」を組み込む
2. 賛否のどちらかを別の入り口（具体的な場面、数字、未解決点）から書き直す
3. `python3 scripts/verify_ai_tone.py` で baseline を下回ることを確認し、`configs/ai-tone.json` の
   baseline を実測値まで下げる（**下げ忘れると次の劣化を検知できない**）
4. `verify_page_originality.py` と `verify_theme_page.py` を通す

**注意**: X の投稿済み台帳（`content/x/posts.md`）に「〜ではないでしょうか」が4件ある。
過去の投稿は取り消せないため検査対象外にしたが、同じ癖が続いていたことは記録に残す
（`x-daily/references/writing.md`「テーマ全体の感想を求めない」に反する）。今後は
`writer-x` と下書き段階の検査で止める。

---

### 課題53: X検索実測を1週間記録し、X API移行費用をレビューする

**状態**: 進行中（実測期間 2026-08-29〜2026-09-05）
**優先度**: 中
**期限**: 2026-09-05
**判断待ち**: なし
**関連テーマ**: X運用、課題49
**次にすること**: CodexまたはClaudeアプリで`x-daily`を使うたびに検索実測を共通台帳へ保存し、2026-09-05に7日分をレビューする

**記録するもの**:
- 検索回数、読み込んだ投稿数、重複除外後の投稿数、個別確認数、投稿者数、候補数
- 完全記録か一部欠測か
- 投稿取得だけの場合と投稿者情報も取得する場合のX API換算費用

**レビュー内容**:
1. 記録できた日数・実行回数と欠測理由
2. 1回・1日あたりの確認投稿数と投稿者数
3. 7日間のAPI換算費用と、同じペースでの月額予測
4. 収益化前の月額運営費上限3,000円に対する割合
5. Chrome運用継続、検索だけAPI化、API移行見送りのいずれを推奨するか

**完了条件**: 7日分を集計し、実測に基づく推奨案を`content/x/weekly-reviews.md`へ記録して、この課題の状態を完了へ更新する。

---

### 課題56: 公開後の反映確認が index.html を誤ったパスで読んでいる

**状態**: 未着手（2026-08-31、課題55の段階2独立レビューで検出。課題55より前から存在する既存バグで、今回の移行が原因ではない）
**発見**: 2026-08-31
**優先度**: 低〜中（管理画面からの公開作業でしか発現しない。手動 `git push` では影響しない）

**概要**: `scripts/admin_dashboard/jobs.py` の `_verify_live_pages`（635行目）が、公開後にトップページが
本当に反映されたかを確認する際、`self.root / "index.html"` を読んでいる。しかし実際のトップページは
`docs/index.html` にあり、リポジトリ直下に `index.html` は無い。1行上でテーマページを読む処理は
`THEMES.yaml` の `html:` の値（`docs/...` を含む）をそのまま使っており正しい。

**やること**: 635行目を `(self.root / "docs" / "index.html").read_bytes()` に直す。

**完了条件**: 管理画面から公開を実行したとき、`_verify_live_pages` がトップページを正しく検証し、
`FileNotFoundError` で失敗しないこと。

---

## 連絡メモ（AI間の申し送り）

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-27 | Antigravity | 全員 | AdSense審査通過後にプロジェクト用アドレスを「管理者」として招待し権限移行すること |
| 2026-07-01 | Antigravity | 全員 | 課題16 OGP対応完了。build_reaction_map.pyにOGP自動挿入機能を追加済み |
| 2026-08-01 | Claude | 全員 | `archive/planning-2026-08/WORK_PLAN_2026-08.md` と `archive/planning-2026-08/WORK_PLAN_2026-08_SESSIONS.md` を追加。8月はこの計画に従い、S1〜S5 のセッション単位で進める。発注書は `configs/prompts/codex/` に置く |
| 2026-08-01 | Claude | 全員 | S1完了。トップの数値は `THEMES.yaml` の `sample_file` の実レコード数から生成される。**数値をHTMLに直接書かないこと。** 変更後は必ず `python3 scripts/verify_top_page.py` を実行し、NG（exit 1）がないことを確認する |
| 2026-08-10 | Claude | 全員 | 課題44は生成AIのみ完了。アリーナの母数は `data-arena-total` 属性が正典。表示文字列を検査・ビルダーの目印にしないこと |
| 2026-08-15 | Claude | 全員 | **ルート（`issue-stance-lab.github.io/`）は入口。説明を書き足さないこと。** 調査方法・編集方針・数字の読み方は `docs/about.html` に一本化する。ルートは `scripts/build_root_index.py` が正典から生成するので手で編集せず、変更後は `--check` で一致を確認する。読者にとってのトップは `/sns-reaction-map/` 側。詳細は課題48 |
| 2026-08-30 | Codex | 全員 | **上の2026-08-15ルールは廃止。** `sns-reaction-map.jp/` を唯一のトップにし、`issue-stance-lab/issue-stance-lab.github.io` を唯一の公開専用リポジトリとする。公開物は `docs/` から `scripts/sync_public_site.py` で同期する。詳細は課題48と `quality/designs/domain-migration-2026-08-30.md` |
