# OPERATIONS.md — 定例作業の定義

このプロジェクトで「期日が来たらやること」の一覧。着手前の作業場所の作り方もここにある。

## この文書の位置づけ（2026-08-23 に運用を切り替えた）

**それまでの「2つのループ」（`LOOP.md` の制作ループ、`GROWTH_LOOP.md` のグロースループ、
および毎朝7時の自動タスク `daily-growth-loop`）は廃止した。**

廃止の理由は、設計が悪かったからではなく、**周回そのものが続かなかった**ため。

- 自動タスク `daily-growth-loop` は 2026-07-09 を最後に実行されず、45日間オフのままだった
- `GROWTH.yaml` の `activity_log` は 2026-07-28 で止まった
- `content/x/weekly-reviews.md` は週次レビューの実績が一度もない（テンプレートのみ）
- `recurring.x-profile.last_run` は 2026-07-09 のまま
- 一方、X日次運用とデータ更新は**ループの外で手動セッションとして毎日回っていた**

つまり「見えている作業は続き、周回の中に埋め込まれた見えない作業だけが消えた」。
`LOOP.md` 自身も 2026-08-07 の時点で「自律ループとしては成立しなかった」と書いていた。

そこで、**周回をやめ、期日駆動に切り替える。**
何が遅れているかは人が覚えるのではなく、管理ダッシュボードが検知する。

---

## ⓪ 着手前に必ず — 作業場所を確保する

**1エージェント＝1 worktree（作業用のコピー）。** 複数のセッションが同じ作業ツリーを共有すると、
片方の `git checkout` がもう片方のファイルをディスクから消す。2026-08-07 に実際に発生し、
実行中だった分類処理の参照先ファイルが消えた（処理はメモリ上の版で継続したため助かった）。

```sh
git worktree add ../isa-wt-{作業名} -b task/{作業名}
cd ../isa-wt-{作業名}

# 非公開の正典データを復元する（gitignore対象なので worktree には複製されない）
tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" \
  -C . --exclude=manifest.json
python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; \
  print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"

# 収集ツールを動かせるようにする（node_modules も gitignore 対象で複製されない）
cp -R ../issue-stance-aggregator/node_modules .
```

文章を書く作業（Website本文・X・note）では、ライターのペルソナも復元する。

```sh
# バックアップに含まれている。上の tar 復元で一緒に戻る
ls configs/persona.private.json || echo "無い → バックアップから戻す"
python3 scripts/verify_ai_tone.py   # 「ペルソナ検査は飛ばしています」と出たら復元漏れ
```

**無くても検査は exit 0 で通る。** ペルソナ流出の検査だけが黙って外れるので、
書き手の名前が公開ページに載っても止まらない。文章を書く前に上の1行を確認する。

**この2つはどちらも「gitignore されているから worktree に入らない」もので、
入っていないことが `git status` に出ない。** 忘れても静かに進み、後の工程で落ちる。

**正典を復元しないと、テストと検査が「ファイルがない」で落ちる。** 5テーマの正典
（bukatsu / constitutional / school-nickname / henoko / consumption-tax / ai-copyright）は
本文を含むため Git 管理外で、新しい worktree には入らない。

**`node_modules` を複製しないと、収集が最初の疎通確認で止まる。**
`Cannot find package 'playwright'` と出る。2026-08-08 の憲法改正の収集で実際に発生した。
収集を伴わない作業では不要なので、収集するときだけでよい。

- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象なので、
  古いブランチからは「どこからも参照されていない不要ファイル」に見える。判断する前に
  `origin/main` を取り込むこと（2026-08-07、統合したばかりの正典1,606件が削除されかけた）
- **バックアップは作業したブランチの上で取る。** `backup_private_data.py` は
  いまいるブランチの `THEMES.yaml` と `.gitignore` を見て対象を決めるため、
  古いブランチで実行すると新しい正典が対象から漏れる
- 作業が終わったら `git worktree remove` で片付ける。その前に、そのツリーにしかない
  非公開ファイルを共有ツリーへ複製し、バックアップを取り直す（`release` スキル）
- 共有ツリーで作業する場合は、着手前に `git status` を確認する。
  他セッションの未コミット変更があれば、先にコミットしてもらってから始める
- `git checkout -- <ディレクトリ>` を使わない。**自分が変更したファイルだけ**をパス指定で戻す
  （ディレクトリごと戻すと他セッションの未コミット変更を消す）

---

## 遅れの見つけ方（唯一の入口）

セッションの最初にこれを実行する。何が期限を過ぎているかが一覧で出る。

```sh
python3 scripts/build_admin_dashboard.py
```

検知される遅れ:

- テーマごとの収集予定日（`collect_at`）・公開更新予定日（`refresh_at`）の超過
- 週次KPIの記録が止まっている日数
- X の候補確認日（`recurring.x-posting.last_run`）が未記録
- 数字の取得元（GA4 / Search Console / Supabase）が壊れていないか

**この一覧に出ないものは、定例作業として成立していない。**
新しく定例にしたい作業があるときは、下の表に足すだけでなく、
ダッシュボードが遅れを検知できるようにすること（`scripts/admin_dashboard/render.py`）。

---

## 自動実行している定期タスク

| タスクID | 実行 | 何をするか |
|---|---|---|
| `x-daily-measure` | 毎日 20:05頃 | 24時間経過した未計測投稿の表示回数を読み、`content/x/posts.md` に記録する |
| `x-weekly-review` | 日曜 20:32頃 | 直近7日のX運用を振り返り、`content/x/weekly-reviews.md` に記録する |

どちらも**投稿はしない**（計測と記録だけ）。返信案は出すが送信はしない。

**このアプリが開いていないと動かない。** 実行時刻にアプリが閉じていれば、次に開いたときに
遅れて実行される。廃止した `daily-growth-loop` が45日間気づかれなかった原因もこれである。

### 止まったことに気づくための仕掛け

**タスクの登録状態を見て「生きているか」を確かめない。** 動いてはいるが毎回失敗している
場合を見逃す。代わりに**結果が滞っているか**を管理ダッシュボードが警告する。

- 未計測の投稿が溜まっている → 「X投稿の表示回数が N 件未計測です」
- 週次レビューが10日以上更新されていない → 「X週次レビューが N 日前で止まっています」

この2つは `tests/test_admin_dashboard.py` の `MeasurementStallTests` で守っている。
警告の文言や条件を変えるときは、テストも同時に直すこと。

---

## 定例作業の一覧

### Codex連携管理画面

- 必要なときだけ `管理画面を開く.command` から起動する。自動スケジュールでは起動しない。
- ボタンごとにCodexの永続セッションを1つ作る。同じ履歴はCodexデスクトップアプリからも開ける。
- 変更を伴う作業は同時1件まで。専用worktreeと `task/dashboard-<job-id>` ブランチを使う。
- 共有作業場に未コミット変更がある間は変更作業を始めない。読み取りと流入取得は実行できる。
- 管理画面を閉じても実行中の作業は継続する。作業がなく、画面が開かれていなければ2分後に終了する。
- Xは最後の投稿操作を自動化しない。公開は `ready_for_ceo` と候補ハッシュを確認した後のCEO承認でのみ進む。

| 作業 | 頻度 | 期日の決まり方 | 正典 | 人間が必要なこと |
|---|---|---|---|---|
| **データ更新**（収集・分類・公開） | テーマごと | `THEMES.yaml` の `collect_at` / `refresh_at` | `DATA_REFRESH.md` | 公開側への昇格は最終承認／自転車青切符は再読工程あり |
| **X日次運用** | 毎日（候補0件なら見送り可） | 毎日 | `.claude/skills/x-daily/SKILL.md` | 最終承認と実際の投稿操作 |
| **X投稿の計測**（表示・反応） | 毎日20:05頃 | 定期タスク `x-daily-measure` が自動実行 | `.claude/skills/x-daily/references/measurement.md` | なし（ログイン済みChromeが開いていること） |
| **X週次レビュー** | 日曜20:32頃 | 定期タスク `x-weekly-review` が自動実行 | `.claude/skills/x-daily/SKILL.md` §週次レビュー | なし |
| **KPIスナップショット** | 週1（月曜） | 前回から7日 | `scripts/fetch_growth_kpi.py` → `GROWTH.yaml` | OAuth再認証・フォロワー数の手動確認 |
| **新テーマの追加** | 不定期 | オーナーの指示 | `.claude/skills/new-topic/SKILL.md` | 画像生成（GPTimage2） |
| **本番反映** | 作業完了ごと | 作業完了時 | `.claude/skills/release/SKILL.md` | 最終承認（マージ・pushは承認後にAIが実行） |
| **note 記事** | 3日に1本を目安（候補なしは見送り可） | 前回から3日 | `.claude/skills/note-operation/SKILL.md` | 最終承認と note への投稿操作 |
| **サイト改善を1つ進める** | 週1 | 前回から7日 | 下の「サイト改善の進め方」 | 最終承認 |
| **一次資料メモの再確認** | テーマごと90日目安（法改正が近いテーマは短縮） | `quality/research/status.yaml` の `last_verified` + `review_days` | `.claude/skills/primary-research/SKILL.md` | 業界団体等を例外採用する場合の承認 |
| **Xデータの保全確認** | 更新直後＋週1回 | `company/data-operations.yaml` と復元記録から7日 | [段階Eの手順](quality/designs/2026-09-06-stage-e-data-preservation.md) | 別実機の用意のみ。通常のバックアップ・復元検査はAIが実行 |
| **作業ツリーの片付け** | 本番反映ごと | 反映完了時 | `.claude/skills/release/SKILL.md` | なし |

---

## サイト改善の進め方

**これが1ヶ月間、誰の担当でもなくなっていた工程。** 週1回、以下を1つだけ進める。

台帳は `GROWTH.yaml` の `capabilities`。工程は `idea → building → built → measuring → done`。

1. `judge_at` を過ぎた `measuring` があれば、まずそれを片づける
   - `phase.current: initial_traction` の間は判定を急がず、`reflection` に観察ログを書いて延長する
   - **延長は1回まで。** 2回目も母数が足りなければ `closed_undecided` で閉じ、`reopen_when` を書く
2. `built`（実装済み・マージ待ち）があれば main に入れて `measuring` に進める
3. どちらも無ければ `priority` 順に `idea` を1つ着手する

守ること:

- 保護タグ（GA4 / AdSense / Supabase / OGP）を壊さない
- 375px で横スクロールなし・コンソールエラーなし
- 新しい導線には GA4 イベントか utm を必ず付ける。**計測できない施策は実装しない**
- ブランチは `task/growth-{id}`。main への直接コミットはしない
- 規模が大きいものは `configs/prompts/{YYYYMMDD}_growth-{id}.md` に発注プロンプトを書いて止める
- やったことは `GROWTH.yaml` の `activity_log` に1行残す

---

## 台帳を更新するのは誰か

**作業したセッションが、その場で更新する。** 別工程にまとめない。
まとめる設計にしていたために、ループが止まったとき台帳だけが1ヶ月取り残された。

| 台帳 | 更新するタイミング |
|---|---|
| `THEMES.yaml` | データ更新の直後（`DATA_REFRESH.md`）。工程の状態だけを書く欄で、経緯は `themes/{テーマ名}.md` へ（`python3 scripts/verify_themes_yaml.py` で検査） |
| `themes/{テーマ名}.md` | テーマの更新・調査の直後。そのテーマの経緯はここが唯一の置き場 |
| `content/x/posts.md` | X投稿の直後 |
| `GROWTH.yaml` `recurring.*.last_run` | その定例作業をやった直後。**実際に運用が動いた日**を書く（ループが動いた日ではない） |
| `GROWTH.yaml` `kpi.snapshots` | KPI取得の直後（週1） |
| `GROWTH.yaml` `activity_log` | サイト改善を進めた直後 |
| `quality/research/status.yaml` `last_verified` | 一次資料メモを再確認した直後（`.claude/skills/primary-research/SKILL.md`） |
| `TASK_BOARD.md` と `tasks/task-{番号}.md` | 課題を見つけた時・片づけた時。索引は6欄1行ずつ、経緯は詳細ファイルへ（`python3 scripts/verify_task_board.py` で検査） |

X日次スキルは `GROWTH.yaml` を読むだけで書かないため、
`recurring.x-posting.last_run` の更新が誰の担当でもなくなっていた（2026-08-23 時点で実態と6日ずれていた）。
**X運用をしたセッションが更新すること。**

---

## 人間（オーナー）の役割

- Website の公開・公開内容変更の最終承認
- X の投稿・リプライの最終承認と操作
- note の投稿・有料化の最終承認と操作
- 画像生成（GPTimage2）
- AdSense / GA4 など管理画面での操作、OAuth の再認証
- 支出・有料契約・重要方針変更・データ削除の最終承認
- 施策を `adopted` / `rejected` に倒すときの最終承認

調査、候補作成、分析、検査、承認後のマージ・pushは原則 AI が行う。
承認記録は `company/APPROVALS.yaml` に残す。数値取得は原則不要
（`scripts/fetch_growth_kpi.py` が自動取得する）。
フォロワー数だけは自動取得できないため `scripts/record_x_followers.py` を使う。

---

## 廃止したもの（復活させないこと）

- **①〜⑥の周回**（制作ループ・グロースループ）。チェックリストとして必要な部分は
  `DATA_REFRESH.md` と各スキルに移した
- **毎朝7時の自動タスク `daily-growth-loop`**。45日間オフのまま気づかれなかった。
  自動起動に頼らず、セッション開始時のダッシュボード確認で代替する
- **「ループが判断し、人間は実行のみ」という分担**。実態と合っていなかった
