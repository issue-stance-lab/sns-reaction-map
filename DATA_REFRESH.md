# データ更新の運用手順

## 基本方針

- `collect_at` は収集・分類・更新回保存の内部期限。ページを公開できないテーマも予定どおり実行する。
- `refresh_at` は公開まで昇格できるテーマだけに設定する。
- 収集・分類は全テーマで `scripts/refresh_topic.py --topic ...` を使う。
- ページ生成だけを `scripts/refresh_adapters/` のテーマ別adapterへ委譲する。
- `--promote` を付けない限り、累積正典、公開HTML、`updated_at`、`refresh_at` は変更しない。
- **分類モデルは `kimi-k2.6`（Hermes / OpenCode Go）。** `~/.hermes/config.yaml` の
  `model.default` が全テーマ・全セッションに効き、スクリプト側にモデル指定は無い。
  2026-08-18 に OpenCode Go 側の障害（503）で一時 `minimax-m2.7` へ切り替えたが、
  同日中に復旧を確認して戻した。**この間に本番のデータは作っていないので、
  累積正典はすべて `kimi-k2.6` 分類のまま。**
- 障害でモデルを変えるときは、①分類が走っている他セッションが無いか確認する
  （`pgrep -fl "classify_.*hermes|refresh_topic"`）②復旧したら戻す
  ③この文書の記述を実際の設定に合わせ直す。設定を変えた瞬間に他セッションも切り替わるため、
  分類の途中だと1回の更新の中でモデルが混ざる。
- **分類モデルをまたぐ回は「世論の潮目」の扱いをオーナーに確認する（出す／出さない／注記つきで出す）。**
  潮目は前回の収集回と今回を比べる作りだが、モデルが変わるとラベルの引き方が変わり、
  世論が動いたのかモデルが変わったのか区別できない。回ごとに判断するため既定のルールは置かない。
  2026-08-18に消費税減税の同一30件で検証したところ、`kimi-k2.6` との一致率は
  `minimax-m2.7` が論点67%・賛否67%、`kimi-k2.7-code` が論点77%・賛否73%だった
  （関係あるかの判定は両方100%）。賛否の構成比は最大4pt動き、潮目が拾う変化と同じ大きさになる。
  ズレを消したうえで出したい場合は、比較相手の回も同じモデルで分類し直す。

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

`page_update_mode: adapter` のテーマだけ `--promote` を付けられる。

```sh
python3 scripts/refresh_topic.py \
  --topic takaichi \
  --date 2026-08-06 \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups \
  --promote
```

更新回保存後にadapterを使って候補ページを2回生成し、冪等性、投票互換性、保護タグを検査する。全検査合格時だけ累積正典・ページ・台帳・SEO・トップ・sitemapを一括昇格する。昇格後にもう一度バックアップし、失敗時は公開側を昇格前へ戻す。

### 学校あだ名は全自動（人が読む工程なし）

`school-nickname-ban` の adapter は正典だけを読んで、件数を出している場所を毎回
すべて作り直す（リード文・調査条件・注目ポイント4枚・論点カードの内訳文・投票の件数・
論点ナビ・論点ブロック6つ・詳細データ表・アリーナの点）。代表投稿も
`article_usable` かつ `risk: low` から自動で選ぶので、`--promote` を流すだけでよい。

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

**変化あり → 以下を同タイミングで行う：**
1. note 記事の「前回からの変化」セクションを追記した更新案を Artifact（HTML）で出力する
2. サイトの論点説明文（ビルダが生成している箇所）も同じ変化に合わせて更新する

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
- [ ] `data/issue-counts/` を source にしているテーマ（constitutional-amendment / elderly-license-revocation / henoko-student-accident / koshitsu-tenpakai）は、再分類したら `issue_counts.source` を `sample_file` へ戻す（TASK_BOARD 課題29）

---

**注意事項:**
- `hero-total-samples` は全 topic-card の「投稿 XX件」の合計値。新テーマ公開直後に更新漏れが起きやすいので都度合算して確認する。
- 割れ度スコアを変更するとランキング順位も変わる。DOM 順序（first-child が金色）も連動して並び替えること。
- 論点アリーナ（P=[...] データ）は今回の分類結果を反映していないが、潮目ウィジェットで最新比較を表示しているため、現状はそのままでよい。

---
