# データ更新の運用手順

## 基本方針

- `collect_at` は収集・分類・更新回保存の内部期限。ページを公開できないテーマも予定どおり実行する。
- `refresh_at` は公開まで昇格できるテーマだけに設定する。
- 収集・分類は全テーマで `scripts/refresh_topic.py --topic ...` を使う。
- ページ生成だけを `scripts/refresh_adapters/` のテーマ別adapterへ委譲する。
- `--promote` または `--apply-promotion` を付けない限り、累積正典、公開HTML、`updated_at`、`refresh_at` は変更しない。
- 収集・分類・検査・公開候補の作成までは AI が自律的に行う。
- **`--apply-promotion` は、候補manifestの品質監査が `ready_for_ceo` になり、CEO承認を `company/APPROVALS.yaml` に記録した後だけ実行する。**
- `--promote` は従来手順との互換用に残す。管理画面からは使わない。
- **分類モデルは `kimi-k2.6`（Hermes / OpenCode Go）。** `~/.hermes/config.yaml` の
  `model.default` が全テーマ・全セッションに効き、スクリプト側にモデル指定は無い。
  2026-08-18 に OpenCode Go 側の障害（503）で一時 `minimax-m2.7` へ切り替えたが、
  同日中に復旧を確認して戻した。**この間に本番のデータは作っていないので、
  累積正典はすべて `kimi-k2.6` 分類のまま。**
- 障害でモデルを変えるときは、①分類が走っている他セッションが無いか確認する
  （`pgrep -fl "classify_.*hermes|refresh_topic"`）②復旧したら戻す
  ③この文書の記述を実際の設定に合わせ直す。設定を変えた瞬間に他セッションも切り替わるため、
  分類の途中だと1回の更新の中でモデルが混ざる。
- **戻すときは `model.default` だけでなく `provider` / `base_url` / `api_mode` も戻す。**
  `kimi-k2.6` は `provider: opencode-go` / `base_url: https://opencode.ai/zen/go/v1` /
  `api_mode: chat_completions` とセット。`default` だけ書き換えると別の提供元へ繋がる。
- **2026-09-06、`model.default` が `upstage/solar-pro4:free`（同日 08:18 更新）に
  なっているのを発見し、`kimi-k2.6` へ戻した。**誰がいつ替えたかの記録は無い。
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

## 収集から山なみへの反映まで（2026-09-09〜）

**山なみ向けの更新は、収集した直後に追加・変更分の本文確認まで続ける。**
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
   判断材料が足りない投稿は理由付きで保留し、確認済みとして混ぜない。
4. **山なみの公開候補へ反映** — 採用するデータと再読記録を対応させ、非公開の候補を作る。
   件数・理由のまとまり・表示を更新する。原本の判定変更、正式台帳への採用、ページ生成は
   それぞれの手順に従い、読了記録を作っただけで自動的に採用・公開されたとは扱わない。
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
保存場所・確認済み範囲・保留理由・次の作業を残す。収集成功時だけ次回 `collect_at` を進め、
未公開のまま `updated_at` や `refresh_at` を公開済みの値へ進めない。

この節は山なみ向けの更新手順。下記の既存ページ用adapterの個別手順で
「手動再読不要」とある場合も、それを山なみの本文確認を省く根拠にはしない。

### 公開済みの山なみページを更新する（2026-09-12〜）

**`build_planet_page_preview.py`は「旧デザイン→山なみ」の1回きりの変換専用で、
既に山なみが入ったページに使うと安全装置が拒否する。** `build_bukatsu_arena.py`／
`update_bukatsu_tide.py`／`sync_issue_counts.py`は、いずれも山なみ判定
（`<!-- PLANET_SECTION_START -->`の有無）で件数更新を意図的にスキップする作りで、
公開後の更新手段そのものが無かった（2026-09-10のコード内コメントに「段階3で
挿入先を設計する」と将来の宿題のまま残っていた。課題63の反映作業で実際に発生し発覚）。

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

1. **セクション本体が作らない、テーマ固有のリンク挿入。** bukatsu-chiikiの
   「この論点のなかを見る」リンク（go-card）は`build_section()`自体には無く、
   初回変換時の`build_bukatsu()`内の後処理でのみ挿入されていた。再現しないと
   再生成のたびに消える（課題47と同型）
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

候補では保留投稿を原本へ追加せず、更新回の原文と判断理由を別に保持する。
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
9. 成功時だけ `last_refresh_attempt_at` と次回 `collect_at` を更新

バックアップが失敗した場合は更新回を確定せず、`collect_at` も進めない。新規0件でも収集成功回として履歴を残すが、公開更新にはしない。

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

### 学校あだ名は公開承認以外を自動化（人が読む工程なし）

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
- [ ] `collect_at` → 次回の収集・staging作成予定日
- [ ] `refresh_at` → 次回の公開更新予定日（公開まで昇格できるテーマのみ。既定14日、今回の新規意見が50件以上なら次回だけ7日）

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

### 4. テーマページ（insight-stats カード 4枚）

- [ ] 「分析対象の意見」件数（`insight-value`）
- [ ] 「最も多い立場」% + 件数注（`insight-note`）+ `insight-meter` 幅
- [ ] 「最も話された論点」件数（`insight-value`）
- [ ] 「論点による逆転」注釈（件数が変わる場合）
- [ ] ヒーローセクション「議論の中心」バッジ件数（`conclusion-count`）
- [ ] lead文の件数
- [ ] `data-method` テキスト（データの集め方）

### 5. index.html（ポータル）

- [ ] `rank-card` スタンス比率バー（`rank-dist` + `rank-track` の4項目）
- [ ] 割れ度スコア（`split-score` の meter 幅 + 数値）
- [ ] スコアが変動した場合: `rank-num` 順位番号 + カードの DOM 順序を更新
- [ ] `topic-card` スタンス比率バー（`topic-percent` + `topic-bar` の各項目）
- [ ] `topic-card` 件数（`topic-meta` 内の「投稿 XX件」）
- [ ] `topic-card` 更新バッジ（`.topic-fresh` テキストと日付）
- [ ] badge data `B` 変数（`upd` → 今日の日付、`delta` → 今回追加件数）
- [ ] `hero-total-samples` → 全テーマ topic-card 件数の合計に更新
- [ ] `hero-total-samples` の横の更新日テキスト（例: `7/26更新`）

### 6. sitemap.xml

- [ ] 該当テーマの `lastmod` → 今日の日付

### 7. 論点カードの件数

- [ ] `python3 scripts/sync_issue_counts.py {theme}` を実行（件数は分類結果から生成する。HTMLに直接書かない）
- [ ] 論点のラベルが変わった場合は `configs/{theme}-reaction-map.json` の `issue_counts.cards` を先に直す
- [ ] `python3 scripts/verify_theme_page.py {theme}` が exit 0
- [ ] `data/issue-counts/` を source にしているテーマ（constitutional-amendment / elderly-license-revocation / henoko-student-accident / koshitsu-tenpakai）は、再分類したら `issue_counts.source` を `sample_file` へ戻す（課題29。2026-08-08に完了し `archive/tasks/task-29.md` へ移した）

---

**注意事項:**
- `hero-total-samples` は全 topic-card の「投稿 XX件」の合計値。新テーマ公開直後に更新漏れが起きやすいので都度合算して確認する。
- 割れ度スコアを変更するとランキング順位も変わる。DOM 順序（first-child が金色）も連動して並び替えること。
- 論点アリーナ（P=[...] データ）は今回の分類結果を反映していないが、潮目ウィジェットで最新比較を表示しているため、現状はそのままでよい。

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

自転車正典の本文なし検証データは `python3 scripts/build_bike_verification.py` で作る。旧形式のトップ階層 `is_opinion` と新形式の分類内フラグを、公開集計と同じ優先順で保持する（収集回の保存済み検証ファイルは変更しない）。
