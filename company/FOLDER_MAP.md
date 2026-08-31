# ファイル配置の正典

最終更新: 2026-08-27

各成果物の置き場所と、Gitへ残すかどうかを決める文書。場所を変える前にこの文書を更新する。

## ルート直下の大分類

| 大分類 | 役割 |
|---|---|
| `company/` | 会社方針、部門、承認、収支、引き継ぎ、ローカル管理画面 |
| `content/` | Website・X・noteの非公開制作物、調査、実績 |
| `creative/` | ブランド、デザイン、画像プロンプト、制作テンプレート |
| `quality/` | 品質監査、設計レビュー、訂正判断の証拠 |
| `docs/` | 公開専用リポジトリへ同期する静的サイトの正典 |
| `configs/` / `scripts/` / `data/` / `tests/` | Websiteの設定、生成、検査、検証データ |
| `social-samples/` | 投稿本文を含む非公開の累積正典 |
| `supabase/` | 投票基盤 |
| `archive/` | 現在の運用から外れた資料・実験・ローカル生成物 |

`docs/`、`configs/`、`scripts/`、`data/`、`tests/`、`social-samples/`、`supabase/` は
公開・収集・検査の実行経路そのものなので、見た目だけを目的に大分類の下へ移さない。

## 成果物ごとの正式配置

| 区分 | 正式な場所 | Git | 備考 |
|---|---|---|---|
| 会社の方針・台帳 | `company/` | 管理する | 理念、承認、引き継ぎ、収支、訂正、部門責任 |
| CEO管理画面 | `company/dashboard/` | 管理しない | ローカル生成物と実測キャッシュ |
| Website公開物 | `docs/` | 管理する | 公開専用リポジトリの `public/` へ同期する正典。運用メモを置かない |
| Website内部資料 | `content/website/internal/` | 管理する | 計測、SEO、投票などの非公開運用メモ |
| Website調査 | `content/website/research/` | 管理する | テーマ調査と分類レポート |
| Websiteの設定・生成・検査 | `configs/` / `scripts/` / `tests/` | 管理する | 参照を更新できる変更だけを行う |
| Xの投稿案・実績・週次レビュー | `content/x/` | 管理する | 投稿本文・実績は公開ディレクトリに置かない |
| Xの調査 | `content/x/research/` | 管理する | 日付・出所・一般化できない点を残す |
| noteの下書き・画像・再生成元 | `content/note/drafts/` | 管理する | 公開前の原稿と画像の作業素材 |
| noteの投稿実績 | `content/note/posts.md` | 管理する | 公開日、URL、UTM、7日後・28日後計測 |
| noteの調査・一次資料メモ | `content/note/research/` | 管理する | 原資料の転載ではなく、出所リンクと要約を保存 |
| noteの字幕・ローカル調査環境 | `content/note/raw-research/` | 管理しない | 再生成可能な原資料。削除せずローカル保全 |
| ブランドとデザイン | `creative/brand-concepts/` / `creative/design/` | 管理する | 現在の制作判断に使う資料 |
| 漫画・図解プロンプト | `creative/manga-prompts/` | 管理する | 画像生成の正典 |
| 制作テンプレート | `creative/templates/` | 管理する | 新テーマ、ページ、ワーカー発注の雛形 |
| データ本文を含む正典 | `social-samples/` | 非公開保全 | `.gitignore`対象。バックアップから復元する |
| 検証用サマリ | `data/verification/` | 管理する | 本文を持たない再現用データ |
| 公開候補の品質記録 | `quality/reviews/` | 管理する | 公開前・公開後の監査記録 |
| 設計記録 | `quality/designs/` | 管理する | 現行設計の判断根拠 |
| 古い構想・一時スクリプト | `archive/` | 管理する | 現在の手順としては参照しない |
| デザイン同期の休止実験 | `archive/design-system-experiment/` | 管理する | 公開サイトから未使用。再開用に削除せず保存 |
| 同期実験のローカル環境 | `archive/local/design-sync-runtime/` | 管理しない | `.ds-sync`と`ds-bundle`の保全先 |

## フェーズ3.1で解消した旧配置

- `brand-concepts/`、`design/`、`manga-prompts/`、`templates/`を`creative/`へ集約した。
- `docs-internal/`と`research/`を`content/website/`へ集約した。
- 未使用の`design-system/`と`.design-sync/`を`archive/design-system-experiment/`へ移した。
- 管理画面の出力先を`admin/`から`company/dashboard/`へ移した。
- `content/note/raw-research/`のローカル原資料は`content/note/raw-research/`へ移し、Gitには入れない。
- 2026年8月の完了計画を`archive/planning-2026-08/`、設計レビューを`quality/`へ移した。

## 移動時の順番

1. 正式な場所、参照元、バックアップ対象をこの文書に書く。
2. `rg`で参照先を洗い出し、移動と同じ変更で更新する。
3. 管理画面生成、全テーマ検査、数字の出所、トップ検査、全テストを実行する。
4. 非公開データを共有ツリーへ戻し、バックアップの復元確認を行う。
5. 公開物または運用手順を変える場合は品質監査とCEO承認を記録する。
