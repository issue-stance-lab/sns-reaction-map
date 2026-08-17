## タスク: 自転車青切符を manual から adapter へ昇格させる

### 出典
TASK_BOARD.md 課題34（残る manual 1テーマ）／2026-08-17 の自転車青切符 公開更新（累計355件）

### 目的
このテーマだけ「再実行できるページ更新スクリプトが無い」状態で残っている。
2026-08-17 の更新では、ページ内の十数か所を手で書き換えた。次回も同じ手作業が要る。
`refresh_topic.py --topic bike-blue-ticket --promote` で公開まで通せる状態にする。

### 着手前に必ず読む
- `DATA_REFRESH.md`（データ更新の正典）
- `.claude/skills/release/SKILL.md`（マージ・公開・片付け）
- `THEMES.yaml` の `bike-blue-ticket` の `notes`（このページ固有の作りが全部書いてある）

作業ツリー（作業用のコピー）を作ってから着手すること。共有ツリーで作業しない。

### 背景（2026-08-17 に調査済み・再調査不要）

**もう終わっているもの。作り直さないこと。**

| 対象 | 状態 |
|---|---|
| 論点カードの件数の出所 | `sample_file`（正典）そのもの。課題29の暫定ソース `bike_arena_hermes_classified.json` 依存は解消済み |
| 7/26・8/10・8/17 収集回の正典統合 | 完了（累計355件）。課題40 の自転車分は消滅 |
| 冒頭3セクション＋全件表＋区分の根拠 | `scripts/build_bike_process_sections.py` が正典から毎回生成 |
| アリーナの点（SM_RAW） | `scripts/build_bike_arena_points.py` が正典から355点を生成 |
| 論点カード・ナビ・議論の中心・アリーナのセクター・リード文 | `scripts/sync_issue_counts.py bike-blue-ticket` |
| トップの件数・更新日・delta | `scripts/sync_portal_stats.py` |
| 調査条件ブロック・信頼性メタ・分かったこと | `scripts/seo/apply_theme_trust.py`（入力は `configs/theme-seo.json`） |
| 数字の出所検査 | `verify_number_provenance.py` が NG 0件で通る状態 |

**まだ手書きで、今回も手で直した場所。ここが本タスクの主戦場。**

- `insight-stats` カード4枚（分析対象の意見／5論点の内訳／最も話された論点／第三の選択）。
  件数・注釈・メーター幅すべて手書き
- 論点ごとの `temp-bar`（賛成／中立／反対の内訳と%）と `issue-sides` の件数。
  これは論点×立場のクロス集計で、正典から計算できる
- 「本当の対立点」の段落に埋まっている論点別件数（`argument-point` 内）
- 「世論の潮目」は `scripts/inject_tide_widget.py` に**前回・今回の固定ファイル名を直書き**する方式。
  引数を取らず全テーマを書き換えるため、実行すると他テーマが古いデータへ巻き戻る（課題38）。
  adapter 化するなら、更新回から生成する方式へ移すこと

### 判断が要る点（着手前にオーナーへ選択肢を出すこと）

**このページには、機械では埋められない人手の工程が2つある。**

1. **反対投稿の再読**。新しく増えた「反対」を、編集部が1件ずつ読んで5区分
   （青切符では足りない／対象と順番に異議／走る場所がない／警察の運用への不信／
   制度そのものに反対）へ割り当てる。`data/bike-blue-ticket_opposition_reread.json`。
   **件数が反対の総数と一致しないと `build_bike_process_sections.py` は落ちる**（意図的な設計）
2. **事実確認7主張の該当投稿の走査**。`data/bike-blue-ticket_claim_posts.json`。
   本文のキーワード抽出をそのまま件数にすると3〜4割多く出るため、人が読んで確定している

つまり **`--promote` を無条件に通せるようにすると、この2つを飛ばした状態で公開されうる**。
ページの中心的な主張（「反対はひとつの塊ではない」）が、古い割り当てのまま新しい件数で
表示されることになる。次のどれを取るかをオーナーに決めてもらうこと。

- **A案（推奨）**: adapter 化はするが、再読が未更新なら adapter が**明示的に失敗する**。
  新規の反対投稿のうち再読マッピングに無いIDを列挙して止める。人が再読を足してから
  `--promote` を再実行する。自動化されるのは「読む」以外の全部
- **B案**: 再読を伴う3セクションを更新対象から外し、凍結した件数のまま据え置く。
  ページの主役が古くなるので推奨しない
- **C案**: manual のまま据え置き、今回作った生成スクリプト群を手順書にまとめるだけ

### やること（A案を選んだ場合）

1. `scripts/build_bike_arena.py` を新設する。`scripts/build_elderly_arena.py` が手本。
   正典（`THEMES.yaml` の `sample_file`）だけを読んで次を丸ごと作り直す
   - アリーナの点（既存の `build_bike_arena_points.py` を取り込むか、呼び出す）
   - `insight-stats` カード4枚
   - 論点ごとの `temp-bar` と `issue-sides`（論点×立場のクロス集計）
   - 「本当の対立点」段落の論点別件数
   - `--check` / `--input` / `--html-template` / `--output-html` に対応する
2. 「世論の潮目」を更新回から生成する形に移す。`inject_tide_widget.py` の
   `THEMES` から `bike-blue-ticket` を外す（課題38の②と同じ方針）
3. `scripts/refresh_adapters/bike.py` を追加する。`elderly.py` が手本。
   候補ページを2回生成して差分ゼロ、投票の topicId と選択肢数、
   GA4／AdSense／canonical／og:image の保護タグの個数が変わらないことを検査する。
   **加えて、再読マッピングに無い反対投稿があれば tweet_id を列挙して失敗させる**
4. `configs/refresh-pipeline.yaml` の `bike-blue-ticket` に `adapter: bike` を足す
5. `THEMES.yaml` の `page_update_mode` を `adapter` へ、`refresh_at` を設定する
6. `tests/test_bike_adapter.py` を追加する（`tests/test_koshitsu_adapter.py` が手本）

### 併せて直すこと

- **新規収集レコードに `is_opinion` が付かない。** 2026-08-17 の更新では、既存181件が
  全件 `is_opinion: true` だったことに合わせ、追加174件にも一律 `true` を付与した。
  論点カードの母数は `issue_counts.basis: opinion` なので、付いていないと新規分が
  丸ごと数から消える（実際に一度消えた）。分類器か adapter のどちらが付けるかを決めて、
  片方に寄せること

### やらないこと

- 投票の選択肢・topicId の変更（`bike-blue-ticket-issue-stance-v1` と現行の選択肢数を維持）
- 論点体系（6論点）の変更。変えるなら `taxonomy-migration` スキルの手順が別途要る
- 冒頭3セクションの文章の作り直し。STEP3 は結論次第で形が変わるため定型化しない
- 再読と事実確認の人手工程を、キーワード抽出で置き換えること（3〜4割ずれる。実測済み）

### 完了の条件

- `python3 scripts/refresh_topic.py --topic bike-blue-ticket --date <当日> --backup-dest <保全先> --promote` が通る
- `verify_theme_page.py` / `verify_number_provenance.py` / `verify_top_page.py` / `unittest` が
  **マージ後の main で**すべて通る
- 同じ入力で2回実行して差分ゼロ
- 再読を故意に古いまま `--promote` すると、adapter が理由を出して止まる（A案の要）
