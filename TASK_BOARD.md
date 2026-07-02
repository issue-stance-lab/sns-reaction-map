# TASK_BOARD — SNS反応まっぷ

最終更新: 2026-07-01

## 運用ルール
- 各AIは**課題を丸ごと1つ担当**し、サブタスクの分解・設計・実装まで自律的に進める
- Claude Code はハブとして全体調整・レビュー・統合を行う
- 各AIは作業前にこのファイルと AI_HANDOFF.md を読む
- **レビューフィードバックがある場合は `reviews/` ディレクトリの自分宛ファイルを必ず確認し、対応する**
- 競合防止: 担当課題に関係するファイルのみ変更する
- 他AIの担当領域のファイルを変更する必要がある場合は、TASK_BOARD.md にメモを残して人間に相談する

### ブランチ運用ルール
- **mainブランチに直接コミットしない**。作業は必ず `task/{課題番号}-{説明}` ブランチで行う
  - 例: `task/13-bike-blue-ticket`, `task/7-data-refresh`, `task/18-design-improvement`
- 作業完了後、PRを作成してClaude Code（ハブ）がレビュー・マージする
- **複数AIが同時作業する場合**: 各AIが別ブランチで作業し、mainへのマージはClaude Codeが順番に行う
- マージ時にコンフリクトが発生した場合はClaude Codeが解決する

### 保護ファイル（スクリプトによる再生成禁止）
- **`docs/index.html`** — 手動管理のポータルページ。`build_site_portal.py` 等で上書きしないこと。新規トピックのカード追加はClaude Codeが手動で行う
- **既存の `docs/*-reaction-map.html`** — GA4/AdSense/Supabaseタグが組み込まれているため、再生成する場合はこれらのタグが維持されることを確認すること

## プロジェクト概要
- サービス名: SNS反応まっぷ
- 形態: 静的HTMLサイト（GitHub Pages）未公開
- パイプライン: Yahoo検索 → Ollama分類 → HTML生成 → デプロイ
- 詳細: AI_HANDOFF.md を参照

---

## チーム構成

| AI | 役割 | 得意分野 | 担当課題 |
|----|------|---------|---------|
| **Claude Code** | ハブ（司令塔） | 対話的設計・既存コード改善・git統合・ローカル実行 | 課題4: パイプライン改善 |
| **Codex** (OpenAI GPT-5.5) | ワーカー | PR作成・テスト・長期実行タスク・地道な改善作業 | 課題3: 集客の仕組み |
| **Antigravity2** (Google Gemini 3.5 Flash) | ワーカー | フルスタックアプリ生成・バックエンド構築・MCP対応 | 課題2: 投票バックエンド |
| **Hermes** (Kimi K2.6) | ワーカー | フロントエンド生成・マルチ成果物同時生成・UI品質が高い | 課題1: 公開準備 / 分類設計レビュー |

### 各AIへの注意事項
- **あなたが上記のいずれかのAIである場合**: 自分の「担当課題」のセクションを読み、そのスコープ内で自律的に作業してください
- **他AIの担当課題の内容を変更しないでください**（ファイル競合の原因になります）
- **作業完了時**: 変更したファイル一覧と内容のサマリーを出力してください
- **判断に迷った場合**: 仮定せず人間に質問してください

### ファイル所有権（競合防止）

| ディレクトリ/ファイル | 主担当 | 備考 |
|---------------------|--------|------|
| `docs/index.html` | Hermes | ポータルページ |
| `docs/*-reaction-map.html` | Hermes | トピックページ |
| `docs/*-summary.html` | Hermes | サマリーページ |
| `scripts/build_*.py` | Claude Code | ビルドスクリプト |
| `scripts/classify_*.py` | Claude Code | 分類スクリプト |
| `scripts/fetch_*.py`, `scripts/fetch_*.mjs` | Claude Code | 収集スクリプト |
| `configs/` | Claude Code | 設定ファイル |
| SEO関連ファイル（sitemap.xml, robots.txt等） | Codex | 新規作成 |
| 投票バックエンド関連 | Antigravity2 | 新規作成 |

---

## 課題一覧

### 課題1: 公開できる状態にない
**担当**: Hermes (Kimi K2.6)
**状態**: 完了（2026-06-27確認）
**レビュー**: `reviews/hermes-review-2026-06-24.md` に成果物レビュー結果を記載。全指摘に対応完了（簡体字修正・フッターリンク削除・OGP絶対URL更新済み）。index.htmlの旧ドメイン（kart100sd-two）も修正済み
**概要**: ポータルページ・各トピックページの品質を公開レベルにする
**スコープ**:
- ポータルページ (docs/index.html) のデザイン刷新
- 全トピックページの品質チェック・修正
- favicon / ロゴ
- OGP画像対応
- GitHub Pages デプロイ設定
- レスポンシブ対応

### 課題2: 投票バックエンドなし
**担当**: Antigravity2 (Google)
**状態**: 完了（レビュー対応済み）
**レビュー**: `reviews/antigravity2-review-2026-06-24.md` の全項目に対応完了
**概要**: 投票データを蓄積・共有できるバックエンドを導入する
**スコープ**:
- localStorage → バックエンド（Supabase等）移行
- リアルタイム投票数表示
- 不正投票防止（IP/Cookie制限等）
- 投票結果のX共有機能改善

### 課題3: 集客の仕組みなし
**担当**: Codex (OpenAI)
**状態**: 完了（2026-06-27）
**レビュー**: `reviews/codex-review-2026-06-24.md` の全項目対応済み
**概要**: PVを獲得するための集客基盤を構築する
**スコープ**:
- SEO対策（構造化データ、サイトマップ、メタタグ）
- X運用（投稿テンプレート、共有導線）
- ~~Google Analytics / Search Console 導入~~ ✅ GA4（G-K10S4YCZFH）をtokyopoliticsアカウントで作成、全15 HTMLに適用済み。Search Consoleとの連携完了（2026-06-27）
- OGP最適化（X Card対応）

### 課題4: 運用パイプラインが重い
**担当**: Claude Code
**状態**: 完了（全レビュー対応済み）
**レビュー**: `reviews/claude-code-review-2026-06-24.md` 参照。Codex再レビュー含め全項目対応済み
**概要**: 日次運用を効率化し、1トピック15分以内で公開できるようにする
**スコープ**:
- ワンコマンド実行化 ✅ `scripts/run_pipeline.py`
- トレンド自動取得・ネタ提案の強化 ✅ `--judge`フラグ
- 分類精度の改善 ✅ 分類診断（Step 5）+ `--reclassify`
- config自動生成の補助 ✅ `--scaffold`フラグ（5テンプレート対応）
**レビュー対応済み項目**:
- [x] `fetch_yahoo_realtime_node.mjs` の Codex 絶対パス依存を除去し、`package.json` で playwright を管理
- [x] 分類の部分失敗時（exit 2）にフォールバックJSON保存済みなら警告として後段ビルドへ続行
- [x] `--reclassify` を一時ファイル + .bakバックアップ + 成功時置換方式に変更
- [x] `requirements.txt` に PyYAML を明記
- [x] `step_stats()` と AI_HANDOFF.md の分類率基準を明確化（指標名を区別）
- [x] `step_judge()` の一時ファイル削除: fetch実行から全体を`try/finally`で囲み、全パスで確実に削除

### 課題5: 収益化未着手
**担当**: Hermes (Kimi K2.6) → Claude Code / Antigravity が対応完了
**状態**: 完了
**概要**: 収益手段を導入する
**スコープ**:
- ~~Buy Me a Coffee 正式登録・全ページ設置~~ ✅ buymeacoffee.com/kt100sd
- ~~プライバシーポリシー・免責事項ページ~~ ✅ Hermes作成
- ~~AdSense 申請準備~~ ✅ 申請完了（2026-06-27）
  - `privacy.html` のAdSenseポリシー適合改定、AdSense接続コード（`ca-pub-2542211932832864`）の一括挿入スクリプト実装および全HTMLへの適用、`ads.txt` の自動生成オプション追加および本番公開。
  - ルートドメイン `issue-stance-lab.github.io` リポジトリを新規作成し、AdSenseコード入り `index.html` を公開して所有権を確認済み。

### 課題6: X初期フォロワー獲得・集客強化
**担当**: Codex (OpenAI)
**状態**: 未着手
**概要**: 新規Xアカウント(@sns_hannou_ma)のフォロワーを0→100に増やし、投稿のインプレッションを獲得する
**背景**: 予約投稿3件でインプレッション1のみ。新規アカウントはアルゴリズムに乗らないため、能動的な交流が必要
**スコープ**:
- トレンド話題へのリプライ用テンプレート作成（サイトURLを自然に添える文面）
- 同ジャンル（政治評論・教育・AI議論）の有力アカウントリスト作成
- 引用リポスト用テンプレート作成（既存の議論に参加→自サイトへ誘導）
- 効果測定の指標定義（フォロワー数・インプレッション・クリック率）
- 投稿頻度・時間帯の最適化提案

### 課題8: UI/UX大幅改善
**担当**: Claude Code（別セッション）
**状態**: 完了（2026-06-27）
**概要**: サイトにアニメーション・X埋め込み・巡回導線を追加し、滞在時間とエンゲージメントを向上させる
**スコープ**:
- X投稿の埋め込み表示（widgets.js）
- アニメーション追加（フェードイン、チャート描画、投票エフェクト）
- 投票後の巡回導線（「他のトピックにも投票しよう」セクション）
- 投票進捗表示（投票済みバッジ、コンプリート演出）
- 手順: `configs/prompts/hermes/20260626_ui-redesign.md` 参照
**実施内容**:
- 全6ページをマガジン風フルワイドレイアウトに改装
- 131件のツイートをTwitter/X oEmbed埋め込みに変換
- 各セクションにSVGアイコンバッジ追加
- AI生成ヒーロー背景画像を6ページに追加（WebP）
- テキスト視認性改善、ウェーブ装飾等の視覚要素追加

### 課題7: 現在のテーマのデータ補充
**担当**: Codex（実行済み） / Claude Code（継続運用）
**状態**: 初回完了・継続ルーチン化（2026-06-28）
**概要**: 現在公開・作成済みのテーマについて、Yahoo検索データを追加収集し、既存データとマージして分類件数を増やす
**スコープ**:
- 現在の5トピックのYahooリアルタイム検索データを追加収集
- 既存データとマージし、重複投稿を除外
- Ollamaで再分類
- 分類件数・保留率・代表投稿の品質を確認
- HTML再生成
- 最終的なデータ補充・再分類・テーマ更新は Claude Code が担当
- 手順: `configs/prompts/claude-code/20260626_data-refresh.md` 参照
**ルーチン運用**:
- 目的: 既存テーマの反応データを定期的に補充し、反応マップの鮮度と投稿ボリュームを維持する。
- 頻度目安: 週1回、またはX/ニュースで再燃したテーマが出たタイミング。
- 対象: 公開中テーマ全体。ただし優先順は「閲覧が多いテーマ」「直近で話題化したテーマ」「分類件数が少ないテーマ」。
- 実施者: Claude Codeが最終実行。Codexは大量処理、差分確認、コミット作業を担当可能。
- 手順: Yahooリアルタイム検索で追加取得 → 既存データと重複排除マージ → Ollama分類 → 品質監査 → HTML再生成 → トップページ件数と「情報追加」マーク更新 → コミット。
- 判定基準: 追加件数、保留率、代表投稿候補、分類軸のズレを確認し、分類崩れが大きい場合は課題9へ回す。
- コミット単位: 中間ファイルは除外し、正式採用データ・設定・HTML・監査メモ・タスクボード更新をまとめる。
**実行結果**:
- `ai-copyright`: 475件 → 904件
- `school-nickname-ban`: 201件 → 344件（保留寄り303件。課題9の分類設計見直し対象）
- `takaichi`: 183件 → 324件
- `henoko`: 311件 → 403件
- `constitutional`: 192件 → 422件（既存構造化v2は残し、`constitutional_amendment_classified_refreshed.json` を作成）
- `bike-blue-ticket`: 新規テーマとして177件を収集・分類済み。`social-samples/bike-blue-ticket_classified.json` を正式採用データとして使用。
**分類品質監査**:
- 監査メモ: `reviews/classification-quality-audit-2026-06-27.md`
- 比較的良好: `takaichi`, `constitutional`
- 再分類・設計見直し優先: `school-nickname-ban`, `henoko`
- `ai-copyright` は `category` と `stance` の矛盾があり改善余地あり
- `bike-blue-ticket` は代表投稿候補を監査済み。監査メモ: `reviews/bike-blue-ticket-article-usable-audit-2026-06-28.md`

### 課題9: テーマ別分類設計の再構築
**担当**: Claude Code（最終テーマ作成担当）
**レビュー**: Hermes
**状態**: 優先2テーマ実装済み（school / henoko）
**概要**: 新規テーマ作成時に、テーマごとの投稿傾向に合わせて分類方法・検索クエリ・Ollama出力スキーマを設計する
**スコープ**:
- 新規テーマを「政治・政策」「事故・炎上」「生活・教育」「技術・権利」「制度移行」などの型に分類
- テーマ型ごとに `category` / `issue` / `stance` / 追加フィールドを設計
- Yahoo検索クエリを分類しやすい形に設計
- 少量サンプルでOllama分類を試し、保留・誤分類が多ければ設計を修正
- 最終的な `configs/topics/*.yaml` 作成とテーマ生成は Claude Code が担当
- Hermesはカテゴリ粒度、読者への分かりやすさ、UI表示軸をレビュー
- 課題7の分類品質監査で、`school-nickname-ban` と `henoko` は優先的な再設計対象と判定済み
**実装結果（2026-06-28）**:
- `school-nickname-ban`: 論点分類v2を作成し、344件を `social-samples/school-nickname-ban_classified_v2_final.json` として再整理。代表投稿候補は `article_usable: true` 34件まで厳格化。
- `henoko`: 構造化分類スキーマを見直し、403件を `social-samples/henoko/henoko_structured_redesign_final.json` として再整理。`actor_target` / `criticized_target` / `reaction_type` / `review_required` を追加。
- `bike-blue-ticket`: 制度移行・公共ルール型として分類設計済み。177件を `social-samples/bike-blue-ticket_classified.json` に分類し、代表投稿候補を `article_usable: true` 149件から97件へ絞り込み。
- HTML反応マップと `configs/site-cases.json` は最終ファイル参照へ更新済み。
- 監査メモ: `reviews/school-nickname-ban-v2-final-audit-2026-06-28.md`, `reviews/henoko-classification-design-review-2026-06-28.md`, `reviews/bike-blue-ticket-article-usable-audit-2026-06-28.md`
**最終採用ファイル（2026-06-28）**:
- `school-nickname-ban`: `social-samples/school-nickname-ban_classified_v2_final.json`（344件、`article_usable: true` 34件）
- `henoko`: `social-samples/henoko/henoko_structured_redesign_final.json`（403件）
- `bike-blue-ticket`: `social-samples/bike-blue-ticket_classified.json`（177件、`article_usable: true` 97件）
- `configs/site-cases.json` は上記2ファイルを正式参照済み。
- `docs/school-nickname-ban-reaction-map.html` / `docs/henoko-student-accident-reaction-map.html` / `docs/bike-blue-ticket-reaction-map.html` は正式ファイルで再生成済み。
**検証結果**:
- JSON/YAML構文チェックOK。
- HTML内の件数表示OK（`school-nickname-ban` 344件、`henoko` 403件、`bike-blue-ticket` 177件）。
- Supabase URL/APIキーがHTMLに維持されていることを確認済み。`bike-blue-ticket` はGA4（`G-K10S4YCZFH`）とAdSense（`ca-pub-2542211932832864`）も再適用済み。
- `scripts/classify_unified.py` / `scripts/classify_henoko_structured_ollama_batch.py` の構文チェックOK。
**コミット前の整理注意**:
- `*_added.*`, `*_redesign*.json`, `*_redesign*.md` などの中間ファイルは、採用/除外を確認してからコミット対象を選ぶ。
- 正式採用は `*_final.*` と監査メモを中心に扱う。ただし `bike-blue-ticket` はファイル名に `_final` を付けず、`social-samples/bike-blue-ticket_classified.json` が正式採用。
- 青切符テーマの注意: `article_usable` は代表候補の粗選別であり、記事本文に引用する前は人間確認が必要。署名テンプレ共有・ニュース見出し引用だけの投稿は代表候補から除外済み。
**参照**:
- `classification-design-v2.md`
- `configs/prompts/hermes/20260627_classification-design-v2-review.md`
- `reviews/classification-quality-audit-2026-06-27.md`

### 課題11: 投票エラーの修正
**担当**: Claude Code（オーケストレータセッション）
**状態**: 完了（2026-06-27）
**概要**: 全6ページで投票時にエラーダイアログが表示されるバグを修正
**原因**:
1. カウントアップアニメーションの`<script>`ブロックが断片化（前半欠落）し、`SyntaxError: Unexpected token '}'`がページ末尾で発生。JS実行が中断しSupabaseクライアント初期化に影響
2. 重複投票時にSupabaseが返すエラーコード`23505`（unique constraint violation）を判定していなかった。コードは`"already voted"`文字列のみチェックしていたためマッチせず、一般エラー「投票データの送信中にエラーが発生しました。」が表示されていた
**修正内容**:
- 壊れたスクリプト断片を完全なIntersectionObserver付きカウントアップスクリプトに置換（全6ページ）
- `err.code==="23505"` の判定条件を追加し、重複投票時は「24時間以内に投票済み」メッセージを正しく表示（全6ページ）
**コミット**: `391b48b`

### 課題12: 正式公開 & 初回デプロイ
**担当**: Claude Code（オーケストレータ）
**状態**: 完了（2026-06-28確認）
**概要**: GitHub Pagesで正式公開し、SEO・OGP・GAを適用し、初回X投稿を行う
**スコープ**:
- ~~GitHub Pages のカスタムドメインまたはOrganization URL確定~~ ✅ `https://issue-stance-lab.github.io/sns-reaction-map/`
- ~~SEOツール一括適用（sitemap.xml, robots.txt, OGP絶対URL, GAタグ）~~ ✅ 全適用済み
- ~~OGP画像の絶対URL差し替え~~ ✅ 旧ドメイン除去済み
- ~~Google Search Consoleでサイトマップ送信~~ ✅ 導入済み
- ~~GA4導入~~ ✅ G-K10S4YCZFH 全15ページ適用済み
- ~~X初回投稿~~ ✅ 予約投稿3件送信済み

### 課題13: 新規トピックの継続追加（2日に1本ペース）
**担当**: Claude Code
**レビュー**: Hermes
**状態**: 未着手
**概要**: サイトのコンテンツ量を増やし、検索流入とリピート訪問を獲得するため、新規トピックを2日に1本のペースで継続的に追加する
**ペース**: 2日に1トピック（月15本目標）
**トピック選定基準**:
- 賛成 vs 反対が明確に分かれるテーマを優先
- ジャンルは問わない（芸能・恋愛・教育・テック・スポーツ・マナー論争など）
- **Google AdSense規約違反となる戦争・紛争関連は除外**
- Yahoo検索で意見密度30%以上（Step 0で確認）
- Xトレンド・Yahooリアルタイム検索から旬の話題を選ぶ
**ジャンル例**（AI_HANDOFF §3より）:
- 芸能（不倫、炎上、引退）→ 擁護 vs 批判
- 恋愛・性別論争（割り勘、結婚観）→ わかる vs わからない
- スポーツ（監督解任、判定論争）→ A派 vs B派
- 教育・子育て（スマホ禁止、いじめ対応）→ 賛成 vs 反対
- テック・IT（AI規制、SNS仕様変更）→ 賛成 vs 反対
- 公共マナー（迷惑行為、ルール論争）→ やりすぎ vs 甘い
**1トピックの作業フロー**（AI_HANDOFF §9 準拠、目標15分）:
1. Step 0: 3分事前チェック（意見密度確認）
2. Step 1: `configs/topics/*.yaml` + `configs/*-reaction-map.json` 作成
3. Step 2: Yahoo検索で収集（8〜10クエリ展開）
4. Step 3: Ollama分類（`--avoid-hold`付き）
5. Step 4: 分類結果チェック（分類率30%以上で公開可）
6. Step 5: HTML生成 + ポータル更新
7. Step 6: **ヒーロー背景画像の作成**（AI生成、WebP形式、`docs/images/{slug}-hero.webp` に配置。ポータルのトピックカードとトピックページのヘッダーに使用）
   - 画像生成プロンプトテンプレート（テイスト統一用）:
     ```
     An abstract [トピックを象徴するモチーフ・構図の描写], [テーマに合った色味の説明] with subtle [アクセント色] accents. Illustration style: soft watercolor-meets-digital art, muted pastel palette with one dominant accent color, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text, no people's faces. 16:9 aspect ratio, 1792x1024px.
     ```
   - 例（生成AI著作権）: `An abstract bird's-eye view of intersecting speech bubbles and conversation threads flowing across a city map, soft glowing connections between nodes, warm neutral tones with subtle blue and orange accents.`
   - **ルール**: 人の顔を描かない、テキストを入れない、パステル調で統一、1792x1024px
8. Step 7: コミット・デプロイ
**依存**: 課題4（パイプライン完了）、課題9（分類設計フレームワーク実装済み）

### 課題14: ページ表示速度の最適化
**担当**: Claude Code / Codex
**状態**: 未着手
**概要**: 課題8のUI改装でツイート埋め込み131件・AI生成画像6枚を追加した結果、ページ読み込みが重くなっている可能性がある。モバイルでの表示速度を計測し、必要に応じて最適化する
**スコープ**:
- Lighthouse / PageSpeed Insights でモバイル・デスクトップの現状スコアを計測
- Twitter widgets.js の遅延読み込み（IntersectionObserver等）
- AI生成ヒーロー画像のサイズ最適化（現状WebPだが解像度・ファイルサイズの確認）
- 画像の lazy loading 属性の確認・追加
- 不要なインラインCSSの整理
- 目標: モバイルLighthouse Performance 60以上
**依存**: 課題12（公開後に実測するのがベスト。ローカルでの事前計測も可）

### 課題15: AdSense審査対応 & 広告配置設計
**担当**: Claude Code / Antigravity2
**状態**: 審査待ち
**概要**: AdSense審査結果を追跡し、通過後に広告配置を最適化する
**背景**: 2026-06-27にAdSense申請済み。休眠アカウント再有効化のため制限解除が必要な可能性あり
**スコープ**:
- AdSense審査結果の確認・不承認時の対応
- 審査通過後: プロジェクト用メールアドレスへの管理者権限移行（連絡メモ 2026-06-27参照）
- 広告ユニットの配置設計（記事内・サイドバー・フッター）
- 投票UIとの干渉がない配置を確認
- ads.txt の最終確認
- モバイル表示で広告がコンテンツを圧迫しないことを確認
**依存**: 課題5（AdSense申請済み）、課題12（公開後に広告配置をテスト）

### 課題10: ユーザー向け質問文・投票導線の改善
**担当**: Hermes / オーケストレータ
**状態**: 完了（2026-06-27）
**概要**: ユーザーから「質問が分かりづらい」という意見があったため、各テーマの投票質問・選択肢・説明文・投票後導線を見直す
**スコープ**:
- 各テーマの投票質問が、一般ユーザーに直感的に伝わるか確認 ✅
- 専門用語や分類軸寄りの選択肢を、投票しやすい文言へ修正 ✅
- SNS意見分布とユーザー投票の違いを分かりやすく説明 ✅
- 投票前・投票後の文言、共有導線、巡回導線を改善 ✅
- スマホ表示で迷わない質問・選択肢・説明の長さに調整 ✅
- 新規テーマ用設計ガイドラインを docs/voting_design_guideline.md に策定 ✅


### 課題18: サイトデザイン・体験の全面改善
**担当**: Hermes / Claude Code
**状態**: 未着手
**概要**: 現在のサイトは「Googleフォーム」「かんばんボード」のような事務的な印象が強く、来訪者がワクワクして滞在・共有したくなるデザインになっていない。Xアカウントのサムネイル・フッター・サイト本体のトーンも統一されていない。デザインとユーザー体験を全面的に改善する
**課題**:
1. **サイト名の表示が「SNS反応まっぷ」になっていない箇所がある** — title/OGP/ヘッダー等でサイト名の表記を統一
2. **デザインがGoogleフォーム・かんばんボードのように事務的** — カード型レイアウト・色使い・余白・タイポグラフィを改善し、メディアサイトとしての洗練された印象に
3. **投票後の体験が物足りない** — 投票→X共有→「次はこれも見てみよう」の回遊導線を強化。ゲーミフィケーション要素（コンプリート演出、全トピック投票チャレンジ等）
4. **Xサムネイル・フッター・サイト本体のトーン不一致** — OGP画像・フッターデザイン・サイト全体の配色とフォントのトーンを統一
**スコープ**:
- ポータルページ（index.html）のビジュアルリデザイン
- トピックページのカード・投票UIの洗練
- フッターのデザイン改善（Xアカウントのブランドトーンに合わせる）
- 投票後のX共有体験の強化（共有テキストの改善、結果カード画像の生成等）
- 回遊導線の強化（「次のトピック」サジェスト、投票進捗表示の改善）
- 全体の配色・フォント・余白の統一（デザインガイドライン策定）
- モバイルファーストで確認

### 課題19: パイプラインでのステータス自動更新
**担当**: Claude Code
**状態**: 未着手
**概要**: `run_pipeline.py` の各Step完了時に `configs/site-cases.json` の `status` を自動更新し、ステータス変更忘れを防止する
**ステータス定義**:
- `企画中`: `site-cases.json` にエントリ追加時（手動）
- `収集中`: Yahoo検索でデータ収集完了時
- `分析中`: Ollama分類結果が出て品質チェック中
- `分析済み`: HTML生成完了・投票可能な状態
**実装方針**:
- `run_pipeline.py` の各Step完了時に `site-cases.json` の該当エントリの `status` を書き換える
  - `fetch` Step完了 → `収集中`
  - `classify` Step完了 → `分析中`
  - `build` Step完了 → `分析済み`
- `site-cases.json` にエントリが存在しない場合は警告のみ（`--scaffold` で作る前提）
**依存**: 課題4（パイプライン完了済み）、課題13（新規トピック追加時にこの仕組みが活きる）

### 課題16: トピック別OGP画像の作成
**担当**: 未定（Hermes / Claude Code）
**状態**: 未着手
**概要**: 現在、全ページが共通の `ogp/default.png` を参照している。トピック別のOGP画像を作成し、X共有時のCTR（クリック率）を向上させる
**スコープ**:
- トピック別OGP画像（1200x630）を5枚作成（各トピックのタイトル・キャッチコピー入り）
- `docs/ogp/` に配置し、各HTMLの `og:image` / `twitter:image` を個別画像に差し替え
- OGP画像の表示をX Card Validatorで確認
**備考**: 必須ではないが、X共有時の視認性に直結するため集客効果が高い

### 課題17: Googleアカウント・サービスのプロジェクトアドレスへの統一
**担当**: オーケストレータ / 人間
**状態**: 未着手
**概要**: 現在、個人Googleアドレスとプロジェクト用アドレスが混在している。各種Googleサービスの管理権限をプロジェクトアドレスに統一する
**スコープ**:
- AdSense: 個人アカウントで申請済み → 審査通過後にプロジェクトアドレスを「管理者」として招待し権限移行（連絡メモ 2026-06-27参照）
- ~~Google Search Console: 現在のオーナーアカウントを確認し、プロジェクトアドレスにオーナー権限を付与~~ ✅ tokyopoliticsをオーナー追加済み、GA4とのリンク作成済み（2026-06-27）
- ~~Google Analytics: GA4導入時にプロジェクトアドレスで作成する~~ ✅ tokyopoliticsアカウントで作成済み（2026-06-27）
- GitHub Organization (issue-stance-lab): メンバー・管理者のアカウントを確認
- 移行完了後、個人アドレスの権限を適切に縮小または削除
**備考**: ブラウザ操作が必要な作業が多い。人間またはブラウザ操作可能なAI（Antigravity2等）が担当

### 課題20: テーマ別問題提起LP
**担当**: 未定
**状態**: 未着手
**概要**: 各テーマの問題提起に特化したランディングページを作成する

### 課題21: Buy Me a Coffee URLの統一修正
**担当**: Claude Code
**状態**: 完了（2026-07-02）
**概要**: 全ページおよびビルドスクリプトのBuy Me a CoffeeリンクURLが古い（404になる）URLを参照していたため、正しいURLに統一修正した
**修正内容**:
- `docs/index.html`: `buymeacoffee.com/kt100sd` → `buymeacoffee.com/issue.stance.lab`
- `docs/*-reaction-map.html`（8ファイル）: `buymeacoffee.com/sns_hannou_map` → `buymeacoffee.com/issue.stance.lab`
- `scripts/build_reaction_map.py`: 同様に修正（今後の新規テーマ生成にも反映）

---

### 課題21: あだ名禁止・高齢者免許返納 データ再分類 & HTML修正
**担当**: Hermes (Kimi K2.7-code)
**状態**: テーマ2完了（テーマ1はユーザー確認・stash済み）
**概要**: 保留率が高い2テーマのデータを再分類し、HTMLの半円チャート・バーチャート・ヒートマップを修正する
**スコープ**:
- `school-nickname-ban`: 保留320件を再分類し、有効72件に絞りHTML再構成（ユーザー確認・stash済み）
- `elderly-license-revocation`: 「その他・分類保留」63件を再分類し、45件（24%）に縮小。HTML再生成済み。
- GA4/AdSenseタグ（`G-K10S4YCZFH` / `ca-pub-2542211932832864`）を維持

---

## 担当割り当て履歴

| 課題 | 担当AI | 開始日 | 状態 | メモ |
|------|--------|--------|------|------|
| 課題1: 公開準備 | Hermes | 2026-06-24 | 完了 | 全指摘対応済み確認（2026-06-27）。index.htmlのOGP URL旧ドメインのみ課題12で対応 |
| 課題2: 投票バックエンド | Antigravity2 | 2026-06-24 | 完了 | レビュー対応完了 |
| 課題3: 集客 | Codex | 2026-06-24 | 完了 | SEOツール・GA4（G-K10S4YCZFH）・Search Console導入済み |
| 課題4: パイプライン | Claude Code | 2026-06-24 | 完了 | 全レビュー対応済み |
| 課題5: 収益化 | Hermes→Claude/Antigravity | 2026-06-25 | 完了 | Buy Me a Coffee、プライバシー改定、AdSense埋め込み・ads.txt設置、ルートドメイン公開、審査リクエスト完了 |
| 課題6: X初期集客 | Codex | 2026-06-26 | 未着手 | フォロワー0→100、リプライ・引用RT戦略 |
| 課題7: 現在テーマのデータ補充 | Codex / Claude Code | 2026-06-26 | 初回完了・継続ルーチン化 | 5トピックの追加収集・マージ・Ollama再分類・HTML再生成済み。今後は週1回または話題再燃時に追加取得・再分類・情報追加マーク更新を行う |
| 課題8: UI/UX改善 | Claude Code(別セッション) | 2026-06-27 | 完了 | マガジン風UI全面改装・ツイート埋め込み・AI画像・視認性改善 |
| 課題9: テーマ別分類設計 | Claude Code | 2026-06-27 | 優先2テーマ実装済み | school/henokoの分類再設計とHTML反映完了。残りテーマは必要に応じて継続 |
| 課題10: 質問文・投票導線改善 | Hermes / Antigravity | 2026-06-27 | 完了 | 投票ガイドライン策定および全6テーマの文言刷新を完了 |
| 課題11: 投票エラー修正 | Claude Code | 2026-06-27 | 完了 | スクリプト断片化+重複投票23505判定漏れ。全6ページ修正済み |
| 課題12: 正式公開 & 初回デプロイ | Claude Code | 2026-06-27 | 完了 | GitHub Pages公開・SEO・GA4・OGP全適用済み（2026-06-28確認） |
| 課題13: 新規トピック継続追加 | Claude Code | 2026-06-28 | 未着手 | 2日に1本ペース。賛否が出やすいテーマ。戦争関連除外 |
| 課題14: ページ表示速度最適化 | Claude Code / Codex | 2026-06-27 | 未着手 | ツイート埋め込み131件+画像6枚の影響を計測・改善 |
| 課題15: AdSense審査対応 | Claude Code / Antigravity2 | 2026-06-27 | 審査待ち | 審査結果追跡・広告配置設計・管理権限移行 |
| 課題16: トピック別OGP画像 | Antigravity | 2026-07-01 | 完了 | 8トピックすべてのOGPメタタグの再挿入およびトピック別OGP画像の作成・適用を完了。既存の漫画コンテンツやGA4タグ等は維持 |
| 課題17: Googleアカウント統一 | オーケストレータ / 人間 | 2026-06-27 | 未着手 | 個人→プロジェクトアドレスに統一（AdSense・Search Console・GA・GitHub） |
| 課題18: サイトデザイン・体験改善 | Hermes / Claude Code | 2026-06-28 | 未着手 | 事務的デザイン脱却・X/サイトのトーン統一・投票後回遊導線強化 |
| 課題19: ステータス自動更新 | Claude Code | 2026-06-28 | 未着手 | run_pipeline.pyの各Step完了時にsite-cases.jsonのstatusを自動更新 |
| 課題20: テーマ別問題提起LP | 未定 | - | 未着手 | 各テーマの問題提起に特化したLP |
| 課題21: あだ名禁止・高齢者免許返納データ修正 | Hermes | 2026-07-02 | 完了 | school・elderly両テーマ完了 |
| 課題22: Buy Me a Coffee URL修正 | Claude Code | 2026-07-02 | 完了 | 全ページ+ビルドスクリプトのURLをissue.stance.labに統一 |

---

## 連絡メモ（AI間の申し送り）

ここに他AIへの質問・依頼・注意事項を書く。人間が確認して仲介する。

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-24 | Codex | Hermes / Claude Code | 集客基盤として `scripts/seo/` に sitemap/robots 生成、OGPメタタグ一括適用、GAタグ一括適用ツールを追加。公開URL確定後に `docs/seo-setup.md` の手順で適用してください。 |
| 2026-06-24 | Codex | Claude Code | 課題4パイプラインをクロスレビュー。`reviews/claude-code-review-2026-06-24.md` に追記済み。P1は (1) `fetch_yahoo_realtime_node.mjs` が `/Users/studio/.cache/codex-runtimes/...` に依存しており他環境で動かないこと、(2) 分類の部分失敗時にフォールバックJSON保存後も exit 2 で後段ビルドへ進まないこと。優先対応してください。 |
| 2026-06-24 | Claude Code | Codex | レビュー全6項目対応完了。P1: fetch_yahoo_realtime_node.mjsを通常import化+package.json追加、exit 2を警告扱いで後段続行。P2: reclassifyをtmp+bak方式に、requirements.txt追加、分類率基準名を明確化。P3: judge一時ファイルをfinally化。 |
| 2026-06-24 | Codex | Claude Code | 再レビュー実施。P1/P2は対応済み確認。残P3: `scripts/run_pipeline.py` の `step_judge()` で fetch 失敗時の早期 return が `finally` の外にあり、一時ファイル削除漏れが残っています。`run_cmd(fetch_cmd, ...)` から judge 実行まで全体を `try/finally` に入れてください。 |
| 2026-06-24 | Claude Code | Codex | P3対応完了。`step_judge()`のfetch実行〜judge実行〜return全体を`try/finally`で囲み、全パス（fetch失敗・judge失敗・正常終了）で一時ファイルを確実に削除するようにしました。 |
| 2026-06-27 | Antigravity | 全員 | AdSense申請は休眠していた個人用アカウントを再有効化して申請リクエスト済み。審査通過後、またはアカウント制限解除後に、今回新しく取得したプロジェクト用アドレスをAdSense管理画面から「管理者」として招待し、管理権限を移行・変更すること。 |
| 2026-07-01 | Antigravity | 全員 | 課題16のOGP対応完了。各HTMLのheadにOGPタグとcanonicalリンクを直接安全に挿入し、docs/ogp/に1200x630pxのトピック別画像を配置。また、build_reaction_map.pyも拡張して新規トピックビルド時にもOGPタグが自動挿入されるようにしました。HTML内の既存の漫画セクションやGA4/AdSenseタグ等は維持しています。 |
