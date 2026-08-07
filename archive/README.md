# archive/

運用から外れた文書・発注書・スクリプトの置き場。

**ここにあるものを現在の手順として参照しないこと。** 消していないのは、当時の判断の根拠が残っているため。

---

## planning-2026-06/

2026-06 の企画段階の文書。**いまとは別のサービス構想**を書いている。

> 編集者がソースURLを登録 → AIが要約・論点・根拠を抽出 → 人間がレビュー → 記事ページとニュースレターとして公開。Substack を最初の収益化チャネルにする。

実際に作られたのは、Yahooリアルタイム検索から公開投稿を自動収集し、AIで論点・立場を分類して静的サイトに出す「SNS反応まっぷ」で、編集者もSubstackも存在しない。

| ファイル | 内容 |
|---|---|
| `README-original.md` | 旧README（「Issue Stance Aggregator 企画」） |
| `agent.md` | 旧エージェント指針。2026-08-07 まで `CLAUDE.md` が `Agent.md` として参照し続けていた |
| `product-plan.md` / `operations-plan.md` | 企画・運用計画 |
| `topic-roadmap.md` / `case-comparison.md` / `research-memo.md` | 題材の下調べ |
| `article-workflow.md` | 記事制作フロー |
| `sample-takaichi-bunshun-article.md` | 記事サンプル |
| `articles/` | Substack向け記事ドラフト |

**注意**: `agent.md` は macOS のファイル名大文字小文字非区別により、`CLAUDE.md` の `Agent.md` という指示が解決してしまう位置にあった。同様の事故を防ぐため、ここに移動している。

## pipeline-ollama/

ローカル Ollama で分類していた時代（〜2026-06）の手順書。現在の分類は Hermes（kimi-k2.6）と OpenCode Go（minimax-m2.7）で、THEMES.yaml に ollama の記載はない。

スクリプト本体は `scripts/archive/ollama-era/` にある。

## prompts/

実行済みのワーカーAI発注書（2026-06〜07）。作業結果は `THEMES.yaml` と `TASK_BOARD.md` に記録済み。

進行中・直近の発注書は `configs/prompts/` に残してある。

## TASK_BOARD_ARCHIVE.md

完了した課題。`TASK_BOARD.md` から移されたもの。
