# SNS反応まっぷ

社会の問いについて、SNSの公開投稿サンプルを立場ごとの「理由」まで分解して見せる静的サイト。

**公開URL**: https://issue-stance-lab.github.io/sns-reaction-map/

「どちらが正しいか」をAIに決めさせない。対立の向こう側にある
「もう一つの正義」を可視化し、人々が互いを悪と決めつけずに向き合える状態を目指す。

---

## 現状

| 項目 | 値 |
|---|---|
| 公開テーマ数 | 11 |
| 累積サンプル数 | 5,723件 |
| 形態 | 静的HTML（GitHub Pages、`docs/` を公開） |
| データ源 | Yahooリアルタイム検索の公開投稿 |
| 分類エンジン | Hermes（kimi-k2.6）／ OpenCode Go（minimax-m2.7） |
| 投票基盤 | Supabase Edge Function（`supabase/functions/cast-vote/`） |
| 計測 | GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` |

テーマごとの工程状態・データ更新履歴は **[THEMES.yaml](THEMES.yaml) が単一の真実源**。README には書かない。

## 1テーマのページ構成

1. **ヒーロー** — 問いと、いま議論の中心にある論点
2. **論点アリーナ** — 何が争われているかを論点単位で分解
3. **2Dスタンスマップ** — 投稿を2軸に配置した散布図＋ヒートマップ
4. **投票** — 読んだ人自身の立場を記録し、全体分布と比べる
5. **漫画・図解** — 論点を絵で説明する
6. **背景解説** — 争点そのものの経緯

## リポジトリ構成

```
company/             会社理念、目標、承認、収支、AI部門の責任
content/             X・noteの下書き、調査、投稿実績（公開しない）
quality/             公開候補と公開後の品質監査記録
docs/                公開される静的サイト（GitHub Pages のルート）
social-samples/      収集した投稿の累積正典。本文を含むため一部は Git 管理外
data/verification/   本文を除いた検証用サマリ。クリーンクローンとCIはこれを読む
scripts/             収集・分類・生成・検証。scripts/refresh_adapters/ はテーマ別のページ更新
configs/             テーマ別の設定、収集条件、ワーカーAIへの発注書
manga-prompts/       漫画・図解の生成プロンプト
templates/           新規テーマ・ページの雛形
tests/               unittest
archive/             運用から外れた文書・スクリプト（下記）
```

## 運用ドキュメント

セッションを始めるAIは [CLAUDE.md](CLAUDE.md) の指示に従うこと。

| 文書 | 役割 |
|---|---|
| [company/COMPANY.md](company/COMPANY.md) | 会社の理念、事業、組織、CEO承認範囲 |
| [company/GOALS.yaml](company/GOALS.yaml) | 90日・1年・3年の数値目標 |
| [company/ROADMAP.md](company/ROADMAP.md) | 会社化のフェーズ、成果物、完了条件 |
| [company/HANDOFFS.yaml](company/HANDOFFS.yaml) | 進行中業務の担当、期日、承認、次の一手 |
| [company/QUALITY_GATE.md](company/QUALITY_GATE.md) | Website / X / note 共通の公開品質基準 |
| [company/FOLDER_MAP.md](company/FOLDER_MAP.md) | 成果物の正式な置き場所と保全方針 |
| [company/APPROVALS.yaml](company/APPROVALS.yaml) | CEO承認の待ち・決定ログ |
| [company/FINANCE.yaml](company/FINANCE.yaml) | 月次の収益、費用、利益 |
| [company/CORRECTIONS.yaml](company/CORRECTIONS.yaml) | 訂正・一時非公開・引用削除依頼の記録 |
| [OPERATIONS.md](OPERATIONS.md) | 定例作業の定義。作業場所の作り方・頻度・担当・遅れの見つけ方 |
| [DATA_REFRESH.md](DATA_REFRESH.md) | データ更新の正典。`refresh_topic.py` の使い方と公開ゲート |
| [THEMES.yaml](THEMES.yaml) | テーマ台帳（単一の真実源） |
| [GROWTH.yaml](GROWTH.yaml) | グロース指標の実測値 |
| [TASK_BOARD.md](TASK_BOARD.md) | テーマ横断の課題 |
| [X_POSTING_GUIDE.md](X_POSTING_GUIDE.md) | X（Twitter）投稿の型とルール |
| [FACT_CHECK_GUIDE.md](FACT_CHECK_GUIDE.md) | 投稿の主張を一次資料と突き合わせる手順と発注文 |
| [AI_HANDOFF.md](AI_HANDOFF.md) | 新規参加AI向けの会社運営エントリーポイント |
| [AGENTS.md](AGENTS.md) | Codex 向けの GitHub 認証まわりの注意 |

## 運用状況をまとめて見る（ローカル専用の管理画面）

いま何が期限切れか、流入がどう動いているか、X に何を投稿したか、何を変更したかを1画面にまとめる。

```bash
python3 scripts/build_admin_dashboard.py --open
```

`admin/dashboard.html` を作ってブラウザで開く。**公開されない**（`docs/` の外、`.gitignore` 対象、
`noindex`）。中身はリポジトリ内のファイルの写しなので、開いた時点の実測ではない。
GA4・Search Console・Supabase の実測値も取り直すときは `--fetch` を足す（最大3分、
認証が切れていればその旨が画面に出る）。

読む材料: `THEMES.yaml`（予定日・工程）/ `GROWTH.yaml`（週次KPI・施策）/ `content/x/posts.md`（X投稿実績）/
`TASK_BOARD.md`（課題）/ `data/verification/updates/`（データ更新の検査結果）/ `git log`（変更履歴）。
**画面が古い・空欄になるのは、これらの元ファイルが更新されていないということ。**

## よく使うコマンド

データ更新（収集→分類→検証→バックアップ→承認済み公開まで1コマンド）。
`--promote` は `DATA_REFRESH.md` の検査と CEO 承認後だけ使う:

```bash
python3 scripts/refresh_topic.py --topic <theme> --date <YYYY-MM-DD> --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups --promote
```

ページ検証:

```bash
python3 scripts/verify_theme_page.py <theme>
```

トップページ検証:

```bash
python3 scripts/verify_top_page.py
```

テスト:

```bash
python3 -m unittest discover -s tests -v
```

## archive/ について

運用から外れたものはここに移してある。消していないのは、当時の判断の根拠が残っているため。

- `archive/planning-2026-06/` — 2026-06 の企画段階の文書。**編集者がURLを登録しSubstackで配信する**という、いまとは別のサービス構想。現在の運用とは無関係
- `archive/pipeline-ollama/` — ローカル Ollama で分類していた時代の手順書
- `archive/prompts/` — 実行済みのワーカーAI発注書（2026-06〜07）。結果は THEMES.yaml と TASK_BOARD.md に記録済み
- `archive/TASK_BOARD_ARCHIVE.md` — 完了した課題
- `scripts/archive/ollama-era/` — Ollama 時代の分類スクリプト
