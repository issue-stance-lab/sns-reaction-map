# データ更新の運用手順

## 基本方針

### 収集と公開は同じセッションで（2026-09-25〜、オーナー決定）

- **収集したら、同じセッションで本文確認・正典反映・公開まで終える。** 収集だけで終わる回を作らない。
  X日次のついでの収集（旧 `collection-bridge.md`）は廃止した。
- 公開の直前に、チャットでオーナーの承認をもらう（Website公開は毎回承認。`company/APPROVALS.yaml` に記録）。
  承認を待つ間もセッションは閉じず、承認後に同じセッションで公開まで進める。
- 予定日は1本。`collect_at` と `refresh_at` は**公開を終えた時点で**同じ日にそろえて進める
  （`refresh_topic.py` の `publication_schedule_fields()`）。そろっていないと
  `tests/test_refresh_topic.py` の `test_registry_keeps_collect_and_refresh_on_the_same_date` が落ちる。
- その日のうちに公開できなかった（検査NG・承認が得られない等）ときは、集めた回を保存したまま
  `THEMES.yaml` に `pending_wave: <収集日>` が残り、予定日は進まない（期限超過として見え続ける）。
  次のセッションは新しく集めず、その回を `--resume --run-id <前回のrun-id>` で公開まで仕上げる。
  `pending_wave` があるテーマで `--resume` なしの収集を始めると `refresh_topic.py` が止める。
- 例外: 新規0件の回と、`--allow-taxonomy-mismatch`（保管だけ）の回は公開するものが無いので、
  収集の時点で予定日を進める。
- 経緯: 収集日と公開日が別々に進んでいたため、公開日が収集日より先に来て
  「公開するものが無い更新作業」が起きた（皇室典範・憲法改正、2026-09-25）。

- `collect_at` は収集・分類・更新回保存の内部期限。ページを公開できないテーマも予定どおり実行する。
- `refresh_at` は公開まで昇格できるテーマだけに設定する。
- 収集・分類は全テーマで `scripts/refresh_topic.py --topic ...` を使う。
- ページ生成だけを `scripts/refresh_adapters/` のテーマ別adapterへ委譲する。
- `--promote` または `--apply-promotion` を付けない限り、累積正典、公開HTML、`updated_at`、`refresh_at` は変更しない。
- 収集・分類・検査・公開候補の作成までは AI が自律的に行う。
- **`--apply-promotion` は、候補manifestの品質監査が `ready_for_ceo` になり、CEO承認を `company/APPROVALS.yaml` に記録した後だけ実行する。**
- `--promote` は従来手順との互換用に残す。管理画面からは使わない。
- **分類モデルは `kimi-k2.7-code`（Hermes / OpenCode Go）。** `~/.hermes/config.yaml` の
  `model.default` が全テーマ・全セッションに効く。2026-09-28、従来の `kimi-k2.6` が
  OpenCode GoからHTTP 410（廃止）を返したため、提供元の案内とオーナー承認に従って
  `kimi-k2.7-code` へ切り替えた。変更したのは `model.default` だけで、
  `provider: opencode-go` / `base_url: https://opencode.ai/zen/go/v1` /
  `api_mode: chat_completions` は維持している。直近の同一30件比較では、K2.7 Codeは
  K2.6と論点77%・賛否73%が一致し、関係有無は両方100%だった。更新回ごとの実モデルは
  必ず `report.json` の出所記録で確かめる。
- **共有モデル設定を変える前は、分類中の他セッションが無いことを確認する**
  （`pgrep -fl "classify_.*hermes|refresh_topic"`）。設定を変えた瞬間に他セッションも
  切り替わるため、分類の途中だと1回の更新の中でモデルが混ざる。利用可能な代替へ
  切り替えたときは、10件の試験分類と結果確認を済ませてから全件へ進み、この文書の
  現行モデル・設定を実態に合わせる。
- **providerを切り替えるときは `model.default` だけでなく `provider` / `base_url` /
  `api_mode` も揃える。** K2.7 Codeも現在のOpenCode Go経路で使う。`default` だけを
  別provider向けのモデルへ書き換えると、意図と違う提供元へ繋がることがある。
- **2026-09-06、`model.default` が `upstage/solar-pro4:free`（同日 08:18 更新）に
  なっているのを発見し、当時の基準だった `kimi-k2.6` へ戻した。**誰がいつ替えたかの記録は無い。
  この間に本番のデータは作っていない（直近の収集回は 2026-09-05 まで）。
  正確な識別子は `~/.hermes/config.yaml.bak.20260818_184335` から確認した。
  **モデルが黙って替わってもデータからは分からない、というのがこの一件の要点。**
  だから回ごとの記録にモデル名を残すことにした（次項）。

### 回ごとの記録に残すもの（2026-09-06〜）

`social-samples/updates/{テーマ}/{日付}/report.json` と、その公開側の
`data/verification/updates/{テーマ}/{日付}/report.json` に `provenance` が入る。
書き手は `scripts/refresh_topic.py`。

| 項目 | 中身 | なぜ要るか |
|---|---|---|
| `model` | `name` / `provider` / 設定の出所 | どの回をどのモデルで分類したか |
| `classifier.script_sha256` | 分類器スクリプトの指紋 | プロンプトを変えたのか判別する |
| `classifier.taxonomy_sha256` | ISSUES / STANCES の指紋 | 分類基準を変えたのか判別する |
| `input.raw_sha256` | 収集した生データの指紋 | 同じ入力から同じ結果が出るか後で確かめる |
| `sources` | 取得元ごとの件数 | 投稿ごとには入っていたが回の単位に無かった |

基準を変えたのか、モデルが変わったのか、世論が動いたのかを、この3つの指紋で区別する。

**新規0件の回は `model` が `null`。**分類が走っていないので、走っていない分類の
モデル名は書かない。**過去の回にはこの項目が無い。さかのぼって埋めない**
（推測値を記録に混ぜると、記録が記録でなくなる）。必須になるのは
`scripts/verify_update_provenance.py` の `REQUIRED_FROM`（2026-09-07）以降の回だけ。

**再開時の記録（2026-09-06 修正）**: 分類を始める前に作業用の
`classification-provenance.json` へ設定・分類基準・入力の指紋を保存し、完了後に結果の指紋を加える。
`--resume` で完了済み結果を使うときは、保存された記録をそのまま引き継ぐ。
当時の記録が無い結果に、現在のモデル名や分類器の指紋を代入しない。
複数の保存回をまとめる候補は `reused_waves` に回ごとの記録を残す。
元の保存回は書き換えない。記録の無い旧回を後から「確認済み」にはしない。

途中までの分類結果や未完了の記録がある場合は、別モデルが混ざるのを防ぐため停止する。
自動で結果を捨てたり、有料の再分類を始めたりしない。元の作業用ファイルを保持し、
入力と当時の設定を確認したうえで別の作業回として再分類する。
分類前後で設定・分類器・入力に差があった場合も停止する。
この前後照合だけで、実行途中に設定が変わって元へ戻ったケースまでは検出できないため、
分類中に共有設定を変更しない運用は引き続き必要。

**検査**: `python3 scripts/verify_update_provenance.py`。回ごとの4項目に加えて、
投稿ごとの必須項目（`fetched_at` / `query` / `source`）も見る。
`refresh_topic.py` 側でも収集直後に投稿ごとの必須項目を検査して、欠けていれば止める。
自転車の青切符の116件は、これが欠けたまま通ってしまったところから生まれた。
- **分類モデルをまたぐ回は「世論の潮目」の扱いをオーナーに確認する（出す／出さない／注記つきで出す）。**
  潮目は前回の収集回と今回を比べる作りだが、モデルが変わるとラベルの引き方が変わり、
  世論が動いたのかモデルが変わったのか区別できない。回ごとに判断するため既定のルールは置かない。
  2026-08-18に消費税減税の同一30件で検証したところ、`kimi-k2.6` との一致率は
  `minimax-m2.7` が論点67%・賛否67%、`kimi-k2.7-code` が論点77%・賛否73%だった
  （関係あるかの判定は両方100%）。賛否の構成比は最大4pt動き、潮目が拾う変化と同じ大きさになる。
  ズレを消したうえで出したい場合は、比較相手の回も同じモデルで分類し直す。

### Jevシャドー観測（課題91、2026-09-23〜）

JevはHermesの代替分類器ではなく、収集回を別の目で点検する**非本番の品質観測**として使う。
収集が成功した直後に、その回の新規分だけ（`.staging/refresh/{テーマ}/{run-id}/new-only.json`）を
`scripts/run_jev_shadow.py`へ渡す。累積正典全体は送らない。

- 主論点・賛否・投稿者本人の意見か・本文確認が必要かを構造化して記録する。
- 非公開結果は `social-samples/updates/{テーマ}/{日付}/jev-shadow.json` に保存する。
- 公開側の `data/verification/updates/{テーマ}/{日付}/jev-shadow.json` には、本文・URL・投稿IDを含めず、
  件数、返却モデル、トークン数、推定費用、スキーマ指紋、入力指紋だけを保存する。
- Jevの結果だけで正典、件数、山なみ、公開ページ、X投稿、世論の潮目を変更しない。収集しただけの未確認データを投稿の根拠にも使わない。
- `TYPESAFE_API_KEY`が無い場合は `skipped_no_key` を記録して収集を続ける。APIエラー時も再試行を重ねず、
  失敗を記録して通常のHermes収集・main反映へ進む。

次の異なるテーマの収集2回で、Hermesとの主論点・賛否・意見判定の一致率、本文確認対象の再現率・精度、
所要時間・費用を比較する。結果を課題91へ追記し、その後に「品質ゲートとして継続」「候補抽出だけに限定」
「停止」を判断する。

## 収集から山なみへの反映まで（2026-09-09〜）

**Kimiによる自動分類＋担当AIの再読を維持し、今回の追加・変更分は、その回で最後まで処理する。**
収集と確認を別々の未処理作業として溜めず、次の流れを1回の更新作業として扱う。
自動分類が終わっただけでは、本文確認済み・公開可能とはしない。

1. **収集・自動分類・保存** — 期限を迎えたテーマを収集し、更新回とバックアップを保存する。
   この時点では、未確認の追加分を累積正典（正式な元データ）や公開ページへ反映しない。
2. **確認対象を固定** — 課題54・63の既存の再読記録と、確認中の対象を照合する。
   既存の未読分と今回の追加・変更分を区別し、今回読む対象を確定する。
   別担当が同じテーマを確認中なら対象と結果を引き継ぎ、重複して発注しない。
   確認済みで本文・分類等に変更がない投稿は読み直さない。
3. **本文確認・独立確認** — 担当AIまたは人が対象の本文を読み、論点・賛否・意見としての採否を
   確認し、根拠を残す。別の担当が本文と根拠を照合する。
   意味を判断できない投稿は意見に採用せず、収集記録に残す。短い除外理由を記録し、
   長い説明を作るために保留を増やさない。ニュース紹介などの意見外も確認対象に含める。
4. **山なみの公開候補へ反映** — 採用するデータと再読記録を対応させ、非公開の候補を作る。
   件数・理由のまとまり・表示を更新する。原本の判定変更、正式台帳への採用、ページ生成は
   それぞれの手順に従い、読了記録を作っただけで自動的に採用・公開されたとは扱わない。
   **今回分の本文確認・採否・論点と賛否・必要な理由分類・記録への反映がすべて完了するまで、
   公開候補を確定しない。40％以内を理由とした持ち越しは禁止する。**
5. **検査・承認・公開** — データと表示の整合性、再読記録、保護機能を検査し、品質監査と
   CEOの公開承認後に反映する。課題54の新ページ初回公開は、段階11の総合監査・公開承認も必要。
   収集期限の超過を理由に、確認や公開条件を省略しない。

本文確認と記録の詳細は、下記「再読記録の共通管理」と
[課題63 段階Cの手順](quality/designs/2026-09-06-stage-c-reread-registry.md)に従う。
段階Cの差分確認は現行原本と台帳の比較であり、保存しただけの未採用更新回を自動では拾わない。
未採用の追加分も読む対象に含め、非公開の作業候補で対象と証拠を対応させる。
既存の読了記録を初期化し直したり、確認対象の検出だけのために未確認データを正式原本へ入れたりしない。

**課題54の全体完了を待たず、テーマごとに収集から確認・非公開候補作成まで進める。**
確認や公開が途中で止まる場合は、更新回を保全し、テーマの経緯ファイルに
保存場所・確認済み範囲・保留理由・次の作業を残す。`collect_at` と `refresh_at` は公開を終えた時点で
そろえて進め、未公開のまま `updated_at`・`collect_at`・`refresh_at` を進めない（上の「収集と公開は同じセッションで」）。

この節は山なみ向けの更新手順。下記の既存ページ用adapterの個別手順で
「手動再読不要」とある場合も、それを山なみの本文確認を省く根拠にはしない。

### 公開済みの山なみページを更新する（2026-09-12〜）

**`build_planet_page_preview.py`は「旧デザイン→山なみ」の1回きりの変換専用で、
既に山なみが入ったページに使うと安全装置が拒否する。** `build_bukatsu_arena.py`／
`update_bukatsu_tide.py`／`sync_issue_counts.py`は、いずれも山なみ判定
（`<!-- PLANET_SECTION_START -->`の有無）でSNS反応マップ（アリーナ）・論点別内訳の
更新を意図的にスキップする作りで、公開後の更新手段そのものが無かった（2026-09-10の
コード内コメントに「段階3で挿入先を設計する」と将来の宿題のまま残っていた。課題63の
反映作業で実際に発生し発覚）。アリーナ・論点別内訳の2区間は山なみでは`#planet-block`が
引き継いでおり恒久的に対象外だが、**「世論の潮目」（潮目カード、`update_bukatsu_tide.py`の
`tide_card()`）だけは同じ判定で丸ごとスキップされたまま2026-09-20まで残っていた**
（公開後は「立場の変化」「論点の変化」タブが一度も更新されない状態だった）。
`update_bukatsu_tide.py`のPLANET_SECTION判定分岐に、潮目カードだけを
PLANET_SECTIONの外（`<!-- PLANET_SECTION_END -->`直後）へ差し込む経路を追加して解消した。
**2026-10-06に、この潮目カードは外した。** 同じ場所（`<section class="update-dashboard">`）には「意見の推移」だけを置く
（下の「3. テーマページ」の部活動の項目）。`tide_card()` はもう無く、`update_bukatsu_tide.py` は枠だけを残す
（ファイル名の tide は名残）。

**「論点ごとのX投稿」（`x_posts_panel()`）も同じ理由で2026-09-20まで表示されていなかった。**
代表投稿の選定ロジック自体（`REPRESENTATIVE_POSTS`優先・confidence順フォールバック）は
旧2D版の`issue_panel()`にすでにあったが、`issue_panel()`ごと山なみでスキップされる
対象だったため、山なみ移行（2026-09-12）以降は呼ばれていなかった。koshitsu-tenpakaiの
「論点ごとのX投稿」（#issue-cards、2026-09-18の起承転結型再編で今の形になった）と
同じ見た目で作り直し、潮目カードと同じくPLANET_SECTIONの外へ置いた
（`<!-- BUKATSU_AUDIT_END -->`直後、無ければ`<!-- PLANET_SECTION_END -->`直後）。

本文確認が済み、正典（social-samples）を更新した後は次を使う。

```sh
python3 scripts/refresh_planet_section.py --topic bukatsu-chiiki --for-docs
```

`<!-- PLANET_SECTION_START -->`〜`END`の区間だけを最新の正典データで作り直す。
区間の外（ヘッダー・フッター・投票・SNS投稿サンプル・関連テーマ・広告枠・OGP）は
変更しない。同じ入力で2回実行しても差分が出ない。成功の形: 2回目の実行が
`OK. Lines: N → N`（差分なし）になること。

**テーマ固有の追加処理が要る場合がある。** bukatsu-chiikiでは以下3つを
`refresh_planet_section.py`内に実装済み（他テーマを山なみへ移すときは、同様の
見落としが無いか、初回変換時の`build_bukatsu()`／`build_generic()`の後処理を
必ず確認すること）。

1. **セクション本体が作らない、テーマ固有の要素差し込み。** bukatsu-chiikiは
   論点ごとの図解画像（`_inject_bukatsu_landing_images`、consumption-tax-cut等と
   同型）を`<h2>`直後とJSのdrawPanel相当の両方へ差し込んでいる。`build_section()`
   自体は作らないため、再現しないと再生成のたびに消える（課題47と同型）。
   2026-09-20までは同じ位置に「この論点のなかを見る」リンク（go-card）を
   挿入していたが、オーナー指示で画像表示へ置き換えて廃止した
   （[themes/bukatsu-chiiki.md](themes/bukatsu-chiiki.md)参照）
2. **lead文・data-methodテキスト等、論点カード構造に依存しない単純な文字列。**
   山なみ判定で`sync_issue_counts.py`／`build_bukatsu_arena.py`から素通り
   されるため、`apply_lead`/`apply_note`（`sync_issue_counts.py`）を直接呼ぶか、
   個別の正規表現で揃える
3. **生成できない旧データ（例: 旧2Dスタンスマップのsm_raw）。** 現行分類器に無い
   専用フィールドが要る等で再生成できないものは、無理に作らず
   `configs/{テーマ}-reaction-map.json`の`denominator_exceptions`へ
   理由付きで登録する（不確実な再生成より、更新しない理由を残す方を選ぶ）

反映後は`data/verification/{テーマ}.json`（仮名化検証データ）の再生成
（`scripts/verification_data.py --input <sample_file> --output <verification_file>`）と、
トップページの同期（`scripts/sync_portal_stats.py`）も忘れないこと。

`updated_at`が動く反映では、`scripts/refresh_featured_slots.py`（トップページ
「今週の注目テーマ」「いま考えたい4つの問い」の自動選定。基準は
`GROWTH.yaml`の`featured_questions.criteria`）も`sync_portal_stats.py`と
セットで実行する。同じ入力なら「変更なし」と出るだけなので、毎回実行して構わない。

### 自転車の定期回を山なみへ接続する（2026-09-12〜）

`data/bike-blue-ticket_editorial-updates/*.json` に収集回ごとの本文確認を保存し、
`build_bike_editorial_reread.py` が既存の468件の確認成果に追加する。ファイルには
`review_kind: editorial_body_reread`、`read_at`、`finalized_by` と投稿別の `items` が必要。
各項目は `tweet_id`、本文の `text_sha256`、`decision`（adopt / exclude / hold）、
`main_issue`、`stance`、既存の `bucket`、個別の `reason` とその指紋 `reason_sha256` を持つ。
各投稿にも `body_reviewed: true`、`review_kind: editorial_body_reread`、
`independently_checked: true`、`reviewer`、`read_at` が必要で、未確認項目は拒否する。
強度は山の高さにも使うので、採用分の `intensity` と確認根拠も保存する。
本文を読まずにこの記録を生成しない。原文付きの入力・Hermes出力は非公開側で保全する。

過去の保留投稿は更新回の原文と判断理由を別に保持する。2026-10-09以降の今回分は
保留を残して完了にせず、本文を判断できない投稿も意見外として候補に残す。
除外投稿は理由付きで候補に残し、意見数から外す。既存の確認成果と重複するID、
本文・論点・賛否の不一致、保留の混入、未登録区分は生成を止める。
追加記録を再読共通台帳の `create_target` / `record_reviews` と対応させ、派生資料を
再生成した後に出所の指紋を更新する。既存の読了日時は進めない。

自転車は `build_bike_arena.py` で残存する旧配列と投票件数を同期し、
`refresh_planet_section.py` で山なみ・冒頭・調査条件・横断整理の件数を同期する。
取得履歴の検証サマリも `build_bike_fetch_history_recovery.py` で再照合する。
「語られていない争点」は追加本文を確認してから母数・該当投稿・説明を更新する。
同じ入力での再生成一致と、自転車のページ・数字出所・再読・公開JSON検査を確認する。

今回の自動分類器には全件を意見扱いにする旧処理が残る。自動分類の保存回を
本文確認済みの採用データと混同しない。新規収集と確認済み候補の件数差は、
各回の結果報告に明示する。定期日の登録は時刻指定の自動起動を意味しない。

## 実行前ゲート

**作業場所**: 収集・更新は専用の git worktree で行う（`git worktree add ../isa-wt-{テーマ} -b task/{テーマ}`）。
共有ツリーを他セッションと同時に使うと、`--promote` の「未コミット差分なし」の前提が崩れる。
新しい worktree では、**先にバックアップから非公開の正典を復元し、`node_modules` を複製する**（`OPERATIONS.md` ⓪ のコマンド）。正典を復元しないと収集は走っても検査で落ちる。`node_modules` が無いと収集自体が最初の疎通確認で `Cannot find package 'playwright'` で止まる（2026-08-08 の憲法改正で発生）。どちらも gitignore 対象のため、不足していても `git status` には出ない。

**数えるのは意見だけ。** 収集件数と意見件数の両方をページに出す。

**1つの文の書き手は1つ。** ビルダと `apply_theme_trust.py` が同じ場所を書かない。

**論点の件数は `sync_issue_counts.py` から出す。** テーマページには件数が4か所（論点カード・
論点ナビ・論点セクションの見出し・アリーナのセクター）に出る。カードだけ更新して残りを放置すると、
同じ論点に新旧2つの数字が並ぶ（2026-08-09、生成AIのページで「126件」と「340件」が同時に出ていた）。
`configs/{テーマ}-reaction-map.json` の `issue_counts.sync` に `headings` / `nav` / `conclusion` /
`arena` を書くと、その4か所も同じ数字で揃う。ビルダがその場所を書くテーマ（副首都・消費税・皇室・
憲法改正・高齢者）は `sync` に入れない。ずれは `python3 -m unittest tests.test_issue_count_sync` で落ちる。
`lead`（リード文「分析対象となった意見N件をAIがK つの論点に整理しました」）と
`note`（「※ SNS投稿N件をAIが分類した結果です」）も同じ仕組みで書ける。

**ページに出る数字は、すべて正典から導けるか、理由付きで登録されていること。**
場所を列挙するのをやめ、`python3 scripts/verify_number_provenance.py` が
ページ（と同ディレクトリのJS）から `N件` と アリーナのセクター `n:N` を総当たりで拾い、
正典から導けない数字が1つでもあれば落とす。新しい表示場所が増えても、同期し忘れれば必ず落ちる。
引用・一次情報は `configs/{テーマ}-reaction-map.json` の
`number_provenance.exclude_selectors` で領域ごと外し、それ以外の例外は
`number_provenance.allow` に**値と理由をセットで**書く。理由なしでは登録できない。


本文付き正典と更新回履歴の正規保存先は、次の外付けディスク上のディレクトリとする。

`/Volumes/HD-LE-B/issue-stance-private-backups`

個人サイトとして運用するオーナー判断により暗号化は行わない。生成するtar.gz自体も暗号化されない。ディスクを共有・譲渡・廃棄するときは、保存済みアーカイブを先に削除する。

**2026-08-02: 復元確認済み。本収集を開始してよい。** Gitのクリーンクローン（非公開 `sample_file` 5本が欠落した状態）へアーカイブを展開し、①欠落0件になること ②復元した正典から再生成した検証データが `data/verification/*.json` と一致すること ③復元した正典から再生成した部活動ページが公開版と差分ゼロになること ④その環境で unittest 45件と全検査が通ることを確認した。作業ツリーに依存せず、Git＋アーカイブだけで再構成できる。物理的に別マシンへ接続する確認は未実施。

更新のたびにバックアップは自動実行される（`refresh_topic.py` が更新回確定後と昇格後の2地点で実行し、失敗時は確定しない）。ディスク未接続のまま本収集を始めると、この地点で止まる。

## staging止まりの更新

migration、manual、adapter_candidateのテーマも同じコマンドで収集・分類する。

```sh
python3 scripts/refresh_topic.py \
  --topic consumption-tax-cut \
  --date 2026-08-04 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

処理内容:

1. 先頭1検索語で疎通確認
2. 正典の `refresh_config` にある全検索語で収集
3. tweet_id → URL内status ID → URL → 本文ハッシュの順で重複判定
4. 10件の試験分類後に全件分類
5. 集合・件数・許可ラベル・エラー率を検査
6. `social-samples/updates/<topic>/<date>/` に非公開更新回を保存
7. 保存直後に非公開データをバックアップし、復元検査
8. 仮名化した更新回サマリを `data/verification/updates/` に保存
9. 成功時は `last_refresh_attempt_at` と `pending_wave` を記録する（`collect_at` は公開時に進む）

バックアップが失敗した場合は更新回を確定せず、`collect_at` も進めない。新規0件でも収集成功回として履歴を残すが、公開更新にはしない（この場合だけ収集の時点で `collect_at` と次回予定を進める）。

## 公開まで行う更新

`page_update_mode: adapter` のテーマだけ公開候補を作れる。収集が完了した同じworktreeで、まず正典と公開ページを変えずに候補を固定する。

```sh
python3 scripts/refresh_topic.py \
  --topic takaichi \
  --date 2026-08-06 \
  --run-id <収集時のrun-id> \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups \
  --resume --prepare-promotion
```

`promotion-manifest.json` に対象ファイル、SHA256、件数、調査期間、検査結果が保存される。別の読み取り専用Codexセッションで品質監査し、CEO承認後に同じmanifestを適用する。

```sh
python3 scripts/refresh_topic.py \
  --topic takaichi \
  --date 2026-08-06 \
  --run-id <収集時のrun-id> \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups \
  --resume --apply-promotion
```

適用時はmanifestと実物のハッシュが一致しなければ停止する。全検査合格時だけ累積正典・ページ・台帳・SEO・トップ・sitemapを一括昇格し、昇格後に再度バックアップする。

### 同じ日に2テーマ以上を公開する（課題59、2026-09-21〜）

**同じ日に2テーマ以上を、上記の単独テーマ版`--prepare-promotion`→`--apply-promotion`で別々に公開しない。**
`docs/index.html`・公開データcatalog・sitemap等は全テーマ共有のファイルで、`--prepare-promotion`は
その時点のTHEMES.yaml全体を読み直して作り直す。2テーマを個別に候補化すると、後から適用した側の
共有ファイルには先に適用した側の新しいデータが入っておらず、**適用した瞬間に先に公開した分の
合計数が古い値へ巻き戻る。**

同じ日に2テーマ以上を公開するときは、各テーマを`--resume`まで進めてから
（**単独テーマ版の`--prepare-promotion`は実行しない**。実行すると単独テーマ版のmanifestが
できてしまい、下記の統合の対象にならない）、`scripts/promote_multi_topics.py`で1つの
公開候補へまとめる。

```sh
# 各テーマを --resume まで進める（--prepare-promotion は使わない）
python3 scripts/refresh_topic.py --topic bike-blue-ticket --date 2026-09-21 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --resume
python3 scripts/refresh_topic.py --topic consumption-tax-cut --date 2026-09-21 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --resume

# 2テーマぶんの候補を1つのmanifestへまとめる（正典・公開ページはまだ変更しない）
python3 scripts/promote_multi_topics.py --date 2026-09-21 \
  --entry bike-blue-ticket:.staging/refresh/bike-blue-ticket/<run-id> \
  --entry consumption-tax-cut:.staging/refresh/consumption-tax-cut/<run-id> \
  --combined-stage .staging/refresh/multi/<run-id> \
  --prepare
```

品質監査・CEO承認は単独テーマ版と同じ扱い（できた`promotion-manifest.json`を確認する）。
承認後、`--prepare`のときと同じ`--entry`・`--combined-stage`・`--date`を指定して`--apply`する。

```sh
python3 scripts/promote_multi_topics.py --date 2026-09-21 \
  --entry bike-blue-ticket:.staging/refresh/bike-blue-ticket/<run-id> \
  --entry consumption-tax-cut:.staging/refresh/consumption-tax-cut/<run-id> \
  --combined-stage .staging/refresh/multi/<run-id> \
  --apply --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

`--prepare`で束ねた全テーマ・run-idが、`--apply`側の指定と完全に一致しないと拒否される
（一部だけ適用する、束ねていないテーマを混ぜる等の混在適用を防ぐ）。

**1テーマだけを同日に公開するなら、従来どおり単独テーマ版の`--prepare-promotion`/`--apply-promotion`でよい。**
このコマンドが要るのは「同じ日に2テーマ以上」の場合だけ。

実装の経緯・残作業は[課題59](tasks/task-59.md)、コードは`scripts/refresh_topic.py`の
`prepare_public_candidate_bundle_multi`等・`scripts/promote_multi_topics.py`。
テストは`tests/test_refresh_topic.py`の`MultiTopicPromotionTests`（合成データ）。
**実データでまだ使ったことはない**ため、初めて使うときは`--prepare`後の
`promotion-manifest.json`の中身（テーマ・run-id・ファイル件数）を目視確認してから
品質監査へ進めること。

### 学校あだ名は公開承認以外を自動化（人が読む工程なし）

**2026-10-13 から新デザインで公開する間は、新しい意見の追い読み（人が読む工程）が1つ要る**（下の「学校でのあだ名禁止の定期更新（新デザインを維持する）」の節）。
この節の内容は、元HTML（`data/page-sources/school-nickname-ban.html`）を作り直す旧形式の部分についての説明として残す。

`school-nickname-ban` の adapter は正典だけを読んで、件数を出している場所を毎回
すべて作り直す（リード文・調査条件・注目ポイント4枚・論点カードの内訳文・投票の件数・
論点ナビ・論点ブロック6つ・詳細データ表・アリーナの点）。代表投稿も
`article_usable` かつ `risk: low` から自動で選ぶ。内容の手動再読は不要だが、
`--promote` 前の CEO 承認は他テーマと同じく必要。

`docs/school-nickname-ban-arena-data.js` も公開対象に入っている。ページだけ差し替えると、
数字は新しいのにアリーナの点だけ古い状態になる。

**`scripts/upgrade_nickname_arena.js` を流さないこと。** 一度きりの移行用で、
`archive/scripts/` へ移した。流すと空行が1行増え、SEO meta が374件時代へ戻る。

### 自転車青切符だけ、人が読む工程が1つ残っている

`bike-blue-ticket` の adapter は、**新しい「反対」投稿が再読マッピングに入っていなければ
意図的に失敗する**。ページの中心的な主張「反対はひとつの塊ではない」は、編集部が反対投稿を
1件ずつ読んで5区分へ割り当てた結果に載っているためで、ここだけは機械で埋められない。
（本文のキーワード抽出を件数にすると3〜4割多く出ることを実測済み。）

失敗すると、未再読の tweet_id と本文の冒頭が並んで出る。次の手順で進める。

1. 出た tweet_id の投稿を読む
2. `data/bike-blue-ticket_opposition_reread.json` の `buckets` の該当区分へ tweet_id を足す
   （区分: `strict` 青切符では足りない／`scope` 対象と順番に異議／`place` 走る場所がない／
   `distrust` 警察の運用への不信／`abolish` 制度そのものに反対）
3. `--promote` を実行し直す

事実確認7主張の該当投稿（`data/bike-blue-ticket_claim_posts.json`）も人が確定したもので、
こちらは件数が合わなくても止まらない。新しい収集回を公開するときは併せて見直すこと。

**取得期間も人が直す。** `bike-blue-ticket` と `ai-copyright` は
`sample_period_source: owner_confirmed` で、`--promote` では `sample_period` が伸びない。
直し忘れると、ページの取得期間が前回の収集日のまま公開される（2026-08-17 に発生）。
`verify_sample_periods.py` が「期間の終わり ≠ `updated_at`」で止めるので、
公開前に `THEMES.yaml` の `sample_period` を今回の収集日まで伸ばしておくこと。

**言い回しの使い回しも検査する。** 新しいセクションを別テーマへ広げるとき、先行事例の
見出しや書き出しがそのまま複製されやすい（2026-08-18 に自転車→高齢者で発生）。
`python3 scripts/verify_page_originality.py` が、ページ間で同じ文・似すぎた見出しを見つけて
止める。共通で当たり前の文は `configs/page-originality.json` に理由つきで登録すること。

## note 記事の更新要否チェック（公開後）

`--promote` による昇格が完了したら、論点に変化があるか確認し、必要なら note 記事とサイトを同時に更新する。

**確認方法：**
- 今回の主要論点の件数・割合を、前回公開時の `data/verification/<topic>.json` と比較する
- 新しい論点が浮上したか、既存論点の比率が ±5pt 以上変化したか

**変化なし → スキップ。** note は更新しない。

**変化あり → 以下を同タイミングで準備する：**
1. note 記事の「前回からの変化」セクションを追記した更新案を Artifact（HTML）で出力する
2. サイトの論点説明文（ビルダが生成している箇所）も同じ変化に合わせて更新する
3. note の更新案は Website の公開承認と別に CEO へ提出し、承認を `company/APPROVALS.yaml` に記録してから投稿する

更新ルールの詳細は `note-operation` スキルを参照。

---

## コミット対象

収集した回は、次を必ずコミットする。**`data/verification/updates/` を忘れやすい。**

| パス | 内容 | staging止まり | `--promote` |
|---|---|---|---|
| `data/verification/updates/<topic>/<date>/` | 仮名化した更新回サマリ（raw / classified / report） | ✅ | ✅ |
| `data/verification/<topic>.json` | 仮名化した累積サマリ | — | ✅ |
| `THEMES.yaml` | 期限・件数・取得期間 | ✅ | ✅ |
| `DATA_SHEET.md` | データ台帳（`scripts/build_data_sheet.py` で再生成） | ✅ | ✅ |
| `configs/theme-seo.json` / `docs/` 配下 | ページ・SEO・sitemap | — | ✅ |
| `social-samples/` 配下 | 本文付きの正典・更新回 | ❌ gitignore | ❌ gitignore |

`data/verification/updates/` は gitignore されていない**Git管理対象**で、収集の履歴を
本文なしで残す唯一の場所。**作業ツリーを消すと失われる。**
2026-08-08 の憲法改正で、発注書のコミット対象リストから漏れて未追跡のまま残った。

確認コマンド（作業ツリーを消す前に実行する）:

```sh
git status --short data/verification/
```

成功の形: 何も出ない。`??` で更新回のディレクトリが出たらコミットしていない。

## 溜まった更新回をまとめて公開する

公開できない期間に収集だけが進むと、未公開の更新回が溜まる。1回ずつ公開しようとすると
**途中の状態が「collect_at 期限超過」で必ず落ちる**ため、最後の回に畳み込む。

```sh
python3 scripts/refresh_topic.py \
  --topic consumption-tax-cut \
  --date 2026-08-17 \
  --include-wave 2026-08-03 --include-wave 2026-08-10 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups \
  --resume --promote
```

`--resume` は再収集しない。保管済みの更新回はそのまま残し、公開候補だけを現在の正典に対して
重複判定し直す。`--date` に指定した回の次回予定日が `collect_at` になる。

`--resume` を使うときは、保管済みの更新回から作業場を組み直しておく（`--include-wave` を
使う場合は、指定した全回の raw を1つに結合したものを置く）。

```sh
mkdir -p .staging/refresh/<topic>/<run-id>
# raw.json  … 対象の全回の raw.json を結合したもの
# new-only.json … 空の [] でよい（保管済みclassifiedから組み直される）
```

## 周期

- 既定14日
- 新規意見50件以上なら次回だけ7日
- 新規意見20件未満が2回連続なら28日
- 新規0件が2回連続なら `collect_mode: event-driven` に切り替え、`collect_at` を空欄にする
- 収集失敗時は期限を進めず、`verify_top_page.py` の期限超過NGを残す

## ページadapter整備時の追加条件

課題29の暫定的な論点件数ソースも同時に解消する。

- bike-blue-ticket: `social-samples/bike_arena_hermes_classified.json` 依存
- constitutional-amendment: `data/issue-counts/constitutional-amendment.json` 依存
- elderly-license-revocation: `data/issue-counts/elderly-license-revocation.json` 依存
- henoko-student-accident: `data/issue-counts/henoko-student-accident.json` 依存

累積正典またはGit管理する仮名化検証データから論点件数を再現できる状態をadapter昇格条件とする。

---

## 更新後の画面チェックリスト

collect_at を迎えたテーマにデータを追加した後、以下を順番に確認する。
手動更新テーマで使う（adapter テーマは生成スクリプトが埋めるので、生成後の差分確認だけでよい）。
2026-08-23 に `LOOP.md` の廃止にともないこちらへ移設した。

### 1. データ分類

- [ ] Yahoo リアルタイム検索で収集（fetch_yahoo_realtime_node.mjs / fetch_topic_refresh.py）
- [ ] 重複チェック（既存 tweet_id と照合、件数を記録）
- [ ] Hermes 分類実行（classify_{theme}_arena_hermes.py）
- [ ] 新規分類データを既存 `{theme}_hermes_arena_classified.json` にマージ

### 2. THEMES.yaml

- [ ] `updated_at` → 今日の日付
- [ ] `collect_delta` → 今回追加件数（重複除外後）
- [ ] `collect_at` と `refresh_at` → 次回の収集・公開予定日（同じ日にそろえる。既定14日、今回の新規意見が50件以上なら次回だけ7日）
- [ ] `pending_wave` → 公開を終えたら行ごと消す

**経緯は `THEMES.yaml` に書かない。** ここは毎セッション読まれる登録簿で、
書き足した分だけ実際の作業に使える余力が減る（課題60）。

### 2-2. themes/{テーマ名}.md（そのテーマの経緯）

- [ ] 今回の収集件数・重複除外件数・分類モデル・数字が変わった理由を追記
- [ ] `python3 scripts/verify_themes_yaml.py` が通る

### 3. テーマページ（潮目ウィジェットがある場合）

- [ ] `tide-widget-period` テキスト（例: 6月27日 → 7月26日）
- [ ] SVG `tide-slope-date` テキスト（前回/今回の日付）
- [ ] `aria-desc` 内の件数
- [ ] `datasets` JS変数（`max`・`headline`・`rows` の `previous`/`current` 値）
- [ ] `tide-widget-note` 注釈テキスト（収集件数・日付・背景説明）
- [ ] 消費税減税だけ: **潮目カードは出さない**（2026-10-05に外した。上の `tide-` の項目は他のテーマ向け）。前回との比較は、
  次の「意見の推移」の冒頭の1行とグラフの帯が見せる。`consumption-tax-cut-tide-widget` が戻ると数字検査が止める
- [ ] 消費税減税だけ: 外枠（`<section class="update-dashboard">`）の中の「意見の推移」（`#consumption-tax-cut-trend`、立場・論点・理由の3タブ）。
  手では直さない。`adapter.build` が、昇格前の累積候補（`cumulative-candidate.json`）から貼り直す。
  枠は、ページ生成器（`build_consumption_tax_page.py`）が `<!-- TREND_CARD_END --></section>` を目印に、外して差し戻す
  （`scripts/build_trend_section.py`）。新しい回は表に1行、グラフに1点増え、「○年○月○日時点」も最新の収集日になる
  - 各タブの見出し（H2）の末尾と右上のバッジの「○年○月○日時点」も、同じ呼び出しで最新の収集日になる（手では直さない）
  - グラフの縦線と「同じ期間にあった出来事」は、ページの年表（`configs/consumption-tax-background.json` の `timeline`）から作る。
    年表に出来事を足したら、次の更新で自動で入る。急ぐときは `python3 scripts/build_trend_section.py --topic consumption-tax-cut --apply`。
    2026-10-13 の新デザイン公開後は、公開ページへの `--apply` は止まる。`--page data/page-sources/consumption-tax-cut.html` で元HTMLに貼ってから
    `python3 scripts/build_consumption_tax_page.py`（下の「消費税減税の定期更新（新デザインを維持する）」の節）で公開ページを作り直す。
    日付は「2026年9月15日」の形で書く（月までしか書けない行は、グラフに出せず数字検査が止める）。
    直前・直後の回の比較は事実だけを書き、原因は書かない。出来事の一次資料リンクは年表の `links` を使う
  - 「反対・慎重の理由」タブ（立場が「減税反対・慎重」の投稿の論点別の内訳）も、同じ呼び出しで貼り直される。
    数字検査が正典から数え直して照合する。注目する立場を変えるときは `TREND_THEMES.focus_stance` と
    `consumption_tax_count_provenance._FOCUS_STANCE` の両方を直す
  - 単体で配る画像（`docs/images/trend/consumption-tax-cut-{stance,issue}-trend-{summary,detail}.png`。ページの「このグラフを画像で使う」から
    ダウンロード・埋め込みできる）も、同じ呼び出し（`adapter.build`）が作って公開物に加える（`scripts/build_trend_images.py`）。
    画像は貼る場所で使い分ける2種類。**ひと目版（summary）**は、Xのタイムラインや記事の本文幅（幅300〜600px）に縮めても読めるよう、
    見出し1つ・線2本（最初と最新で差が大きい2項目）・大きな数字に絞る。見出しは、ぶれの範囲を超えた動きだけを「上がった・下がった」と
    言い切る（`build_trend_section.glance_lines`）。**詳細版（detail）**は全項目と各回の動きを入れた、資料・数字の確認向け。
    日本語フォント（macOS のヒラギノ角ゴシック）が無い環境では作れず、そこで止まる。見出しが画像の幅に収まらないときも、切れた画像を出さず止まる
    （項目名を長くしたら `HEADLINE_MIN_SIZE` と見出しの文型を見直す）。
    公開向け検査（`scripts/verify_trend_images.py`）が、4枚それぞれのPNGに入れた数字の指紋・種類・最新の収集日を、ページの数字と照合する。
    割合だけでなく、実際の投稿数（件数）も出す。ページは表の各セルの割合の下、ツールチップ、グラフ右端の最新値に、画像は最初と最新の点（ひと目版）・右端の最新値と各回の意見の合計（詳細版）に出す。
    件数は埋め込みデータ（`rounds` の `c`）に入れ、数字検査（`consumption_tax_count_provenance`）が正典から数え直して、表のセルと埋め込みデータの両方を照合する
    手で作り直すときは `python3 scripts/build_trend_images.py --topic consumption-tax-cut --apply`
    推移の冒頭の「前回（○月○日）から今回（○月○日）にかけて、…」の1行（`previous_sentence`。いちばん大きく動いた項目と、ぶれの範囲の判定つき）と、
    グラフの「前回→今回」の帯は、潮目が見せていた内容を取り込んだもの。更新のたびに自動で変わり、数字検査が正典から数え直して照合する。
    グラフには「変化を再生」（左から右へ線が伸びる動き）がある。動きを減らす設定の端末では動かさず、完成した状態で出す
    「このグラフを画像で使う」は開いたまま出す（畳まない）。中の「Xで投稿する」は、見出しの文（`glance_lines`）から作った下書きと、
    UTM付きのページURL（campaign=`trend_share`。サイト共通の `window.buildShareUrl` / `trackShareClick` を通す）で投稿画面を開く。
    Xの仕様で画像は自動では付けられないので、画像を保存して添付してもらう
    利用条件の文言（`build_trend_section.EMBED_TERMS`）は2026-10-05にオーナーが承認済み（approval-20261005-002）。文言を変えるときは再度承認が要る
  - 累積候補を渡さない呼び方（部分更新・テスト）でも、正典（`THEMES.yaml` の `sample_file`）から作る。
    正典も無い隔離環境では、既存の節をそのまま残す（黙って消さない）
  - `python3 scripts/verify_number_provenance.py consumption-tax-cut` が、表の各行を正典から独立に数え直して照合する。
    貼り直しが漏れて古い回のまま残る、または節が消えると、ここで止まる
  - 収集日は `fetched_at`（UTC）を日本時間に直した日付。同じ日本時間の日に2回収集すると1回分にまとまる
  - 論点・立場のラベルや並びを変えるとき（`taxonomy-migration`）は、`inject_tide_widget.py` の同じ定義が元になるので、
    `scripts/build_trend_section.py` の `TREND_THEMES.short_labels`（スマホの表の短い見出し）も合わせて直す

- [ ] 部活動の地域移行だけ: **潮目カードは出さない**（2026-10-06に外した。`bukatsu-tide-widget` が戻ると数字検査が止める）。
  外枠（`<section class="update-dashboard">`）の中の「意見の推移」（`#bukatsu-chiiki-trend`、立場・論点の2タブ。理由タブと年表の縦線は無い）と、
  単体で配る画像（`docs/images/trend/bukatsu-chiiki-{stance,issue}-trend-{summary,detail}.png`）は、上の消費税減税の項目と同じ仕組みで、
  `adapter.build` が累積候補から貼り直す（枠は `update_bukatsu_tide.py` が `<!-- TREND_CARD_START -->` を目印に残す）。
  数字検査は `scripts/trend_count_provenance.py`（消費税減税と共通）が、表の各行・埋め込みデータ・前回比の1行を正典から数え直して照合する。違いは次の3つ。
  - **並べ始める日**（`TREND_THEMES["bukatsu-chiiki"]["series_from"]`）。集計のしかたが変わる前の回は並べない。
    論点は **2026-07-23**（この回から収集の検索語を7本から10本に増やした。検索語の違いは数え直せない）。理由は、グラフの注意書きにも出る（`series_notes`）。
    立場は並べ始める日が無く、全回を並べる。2026-09-12に賛否の判定基準を見直した（コミット`e81f86b5`）が、見直し前の回の賛否は
    **2026-10-06に新しい基準で判定し直した**（`scripts/rejudge_bukatsu_stance.py`。判定し直す前は「中立・情報」が約3%から約3割へ跳ねる見かけの動きが出ていた）。
    **判定し直したのは賛否（stance）だけ**で、関連・意見か・論点は変えていない。記録は `data/verification/rejudge/bukatsu-chiiki-stance-20261006.json`（件数と指紋だけ）
  - **分類の指示文（`classify_bukatsu_arena_hermes.py` の `prompt_for`）の判定基準を変えたら、既存の回も同じ指示文で判定し直す。**
    判定し直さないと、正典の中で回ごとに物差しが違い、推移のグラフに存在しない動きが出る。手順は `rejudge_bukatsu_stance.py` の冒頭（prepare → run → merge → report → apply → record）。
    1,000件規模で約1時間（4並列）。分類中は共有設定（`~/.hermes/config.yaml` のモデル）を変えない。賛否が動くと、ページ全体の立場の集計・
    編集部の横断整理（`data/verification/bukatsu-chiiki-editorial.json`。数字が動いて成り立たなくなった文は書き直す）・保存回台帳（`build_adoption_registry.py`）も作り直す
  - **分類に使うAIが変わったら止まる**（`trend_support.check_model_break`）。`adapter.build` が前回と今回の `report.json`（`provenance.model.name`）を比べ、
    変わっていて `TREND_THEMES["bukatsu-chiiki"]["model_breaks"]` の**立場・論点の両方**に今回の収集日が無いと止まる。日付を足すと、グラフの注意書きに
    「この回からAIを切り替えました。それ以前の回との差には、AIの違いも含まれます」が出る。2026-10-01の切替は、論点だけに記録してある
    （立場は、それより前の回を同じAIで判定し直したため、切替の影響を受けない）
  - 論点の「その他」は割合から外す。立場・論点の並びは `scripts/bukatsu_taxonomy.py`（`inject_tide_widget.THEMES` には無いテーマ）。
    ラベルを変えるときは `TREND_THEMES.short_labels` も合わせて直す
  - **新デザイン**: 2026-10-14 から最新の型（`configs/bukatsu-layout.json` の `version: "redesign-v2"`、`scripts/build_bukatsu_redesign_v2.py`）。
    更新時に確かめることは、下の「部活動の地域移行の定期更新（新デザインを維持する、最新の型）」の節。初期型（`build_bukatsu_redesign.py`、
    planet.js・planet.css）は `version` を外したときだけ使う

- [ ] 生成AIと著作権だけ: **潮目カードは出さない**（2026-10-08に外した。`ai-copyright-tide-widget` が戻ると数字検査が止める）。
  外枠（`<section class="update-dashboard">`）の中の「意見の推移」（立場・論点の2タブ。理由タブと年表の縦線は無い）と、
  単体で配る画像（`docs/images/trend/ai-copyright-{stance,issue}-trend-{summary,detail}.png`）は、消費税減税・部活動と同じ仕組みで、
  `scripts/refresh_adapters/ai_copyright.py` の `adapter.build` が累積候補から貼り直す。`inject_tide_widget.py` は、このテーマを注入の対象外にしてある
  （`prev_file`・`cur_file` を空にした。課題38）。数字検査は `scripts/trend_count_provenance.py`（共通）。違いは次のとおり。
  - **立場は3つ**（規制・制限強化支持／推進・活用支持／中立・情報）、論点は「その他」を除く6つ。並びは `scripts/ai_copyright_taxonomy.py`（ページ・投票と同じ単一ソース）。
    潮目の定義（`inject_tide_widget.THEMES`）は立場が2つだけでページの内訳と合わないので使わない。
    色は `TREND_THEMES["ai-copyright"]["palette"]`（規制＝赤、推進＝緑、中立＝灰）。論点名が長いので、ひと目版の見出しの文だけ `headline_labels` で短くする
    （2項目が並ぶ文が画像の幅に収まらなくなるのを、`tests/test_trend_images.py` が検出する）
  - **並べ始める日は2026-08-03**（`series_from`。7/26までの回は分類のしかたが今と違う）。
  - **2026-09-05の回だけ、2026-10-07に現行のAI（`kimi-k2.7-code`）で判定し直した。** この回だけ分類の傾向が他の回と違った
    （関連あり92.8%・中立・情報35.1%・要約が約2倍の長さ。指示文は変わっていないので、分類したAIが違った疑い）。
    手順は `scripts/rejudge_ai_copyright_wave.py`（検証 → 退避 → 置き換え → 再読の記録から、意見でなくなった／論点が変わった投稿を外す → 記録）。
    置き換えたのは**関連・意見か・論点・立場のすべて**（部活動の数え直しは賛否だけだった。この回のずれの正体は「意見とみなす幅」で、賛否だけでは直らない）。
    再読の記録は読み直さず、外すだけにした（外した分は未読として数える）。ほかの回は判定し直していない。
    置き換えると、ページ全体の件数・論点別・立場別・山なみ・「語られていない争点」の母数・保存回台帳が動く。**通常の更新と同じ作り直しの順序**
    （検証データ → 公開JSON → `adapter.build` → `adapter.finalize` → 付随する公開物）で行い、正典を先に直したときは**公開JSONを先に作る**
    （ページ生成は、正典と公開JSONの件数が一致していることを前提にする）
  - **分類に使うAIが変わったら止まる**（`trend_support.check_model_break`）。`TREND_THEMES["ai-copyright"]["model_breaks"]` の立場・論点の両方に今回の収集日が必要。
    2026-09-29の切替（`kimi-k2.6` → `kimi-k2.7-code`）は記録済み
  - **代表投稿の注意（2026-10-08に発覚）**: ページに固定で載せる代表投稿（`scripts/ai_copyright_issue_media.py` の `MEDIA`、14件）は、
    **判定を直す作業をすると、別の論点・意見でない投稿になることがある**（9/5の判定し直しで6件がずれた。数字の検査では検出されない）。
    差し替えたら `python3 scripts/ai_copyright_issue_media.py --write-html` でページの「論点ごとのX投稿」を書き直し、**連動表示（各論点の詳細パネルの
    「実際の投稿を読む」。これは前者を組み立て時に写す）も `adapter.build` で作り直す**。`tests/test_ai_copyright_issue_media.py` が、
    載せた投稿がいまの正典でも載せている論点の意見であること、詳細パネルとの一致を検査する（非公開の正典が要る分は、無い環境では飛ばす）
  - **未読割合（編集再読）の上限に注意。** 生成AIと著作権は、AI生成物の権利・創作性が32.9%（警告30%超）で、約2回の収集で上限40%に達する見込み
    （2026-10-07時点）。このルール自体の見直しは `configs/prompts/claude-code/20261007_review-unread-rule.md`（別セッションへの依頼文）

### 4. テーマページ（insight-stats カード 4枚）

- [ ] 「分析対象の意見」件数（`insight-value`）
- [ ] 「最も多い立場」% + 件数注（`insight-note`）+ `insight-meter` 幅
- [ ] 「最も話された論点」件数（`insight-value`）
- [ ] 「論点による逆転」注釈（件数が変わる場合）
- [ ] ヒーローセクション「議論の中心」バッジ件数（`conclusion-count`）
- [ ] lead文の件数
- [ ] `data-method` テキスト（データの集め方）

### 5. index.html（トップページ）

トップページは手で直さない。`configs/top-page.json`（手書き文言）と正典から `scripts/build_top_page.py` が生成する（2026-10-15、課題106）。

- [ ] `python3 scripts/build_top_page.py` を実行する（件数・更新日・注目枠・「いまの段階」を正典から埋め直す）
- [ ] `updated_at` が動いた回は `python3 scripts/refresh_featured_slots.py` も実行する（GROWTH.yaml の featured を同期。index.html は変わらない）
- [ ] `python3 scripts/build_top_page.py --check` と `python3 scripts/verify_top_page.py` が exit 0
- [ ] 文言を変えるときは `configs/top-page.json` を直して再生成し、`python3 scripts/review_with_yomiyasu.py docs/index.html --medium website --strict` を通す
- [ ] 法律の施行・成立・報告書の公表があったら、各テーマの `configs/{テーマ}-opening.json` の日付（`enforcement_confirmed_on` など）を直してから再生成する。「いまの段階」の文はそこから計算している
- [ ] 検索需要が変わったら `entries` の並び順を入れ替える（根拠は UIデザイン調査フォルダー61 の取り方で取り直す）

### 6. sitemap.xml

- [ ] 該当テーマの `lastmod` → 今日の日付
- [ ] `python3 scripts/seo/validate_theme_seo.py` が exit 0（ここを飛ばすとpush後のCI「公開ファイルの検査」で初めて発覚する。2026-09-15のbukatsu-chiiki更新で実際に発生）

### 7. 論点カードの件数

- [ ] `python3 scripts/sync_issue_counts.py {theme}` を実行（件数は分類結果から生成する。HTMLに直接書かない）
- [ ] 論点のラベルが変わった場合は `configs/{theme}-reaction-map.json` の `issue_counts.cards` を先に直す
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] 公開本文を変更した場合は `python3 scripts/review_with_yomiyasu.py docs/{theme}-reaction-map.html --medium website --strict` が exit 0
- [ ] `data/issue-counts/` を source にしているテーマ（constitutional-amendment / elderly-license-revocation / henoko-student-accident / koshitsu-tenpakai）は、再分類したら `issue_counts.source` を `sample_file` へ戻す（課題29。2026-08-08に完了し `archive/tasks/task-29.md` へ移した）

---

**注意事項:**
- `hero-total-samples` は全 topic-card の「投稿 XX件」の合計値。新テーマ公開直後に更新漏れが起きやすいので都度合算して確認する。
- 割れ度スコアを変更するとランキング順位も変わる。DOM 順序（first-child が金色）も連動して並び替えること。
- 論点アリーナ（P=[...] データ）は今回の分類結果を反映していないが、潮目ウィジェット（消費税減税は推移）で最新比較を表示しているため、現状はそのままでよい。

---

## 再読記録の共通管理（課題63 段階C）

部活動・自転車・高齢者の既存再読は `data/verification/reread/` に継承した。
読了時の証拠と移行時の本文指紋を区別し、追加・本文・論点・意見判定の変化を確認する。
日常の差分確認・対象固定・新しい読了結果の登録は
[段階Cの手順](quality/designs/2026-09-06-stage-c-reread-registry.md) に従う。
既存の再読成果を再発注せず、本文を読まずに読了記録を作らない。

## 保存回の採用状態を照合する（課題63 段階D）

保存回・正典・判断根拠を更新したら、同じ作業ツリーで `python3 scripts/build_adoption_registry.py` を実行し、保存回の投稿が正典に存在するかを記録する。成功時はテーマ別件数が表示される。追加・削除・分類は行わない。`python3 scripts/build_adoption_registry.py --check` がOKなら、非公開入力を含む現在の再生成結果と一致する。

公開自動検査には `verify_adoption_registry.py` を接続。本文なし台帳の集計・根拠・公開ファイルの指紋に差があれば停止する。公開JSON全体の原本との照合は従来どおり `verify_public_registry.py --against-private` で行う。外付け証拠の指定方法・状態の意味・初回移行の制約は [段階Dの運用](quality/designs/2026-09-06-stage-d-adoption-registry.md) を参照。正典外を自動採用しない。

## 更新後の保全と復元記録（課題63 段階E）

原本・段階C/Dの台帳を更新したら、原本バックアップ、採否根拠のバックアップ、資産台帳の再生成を行い、本文なしの成功記録を同じブランチへ保存する。バックアップの失敗時に前回の成功日を進めない。[実行手順と成功の形](quality/designs/2026-09-06-stage-e-data-preservation.md)。新しい作業環境からの再生成は `verify_data_asset_restore.py` で試せる。物理的な別マシン試験は課題33/50に残す。

## 編集再読の未読上限と、確認する対象（2026-10-09訂正）

`independence_gate()`（`scripts/build_planet_data.py`）は、再読記録のある論点の全体件数が
意見全体の50%以上か、各再読論点の「読み飛ばし＋読了後に増えた分」が4割以内かを検査する。
前者は論点の件数による範囲の確認で、全意見の50%を実際に読んだことを意味しない。
取得日時・再読境界が不明な未読や、未解決の分類確認候補がある場合も止まる。

**未読4割の上限は、収集が続いていても止まっていても同じ。** たとえば論点内100件のうち
60件を確認済みなら、残り40件がすべて読み飛ばしでも、すべて読了後の追加でも、
この未読割合の条件は満たす。59件の確認では未読41件となり、満たさない。
以前の「収集が止まると増分の枠を使えず、ほぼ全件読む必要がある」という説明は誤りだった。
読み飛ばしと増分は同じ上限で合算されるため、内訳が変わっても必要割合は変わらない。

**4割は未処理量の上限であり、正確さの保証でも、今回の追加分を4割まで飛ばしてよいという
許可でもない。** 各更新では上記「収集と公開は同じセッションで」に従い、追加・変更分の
本文確認を行う。確認済みで本文・分類等が変わっていない投稿は読み直さず、既存の未読と
追加・変更分を区別して対象を決める。**4割の検査は過去から残る理由分類・記録の不足を
監視するために残す。今回分の未完了は0件が条件であり、別の完了検査で止める。**
この変更だけで過去の残件が解消したことにはせず、過去の分類・集計・推移グラフは変更しない。

### 今回分の完了確認（2026-10-09〜）

「本文確認が未完了」と「本文確認済みだが理由分類・記録への反映が未完了」を分けて報告する。
独自性検査の旧 `unread_count` は後者も含むため、その数だけを「本文を読んでいない件数」と
説明しない。本文確認済みであれば、その結果を使って必要な理由分類と記録を完成させる。

`scripts/refresh_completion.py` が、正式原本と公開候補の差分、および今回の `new-only.json`
全件を照合する。採用・意見外の両方に、既存の再読共通台帳と同じ形式の verified な読了証拠を
要求する。候補の指紋に賛否を含む分類全体を結び付け、確認後の分類変更も検出する。
理由分類を設定している論点の意見は、公開生成器が使う投稿別の理由記録、または本文指紋と
短い理由を持つ理由分類対象外の記録に接続する。理由分類を設定していない論点に新設は求めない。

1. 最終判断を反映した非公開の `cumulative-candidate.json` を用意する。収集済み投稿を削除せず、
   判断できないものも `is_opinion: false` で残す。Kimiの出力だけを読了証拠にしない。
2. `python3 scripts/refresh_completion.py prepare --topic <テーマ> --stage <作業ディレクトリ>`
   で `editorial-completion.json` の未確認ひな形を作る。これは読了の自動登録ではない。
3. 本文確認後、各 `records[].review` に共通台帳の verified review 形式で読了証拠を記録する
   （項目は `scripts/reread_registry.py` の `REVIEW_FIELDS`）。出所は `data/verification/` または
   `quality/reviews/` に保存し、本文を含めない。既存の読了証拠を参照できる場合は再利用する。
   共通台帳があるテーマはそちらも整合させる。全履歴の台帳移行を今回分の完了条件にはしない。
4. `python3 scripts/refresh_completion.py check --topic <テーマ> --stage <作業ディレクトリ>`
   を実行する。`OK: 今回分の本文確認・採否・必要な理由分類の記録が揃っています` が成功の形。
   理由記録をまだ候補ファイルにだけ置いている場合は、adapterの対象ファイルに含めて
   `--prepare-promotion` で照合する。
5. 単独・複数テーマの公開候補作成時と適用直前にも同じ検査を行い、完了記録を
   `data/verification/refresh-completion/<テーマ>/<run-id>.json` として公開候補に含めて保存する。
   完了記録や出所が変わった場合は候補を再確認する。未完了を残して収集回の完了報告をしない。

担当AIは完了報告に、今回の収集数・意見採用数・意見外数・本文確認未完了数・必要な理由分類の
未完了数を並べる。今回分の未完了が残る場合は作業を続け、作業不能なら未完了として理由を報告する。

訂正の根拠と分類方法の比較結果は
[2026-10-09の検証記録](quality/reviews/2026-10-09-classification-workflow-decision.md)を参照。

## 共有コードを直したら、全テーマへの反映を確認する（2026-09-13〜）

`build_planet_data.py` / `build_planet_page_preview.py` など、複数テーマが使う
共通の生成器・テンプレートのバグを直したとき、**直した瞬間に効くのは次にそのテーマを
再生成したときだけ**で、既に公開済みの他テーマのページには自動で反映されない。

2026-09-13、副首都の作業中に見つけた共通CSSバグ2件・注意書きの文言バグ1件は、
いずれも「1テーマだけ直して終わり」にせず、**公開済みの全テーマの`docs/*.html`を
`grep`で確認**して初めて、他4〜5テーマが同じバグを本番で公開していたと判明した
（部活動・高齢者・自転車・あだ名禁止の4テーマ、[記録](tasks/task-54.md)）。

**共有コードを修正したら**:
1. 何を直したか（対象の文字列・関数）を明確にする
2. `grep`で、公開済みの**全テーマの`docs/*.html`**にその不具合が残っていないか確認する
   （生成器を直しただけでは、既に生成済みのページには反映されない）
3. 残っていたら、生成器の出力と一致する文言で該当ページを直接修正する
   （該当テーマの定例更新スクリプトがその箇所を再生成しない場合が多いため）
4. 標準4検査を全テーマに対して実行してから確定する

## 他セッション（他AI）が作った編集再読データを取り込む前の検証（2026-09-13〜）

編集再読の本文読みは分量が多く、別セッション・別AIに依頼することがある。
mainへ取り込む前に、**「合格した」という報告を鵜呑みにせず**、次の5点を自分で確認する。

1. **件数の一致**: 指定した対象論点の件数と、成果物（`data/{theme}_*-reread.json`等）の
   `items`件数・`buckets`の合計が一字一句一致するか
2. **本物の判定を実際に動かす**: `independence_gate()`をその場で実行し、「合格した」
   という報告ではなく実際の戻り値（空リストか）を確認する
3. **本文の指紋照合**: 成果物の各項目に`text_sha256`を持たせ、正典の現在の本文から
   計算したsha256と全件一致するか確認する（改ざん・古いデータの流用を検知する）
4. **抜き取りで中身を読む**: 論点ごとに数件、実際の投稿本文と割り振られた区分
   （バケット）が対応しているかを目で確認する
5. **文言そのものを読む**: 区分名（バケットラベル）を一覧表示し、人が読んで意味が
   通るか確認する（2026-09-13、副首都で簡体字混入・誤字・内部マークアップの
   残骸を発見。自動検査では見つからない）

自転車正典の本文なし検証データは `python3 scripts/build_bike_verification.py` で作る。旧形式のトップ階層 `is_opinion` と新形式の分類内フラグを、公開集計と同じ優先順で保持する（収集回の保存済み検証ファイルは変更しない）。

## 収集と山なみ区画の表示更新は別の判断基準で優先順位を決める（2026-09-15〜）

課題54完了に伴い定期収集を再開するにあたり、「収集」と「山なみ区画の表示更新」を
別の判断基準で優先順位付けする。理由：`independence_gate()`（`build_planet_data.py`）は
`scripts/refresh_topic.py`（`--promote`を含む）には一切組み込まれておらず（grep 0件）、
山なみテーマの`--promote`もadapterのfinalize（例: `build_bukatsu_arena.py`）が
`planet_mode`判定で山なみ区画をスキップするため検査に触れない。検査が実際に効くのは
`scripts/refresh_planet_section.py --topic <topic> --for-docs`（または初回変換の
`build_planet_page_preview.py --for-docs`）を実行した瞬間だけである。

**収集（`--promote`まで含む正典保存）**: `collect_at`（=`refresh_at`）の超過日数順（超過が
大きいテーマから）で進めてよい。独自性検査の逼迫度は収集そのものには影響しない。

**山なみ区画の表示更新**: 実行前に必ず`python3 scripts/verify_reread_headroom.py`で
そのテーマの状態を確認する。`danger`（40%超）の論点があれば`--for-docs`が確実に
失敗する。`warn`（30%以上）は、そのテーマ自身の次回収集より前に追い読みを検討する。

## 定期更新1回分の実務手順（課題69、2026-09-15〜、bukatsu-chiikiで確立）

「収集してから最短で公開まで反映する」1テーマ分の通し手順。山なみ移行済みテーマで
実際に動かして確立した。山なみ以外・独自性検査の対象外テーマではステップ4-9・12の
一部が不要になる。

1. **収集する**（`refresh_topic.py`、`--promote`なし）。正典・公開ページには触れない
2. **収集直後にTHEMES.yaml等の変更をコミットする。** `--apply-promotion`は
   `ensure_promotion_targets_clean()`で「THEMES.yaml・docs/配下に未コミット差分が
   ないこと」を前提とする。コミットせずに進むと `公開対象に未コミット差分があります`
   で止まる
3. `--resume --prepare-promotion` で候補（`cumulative-candidate.json`等）を作る
   （正典・公開ページはまだ変更しない）
4. **独自性検査への影響を、正典に統合する前に試算する。** `build_planet_data`の
   `unread_breakdown()`等を直接呼び、候補データを`canonical`として渡せば、
   正典もTHEMES.yamlも書き換えずに「この収集をこのまま反映すると何件読む必要が
   出るか」を正確に計算できる（詳細な例は`quality/reviews/2026-09-15-task54-stage11-audit.md`
   と同日の課題69実施記録を参照）
5. 必要な読み込み確認の対象件数が確定したら、下記「読み込み確認のやり方」に従って読む
6. **山なみテーマは、正典だけを先に候補データへ置き換える。** `--apply-promotion`は
   正典と山なみ区画を同時に検査するため、山なみ区画がまだ古いまま（読み込み確認前）
   だと`verify_theme_page.py`の「件数表示が一致する」検査で必ず落ちる。正典
   （`social-samples/{topic}_*.json`、バックアップを取ってから）だけを先に候補へ
   差し替え、山なみ区画の更新（ステップ10）を後から追いつかせる。
   **辺野古は2026-10-09から、この手作業（6〜12）が要らない。** 候補のまま標準の
   `--prepare-promotion` が通る（下の「辺野古の定期更新」）
7. `manage_reread_registry.py prepare`（`--issue`で論点ごとに）→ 読む →
   `record`で共通台帳（`data/verification/reread/{topic}.json`）を更新する
8. **テーマ固有の専用ファイル（`data/{topic}_*-reread.json`等）を更新したら、
   `manage_reread_registry.py resync-source --source <path> --out ...`で
   共通台帳の`sources`指紋を合わせる。** `record`は共通台帳の`records`だけを
   更新し、`sub_issues`が参照する専用ファイルは書き換えない。専用ファイル側を
   直接更新すると`check_sources()`が「継承元が変わった」と正しく検知して以後の
   コマンドが止まるため、この専用コマンドで「専用ファイルの中身が共通台帳の
   読了記録と1件ずつ一致すること」を確認してから指紋を進める（検査を緩めるの
   ではなく、別の角度からの一致確認を挟んでから進める設計。2026-09-15新設）
9. `build_public_registry.py --topic <topic>` で公開データ契約を再生成する
   （`independence_gate`は`data/public/themes/{topic}.json`を読むため、これを
   忘れると正典・共通台帳を直しても検査に反映されない）
10. `refresh_planet_section.py --topic <topic> --for-docs` で山なみ区画を更新する
11. テーマ別のfinalize相当（例: `build_bukatsu_arena.py`）を実行する
12. `verify_theme_page.py <topic>`・`verify_number_provenance.py <topic>`を実行し、
    残ったNGを1つずつ潰す。**山なみ区画の外側にあるのに件数を持つ箇所
    （bukatsu-chiikiでは「調査条件」の取得期間・件数、`#issue-cards`の論点カード
    件数）は、`build_planet_page_preview.py`の初回変換時にしか更新されない
    見落としが起きやすい。** 見つけたら`refresh_planet_section.py`のテーマ別
    関数（`TOPIC_METHOD_TEXT`等）へ同期処理を追加する（他テーマへは影響しない
    ようテーマ専用関数の中に閉じる）
13. `configs/theme-seo.json`の対象テーマの`dateModified`を今回の日付へ更新し、
    `python3 scripts/seo/apply_theme_trust.py`（`--check`で対象確認→本実行）で
    ページ内「編集・分析情報」の最終更新日とJSON-LDの`dateModified`に反映する。
    **この値は`THEMES.yaml`の`updated_at`から自動では追随しない**（`collection`
    欄の件数はテンプレートに埋め込むため毎回最新化されるが、`dateModified`は
    config内の静的な値。verify_theme_page.py等の機械検査もここは見ていない
    ため、機械検査が全部OKでも古いまま残る）。**同じ`theme-seo.json`の
    `observations`（「収集・分類で分かったこと」）に論点ごとの件数を書くときは、
    数字を打たず`{issue_count:論点名}`と書く**（公開データJSONから差し込まれる。
    べた書きの数字は更新のたびにページを古い値へ戻す。高齢者テーマで2回再発した）
14. **後処理をまとめて実行する**（`python3 -m unittest discover -s tests`で
    まとめて検出できる）: `build_data_sheet.py` / `sync_portal_stats.py` /
    `verify_sample_periods.py --generate` / `build_adoption_registry.py`。
    正典を更新すると採用台帳（`data/verification/adoption/registry.json`）の
    指紋も古くなる（課題68と同型）
15. 全体テスト・標準4検査を最終確認してからコミットする
16. **公開後、実際のページをブラウザで開いて目視確認する。** 機械検査は
    「ページ内の数字同士が矛盾していないか」は見るが、「表示されている値が
    最新かどうか」まではテーマによって見ていない項目がある（13の
    `dateModified`はこの方法で発見した）。件数・調査期間だけでなく、
    ページ末尾の「このページの作り方」欄も含めて一通り読む

### 新ルールの本文確認工程と新論点チェック（2026-10-10〜、道具は `scripts/wave_review/`）

10/9の新ルール（今回分は同じ回で全件本文確認、判断できない投稿は意見外）を、どのセッションでも同じ形で回すための
通し手順は `.claude/skills/theme-refresh/SKILL.md` にある。定期収集では必ずそれを読む。要点だけ書く。

- **読み手の伏せ読み**: `wave_review.py batches` が本文だけのバッチと読み手用の指示文を作る。Sonnet のサブエージェント2本（A・B）が
  自動分類を見ずに意見判定・論点・立場・理由区分・要約・新論点候補を付ける。テーマごとの説明は `configs/wave_review/<topic>.yaml`。
- **突き合わせ**: `compare` が読み手どうしと Kimi の食い違いを `review.txt` に出す。編集担当が本文を読んで `decisions.json` に確定し、
  `decide` で検査（設定に無い論点・立場・区分は止まる）。
- **記録**: `apply` が候補への補正（`data/verification/<topic>-wave-review-YYYYMMDD.json`、adapter の `review_candidate` が読む）、
  読了証拠（`quality/reviews/<date>-<topic>-wave-reading.json`）、専用再読ファイルへの理由区分の追加を書く。
  再読共通台帳があるテーマは候補生成後に `register`。完了記録は `refresh_completion.py prepare` → `fill` → `check`。
  自転車は `bike_plan.py` で `review-plan.json` を作り `build_bike_refresh_candidate.py` を通す（本文確認記録の形式が独自）。
- **新論点チェック**: 読了証拠の `new_issue_check` に「その他」の件数・割合と候補名ごとの件数が残る。目安は
  「その他が今回の意見の5%超、または同じ趣旨が20件以上」。超えても即新設ではなく、監査に書いてオーナーに提案する
  （新設はページの論点ナビ・山なみ・調査条件・note まで動く別作業）。これまでの候補: 自転車「歩道通行の是非／LUUPとの比較／
  自動車との取締り格差」、高齢者「家族の説得／高齢運転者の識別表示」、憲法「皇室・家族条項／首相公選制・大統領制」。
- **線引き**: 同文の連投・署名の定型文は1件1意見で数え監査に明記。皮肉・問いだけ・断片は意見外。中傷・排外・陰謀論は
  代表投稿に使わない（`article_usable: false`）。テーマの主題でない投稿は意見外（高齢者の「免許返納しろ」型の罵倒など）。
- **止まり方の定番**（資料にしかない話の母数、主張の該当投稿数、制度の確認日、立場の対応表、再読台帳の対象集合）と直し方は
  スキルの手順6に一覧がある。初回に回したテーマの記録: `quality/reviews/2026-10-1{0,1,3}-*-refresh-review.md`。

### 辺野古の定期更新（標準の `--prepare-promotion` で通る、2026-10-09〜）

**2026-10-13 から新デザインで公開する間は、新しい意見の追い読み（人が読む工程）が要る**（下の「辺野古高校生死亡事故の定期更新（新デザインを維持する）」の節）。

それまでの辺野古は、`henoko_planet_guard` が「候補＝今ディスクにある正典」を求めたため、新しい回を入れた
候補は必ず止まり、上の6〜12の手作業で通していた（9/16・9/24・10/8）。今は、候補（正典に今回の追加分を
足したもの）を入力に山なみを作り、候補に対応する公開JSONと件数・分類・元データの指紋が一致することを
検査する。**手順は他テーマと同じ**: 収集 → `THEMES.yaml` 等をコミット →
`--resume --prepare-promotion`（正典・公開ページは変わらない）→ 品質監査・オーナー承認 → `--apply-promotion`。

- **次の2つで止まるのは正しい動き**（人が直して、同じコマンドを再実行する）。
  「語られていない争点の母数が確認時点の○件のまま」は、新しい意見を各争点の検索語で再検索して本文を確認し、
  `data/verification/henoko-student-accident-sunk-continents.json` の `sns_base` を更新する。
  過去の理由記録の不足が論点の4割超なら解消する。今回分は割合に関係なく本文確認・理由分類・記録を完了する。
  直すのは作業ツリーの台帳で、公開JSONは候補から作り直される
- **既存の投稿を書き換えた候補は止まる**（本文・分類・件数のいずれも）。候補は「正典に足す形」にする
- 標準の経路が作らないもの: トップの「今週の注目テーマ」（`refresh_featured_slots.py`、全テーマ共通）と、
  note更新の要否確認。`apply_theme_trust.py` を手で直接流すと全10テーマのページが書き換わるので、
  辺野古以外の差分は戻す（標準の経路では隔離コピーの中だけで、公開物には入らない）
- 経緯と検証の記録: [quality/reviews/2026-10-09-task69-henoko-standard-route-details.md](quality/reviews/2026-10-09-task69-henoko-standard-route-details.md)

### 皇室典範改正の定期更新（新デザインを維持する、2026-10-11〜）

皇室典範改正のページは2026-10-11から新デザイン（冒頭・論点ごとの読書面・背景の開閉行）で公開している。
部活動の新デザイン（`scripts/bukatsu_layout.py`・`configs/bukatsu-layout.json`）と同じ型で、
**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-koshitsu-tenpakai-production-candidate.md](quality/designs/2026-10-11-koshitsu-tenpakai-production-candidate.md)

- **`configs/koshitsu-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`koshitsu_layout.materialize`）、旧形式の全処理のあとに
  `koshitsu_layout.finish` で元HTMLを保存し直してから新デザインのページを `docs/` に書く。
  **他テーマの更新でも毎回この処理が走る**（皇室の照合が合わないと、その回の公開候補生成全体が止まる）。
  `false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページを先に戻すこと
- **元HTMLの場所**: `data/page-sources/koshitsu-tenpakai.html`（Git管理）。`refresh_adapters/koshitsu.py`・
  `build_koshitsu_arena.py`（引数なし）はこれを入力にする。手で編集しない。`docs/koshitsu-tenpakai-reaction-map.html` を
  旧形式の生成器に直接渡すと拒否される（新デザインの再入力防止）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_koshitsu_arena.py`（新デザイン公開中は元HTMLと公開ページの両方を作り直す）。
  成功の形: もう一度 `python3 scripts/build_koshitsu_arena.py --check` を実行して `OK` と出ること
- **「論点ごとに読む」の山なみ（2026-10-11〜）**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_koshitsu_redesign.py` が毎回そのまま写す（立場モード6つ・100マス・論点の一覧・見かた）。手で直す所は無い。山を押すと読書面へ移る橋渡しは
  `scripts/koshitsu_redesign/planet.js`（設計記録の10節）
- **折りたたみ（2026-10-12〜、部活動型の圧縮）**: 読書面の論点タブ・理由一覧（上位4件＋「ほかのN区分を表示」）・選んだ理由だけの説明・「理由の数え方」・
  立場（今回案全体への賛否）・投稿例・根拠の照合（同じ心配・制度の確認・主張・資料にしかない話）・論点の説明の2段落目（「続きを読む」）・収集ごとの表の
  `<details>` は `koshitsu_reading.py` が毎回作る。手で開閉や中身を直す所は無い（見出しの文言は `configs/koshitsu-tenpakai-reading.json` の `compact`。設計記録の11節）
- **再読データ（理由区分）を追記したとき**: 新しい収集回の意見は、本文を読んで理由区分を決め、
  `data/koshitsu-tenpakai_issues-reread.json` の `items` に1件ずつ追記し、`buckets` の件数も合わせる。
  **`items` の件数が公開JSONの意見数と一致しないと新デザインの生成が止まる**（公開JSONを先に更新して再読を
  後回しにすると、全テーマの公開候補生成が止まる）。追記後は次の順で反映する。
  1. 共通台帳の指紋を合わせる（上の「定期更新1回分の実務手順」8の `manage_reread_registry.py resync-source`）
  2. `data/verification/koshitsu-tenpakai-issues-reread.json`（専用ファイル items の写し。数字の出所検査の根拠）を作り直す:
     `python3 -c "import json;d=json.load(open('data/koshitsu-tenpakai_issues-reread.json',encoding='utf-8'));open('data/verification/koshitsu-tenpakai-issues-reread.json','w',encoding='utf-8').write(json.dumps(d['items'],ensure_ascii=False,indent=2)+chr(10))"`
     （書式は既存ファイルに合わせる。`git diff --stat` で追記した件数ぶんだけ増えていれば成功）
  3. `python3 scripts/build_public_registry.py --topic koshitsu-tenpakai`
  4. 公開候補生成（`--prepare-promotion`）を流す。単独なら `python3 scripts/build_koshitsu_arena.py`
  5. `python3 scripts/verify_number_provenance.py koshitsu-tenpakai`（新デザインの理由区分の件数を明細から数え直す）
  投稿の説明文や代表投稿2件は `configs/koshitsu-tenpakai-reading.json`。区分が増えたときだけ直す
- **語られていない争点の再検索の記録**（`data/verification/koshitsu-tenpakai-sunk-continents.json` の `sns_note`）は
  画面に出る公開文章。追記したらよみやす検査（`review_with_yomiyasu.py --medium website --strict`）を新デザインの
  ページに掛ける
- **施行日（2026-10-24）以降の時制**: 生成は止まらない。冒頭と背景（年表・よくある質問・未確認事項）は
  公開JSONの更新日（`--as-of` を渡したときはその日）で時制を決める。施行日を過ぎ、施行後の条文をまだ確かめて
  いない間は「施行される予定でした。施行後の条文は、まだ編集部で確かめていません」と出る（施行後・未確認）。
  **e-Gov の現行の条文が改正後の内容に切り替わったことを確かめたら**、`configs/koshitsu-tenpakai-opening.json` の
  `law.enforcement_confirmed_on` に確かめた日（`YYYY-MM-DD`）を入れ、一次資料メモの「確認できなかったこと 7」を
  解消済みにしてから作り直す。冒頭・年表・FAQ が「施行されました」に切り替わり、未確認事項からその1行が消える。
  施行日より前の日付を入れると止まる。施行後の文言は `configs/koshitsu-tenpakai-background.json` の
  `phase_events`（年表）・`phase`（FAQ）・`hide_in`（未確認事項）にあり、欠けていると施行日より前でも生成が止まる
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用を
  掛けない（各スクリプトが skipped と出す）。更新経路では元HTMLに掛かる

### 副首都の定期更新（新デザインを維持する、2026-10-11〜）

副首都のページは2026-10-11から新デザイン（冒頭の路線図と地図・論点ごとの読書面・背景の開閉行）で公開している。
皇室典範改正の新デザイン（上の節）と同じ型で、**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-fukushuto-production-candidate.md](quality/designs/2026-10-11-fukushuto-production-candidate.md)

- **`configs/fukushuto-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`fukushuto_layout.materialize`）、旧形式の全処理（adapter・潮目・finalize・SEO・
  信頼情報・授業節・テーマ共通の見た目・皇室の新デザイン）のあとに `fukushuto_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。**他テーマの更新でも毎回この処理が走る**（副首都の照合が合わないと、その回の
  公開候補生成全体が止まる）。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。
  戻すときは旧形式のページ（`data/page-sources/fukushuto.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/fukushuto.html`（Git管理）。`refresh_adapters/fukushuto.py`（潮目の差し込みを含む）・
  `build_fukushuto_arena.py`（引数なし）はこれを入力にする。手で編集しない。`docs/fukushuto-reaction-map.html` を
  旧形式の生成器に直接渡すと拒否される（新デザインの再入力防止）。旧ページの検索入口（`fukushuto_search_entry.py`、
  FAQ 6問）・連動表示・潮目は元HTMLの中でだけ更新され、新デザインには載せない。新デザインの FAQ の構造化データは、
  背景の「よくある質問（4問）」から毎回作り直す
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_fukushuto_arena.py`（新デザイン公開中は元HTMLと公開ページの両方を作り直す）。
  成功の形: もう一度 `python3 scripts/build_fukushuto_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_fukushuto_redesign.py --mode release --output-dir quality/prototypes/fukushuto-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **「論点ごとに読む」の山なみ（2026-10-11〜）**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_fukushuto_redesign.py` が毎回そのまま写す（立場モード・100マス・論点の一覧・見かた）。手で直す所は無い。山を押すと読書面へ移る橋渡しは
  `scripts/fukushuto_redesign/planet.js`（設計記録の10節）
- **折りたたみ（2026-10-12〜、部活動型の圧縮）**: 読書面の論点タブ・理由一覧（上位4件＋「残りの理由を見る」）・選んだ理由だけの説明・立場別集計・投稿例・
  根拠の照合・論点の説明の2段落目（「説明の続き」）・収集ごとの表、作り方と詳細データ（「集計の方法と、全データ」）の `<details>` は
  `fukushuto_reading.py`・`build_fukushuto_redesign.py` が毎回作る。手で開閉や中身を直す所は無い（見出しの文言は `configs/fukushuto-reading.json` の `compact`。設計記録の11節）
- **再読データ（理由区分）を追記したとき**: 5論点（候補地・防災・災害・優先順位・その他・費用・財源）の新しい意見は、
  これまでどおり本文を読んで理由区分を決め、`data/fukushuto_5issues-reread.json` の各論点の `items` に1件ずつ追記し、
  `buckets` の件数も合わせる。**論点ごとの `items` の件数が公開JSONの論点の件数と一致しないと新デザインの生成が止まる**
  （公開JSONを先に更新して再読を後回しにすると、全テーマの公開候補生成が止まる）。区分ごとの立場の内訳も明細の
  `stance` から数えるので、明細の立場が公開JSONと違っても止まる。追記後は
  1. `python3 scripts/build_public_registry.py --topic fukushuto`
  2. 公開候補生成（`--prepare-promotion`）を流す。単独なら `python3 scripts/build_fukushuto_arena.py`
  3. `python3 scripts/verify_number_provenance.py fukushuto`（新デザインの理由区分・区分ごとの立場を明細から数え直す。
     成功の形: `NG 0件`）
  理由区分の言い換え・「どんな声か」・代表投稿2件は `configs/fukushuto-reading.json`。区分が増えたとき・投稿を
  差し替えるときだけ直す（完成扱いの論点で言い換えの無い区分があると止まる）。都構想・維新と定義・中身は
  再読データが無く「理由別に読み直したデータをまだ公開していません」と出る（データが入れば自動で消える）
- **語られていない争点の再検索の記録**（`data/verification/fukushuto-sunk-continents.json` の `sns_note`・`life_impact`）は
  画面に出る公開文章。母数 `sns_base` が意見数と違うと生成が止まる（再検索して記録を足す）。追記したらよみやす検査
  （`python3 scripts/review_with_yomiyasu.py --medium website --strict docs/fukushuto-reaction-map.html`）を
  新デザインのページに掛ける（成功の形: `完成を止める指摘: 0件`）
- **時制（意見募集の締切 2026-10-16・施行予定日 2026-10-30）**: 生成は止まらない。冒頭（路線図・「いつ決まる？」）と
  背景（定義・手続き・年表・よくある質問・未確認事項）は、公開JSONの更新日（`--as-of` を渡したときはその日）で
  段階を決める。読む日が締切・施行日を過ぎたら、冒頭の路線図と「いつ決まる？」だけは JavaScript が次の段階の文に
  切り替える（背景は次の更新で切り替わる）。
  - 締切を過ぎ、結果を確かめていない間: 「締め切った。結果は編集部でまだ確かめていない」。
    **e-Gov で意見募集の結果公示を確かめたら**、`configs/fukushuto-opening.json` の `comment.result_published_on` に
    確かめた日を入れて作り直す（締切より前の日付、または基準日が締切より前なのに日付があると止まる）
  - 施行予定日を過ぎ、施行後の条文を確かめていない間: 「施行予定でした。施行後の条文は編集部で確かめていません」。
    **e-Gov で施行済みの表示と施行日を確かめたら**、`configs/fukushuto-opening.json` の `law.enforcement_confirmed_on` に
    確かめた日を入れ、一次資料メモの未確認事項を解消済みにしてから作り直す（施行日より前の日付は止まる）
  - 段階ごとの文は `configs/fukushuto-opening.json` の `phase_text` と `configs/fukushuto-background.json` の
    `phase_now`・`phase_comment`・年表の `texts`・FAQ の `phase`・未確認事項の `hide_when`。欠けていると
    締切・施行日より前でも生成が止まる
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  潮目の単独差し込み（`inject_tide_widget.py`）を掛けない（各スクリプトが skipped／SKIP と出す）。更新経路では元HTMLに掛かる
- 「このページの作り方」（ARTICLE_TRUST）・「詳細データ」・「次に読むテーマ」・投票・SEOメタは元HTMLから文字どおり
  引き継ぐ。数字が古いときは元HTML側（`build_fukushuto_arena.py`・`apply_theme_trust.py`）で直る

### 生成AIと著作権の定期更新（新デザインを維持する、2026-10-11〜）

生成AIと著作権のページは2026-10-11から新デザイン（冒頭の2問と件数のものさし・論点ごとの読書面・背景の開閉行）で公開している
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml`）。副首都・皇室典範改正の新デザイン（上の節）と同じ型で、
**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-ai-copyright-production-candidate.md](quality/designs/2026-10-11-ai-copyright-production-candidate.md)

- **`configs/ai-copyright-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`ai_copyright_layout.materialize`）、旧形式の全処理（adapter・意見の推移・finalize・SEO・
  信頼情報・授業節・テーマ共通の見た目・皇室と副首都の新デザイン）のあとに `ai_copyright_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。**他テーマの更新でも毎回この処理が走る**（生成AIの照合が合わないと、その回の
  公開候補生成全体が止まる）。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。
  戻すときは旧形式のページ（`data/page-sources/ai-copyright.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/ai-copyright.html`（Git管理）。`refresh_adapters/ai_copyright.py`（連動表示・
  「意見の推移」の貼り直しを含む）・`build_ai_copyright_arena.py`（引数なし）はこれを入力にする。手で編集しない。
  `docs/ai-copyright-reaction-map.html` を旧形式の生成器に直接渡すと拒否される（新デザインの再入力防止）。
  旧ページの検索入口（`ai_copyright_search_entry.py`・`docs/ai-copyright-connected-page.js`）・連動表示・論点ごとのX投稿14件
  （`ai_copyright_issue_media.py`）は元HTMLの中でだけ更新され、新デザインには載せない。新デザインの FAQ の構造化データは、
  背景の「よくある質問（4問）」から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・共通ヘッダー・
  投票（`ai-copyright-issue-stance-v1`、論点7×立場3）・調査条件（`#caution`）・PLANET_DATA・**「SNS上の意見の推移」
  （画像4枚 `docs/images/trend/ai-copyright-*.png` と説明。`trend_support` が元HTMLに貼り、画像は adapter が同じ累積候補から作る）**・
  「このページの作り方」・「詳細データ」・「次に読むテーマ」・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る。
  アリーナデータ（`docs/ai-copyright-arena-data.js`）は新デザインでは読まないが、adapter が引き続き作って公開物に含める
- **「意見の全体像」の山なみ（2026-10-11〜）**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_ai_copyright_redesign.py` が毎回そのまま写す（立場モード・100マス・論点の一覧・見かた）。元HTMLの山なみが更新されれば新ページにも載り、手で直す所は無い。
  山を押すと読書面へ移る橋渡しは `scripts/ai_copyright_redesign/planet.js`（設計記録の10節）
- **折りたたみ（2026-10-12〜、部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場別集計・投稿例・
  根拠の照合・論点の説明の2段落目（「くわしく」）、意見の推移（「詳しいグラフと表を開く」）、作り方と詳細データ（「調査方法と、集計の全データ」）の
  `<details>` は、`ai_copyright_reading.py`・`build_ai_copyright_redesign.py` が毎回作る。手で開閉や中身を直す所は無い（見出しの文言は
  `configs/ai-copyright-reading.json` の `compact`。設計記録の11節）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_ai_copyright_arena.py`（新デザイン公開中は、元HTMLに公開JSONの集計と旧形式の生成を掛けてから
  公開ページを作り直す。アリーナデータも同じ）。成功の形: もう一度 `python3 scripts/build_ai_copyright_arena.py --check` を
  実行して `OK: 差分なし` と出ること。公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_ai_copyright_redesign.py --mode release --output-dir quality/prototypes/ai-copyright-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**: 5論点（学習データ・無断利用／クリエイター保護・権利／その他／
  AI生成物の権利・創作性／技術競争・推進）の新しい意見は、本文を読んで理由区分を決め、`data/ai-copyright_issues-reread.json` の
  各論点の `items` に1件ずつ追記し、`buckets` の件数も合わせる。**論点ごとの `items` の件数が公開JSONの論点の件数と
  一致しないと新デザインの生成が止まる**（旧ページは「まだ読み直していない分」を残せたが、新デザインは残せない。
  公開JSONを先に更新して再読を後回しにすると、全テーマの公開候補生成が止まる）。区分ごとの立場の内訳は明細の `stance` から
  数えるので、明細の立場が公開JSONと違っても止まる。**判定し直し（`rejudge_ai_copyright_wave.py` など）で正典の立場が
  変わったら、明細の `stance` も正典に合わせる**（2026-10-11 に11件を合わせた記録が `stance_resync_2026_10_11`）。
  共通台帳（`data/verification/reread/ai-copyright.json`）はこのテーマには無いので `resync-source` は使わない。追記後は
  1. `python3 scripts/build_public_registry.py --topic ai-copyright`
  2. 公開候補生成（`--prepare-promotion`）を流す。単独なら `python3 scripts/build_ai_copyright_arena.py`
  3. `python3 scripts/verify_number_provenance.py ai-copyright`（新デザインの理由区分・区分ごとの立場を明細から数え直す。
     成功の形: `NG 0件`）
  理由区分の言い換え・「どんな声か」・代表投稿2件は `configs/ai-copyright-reading.json`。区分が増えたとき・投稿を
  差し替えるときだけ直す（完成扱いの論点で言い換えの無い区分があると止まる）。法制度・規制整備と利用者モラル・倫理は
  再読データが無く「理由ごとに読み分けた結果をまだ載せていません」と出る（データが入れば自動で消える）。
  読書面の生成は非公開の正典を読まないので、GitHub の自動検査でも同じ検査が動く
- **語られていない争点の再検索の記録**（`data/verification/ai-copyright-sunk-continents.json` の `sns_note`・`life_impact`）と
  **立場が違っても共通する心配**（`ai-copyright-veins.json`）は画面に出る公開文章。母数 `sns_base` が意見数と違うと生成が止まる
  （再検索して記録を足す）。追記したらよみやす検査
  （`python3 scripts/review_with_yomiyasu.py --medium website --strict docs/ai-copyright-reaction-map.html`）を
  新デザインのページに掛ける（成功の形: `完成を止める指摘: 0件`）
- **時制（確認日 `checked_on`・プリンシプル・コードの届出開始 2026-10-26）**: 生成は止まらない。
  - 冒頭と背景の「◯月◯日時点」は `configs/ai-copyright-opening.json` の `checked_on`（制度を確かめた日）1か所から出る。
    一次資料を確かめ直したらこの日付を進める
  - 背景（ルールの違い・年表・よくある質問・未確認事項）は、公開JSONの更新日（`--as-of` を渡したときはその日）が届出開始日
    より前か後かで文を切り替える。開始日を過ぎ、届出の開始をまだ確かめていない間は「始まる予定でした。始まったかどうかは、まだ確かめていません」
    （開始後・未確認）と出る。**内閣府（内閣官房「AI時代の知的財産権検討会」）のページで届出の開始を確かめたら**、
    `configs/ai-copyright-opening.json` の `principle_code.filing_confirmed_on` に確かめた日を入れて作り直す（開始日より前の日付、
    または基準日が開始日より前なのに日付があると止まる）。「始まりました（◯月◯日に確認）」に切り替わり、未確認事項からその1行が消える
  - 副首都と違い、冒頭には段階の表示が無いので、読む日による JavaScript の切り替えは無い（背景は次の更新で切り替わる）
  - 段階ごとの文は `configs/ai-copyright-background.json` の `phase_filing`・年表の `texts`・FAQ の `phase_filing`・
    未確認事項の `hide_when`。欠けていると開始日より前でも生成が止まる
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）を掛けない
  （各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 憲法改正論議の定期更新（新デザインを維持する、2026-10-12〜）

憲法改正論議のページは2026-10-12から新デザイン（冒頭の決まり方と争点・対話式の山なみ・論点ごとの読書面・背景の開閉行）で公開する
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261012-constitutional-amendment`）。生成AIと著作権（上の節）と同じ型で、
**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-constitutional-amendment-production-candidate.md](quality/designs/2026-10-11-constitutional-amendment-production-candidate.md)

- **`configs/constitutional-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`constitutional_layout.materialize`）、旧形式の全処理（adapter の山なみ・潮目・連動表示・finalize・
  SEO・信頼情報・授業節・テーマ共通の見た目・皇室／副首都／生成AIの新デザイン）のあとに `constitutional_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。**他テーマの更新でも毎回この処理が走る**（憲法の照合が合わないと、その回の公開候補生成全体が止まる）。
  `false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/constitutional-amendment.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/constitutional-amendment.html`（Git管理）。`refresh_adapters/constitutional.py`（山なみ・潮目・連動表示）・
  `build_constitutional_arena.py`（引数なし）・`inject_tide_widget.py`（潮目の汎用JS・CSSの原型）はこれを入力にする。手で編集しない。
  `docs/constitutional-amendment-reaction-map.html` を旧形式の生成器に直接渡すと拒否される（新デザインの再入力防止）。
  旧ページの検索入口（`docs/constitutional-search-entry.*`）・連動表示（`constitutional_connected*.py`・`docs/constitutional-connected*`）・
  論点ごとのX投稿12件は元HTMLの中でだけ更新され、新デザインには載せない。新デザインの FAQ の構造化データは、
  冒頭の「よく聞かれること」（4問）と背景の「よくある質問」（4問）から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`constitutional-amendment-issue-stance-v1`、論点6×立場4）・調査条件（`#caution`）・PLANET_DATA・**前回の収集との比較（潮目のカード。
  adapter の `_apply_tide` が元HTMLに貼る）**・「このページの作り方」・「詳細データ」・「次に見るテーマ」とクリック計測・フッター。
  数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る。共通ヘッダーは生成器が静的に置く（元HTMLには無い）
- **「意見の全体像」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_constitutional_redesign.py` が毎回そのまま写し、論点タブの上に置く（立場モード・100マス・論点の一覧・見かた）。手で直す所は無い。
  山を押すと読書面へ移る橋渡しは `scripts/constitutional_redesign/planet.js`
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場別集計・投稿例・
  根拠の照合・論点の説明の2段落目（「くわしく」）・「前回の収集と比べると」の累計の表、前回の収集との比較（「立場と論点の比較グラフを開く」）、
  作り方と詳細データ（「このページの作り方と、集計の全データ」）の `<details>` は、`constitutional_reading.py`・`build_constitutional_redesign.py` が
  毎回作る（見出しの文言は `configs/constitutional-amendment-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_constitutional_arena.py`（新デザイン公開中は、元HTMLに公開JSONの集計・山なみ・連動表示を掛けてから
  公開ページを作り直す）。成功の形: もう一度 `python3 scripts/build_constitutional_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_constitutional_redesign.py --mode release --output-dir quality/prototypes/constitutional-amendment-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき（追い読み）**: 新しい意見は本文を読んで理由区分を決め、`data/constitutional-amendment_issues-reread.json` の
  `items` に1件ずつ追記し、`buckets` の件数も合わせる。**論点ごとの明細の件数が公開JSONの論点の件数と一致しないと新デザインの生成が止まる**
  （旧ページと違い「まだ読み直していない分」を残せない。公開JSONを先に更新して追い読みを後回しにすると、全テーマの公開候補生成が止まる）。
  明細には立場が無いので、**追い読みや判定し直しのあとは、毎回立場の対応表を作り直す**:
  1. `python3 scripts/constitutional_reread_stances.py --made-on YYYY-MM-DD`（その日の日付。このスクリプトだけが非公開の正典を読む。
     成功すると `data/constitutional-amendment_reread-stances.json` が書き換わる）
  2. `python3 scripts/build_public_registry.py --topic constitutional-amendment`
  3. 公開候補生成（`--prepare-promotion`）を流す。単独なら `python3 scripts/build_constitutional_arena.py`
  4. `python3 scripts/verify_number_provenance.py constitutional-amendment`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
  作り直さないと「再読データの明細と立場の対応表の投稿が一致しません」または「明細の立場の内訳が公開JSONと一致しません」で止まる。
  対応表には本文・tweet_id を入れない（投稿は post_key で引く）。理由区分の言い換え・「どんな声か」・代表投稿2件は
  `configs/constitutional-amendment-reading.json`。区分が増えたときは、その区分の `voice` も書く（完成扱いの論点で説明の無い区分があると止まる）
- **語られていない争点の再検索の記録**（`data/verification/constitutional-amendment-sunk-continents.json` の `sns_note`）と
  **立場が違っても共通する心配**（`constitutional-amendment-veins.json`）は画面に出る公開文章。母数 `sns_base` が意見数と違うと生成が止まる
  （再検索して記録を足す）。追記した文は1文80字以内に区切り、よみやす検査
  （`python3 scripts/review_with_yomiyasu.py docs/constitutional-amendment-reaction-map.html --medium website --strict`。成功の形: `完成を止める指摘: 0件`）を掛ける
- **時制（確認日 `checked_on`・国民投票法の改正の施行 2026-10-31）**: 生成は止まらない。
  - 冒頭・読書面・背景の「◯月◯日時点」は `configs/constitutional-amendment-opening.json` の `checked_on`（制度を確かめた日）1か所から出る。
    背景台帳（`data/verification/constitutional-amendment-background.json`）の `checked_on` より古い日付は入れられない
  - 冒頭の流れ図の脚注と背景（国民投票法の行・年表・まだ確かめていないこと）は、公開JSONの更新日（`--as-of` を渡したときはその日）が
    施行日より前か後かで文を切り替える。施行日を過ぎ、施行後の条文をまだ確かめていない間は「施行される予定でした。施行後の条文は
    編集部で確かめていません」と出る。**10/31 以降に e-Gov で施行後の条文を確かめたら**、`law.enforcement_confirmed_on` に確かめた日を入れて作り直す
    （施行日より前の日付、または基準日が施行日より前なのに日付があると止まる）
  - 生成AIと同じく、読む日による JavaScript の切り替えは無い（10/31 をまたいで更新が無いと、次の更新まで「予定です」の文が残る）
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）を掛けない
  （各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 自転車の青切符の定期更新（新デザインを維持する、2026-10-12〜）

自転車の青切符のページは2026-10-12から新デザイン（冒頭の「何歳から・いくら？」の短答・対話式の山なみ・論点ごとの読書面・背景の開閉行）で公開する
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261012-bike-blue-ticket`）。憲法改正論議（上の節）と同じ型で、
**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。** 人が読む工程（反対投稿の再読と本文確認記録）は
上の「自転車青切符だけ、人が読む工程が1つ残っている」のまま変わらない。
設計と検査の記録: [quality/designs/2026-10-11-bike-blue-ticket-production-candidate.md](quality/designs/2026-10-11-bike-blue-ticket-production-candidate.md)

- **`configs/bike-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`bike_layout.materialize`）、旧形式の全処理（adapter のアリーナ・山なみ・潮目・連動表示・検索入口・finalize・
  SEO・信頼情報・授業節・テーマ共通の見た目・皇室／副首都／生成AI／憲法の新デザイン）のあとに `bike_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。**他テーマの更新でも毎回この処理が走る**（自転車の照合が合わないと、その回の公開候補生成全体が止まる）。
  `false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/bike-blue-ticket.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/bike-blue-ticket.html`（Git管理）。`refresh_adapters/bike.py`（アリーナ・山なみ・潮目・連動表示・検索入口）・
  `build_bike_arena.py`（引数なし）はこれを入力にする。手で編集しない。`docs/bike-blue-ticket-reaction-map.html` を旧形式の生成器に直接渡すと拒否される
  （新デザインの再入力防止。`bike_issue_media.py --write-html` も新デザインのページには書かない）。
  旧ページの検索入口（`scripts/templates/bike_blue_ticket_search_entry.html`・`docs/bike-blue-ticket-search-entry.*`）・連動表示（`bike_blue_ticket_connected*.py`・
  `docs/bike-blue-ticket-connected*`）・論点ごとのX投稿12件・アリーナの点は元HTMLの中でだけ更新され、新デザインには載せない。
  新デザインの FAQ の構造化データは、冒頭の「歩道・手信号・支払いの短答」（4問）と背景の「よくある質問」（4問）から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`bike-blue-ticket-issue-stance-v1`、論点6×立場3。前置きの1文だけ設定 `compact.vote_lead` に差し替え）・調査条件（`#caution`）・PLANET_DATA・
  **前回の収集との比較（潮目のカード。adapter の `_apply_tide` が元HTMLに貼る）**・「このページの作り方」・「詳細データ」の「注意」
  （旧体系の3表は載せない）・「次はこのテーマ」とクリック計測・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る
- **「意見の全体像」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_bike_redesign.py` が毎回そのまま写し、論点タブの上に置く。手で直す所は無い。写すときに変えるのは、連動表示の橋渡しの
  「読み込み時に件数最多の論点へ自動で着地する」処理だけ（読書面の既定の論点を、ハッシュ・履歴に触れずに選ぶ処理に置き換える。
  元HTMLの該当箇所が変わると生成が止まる）。山を押すと読書面へ移る橋渡しは `scripts/bike_redesign/planet.js`
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場別集計・投稿例・根拠の照合・
  論点の説明の2段落目（「くわしく」）・「前の収集回との違い」の累計の表、前回の収集との比較（「グラフで立場と論点の変化を見る」）、
  作り方と詳細データ（「このページの作り方と詳細データ」）の `<details>` は、`bike_reading.py`・`build_bike_redesign.py` が毎回作る
  （見出しの文言は `configs/bike-blue-ticket-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_bike_arena.py`（新デザイン公開中は、元HTMLに公開JSONの集計・論点ごとのX投稿・アリーナ・山なみと連動表示を掛けてから
  公開ページを作り直す）。成功の形: もう一度 `python3 scripts/build_bike_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_bike_redesign.py --mode release --output-dir quality/prototypes/bike-blue-ticket-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**: 定期更新では adapter が累積候補から `data/bike-blue-ticket_issues-reread.json` と
  **立場の対応表 `data/bike-blue-ticket_reread-stances.json`** を作り直し、昇格対象に含める（手作業は要らない）。
  **論点ごとの明細の件数が公開JSONの論点の件数と一致しないと新デザインの生成が止まる**（旧ページと違い「まだ読み直していない分」を残せない）。
  定期更新の外で再読データを直したとき（判定し直し・追い読み）は、毎回立場の対応表を作り直す:
  1. `python3 scripts/bike_reread_stances.py --made-on YYYY-MM-DD`（その日の日付。このスクリプトだけが非公開の正典を読む。
     成功すると `wrote data/bike-blue-ticket_reread-stances.json（N件）` か `変更なし` と出る）
  2. `python3 scripts/build_public_registry.py --topic bike-blue-ticket`
  3. 単独なら `python3 scripts/build_bike_arena.py`
  4. `python3 scripts/verify_number_provenance.py bike-blue-ticket`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
  作り直さないと「再読データの明細と立場の対応表の投稿が一致しません」などで止まる。対応表には本文・tweet_id を入れない（投稿は post_key で引く）。
  理由区分の言い換え・「どんな声か」・代表投稿2件は `configs/bike-blue-ticket-reading.json`。区分が増えたときは、その区分の `voice` も書く
- **資料にしかない話**（`data/verification/bike-blue-ticket-sunk-continents.json` の `life_impact`・`sns_note`）は画面に出る公開文章。
  adapter が `sns_note` の末尾に追加確認の記録を書き足す。直した文は1文80字以内・読点3個以内に区切り、よみやす検査
  （`python3 scripts/review_with_yomiyasu.py docs/bike-blue-ticket-reaction-map.html --medium website --strict`。成功の形: `完成を止める指摘: 0件`）を掛ける
- **確認日 `checked_on`**: 冒頭・読書面・背景の「◯月◯日時点」は `configs/bike-blue-ticket-opening.json` の `checked_on`（制度を確かめた日）1か所から出る。
  背景台帳（`data/verification/bike-blue-ticket-background.json`、2026-10-12 に「走る場所」を警察庁FAQどおりに直した）の `checked_on` より古い日付は入れられない。
  出典ごとの確認日が `checked_on` より後でも止まる。施行済み（2026-04-01）なので、読む日や基準日による文の切り替えは無い
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）・論点ごとのX投稿の単独差し込み（`bike_issue_media.py`）を
  掛けない（各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 高齢者免許返納の定期更新（新デザインを維持する、2026-10-12〜）

高齢者免許返納のページは2026-10-12から新デザイン（冒頭の「何歳から」の短答と年齢のものさし・対話式の山なみ・論点ごとの読書面・背景の開閉行）で公開する
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261012-elderly-license-revocation`）。自転車の青切符（上の節）と同じ型で、
**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-elderly-license-revocation-production-candidate.md](quality/designs/2026-10-11-elderly-license-revocation-production-candidate.md)

次回の定期更新は **2026-10-14**（THEMES.yaml の `refresh_at`）。この回で次の3つを必ず確かめる。

- **新しい意見が入った回は、追い読みしないと全テーマの公開候補生成が止まる**: 理由区分がある2論点（義務化・事故防止、地方の足・移動権）は、
  再読データ（`data/elderly-license_issues-reread.json`）の明細の件数が公開JSONの論点の件数と一致しないと新デザインの生成
  （`elderly_layout.finish`）が止まる。`finish` は**どのテーマの公開候補生成でも最後に走る**ので、高齢者の新しい意見を追い読みしないままだと、
  その回の公開候補生成全体が止まる（旧ページと違い「まだ読み直していない分」を残せない）。10/14 の回で新しい意見があれば、
  その回のうちに2論点の新しい意見を追い読みして、明細（`items`。`tweet_id`・`main_issue`・**`stance`**・`bucket`）と `buckets` の件数を足す。
  明細の `stance` は正典の `classification.stance` をそのまま書く（立場の対応表は無い。`stance` が無い明細があると adapter の
  `check_reread_stances` が「立場（stance）がありません」で止まる）。新規0件の回は公開候補を作らないので止まらない
  （2026-10-12 に隔離コピーで新規0件の 10/14 を模擬し、新デザインのまま通ることを確かめた）
- **照合「高齢ドライバーの事故は増えている」をやり直す**: 照合（2026-09-30、判定「少しずれる」）は令和7年の年間の統計に基づく。
  その後に出た令和8年上半期の統計（75歳以上の運転者による死亡事故202件、上半期どうしで2年続けて増加。一次資料メモの資料W）は、
  判定を変えずに読書面の注記（`configs/elderly-license-revocation-reading.json` の `claim_notes.increase`）で示している。
  10/14 の回で両方の統計を読み直し、照合の文（`scripts/build_elderly_process_sections.py` の FACT_CHECKS `increase` と `CHECKED_AT`）を直してから
  `python3 scripts/build_public_registry.py --topic elderly-license-revocation` を実行する（成功の形: `OK elderly-license-revocation: collected=… opinion=…`）。
  見直したら注記 `claim_notes.increase` を外す
- **取得期間は自動で伸びない**: THEMES.yaml の `sample_period_source: owner_confirmed` なので、収集した回まで `sample_period` を手で伸ばす
  （伸ばさないと公開候補生成の `verify_sample_periods.py --generate` が「取得期間の終わりが最終更新日と違う」で止まる。新デザイン以前からの動き）

その他の項目（自転車の節と同じ並び）:

- **`configs/elderly-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`elderly_layout.materialize`）、旧形式の全処理（adapter のアリーナ・潮目、finalize、山なみと連動表示、
  SEO・信頼情報・授業節・テーマ共通の見た目・他テーマの新デザイン）のあとに `elderly_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/elderly-license-revocation.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/elderly-license-revocation.html`（Git管理）。`refresh_adapters/elderly.py`（アリーナ・潮目）・
  `build_elderly_arena.py`（引数なし）・`refresh_planet_section.py`（山なみ・連動表示）はこれを入力にする。手で編集しない。
  `docs/elderly-license-revocation-reaction-map.html` を旧形式の生成器に直接渡すと拒否される（`elderly_issue_media.py --write-html` も新デザインのページには書かない）。
  旧ページの検索入口（ページ直書きの SEARCH_ENTRY・`docs/elderly-search-entry.*`）・連動表示（`elderly_connected*.py`・`docs/elderly-connected*`）・
  立場の帯（STANCE_GLANCE）・論点カード（ELDERLY_ISSUE_MEDIA）・アリーナの点は元HTMLの中でだけ更新され、新デザインには載せない。
  新デザインの FAQ の構造化データは、冒頭の「よく検索される疑問」（6問）と背景の「よくある質問」（3問）から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`elderly-license-revocation-issue-stance-v1`、論点6×立場3。前置きの文も元のまま）・調査条件（`#caution`）・PLANET_DATA・
  **前の収集回との比較（潮目のカード。adapter の `_apply_tide` が元HTMLに貼る）**・「このページの作り方」・「詳細データ」の3表
  （論点別・スタンス別・表現強度別）・「次に見るテーマ」とクリック計測・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る
- **「意見の全体像」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_elderly_redesign.py` が毎回そのまま写し、論点タブの上に置く。手で直す所は無い。写すときに変えるのは、連動表示の橋渡し
  （ELDERLY_CONNECTED_BRIDGE の `initialLand`）の「読み込み時に件数最多の論点へ自動で着地する」処理だけ（読書面の既定の論点を、ハッシュ・履歴に
  触れずに選ぶ処理に置き換える。元HTMLの該当箇所が変わると生成が止まる）。山を押すと読書面へ移る橋渡しは `scripts/elderly_redesign/planet.js`
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を開く」）・選んだ理由だけの説明・立場ごとの件数と割合・投稿の例・
  資料に照らす・論点の説明の2段落目（「くわしく」）・累計の表、前の収集回との比較（「グラフで立場と論点の変化を見る」）、
  作り方と詳細データ（「このページの作り方と詳細データ」）の `<details>` は、`elderly_reading.py`・`build_elderly_redesign.py` が毎回作る
  （見出しの文言は `configs/elderly-license-revocation-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_elderly_arena.py`（新デザイン公開中は、元HTMLに公開JSONの集計・旧形式の生成・山なみと連動表示を掛けてから
  公開ページを作り直す）。成功の形: もう一度 `python3 scripts/build_elderly_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_elderly_redesign.py --mode release --output-dir quality/prototypes/elderly-license-revocation-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**（定期更新の外の追い読み・判定し直しも同じ）:
  1. 明細（`items`）と `buckets` の件数を足す。明細には `stance` を必ず書く
  2. `python3 scripts/build_public_registry.py --topic elderly-license-revocation`
  3. 単独なら `python3 scripts/build_elderly_arena.py`
  4. `python3 scripts/verify_number_provenance.py elderly-license-revocation`（新デザインの理由区分・区分ごとの立場を明細から数え直す。成功の形: `NG 0件`）
  **未再読の4論点（適性検査強化57・自主返納支援26・代替交通整備25・その他25、計133件、2026-09-30時点）**を追い読みして、`buckets` に論点を足し、
  `configs/planet/elderly-license-revocation.yaml` の `sub_issues` にその論点を足せば、読書面の「理由は未公開」の1行は自動で理由一覧に変わる
  （そのとき設定の `issues.{論点ID}.reasons` に区分ごとの `voice` を書く。無いと「完成扱いの論点で、説明（voice）の無い理由区分があります」で止まる）
- **再読データの `population` は古いまま（注意）**: `data/elderly-license_issues-reread.json` の `population`（意見全体353・221・29）は
  2026-10-10 の追い読み前の数のまま。新デザインの生成には使っていない（論点ごとの件数は公開JSON、理由区分の件数は明細 `items` から数え直す）ので
  値は変えていない。次に追い読みしたとき、明細と一緒に直す。この数を画面や照合に使わないこと
- **資料にしかない話**（`data/verification/elderly-license-revocation-sunk-continents.json` の `life_impact`・`sns_note`）は画面に出る公開文章。
  直した文は1文80字以内・読点3個以内に区切り、よみやす検査
  （`python3 scripts/review_with_yomiyasu.py docs/elderly-license-revocation-reaction-map.html --medium website --strict`。成功の形: `完成を止める指摘: 0件`）を掛ける
- **確認日 `checked_on`**: 冒頭・読書面・背景の「◯月◯日時点」は `configs/elderly-license-revocation-opening.json` の `checked_on`（制度を確かめた日）1か所から出る。
  主張の照合日・背景台帳の確認日より古い日付は入れられない。一次資料メモの節の確認日が `checked_on` より後でも止まる。期限付きの制度イベントは無いので、
  読む日や基準日による文の切り替えは無い
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）・論点ごとのX投稿の単独差し込み（`elderly_issue_media.py`）を
  掛けない（各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 学校でのあだ名禁止の定期更新（新デザインを維持する、2026-10-13〜）

学校でのあだ名禁止のページは2026-10-13から新デザイン（冒頭の「本当に禁止なの？」「なぜ始まったの？」の短答と止める呼び方の範囲・対話式の山なみ・
論点ごとの読書面・背景の開閉行）で公開する（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261013-school-nickname-ban`）。
高齢者免許返納（上の節）と同じ型で、**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
設計と検査の記録: [quality/designs/2026-10-11-school-nickname-ban-production-candidate.md](quality/designs/2026-10-11-school-nickname-ban-production-candidate.md)

次回の定期更新は **2026-10-18**（THEMES.yaml の `refresh_at`）。9月21日以降の投稿（話題が急に増えた分）はまだ集めていない。この回で次を必ず確かめる。

- **新しい意見が入った回は、追い読みしないと全テーマの公開候補生成が止まる**: 新デザインの読書面は、6論点すべての意見を理由区分に分けた
  再読データ（`data/school-nickname-ban_issues-reread.json` の `items` と `buckets`）から作る。新しい意見が明細に無いと、更新経路の adapter
  （`refresh_adapters/nickname.py` の `build_reread_stances`）が「正典の意見のうち N 件が再読データの明細にありません（追い読みが要ります）」で止まる。
  複数テーマをまとめて作る回（`prepare_public_candidate_bundle_multi`）にあだ名禁止が入っていれば、**その回の全テーマの公開候補生成が止まる**。
  また、どのテーマの公開候補生成でも最後に `nickname_layout.finish` が再読データ・立場の対応表・公開JSONの件数を照合するので、
  手で正典や再読データを動かして食い違ったままだと、他テーマの回も止まる（旧ページの「人が読む工程なし」は新デザインでは成り立たない）。10/18 の回で新しい意見があれば、
  その回のうちに新しい意見を1件ずつ読み、明細（`post_key`＝tweet_id の sha256・`main_issue`・`bucket`）を足し、`buckets` の件数を足す。
  新しい理由区分を作ったら `configs/school-nickname-ban-reading.json` の `issues.{論点ID}.reasons` に区分ごとの `voice` を書く。
  **立場の対応表（`data/school-nickname-ban_reread-stances.json`）は更新経路の adapter が累積候補から作り直して公開対象に含める**ので、
  定期更新の中では手で作らない（自転車の青切符と同じ）。新規0件の回は公開候補を作らないので止まらない
  （2026-10-13 に、切替後の作業ツリーの隔離コピーで新規0件相当の 10/18 の回を adapter から公開候補生成まで通し、新デザインのまま通ることを確かめた）
- **「その他」に件数が出たら**: 「その他」が0件のあいだは、読書面のタブも欄も出さない。公開JSONで1件以上になれば自動で最後に出る
  （理由区分が無ければ「理由は未公開」と出る。理由区分を足すには、`configs/planet/school-nickname-ban.yaml` の `sub_issues` に「その他」を足し、
  再読データの `buckets` に論点を足す）
- **理由区分が4を超える論点が出たら**: 「ほかの理由を読む（残りN分類）」の折りたたみが自動で出る（上位4つを一覧に出す。`compact.top_reasons`）

その他の項目（高齢者の節と同じ並び）:

- **`configs/nickname-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`nickname_layout.materialize`）、旧形式の全処理（adapter のアリーナの点・潮目・立場の対応表、finalize、
  SEO・信頼情報・授業節・テーマ共通の見た目・他テーマの新デザイン）のあとに `nickname_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/school-nickname-ban.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/school-nickname-ban.html`（Git管理）。`refresh_adapters/nickname.py`（山なみの件数・潮目・連動表示・アリーナの点）・
  `build_nickname_arena.py`（引数なし）はこれを入力にする。手で編集しない。`docs/school-nickname-ban-reaction-map.html` を旧形式の生成器に
  直接渡すと拒否される（`nickname_issue_media.py --write-html` も新デザインのページには書かない）。旧ページの検索入口（SCHOOL_NICKNAME_SEARCH_ENTRY）・
  連動表示（`school_nickname_connected*.py`・`docs/school-nickname-connected*`）・立場の帯（STANCE_GLANCE）・論点カード（NICKNAME_ISSUE_MEDIA）・
  旧FAQ（SCHOOL_NICKNAME_FAQ）は元HTMLの中でだけ更新され、新デザインには載せない。**アリーナの点（`docs/school-nickname-ban-arena-data.js`）は
  新デザインでは読み込まないが、更新経路と `build_nickname_arena.py` で引き続き生成され、公開対象に入る**（元HTMLの旧形式の部品が読む）。
  新デザインの FAQ の構造化データは、画面に出ている問い（冒頭の短答2問と背景の「よくある質問」4問）から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`school-nickname-ban-issue-stance-v1`、論点6×立場3。論点と立場の定義・前置きの文も元のまま。投票の後に旧ページにも無い `#issue-arena-section` へ
  移ろうとして止まる1文だけを外す。元HTMLのこの1文が変わると生成が止まる）・調査条件（`#caution`）・PLANET_DATA・
  **前の収集回との比較（潮目のカード。adapter の `_apply_tide` が元HTMLに貼る）**・「このページの作り方」・「調査上の注意」（`#detail-data`。表は無い）・
  「次に読むテーマ」とクリック計測・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る
- **「意見の全体像」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_nickname_redesign.py` が毎回そのまま写し、論点タブの上に置く。手で直す所は無い。写すときに変えるのは、連動表示の橋渡し
  （SCHOOL_NICKNAME_CONNECTED_BRIDGE の `initialLand`）の「読み込み時に件数最多の論点へ自動で着地する」処理だけ（読書面の既定の論点を、
  ハッシュ・履歴に触れずに選ぶ処理に置き換える。元HTMLの該当箇所が変わると生成が止まる）。山を押すと読書面へ移る橋渡しは `scripts/nickname_redesign/planet.js`。
  意見が100件と少ないので、細すぎて押せない山を広げた注記が出る（2026-10-13：すべて＝本人意思・柔軟運用、一律禁止に反対＝いじめ・心理的安全と学校運用・現場体験、
  中立・情報＝一律禁止の実効性とさん付け・ジェンダー配慮）。山なみの生成器が自動で出す注記なので、件数が変われば変わる
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場ごとの件数と割合・投稿の例・
  資料に照らす・論点の説明の2段落目（「くわしく」）・累計の表、前の収集回との比較（「折れ線で、立場と論点の動きを確かめる」）、
  作り方と調査上の注意（「このページの作り方と、調査上の注意」）の `<details>` は、`nickname_reading.py`・`build_nickname_redesign.py` が毎回作る
  （見出しの文言は `configs/school-nickname-ban-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_nickname_arena.py`（新デザイン公開中は、元HTMLに旧形式の生成（山なみの件数・連動表示・アリーナの点）と公開JSONの集計を掛けてから
  公開ページを作り直す）。成功の形: もう一度 `python3 scripts/build_nickname_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_nickname_redesign.py --mode release --output-dir quality/prototypes/school-nickname-ban-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**（定期更新の外の追い読み・判定し直しも同じ）:
  1. 明細（`items`）と `buckets` の件数を足す
  2. `python3 scripts/nickname_reread_stances.py --made-on YYYY-MM-DD`（定期更新の外では立場の対応表を手で作り直す。成功の形: `wrote data/school-nickname-ban_reread-stances.json（N件）` か `変更なし`）
  3. `python3 scripts/build_public_registry.py --topic school-nickname-ban`
  4. 単独なら `python3 scripts/build_nickname_arena.py`
  5. `python3 scripts/verify_number_provenance.py school-nickname-ban`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
- **相談窓口の電話番号**: 24時間こどもSOSダイヤルの番号は冒頭の設定 `safety.phone` の1か所。冒頭の「今、嫌な呼び方でつらい場合」と背景の相談先の行の両方に出る。
  番号を確かめ直したら、一次資料メモに追記して `checked_on` を進める
- **確認日 `checked_on`**: 冒頭・読書面・背景の「◯月◯日時点」は `configs/school-nickname-ban-opening.json` の `checked_on`（国の資料を確かめた日）1か所から出る。
  背景台帳の確認日より古い日付は入れられない。期限付きの制度イベントは無いので、読む日や基準日による文の切り替えは無い
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）・論点カードの単独差し込み（`nickname_issue_media.py`）を
  掛けない（各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 辺野古高校生死亡事故の定期更新（新デザインを維持する、2026-10-13〜）

辺野古高校生死亡事故のページは2026-10-13から新デザイン（冒頭の「何があった？」「原因は分かった？」「何が争点？」の短答とSNSの意見の件数・
対話式の山なみ・論点ごとの読書面・背景の開閉行）で公開する（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261013-henoko-student-accident`）。
学校でのあだ名禁止（上の節）と同じ型で、**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
標準の `--prepare-promotion` の手順（上の「辺野古の定期更新」の節）は変わらない。
設計と検査の記録: [quality/designs/2026-10-11-henoko-student-accident-production-candidate.md](quality/designs/2026-10-11-henoko-student-accident-production-candidate.md)

次回の定期更新は **2026-10-22**（THEMES.yaml の `refresh_at`）。10月8日以降の投稿はまだ集めていない。この回で次を必ず確かめる。

- **新しい意見が入った回は、追い読みしないと全テーマの公開候補生成が止まる**: 新デザインの読書面は、6論点すべての意見を理由区分に分けた
  再読データ（`data/henoko-student-accident_issues-reread.json` の `items` と `buckets`）から作る。新しい意見が明細に無いと、更新経路の adapter
  （`refresh_adapters/henoko.py` の `build_reread_stances`）が「正典の意見のうち N 件が再読データの明細にありません（追い読みが要ります）」で止まる。
  複数テーマをまとめて作る回（`prepare_public_candidate_bundle_multi`）に辺野古が入っていれば、**その回の全テーマの公開候補生成が止まる**。
  また、どのテーマの公開候補生成でも最後に `henoko_layout.finish` が再読データ・立場の対応表・公開JSONの件数を照合するので、
  手で正典や再読データを動かして食い違ったままだと、他テーマの回も止まる。10/22 の回で新しい意見があれば、
  その回のうちに新しい意見を1件ずつ読み、明細（`post_key`＝tweet_id の sha256・`main_issue`・`bucket`）を足し、`buckets` の件数を足す
  （上の「定期更新1回分の実務手順」の追い読みと同じ。`manage_reread_registry.py` の記録も同じ回で）。
  新しい理由区分を作ったら `configs/henoko-student-accident-reading.json` の `issues.{論点ID}.reasons` に区分ごとの `voice` を書く
  （「遺族」「氏名」など配慮で避けた語を区分名に使うときは、冒頭の設定 `count.reason_label_overrides` で表示名を言い換える）。
  **立場の対応表（`data/henoko-student-accident_reread-stances.json`）は更新経路の adapter が累積候補から作り直して公開対象に含める**ので、
  定期更新の中では手で作らない（あだ名禁止・自転車の青切符と同じ）。新規0件の回は公開候補を作らないので止まらない
  （2026-10-13 に、切替後の作業ツリーの隔離コピーで新規0件相当の 10/22 の回を adapter から公開候補生成まで通し、新デザインのまま通ることを確かめた。
  公開ページは最終更新日 10月22日・次の収集 11月5日、他テーマの新デザイン9ページは変わらず、候補の中で検査はすべて合格）
- **語られていない争点の母数**（`data/verification/henoko-student-accident-sunk-continents.json` の `sns_base`）は、上の「辺野古の定期更新」の節のとおり
  新しい意見で再検索してから直す。`sns_note` は画面に出る公開文章なので、追記したらよみやす検査（`review_with_yomiyasu.py --medium website --strict`）を
  新デザインのページに掛ける。船名・氏名・学校名を書かない
- **「その他」に件数が出たら**: 「その他」が0件のあいだは、読書面のタブも欄も出さない。公開JSONで1件以上になれば自動で最後に出る
  （理由区分が無ければ「理由は未公開」と出る。理由区分を足すには、`configs/planet/henoko-student-accident.yaml` の `sub_issues` に「その他」を足し、
  再読データの `buckets` に論点を足す）
- **理由区分が4を超える論点が出たら**: 「ほかの理由を読む（残りN分類）」の折りたたみが自動で出る（上位4つを一覧に出す。`compact.top_reasons`）

その他の項目（あだ名禁止の節と同じ並び）:

- **`configs/henoko-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`henoko_layout.materialize`）、旧形式の全処理（adapter の山なみ・アリーナの点・潮目・立場の対応表、finalize、
  SEO・信頼情報・授業節・テーマ共通の見た目・他テーマの新デザイン）のあとに `henoko_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/henoko-student-accident.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/henoko-student-accident.html`（Git管理）。`refresh_adapters/henoko.py`（山なみの件数・潮目・連動表示・アリーナの点）・
  `build_henoko_arena.py`（引数なし）はこれを入力にする。手で編集しない。`docs/henoko-student-accident-reaction-map.html` を旧形式の生成器に
  直接渡すと拒否される（`build_henoko_arena.py --public-counts-only` に新デザインのページを渡しても止まる）。旧ページの検索入口（HENOKO_SEARCH_ENTRY・
  `docs/henoko-search-entry.*`）・連動表示（`henoko_connected*.py`・`docs/henoko-connected*`）・立場の帯（STANCE_GLANCE）・背景パネル（`#bukatsu-background`・
  `#bukatsu-check`）・旧FAQ は元HTMLの中でだけ更新され、新デザインには載せない。**アリーナの点（`docs/henoko-arena-data.js`）は
  新デザインでは読み込まないが、更新経路と `build_henoko_arena.py` で引き続き生成され、公開対象に入る**（元HTMLの旧形式の部品が読む）。
  山なみの入力の版の守り（`henoko_planet_guard.py`。候補が正典を書き換えていないか、公開JSONと候補が同じ版か）は、元HTMLへの旧形式の生成の途中で
  これまでどおり働く。新デザインの FAQ の構造化データは、画面に出ている問い（冒頭の短答3問と背景の「よくある質問」4問）から毎回作り直す
- **新デザインが元HTMLから文字どおり引き継ぐもの**: SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`henoko-student-accident-issue-stance-v1`、論点6×立場3。TOPIC・ISSUES・STANCES と前置きの文は元のまま。保存キーは本番ホストだけ既存キー。
  元HTMLの保存キーか choiceIdx の計算が変わると生成が止まる。論点ボタンの絵文字は CSS で隠す）・調査条件（`#caution`）・PLANET_DATA・
  **前の収集回との比較（潮目のカード。adapter の `_apply_tide` が元HTMLに貼る）**・「このページの作り方」・詳細データの「注意」・
  「次に読むテーマ」とクリック計測・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る。
  **詳細データの表は公開JSONの4立場で毎回作り直す**（元HTMLの表は投票の3区分で「保留448」とまとめていて、新ページでは使わない）
- **「論点ごとに読む」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_henoko_redesign.py` が毎回そのまま写し、論点タブの上に置く。手で直す所は無い。写すときに変えるのは、連動表示の橋渡し
  （HENOKO_CONNECTED_BRIDGE の `initialLand`）の「読み込み時に件数最多の論点へ自動で着地する」処理（読書面の既定の論点を、
  ハッシュ・履歴に触れずに選ぶ処理に置き換える。元HTMLの該当箇所が変わると生成が止まる）と、論点の絵文字を表示の直前に空にすること
  （浮き輪などの絵文字は船・海の図柄に当たるので使わない。PLANET_DATA は変えない）。山を押すと読書面へ移る橋渡しは `scripts/henoko_redesign/planet.js`。
  「論点を切り分ける」が意見の9割なので、その立場を選ぶと政治的中立性・平和教育の萎縮が細すぎて広げて描く注記が出る（山なみの生成器が自動で出す）
- **配慮の基準と本文確認の工程**: 人が亡くなった事故のテーマ。設定・台帳・照合文・投稿の要約に、亡くなった方の氏名・性別・学年、学校名、船名、
  船長の氏名、遺族への言及、事故の生々しい描写、煽る表現、名指しの批判を書かない（冒頭の設計記録「被害者への配慮で避けた表現」）。
  文を足したり直したりしたら、`python3 -m unittest tests.test_henoko_redesign` を流す（避けた語のリスト `AVOID` が、新ページの見えている文字に無いことを確かめる）。
  機械が見るのは語のリストだけなので、**写した部品（山なみ・潮目のカード・作り方）と新しく足した文は、人が本文を読んで確かめる**。
  代表投稿を差し替えるときは、設定 `posts_common._selection_rule` の基準で本文を読んで選ぶ（機械の条件だけでは足りない）
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場ごとの件数と割合・投稿の例・
  公的機関の資料に照らす・論点の説明の2段落目（「くわしく」）・累計の表、前の収集回との比較（「2回の収集を比べたグラフを開く」）、
  作り方と詳細データ（「集め方と分類、詳しい集計表」）の `<details>` は、`henoko_reading.py`・`build_henoko_redesign.py` が毎回作る
  （見出しの文言は `configs/henoko-student-accident-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_henoko_arena.py`（新デザイン公開中は、元HTMLに旧形式の生成（山なみの件数・連動表示・アリーナの点）と公開JSONの集計を掛けてから
  公開ページを作り直す）。成功の形: もう一度 `python3 scripts/build_henoko_arena.py --check` を実行して `OK: 差分なし` と出ること。
  公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_henoko_redesign.py --mode release --output-dir quality/prototypes/henoko-student-accident-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**（定期更新の外の追い読み・判定し直しも同じ）:
  1. 明細（`items`）と `buckets` の件数を足す
  2. `python3 scripts/henoko_reread_stances.py --made-on YYYY-MM-DD`（定期更新の外では立場の対応表を手で作り直す。成功の形: `wrote data/henoko-student-accident_reread-stances.json（N件）` か `変更なし`）
  3. `python3 scripts/build_public_registry.py --topic henoko-student-accident`
  4. 単独なら `python3 scripts/build_henoko_arena.py`
  5. `python3 scripts/verify_number_provenance.py henoko-student-accident`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
- **確認日 `checked_on`**: 冒頭・読書面・背景の「◯月◯日時点」は `configs/henoko-student-accident-opening.json` の `checked_on`（公的機関の資料を確かめた日）1か所から出る。
  背景台帳（`data/verification/henoko-student-accident-background.json`）の確認日より古い日付は入れられない。資料を確かめ直したら、一次資料メモに追記してから進める
- **報告書の公表 `report`**: 運輸安全委員会の事故調査報告書が公表されたら、冒頭の設定 `report.published_on` に公表日を入れる
  （冒頭の短答「原因は分かった？」・背景の公表の行・まだ確かめていないこと・FAQ の構造化データが「◯月◯日に公表されました。内容は編集部で確認しているところです」に変わる）。
  内容を読んだら `report.content_checked_on` に読んだ日を入れる（「…編集部が内容を確かめました」に変わり、まだ確かめていないことから報告書の行が消える）。
  公表日が `checked_on` より後、読んだ日が公表日より前などは生成が止まる。報告書の中身を年表や短答に足すかはオーナーが判断する
- **年表**: 新デザインの年表の正本は冒頭の設定 `timeline.entries`。背景台帳の `timeline` は元HTML（旧ページ）だけが読む。直すときは両方を同じ中身にする
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・潮目の単独差し込み（`inject_tide_widget.py`）を
  掛けない（各スクリプトが skipped／SKIP／停止と出す）。更新経路では元HTMLに掛かる

### 消費税減税の定期更新（新デザインを維持する、2026-10-13〜）

消費税減税のページは2026-10-13から新デザイン（冒頭の「いつから・何%・いつまで？」「1%と給付付き税額控除とは？」「何が1%になる？」の短答・
レシートの計算・段階図・SNSの意見の件数・対話式の山なみ・7論点の読書面・10回分の推移の要約・背景の開閉行）で公開する
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261013-consumption-tax-cut`）。
辺野古（上の節）と同じ型で、**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
収集・本文確認・`--prepare-promotion` の手順（`theme-refresh` スキル）は変わらない。
設計と検査の記録: [quality/designs/2026-10-13-consumption-tax-cut-production-candidate.md](quality/designs/2026-10-13-consumption-tax-cut-production-candidate.md)

次回の定期更新は **2026-10-20**（THEMES.yaml の `collect_at`）。10月10日以降の投稿はまだ集めていない。この回で次を必ず確かめる。

- **新しい意見が4論点に入った回は、追い読みしないと全テーマの公開候補生成が止まる**: 新デザインの読書面は、理由区分のある4論点
  （減税の対象範囲・減税の効果・給付など他策との比較・事業者の実務負担）の意見を、再読データ（`data/consumption-tax-cut_4issues-reread.json` の
  論点ごとの `items`・`excluded_items`・`buckets`）から数える。新しい意見が明細に無いと、更新経路の adapter（`refresh_adapters/consumption_tax.py` の
  `build_reread_stances`）が「正典の意見のうち N 件が再読データの明細にありません（追い読みが要ります）」で止まる。
  複数テーマをまとめて作る回に消費税減税が入っていれば、**その回の全テーマの公開候補生成が止まる**。また、どのテーマの公開候補生成でも最後に
  `consumption_tax_layout.finish` が再読データ・立場の対応表・公開JSONの件数を照合するので、手で正典や再読データを動かして食い違ったままだと、他テーマの回も止まる。
  10/20 の回で4論点に新しい意見があれば、その回のうちに1件ずつ読み、明細（`tweet_id`・`bucket`。どの区分にも当てはまらなければ `excluded_items`）と
  `buckets` の件数を足す（10/11 の回と同じ。`themes/consumption-tax-cut.md` の 10/11 の節）。新しい理由区分を作ったら
  `configs/consumption-tax-cut-reading.json` の `issues.{論点ID}.reasons` に区分ごとの `voice` を書く（書くまで生成が止まる）。
  **立場の対応表（`data/consumption-tax-cut_reread-stances.json`）は更新経路の adapter が累積候補から作り直して公開対象に含める**ので、
  定期更新の中では手で作らない（明細の `stance` は読み直したときの記録で、正典と違うものがある。読書面は対応表の立場だけを使う）。
  新規0件の回は公開候補を作らないので止まらない（2026-10-13 に、切替後の作業ツリーの隔離コピーで新規0件相当の 10/20 の回を adapter から
  公開候補生成まで通し、新デザインのまま通ることを確かめた。公開ページは最終更新日 10月20日・次の更新予定 10月27日、他テーマの新デザイン9ページは変わらず、
  候補の中で検査はすべて合格）
- **「理由は未公開」の3論点**（選挙の約束・財源と社会保障・その他）: 再読データと `configs/planet/consumption-tax-cut.yaml` の `sub_issues` に
  論点を足して追い読みすれば、冒頭の件数欄の「理由は未公開」と読書面の「未公開」の表示は自動で消え、理由の一覧に変わる
  （区分ごとの `voice` を書くまで生成は止まる）
- **分類AIが変わった回**: 推移の注意書きの記録（`scripts/build_trend_section.py` の `TREND_THEMES["consumption-tax-cut"]["model_breaks"]`。
  2026-10-03 の kimi-k2.7-code への切替を立場・論点とも登録済み）に日付を足すまで adapter が止まる。足すと推移のカードと、ひと目の要約の注記に出る
- **主張の照合の該当投稿数**が変わったら `data/consumption-tax-cut_claim_posts.json` との照合で止まる（読書面の生成器）。照合日は
  `build_consumption_tax_page.py` の `CHECKED_ON`（公開JSON `claim_verification.checked_on` の元。ここだけが正）

その他の項目（辺野古の節と同じ並び）:

- **`configs/consumption-tax-layout.json` の `enabled`**: `true` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`consumption_tax_layout.materialize`）、旧形式の全処理（adapter のページ生成・意見の推移・立場の対応表・推移の画像、
  finalize、SEO・信頼情報・授業節・テーマ共通の見た目・他テーマの新デザイン）のあとに `consumption_tax_layout.finish` で元HTMLを保存し直してから
  新デザインのページを `docs/` に書く。`false` に戻すと、公開ページが新デザインのまま「更新設定が無効」で止まる。戻すときは旧形式のページ
  （`data/page-sources/consumption-tax-cut.html`）を先に `docs/` へ戻すこと
- **元HTMLの場所**: `data/page-sources/consumption-tax-cut.html`（Git管理）。`refresh_adapters/consumption_tax.py`・`build_consumption_tax_page.py`（引数なし）は
  これを入力にする。手で編集しない。`docs/consumption-tax-cut-reaction-map.html` を旧形式の生成器に渡すと拒否される（部分更新の `--conditions-only` など、
  `build_trend_section.py --apply` も止まる）。旧ページの検索入口（TAX_SEARCH_ENTRY・`docs/consumption-tax-search-entry.*`。税率を直書きした計算部品）・
  連動表示（`consumption_tax_connected*.py`・`docs/consumption-tax-connected*`）・立場の帯・論点カード・主張の照合の一覧・背景パネル・旧FAQ は元HTMLの中でだけ
  更新され、新デザインには載せない。**新デザインのレシートの税率と注記は冒頭の設定 `rates`・`calc` だけが正**。新デザインの FAQ の構造化データは、
  画面に出ている問い（冒頭の短答3問と背景の「よくある質問」）から毎回作る
- **新デザインが元HTMLから文字どおり引き継ぐもの**: title・meta description（課題96の判定 10/27 まで変えない）・SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`consumption-tax-cut-issue-stance-v1`、論点7×立場4。VOTE_ISSUES・STANCES・CHOICES と前置きの文は元のまま。保存キーは本番ホストだけ既存キー。
  元HTMLの保存キーか choiceIdx の計算が変わると生成が止まる）・調査条件（`#caution`）・PLANET_DATA・**意見の推移（TREND_CARD。adapter の `_apply_trend` が
  元HTMLに貼る。外部の埋め込みコードが指す `#consumption-tax-cut-trend-panel-stance`・`-issue` を含む。id が変わると生成が止まる）**・「このページの作り方」・
  詳細データ（表の件数が公開JSONと違うと止まる）・「次に読むテーマ」とクリック計測・フッター。数字が古いときは元HTML側（adapter・`apply_theme_trust.py`）で直る
- **「論点ごとに読む」の山なみ**: 元HTMLの対話式の山なみ（`PLANET_SECTION` の `#planet-block`・PLANET_DATA・山なみのスクリプト）を
  `build_consumption_tax_redesign.py` が毎回そのまま写し、論点タブの上に置く。写すときに変えるのは、初期化の「URL の論点へ着地する」処理の後ろに
  「ハッシュが無いときは読書面の既定の論点（件数1位）を、ハッシュ・履歴に触れずに選ぶ」処理を足すことだけ（元HTMLの該当箇所が変わると生成が止まる）。
  連動表示の本体は読み込まないので、橋渡し（TAX_CONNECTED_BRIDGE）は旧来の動きのまま。山を押すと読書面へ移る橋渡しは `scripts/consumption_tax_redesign/planet.js`
- **推移の要約**: 10回分の推移のカードを折りたたみ（「N回分の折れ線と表を開く」）に1文字も変えずに入れ、上に立場4本の小さな折れ線・前回から今回への1行・
  注記1行（1回あたりの件数とぶれ・古い投稿の混入・分類AIの切替。数字と日付は推移の注意書きから写す）を置く。各論点の「回ごとの動き」も同じ数字から描く
- **折りたたみ（部活動型の圧縮）**: 読書面の理由一覧（上位4件＋「ほかの理由を読む」）・選んだ理由だけの説明・立場ごとの件数と割合・投稿の例・資料に照らす・
  論点の説明の2段落目・累計の表、推移、作り方と詳細データ（「集め方と分類、全部の集計表」）の `<details>` は、`consumption_tax_reading.py`・
  `build_consumption_tax_redesign.py` が毎回作る（見出しの文言は `configs/consumption-tax-cut-reading.json` の `compact`）
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）:
  `python3 scripts/build_consumption_tax_page.py`（新デザイン公開中は、元HTMLに旧形式の生成（ページ生成・意見の推移・調査条件・公開JSONの集計と山なみ・
  テーマ共通の見た目）を掛けてから公開ページを作り直す。非公開の正典が要る）。成功の形: もう一度
  `python3 scripts/build_consumption_tax_page.py --check` を実行して `OK: 差分なし` と出ること。公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_consumption_tax_redesign.py --mode release --output-dir quality/prototypes/consumption-tax-cut-release`
  （成功の形: `Built 1 file (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**（定期更新の外の追い読み・判定し直しも同じ）:
  1. 明細（`items`・`excluded_items`）と `buckets` の件数を足す
  2. `python3 scripts/consumption_tax_reread_stances.py --made-on YYYY-MM-DD`（定期更新の外では立場の対応表を手で作り直す。成功の形: `wrote data/consumption-tax-cut_reread-stances.json（N件）` か `変更なし`）
  3. `python3 scripts/build_public_registry.py --topic consumption-tax-cut`
  4. 単独なら `python3 scripts/build_consumption_tax_page.py`
  5. `python3 scripts/verify_number_provenance.py consumption-tax-cut`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
- **確認日 `checked_on`**: 冒頭・読書面・背景の「◯月◯日の時点」と制度の確認日は `configs/consumption-tax-cut-opening.json` の `checked_on` 1か所から出る。
  一次資料メモの節の確認日より新しく、法律案の提出日（`law.bill_on`）より後の節だけを読書面の制度の確認に使える（外れると生成が止まる）
- **法律の段階 `law`**: 国会で成立したら、衆議院の審議経過で確かめて `law.enacted_on`（成立日）・`law.promulgated_on`（公布日）・`checked_on` を入れ、
  一次資料メモに成立を確かめた節を足して、読書面の `issues.consumption-tax-cut-political-trust.memo_checks[trust-status].memo_section` をその節にする
  （しないと生成が止まる）。冒頭の段階・短答・レシートの見出し・段階図・背景の「決まったこと」・年表・まだ確かめていないこと・制度の確認の文がまとめて切り替わる
  （成立後・引下げ中・終了・成立未確認の4段階を `--as-of` で確かめるテストあり）。title・description は課題96の判定（10/27）まで変えない
- **年表**: 新デザインの年表は冒頭の設定 `steps`・`law` と背景の設定 `configs/consumption-tax-cut-background.json` から作る。旧ページの年表
  （`configs/consumption-tax-background.json`）は元HTMLと推移のグラフの縦線（出来事）が読む。10/9 の法律案は旧ページ側には足していない
- **構造化データの更新日**: Article の `dateModified` は `configs/theme-seo.json` の `dateModified`（更新経路の `update_seo_date` が書く）1か所から出る
  （`build_consumption_tax_page.py` の手入力の `MODIFIED_AT` は 2026-10-13 に外した）
- 新デザインのページには、テーマ共通の見た目（`apply_theme_design.py`）・授業節の単独適用・信頼情報の単独適用・
  山なみの単独更新（`refresh_planet_section.py`）・推移の単独差し込み（`build_trend_section.py --apply`）を
  掛けない（各スクリプトが skipped／停止と出す）。更新経路では元HTMLに掛かる

### 部活動の地域移行の定期更新（新デザインを維持する、最新の型、2026-10-14〜）

部活動のページは2026-10-10に初期型の新デザインで公開し、2026-10-14に最新の型（冒頭の「いつから？」「費用はいくら？」「何が問題？」の短答・
改革の期間と段の一覧・SNSの意見の件数・対話式の山なみ・7論点の読書面・13回分の推移の要約・背景の開閉行7行）に組み替えた
（公開切替はオーナー承認待ち。`company/APPROVALS.yaml` の `approval-20261014-bukatsu-chiiki-v2`）。
消費税減税（上の節）と同じ型で、**旧形式の生成器はこれまでどおり「元HTML」に掛け、全生成の最後に新デザインを組み直す。**
収集・本文確認・`--prepare-promotion` の手順（`theme-refresh` スキル）は変わらない。
設計と検査の記録: [quality/designs/2026-10-14-bukatsu-chiiki-production-candidate.md](quality/designs/2026-10-14-bukatsu-chiiki-production-candidate.md)

次回の定期更新は **2026-10-17**（THEMES.yaml の `collect_at`）。この回で次を必ず確かめる。

- **初期型の指紋は使わない**: 初期型（2026-10-10〜10-14）は、元HTMLの集計が1件でも変わると `scripts/bukatsu_redesign/editorial-review.json` の
  指紋で止まった。最新の型は指紋を持たず、下の照合が合えば作れる（`editorial-review.json`・`editorial-source.html`・`template.html`・`parity.*`・
  `refresh_inputs.py`・`build.py`・`app.js` は初期型の経路にだけ残し、最新の型は読まない）
- **新しい意見が5論点に入った回は、追い読みしないと全テーマの公開候補生成が止まる**: 新デザインの読書面は、理由区分のある5論点
  （教員の働き方・制度・移行プロセス・教育的意義・機会・受け皿・指導者・費用・家庭負担）の意見を、再読データ3ファイル
  （`data/bukatsu-chiiki_teacher-reread.json`・`data/bukatsu-chiiki_cost-receiver-reread.json`・`data/verification/bukatsu-chiiki-plan-child-subissues.json`。
  どこにあるかは `configs/planet/bukatsu-chiiki.yaml` の `sub_issues`）の明細から数える。新しい意見が明細に無いと、更新経路の adapter
  （`refresh_adapters/bukatsu.py` の `build_reread_stances`）が「正典の意見のうち N 件が再読データの明細にありません（追い読みが要ります）」で止まる。
  10/17 の回で5論点に新しい意見があれば、その回のうちに1件ずつ読み、明細（`tweet_id`・`bucket`。どの区分にも当てはまらなければ
  `configs/bukatsu-chiiki-reading.json` の `excluded_buckets` に書いた区分）と `buckets` の件数を足す（10/10 の追い読みと同じ）。
  **件数の上位4件の理由が入れ替わったら**、新しく上位に入った区分の `voice`（どんな声か）と `reasons_read`（読んだ件数）を
  `configs/bukatsu-chiiki-reading.json` の `issues.{論点ID}.reasons` に書くまで生成が止まる。新しい理由区分を作ったときも同じ。
  **立場の対応表（`data/bukatsu-chiiki_reread-stances.json`）は更新経路の adapter が累積候補から作り直して公開対象に含める**ので、
  定期更新の中では手で作らない（明細の `stance` は読み直したときの記録で、308件が正典と違う。読書面は対応表の立場だけを使う）。
  新規0件の回は公開候補を作らないので止まらない（2026-10-14 に、切替後の作業ツリーの隔離コピーで新規0件相当の 10/17 の回を adapter から
  公開候補生成まで通し、新デザインのまま通ることを確かめた。公開ページの基準日は 10月17日、他テーマの新デザイン9ページは変わらず、候補の中で検査はすべて合格）
- **「理由は未公開」の2論点**（住む地域で差が出る・その他）: 再読データと `configs/planet/bukatsu-chiiki.yaml` の `sub_issues` に論点を足して
  追い読みすれば、冒頭の件数欄の「理由は未公開」と読書面の「未公開」の表示は自動で消え、理由の一覧に変わる（`voice` を書くまで生成は止まる）
- **分類AIが変わった回**: 推移の注意書きの記録（`scripts/build_trend_section.py` の `TREND_THEMES["bukatsu-chiiki"]["model_breaks"]`。
  2026-10-01 の切替は論点だけに登録済み）に日付を足すまで adapter が止まる。立場の推移に記録があれば、ひと目の要約の注記にも出る
- **主張の照合の該当投稿数**が変わったら `data/bukatsu-chiiki_claim_posts.json` との照合で止まる（読書面の生成器）
- **資料にしかない話の母数**（`data/verification/bukatsu-chiiki-sunk-continents.json` の `sns_base`）が意見数と違うと止まる。
  増えた分を検索し直して再確認の記録を足し、`sns_base` を直す（これまでの各回と同じ）

その他の項目（消費税減税の節と同じ並び）:

- **`configs/bukatsu-layout.json`**: `enabled: true` かつ `version: "redesign-v2"` の間、`refresh_topic.py` の公開候補生成（単一・複数テーマ）は
  隔離コピーで元HTMLを `docs/` に戻し（`bukatsu_layout.materialize`）、旧形式の全処理（adapter のページ生成・意見の推移・立場の対応表・推移の画像、
  finalize の `refresh_planet_section.py`・`build_bukatsu_arena.py`、SEO・信頼情報・授業節）のあとに `bukatsu_layout.finish` で元HTMLを保存し直してから、
  新デザインのページと全文・印刷版（`docs/bukatsu-chiiki-full.html`）を `docs/` に書く。`version` を外すと初期型に戻る（下の「初期型に戻すとき」）
- **元HTMLの場所**: `data/page-sources/bukatsu-chiiki.html`（Git管理）。adapter・`build_bukatsu_arena.py`（引数なし）はこれを入力にする。手で編集しない。
  旧形式の連動表示（`bukatsu_connected*.py`・`docs/bukatsu-connected*`）・立場の帯・検索入口・旧FAQ（`SEARCH_FAQ_JSONLD`）・編集部の横断整理は
  元HTMLの中でだけ更新され、新デザインには載せない。新デザインの FAQ の構造化データは背景の「よくある質問」と同じ設定の items から作り、画面と違えば止まる
- **新デザインが元HTMLから文字どおり引き継ぐもの**: title・meta description・SEOメタ・Article の構造化データ・GA4・AdSense・投票
  （`bukatsu-chiiki-issue-stance-v1`、論点7×立場3。VOTE_ISSUES・V2I・STANCES・前置きと保存の注記の文は元のまま。保存キーは本番ホストだけ既存キー。
  元HTMLの保存キーか choiceIdx の計算か保存の注記が変わると生成が止まる）・調査条件（`#caution`）・PLANET_DATA・**意見の推移（TREND_CARD。外部の
  埋め込みコードが指す `#bukatsu-chiiki-trend-panel-stance`・`-issue` を含む。id が変わると生成が止まる）**・「このページの作り方」・詳細データ
  （表の件数が公開JSONと違うと止まる）・「次に読むテーマ」とクリック計測・フッター
- **「論点ごとに読む」の山なみ**: 元HTMLの対話式の山なみを `build_bukatsu_redesign_v2.py` が毎回写し、論点タブの上に置く。写すときに変えるのは
  山なみのスクリプトの3か所（URL を素の論点IDに書き換えない・読み込み時の画面を動かす着地を外す・画面を動かさない着地でフォーカスを残す。
  `PLANET_PATCHES`。元HTMLの該当箇所が変わると生成が止まる）だけ。山を押すと読書面へ移る橋渡しは `scripts/bukatsu_redesign/planet_v2.js`
- **推移の要約**: 13回分の推移のカードを折りたたみに1文字も変えずに入れ、上に立場4本の小さな折れ線・最初と最新の回で最も多かった立場の1行・
  注記1行（1回あたりの件数とぶれ・古い投稿の混入。数字は推移の立場の注意書きから写す）を置く。論点ごとの「ひと目で見る、この論点の推移」は
  同じ元HTMLの推移から `glance_chart.py` で描く
- **単独で作り直すとき**（データは変えずに見た目や文言だけ直したとき）: `python3 scripts/build_bukatsu_arena.py`（新デザイン公開中は、
  元HTMLに旧形式の生成を掛けてから公開ページと全文・印刷版を作り直す。非公開の正典が要る）。成功の形: もう一度
  `python3 scripts/build_bukatsu_arena.py --check` を実行して `OK` と出ること。公開候補を別フォルダに作って見るだけなら
  `python3 scripts/build_bukatsu_redesign_v2.py --mode release --output-dir quality/prototypes/bukatsu-chiiki-release-v2`
  （成功の形: `Built 2 files (release, as_of …); no deployment performed.`。docs/ は変わらない）
- **再読データ（理由区分）を追記したとき**（定期更新の外の追い読みも同じ）:
  1. 明細（`items`）と `buckets` の件数を足す
  2. `python3 scripts/bukatsu_reread_stances.py --made-on YYYY-MM-DD`（定期更新の外では立場の対応表を手で作り直す。成功の形: `wrote data/bukatsu-chiiki_reread-stances.json（N件）` か `変更なし`）
  3. 単独なら `python3 scripts/build_bukatsu_arena.py`
  4. `python3 scripts/verify_number_provenance.py bukatsu-chiiki`（新デザインの理由区分・区分ごとの立場を明細と対応表から数え直す。成功の形: `NG 0件`）
- **確認日 `checked_on`・改革実行期間の段階**: 冒頭・読書面・背景の「◯月◯日の時点」と制度の確認日は `configs/bukatsu-chiiki-opening.json` の
  `checked_on` 1か所から出る。段階（推進期間・前期・後期・期間の後）は `period` と基準日（公開JSONの更新日）で切り替わる。
  中間評価を確かめたら `period.midterm_checked_on` と `checked_on` を直し、一次資料メモに節を足す（`--as-of 2029-04-01` で後期の文に切り替わるテストあり）
- **自治体の一覧**は `quality/research/bukatsu-chiiki-municipal-plans.md` の「一覧」の表を生成時に読む（2026-09-23 確認のまま。直すとページの表も変わる）
- 新デザインのページには、授業節の単独適用・信頼情報の単独適用（skipped）・山なみの単独更新（`refresh_planet_section.py`。停止）・
  推移の単独差し込み（`build_trend_section.py --apply`。停止）を掛けない。更新経路では元HTMLに掛かる

**初期型に戻すとき・最新の型の公開が 10/17 の回に間に合わなかったとき**（初期型の経路で 10/17 の回を通す手順）:
初期型は、元HTMLの論点別・理由別の件数や詳細データが1件でも変わると `build_bukatsu_redesign.py` が「参照本文か理由分類が変わりました」、
`refresh_inputs.py` が「データが変わりました」で止まる（新規0件の回は、それより先に「集計と推移の最終日が一致しません」で止まるので公開候補を作らない）。
止まったら、公開候補の隔離コピー（`.staging/…/public-candidate`）の `docs/bukatsu-chiiki-reaction-map.html`（更新済みの元HTML）を入力に、
7論点の説明・教員の4理由の説明・投稿例・制度の確認日（`evidence/refresh-check.json` の `review_items` の4項目）がまだ正しいことを読んで確かめ、
作業ツリーで `scripts/bukatsu_redesign/editorial-review.json` の `data_sha256` と `editorial_sha256` を次の2つの値に書き換え、`reviewed_on` と `note` に確認の記録を足してから
`--prepare-promotion` をやり直す。値は `python3 -c "import sys,json;sys.path[:0]=['.','scripts/bukatsu_redesign'];from pathlib import Path;from refresh_inputs import parse_page,digest;from scripts.build_bukatsu_redesign import fingerprint;s=Path(sys.argv[1]).read_text();print(digest(json.dumps(parse_page(s)[0],ensure_ascii=False,sort_keys=True)),fingerprint(s))" <隔離コピーの docs/bukatsu-chiiki-reaction-map.html>`
で出る（1つ目が `data_sha256`、2つ目が `editorial_sha256`。今の元HTMLで実行すると、いまの `editorial-review.json` と同じ2つの値になることを 2026-10-14 に確かめた）。
初期型に戻すときは `configs/bukatsu-layout.json` の `version` を消してから `python3 scripts/build_bukatsu_arena.py` を実行する
（2026-10-14 に初期型の投票注記「試作では…送信しません」とJSなし案内の「試作」は直したので、戻しても出ない）

### 読み込み確認のやり方（質と速さの両立）

消費税減税での失敗（機械的なチェックは通ったのに、実際には本文を読まずに使い回した
要約だった。`tasks/task-54.md`参照）を踏まえ、次を型として固定する。

- **件数の目安**: 対象件数 ÷ 25件くらいを、同時に読む人数（AIの並列数）の目安にする
- **徹底事項**: 「1件ずつ本文を読んで判定する。件数が多くても自動判定プログラムに
  置き換えない」ことを毎回明記する
- **完了確認**: 論点ごとに最低10件を抜き取り、「本文の内容と記録された要約が
  本当に一致しているか」を別の目で確認してから完了とする。summaryのユニーク率
  100%・マークアップ（`START`/`END`等の抽出マーカー）残留0件も機械確認する
- **記録**: 対象・件数・確認結果を`quality/reviews/`へ本文なしで保存し、
  `manage_reread_registry.py record`の`--reviews`の`source_file`として参照する

### 既存の別プロセスで確認済みだが、この論点固有の区分を持たない投稿

`manage_reread_registry.py prepare`が選ぶ対象と、正典から独自に計算した対象は
一致しないことがある。差分は多くの場合、その投稿が既に別の独立確認プロセス
（例: 課題63の部活動38件独立確認）でレビュー済みだが、`review.bucket`が
今回の論点固有の区分（例: P1-P6/R1-R6）ではなく別形式（例: `confirmed`）の
ままになっているケース。共通台帳の`review`は投稿1件につき1つしか持てないため、
これらは`unread_breakdown()`上は「読み飛ばし」として残る。独自性検査（4割上限）
の数だけでは本文を読んだかどうかは分からない。**今回の追加・変更分なら、上限以内でも
理由分類と記録への反映を終える。** 2026-09-15に認めた上限以内の持ち越しは、今後の今回分には
適用しない。以前からの残件は件数を分けて管理し、今回分の読了を取り消したり、未確認のまま
完了扱いにしたりしない。
