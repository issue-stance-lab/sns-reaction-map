# 課題55: カスタムドメイン移行と公開元の一本化（課題54・15-Cの前提）


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
