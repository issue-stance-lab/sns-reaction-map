# AI引き継ぎメモ — SNS反応まっぷ

最終更新: 2026-06-22（あだ名禁止トピック追加・10クエリ展開運用確立）

この文書は、どのAIエージェント（Claude, Hermes, ChatGPT, Gemini等）がこのプロジェクトを扱っても同じ運用方針で動けるようにするための引き継ぎドキュメント。

---

## 1. ミッション

SNSで意見が割れる話題を可視化し、「あなたはどっち？」で閲覧者の参加を促す独立メディアサイト。

キャッチコピー: **「その話題、SNSでは実はどっちが多い？」**

AIに「どちらが正しいか」を決めさせるのではなく、意見・論点・根拠・不確実性を分解して表示する。

---

## 2. サービス概要

| 項目 | 内容 |
|------|------|
| サービス名 | SNS反応まっぷ |
| 形態 | 静的HTMLサイト（GitHub Pages） |
| URL構造 | `/topic/slug.html`（フラット） |
| ターゲット | SNSで話題を見て「みんなどう思ってるの？」と気になる一般ユーザー |
| 差別化 | 投票参加型 + AI自動分類による意見分布の可視化 |

---

## 3. ジャンル戦略

**政治だけに絞らない。** バイラル性の高いジャンルから始めて認知を拡大し、政治は権威性として後から活かす。

### 優先度順

| 優先度 | ジャンル | 理由 |
|--------|---------|------|
| ⭐最優先 | 芸能（不倫、炎上、引退） | 頻度⭐5, バイラル⭐5 |
| ⭐最優先 | 恋愛・性別論争（割り勘、結婚観） | 頻度⭐5, バイラル⭐5 |
| 高 | スポーツ（監督解任、判定論争） | 投票相性⭐5 |
| 高 | 教育・子育て（スマホ禁止、いじめ対応） | 広告単価⭐4 |
| 中 | テック・IT（X仕様変更、AI規制） | 広告単価⭐5 |
| 既存 | 政治・社会（憲法、選挙） | 投票相性⭐5だがバイラル⭐2 |

### 汎用対立軸テンプレート（5パターンで全ジャンル対応）

| テンプレート | 適用場面 |
|-------------|---------|
| 賛成 vs 反対 | 政治・社会・制度変更 |
| 擁護 vs 批判 | 芸能・企業スキャンダル |
| A派 vs B派 | スポーツ・作品評価 |
| わかる vs わからない | 恋愛・マナー・日常論争 |
| やりすぎ vs 甘い | 処分・対応・ルール論争 |

ブランド名「SNS反応まっぷ」は変更しない（SEO損失回避）。ジャンルはカテゴリタグで整理する。

---

## 4. 技術スタック

### パイプライン

```
Yahoo検索 → Ollama分類 → HTML生成 → GitHub Pages → X投稿で集客
```

| ステップ | ツール | スクリプト |
|---------|-------|----------|
| 収集 | Yahooリアルタイム検索 | `scripts/fetch_yahoo_realtime_node.mjs`（Node.js/Playwright版 ← 推奨）, `scripts/fetch_yahoo_realtime.py` |
| 分類 | Ollama qwen2.5:7b（ローカル） | `scripts/classify_unified.py` |
| 設定 | YAML/JSONトピック設定 | `configs/topics/*.yaml`（分類ルール）, `configs/*-reaction-map.json`（HTML設定） |
| HTML生成 | Python | `scripts/build_reaction_map.py` |
| ポータル | Python | `scripts/build_site_portal.py`（`configs/site-cases.json` を読んで `docs/index.html` を生成） |
| まとめUI | Python | `scripts/build_summary_ui.py` |
| DB | SQLite | `data/reaction_map.sqlite3` |

### Ollama分類

```bash
ollama serve   # 事前に起動
```

推奨モデル: `qwen2.5:7b`

注意:
- まず `--limit 10` でテストする。
- OllamaのJSON出力が崩れることがあるため、スクリプト側でバッチ失敗時に1件ずつ再試行する。
- 件数は世論比率ではなく、収集サンプル内の分類件数として扱う。
- `--avoid-hold` フラグを付けると「保留」になりやすい投稿を再分類しようとする（精度向上に有効）。

### 分類率の目安と解釈

| 勢力図比率（主要カテゴリの割合） | 評価 |
|-------------------------------|------|
| 30%以上 | ◎ 勢力図として十分成立 |
| 15〜30% | ○ 最低限の勢力図は成立 |
| 10〜15% | △ 「その他」が目立つが公開可。免責注記を強調 |
| 10%未満 | ✗ トピックかクエリを見直す |

※ この基準は「主要カテゴリ（賛成+反対等）がサンプル全体に占める割合」。Step 5の「分類済み率」（保留を除く率）とは別指標。

**「その他・分類保留」が多い主な理由:**
1. キーワードヒット件数は多くても、投稿内容の大半が「撮影した写真のシェア」「ニュースの転載のみ」など意見を持たないもの（例: ライブ撮影トピック）
2. 検索クエリが広すぎて無関係な投稿を大量に巻き込んでいる（例: 「さん付け」→ドラマ・芸能の「さん付け」が混入）
3. Ollamaが分類に自信を持てず保留とする

→ **対策**: クエリを意見表明が含まれやすい形（「〇〇 賛成」「〇〇 反対」「〇〇 おかしい」「〇〇 やりすぎ」等）に変えてみる。

### 構造化分類v2の主要フィールド

| フィールド | 意味 |
|-----------|------|
| `category` | 最終カテゴリ |
| `topic_target` | 大きな話題 |
| `actor_target` | 評価対象の主体 |
| `criticized_target` | 実際に批判されている対象 |
| `stance_to_target` | 主対象への態度 |
| `stance_to_quoted_author` | 引用元の人物・媒体への態度 |
| `stance_to_quoted_claim` | 引用元の主張内容への態度 |
| `confidence_level` | `high` / `medium` / `low` |
| `review_required` | 人間確認が必要か |

重要: `stance_to_quoted_author` と `stance_to_quoted_claim` は区別する。引用元に反対していても主張内容には賛成のケースがある。

---

## 5. 投票UI仕様

各反応まっぷページに投票セクションがある。

### 構成

1. **トピック導入文**（`vote_intro`） — 問題の背景を2-3行で説明
2. **データ収集方法の説明**（`vote_method`） — Yahoo検索で何件取得しAI分類したか
3. **投票ボタン**（`vote_labels`） — ユーザーフレンドリーな4択
4. **半円チャート**（投票前はブラー） — 投票後に結果と一緒にSNS意見分布を表示
5. **投票結果** — パーセンテージバー + X共有ボタン

### 技術詳細

- 投票データはlocalStorageに保存（バックエンドなし）
- 半円チャートは投票前に `blur(8px)` + 「まず投票してから結果を見よう」オーバーレイ
- DOMContentLoadedでブラー適用（投票UIがチャートより先にDOMに出るため）
- 投票ラベルは技術的な分類軸ではなく、一般ユーザーが直感的に選べる文言にする

### config JSONの投票関連フィールド

```json
{
  "vote_intro": "問題の背景説明...",
  "vote_method": "Yahooリアルタイム検索からSNS投稿183件を取得し...",
  "vote_labels": ["選択肢1", "選択肢2", "選択肢3", "まだ判断できない"]
}
```

---

## 6. 収益化ロードマップ

| フェーズ | 条件 | 手段 |
|---------|------|------|
| Phase 1（現在） | 開始直後 | ☕ Buy Me a Coffee（全ページフッターに設置済み） |
| Phase 2 | 月1万PV | Google AdSense + Amazonアフィリエイト |
| Phase 3 | 月5万PV | note有料レポート + 企業タイアップ |

Buy Me a Coffee URL: `https://www.buymeacoffee.com/sns_hannou_map`（仮。正式登録後に差し替え）

---

## 7. 日次運用フロー（1人45分/日、週3更新）

| 時間 | 作業 | 所要 |
|------|------|------|
| 9:00 | Xトレンド巡回 → ネタ選定 | 15分 |
| 9:15 | config JSON作成 → Yahoo収集 → Ollama分類 | 15分（大半自動） |
| 9:30 | 誤分類チェック → HTML生成 → デプロイ | 10分 |
| 9:40 | X投稿（テンプレ使用） | 5分 |

ボトルネックは「ネタ選定」と「誤分類チェック」の2つだけ。収集・分類・HTML生成はすべて自動化済み。

---

## 8. X投稿テンプレート

```
【投票】{話題}、あなたはどう思う？SNSでは意見が真っ二つ。4択で教えて→ {URL} #SNS反応まっぷ
```

```
{A}派？{B}派？SNSの声を集計してみたら意外な結果に。あなたも投票→ {URL} #SNS反応まっぷ
```

```
{話題}、賛否どっち？4択で意見募集中。SNSではこんな声が→ {URL} #SNS反応まっぷ
```

煽りすぎず、好奇心を引き、投票参加を促すトーン。

---

## 9. 新トピック追加手順

### Step 0: 3分事前チェック（必ず最初にやる）

トピック候補を思いついたら、**作業に入る前にYahoo検索1-2回で適性を判定**する。

```bash
node scripts/fetch_yahoo_realtime_node.mjs --query "候補キーワード" --output /tmp/test.json
```

**判定基準（Hermes提案、生成AI著作権トピックで実証済み）:**

1. `total_available` を確認 → **100件未満なら即見送り**
2. 出力の最初の20件を目視 → 「意見っぽい投稿」を数える
3. 意見密度 = 意見数 / 20

| 意見密度 | 判定 |
|---------|------|
| 50%以上 | ✅ Go |
| 30-49% | ⚠ 別キーワードで追加検証 |
| 30%未満 | ❌ 見送り |

**意見にカウントするもの:** 賛否表明、感想（「やりすぎ」「気持ち悪い」等）、批判、提案
**カウントしないもの:** ニュース転載、広告、無関係な雑談、URL単体

### Step 0.5: 検索クエリ設計（最重要）

**日常トピックの最大の罠は「キーワードが日常会話でも使われる」こと。**

| ❌ 悪いクエリ | ✅ 良いクエリ |
|-------------|-------------|
| 「学校 あだ名」→ 思い出話が混入 | 「あだ名禁止 賛成 OR 反対 OR やりすぎ」 |
| 「ライブ スマホ 撮影」→ 写真シェアが混入 | 「ライブ 撮影禁止 賛否」 |
| 「ガチャ 課金 やりすぎ」→ 自分の課金反省 | 「ガチャ 規制 賛成 OR 反対」 |

**設計原則:**
- **意見誘発語を含める**: 「賛成 OR 反対 OR やりすぎ OR どう思う OR おかしい」
- **制度・ルールを示す語を含める**: 「禁止」「規制」「義務化」「廃止」
- **賛成側と反対側の両方のクエリを作る**（偏り防止）
- 合計8-10クエリで多角的に収集

**実績比較（2026-06-22実証）:**
- あだ名禁止（旧方式クエリ）: 112件中17件分類成功 = **15%**
- 生成AI著作権（改善版クエリ）: 475件中339件分類成功 = **71%**

### Step 1: ネタ選定

Xトレンドから意見が割れている話題を選ぶ。

**向いているトピックの条件:**
- 「規制・権利・ルールのトレードオフ」が存在する
- 好き/嫌いではなく賛成/反対の構造的対立がある
- 今SNSで活発に議論されている（total_available 100件以上）

**向いているジャンル:** 政治・社会規制、教育規制、公共ルール、マナー論争、テック規制
**向いていないジャンル:** 推し活、味覚・趣味の好み、意見でなく感想が主の話題

### Step 2: 設定ファイル作成

- `configs/topics/{slug}.yaml` — Ollama分類ルール
  - categories（6-8個）
  - classification_rules（**Few-shot例を含める** ← 暗黙意見の読み取りに必須）
  - rule_overrides（キーワードマッチ）
  - avoid_hold_rules（保留再分類用）
- `configs/{slug}-reaction-map.json` — HTML/投票UI設定
- `configs/site-cases.json` に新エントリを追加

**Few-shot例の書き方（YAMLの `few_shot_examples` または `classification_rules` 内に記載）:**
```yaml
few_shot_examples:
  - text: "なんか窮屈だよね"
    category: "反対カテゴリ名"
    reason: "制度への否定的感情を表明"
  - text: "子供の気持ち考えると仕方ない"
    category: "賛成カテゴリ名"
    reason: "配慮重視で制度を容認"
```

### Step 3: Yahoo検索で収集（両側クエリ展開）

```bash
node scripts/fetch_yahoo_realtime_node.mjs \
  --query "規制賛成側キーワード1" \
  --query "規制賛成側キーワード2" \
  --query "規制賛成側キーワード3" \
  --query "規制反対側キーワード1" \
  --query "規制反対側キーワード2" \
  --query "中立・広めキーワード1" \
  --query "中立・広めキーワード2" \
  --query "中立・広めキーワード3" \
  --dedupe \
  --output social-samples/{slug}_samples.json \
  --markdown social-samples/{slug}_samples.md
```

⚠️ **タイムアウト対策**: `waitUntil: "domcontentloaded"` を使う（スクリプト55行目）。

### Step 4: Ollama分類

```bash
python3 scripts/classify_unified.py \
  --topic {slug} \
  --input social-samples/{slug}_samples.json \
  --output social-samples/{slug}_classified.json \
  --markdown social-samples/{slug}_classified.md \
  --model qwen2.5:7b \
  --batch-size 3 \
  --timeout 180 \
  --avoid-hold
```

### Step 5: 分類結果チェック

```bash
python3 -c "
import json
from collections import Counter
data = json.load(open('social-samples/{slug}_classified.json'))
cats = Counter(d.get('classification',{}).get('category','?') for d in data)
total = len(data)
others = cats.get('その他・分類保留', 0)
print(f'分類率: {(total-others)*100//total}%  ({total-others}/{total})')
for k,v in cats.most_common(): print(f'  {v:3d}  {k}')
"
```

| 分類率 | 判定 |
|--------|------|
| 60%以上 | ◎ そのまま公開 |
| 30-59% | ○ 公開可。クエリ追加で改善余地あり |
| 10-29% | △ クエリ設計を見直すか、Few-shot例を追加 |
| 10%未満 | ✗ トピックかクエリを根本的に変更 |

### Step 6: HTML生成

```bash
python3 scripts/build_reaction_map.py \
  --config configs/{slug}-reaction-map.json \
  --input social-samples/{slug}_classified.json \
  --output docs/{slug}-reaction-map.html
```

### Step 7: ポータル再生成

```bash
python3 scripts/build_site_portal.py
```

### Step 8: ローカル確認

```bash
python3 -m http.server 8123 --directory docs
# → http://localhost:8123
```

### Step 9: デプロイ + X投稿

```bash
git add -A && git commit -m "add: {slug} topic" && git push
```

X投稿テンプレートで告知。

### config JSONの必須フィールド

```json
{
  "title": "トピック名 SNS反応まっぷ",
  "subtitle": "説明文...",
  "source_label": "Yahooリアルタイム検索",
  "vote_intro": "背景説明...",
  "vote_method": "収集方法の説明...",
  "vote_labels": ["選択肢1", "選択肢2", "選択肢3", "まだ判断できない"],
  "nav_links": [...],
  "category_order": [...],
  "conflict_axes": [...],
  "category_tones": {...}
}
```

---

## 10. 現在のトピック一覧

| トピック | ファイル | ジャンル | 件数 | ステータス |
|---------|---------|---------|------|----------|
| 高市文春問題 | `docs/takaichi-reaction-map-standard.html` | 政治 | 183件 | 公開済み |
| 憲法改正論議 | `docs/constitutional-amendment-reaction-map.html` | 政治 | — | 企画中 |
| 辺野古高校生死亡事故 | `docs/henoko-student-accident-reaction-map.html` | 社会 | 311件 | 分析中 |
| 学校でのあだ名禁止の是非 | `docs/school-nickname-ban-reaction-map.html` | 教育・日常論争 | 201件（賛成13/反対20） | 分析済み |
| 生成AIと著作権問題 | `docs/ai-copyright-reaction-map.html` | テック・著作権 | 475件（分類率71%） | 分析済み ✅ |

### あだ名禁止トピックの分類設計メモ

- **賛成軸**: いじめ防止・心理的安全（6件）＋ジェンダー配慮（7件）
- **反対軸**: 親しみが薄れる（13件）＋本質論で反対（6件）
- **第3軸**: ルール運用（柔軟対応）（2件）
- 「さん付け」クエリは件数が多い（615件）が、ドラマ・芸能の「さん付け」が混入するため分類率が低くなりやすい
- 「あだ名 さん付け」「小学校 あだ名」クエリのほうが意見系投稿の比率が高い（推奨）

---

## 11. ディレクトリ構造

```
issue-stance-aggregator/
├── AI_HANDOFF.md          ← この文書
├── configs/               ← トピックごとのJSON設定
├── data/                  ← SQLite DB
├── docs/                  ← 公開HTML（GitHub Pages）
│   ├── index.html         ← ポータルページ
│   ├── *-reaction-map.html
│   └── *-summary.html
├── research/              ← Hermes調査結果
├── scripts/               ← Python収集・分類・生成スクリプト
├── social-samples/        ← 分類済みJSONデータ
└── social-classification-ollama.md
```

---

## 12. Hermesの使い方

Hermes Agent CLIはこのMacにインストール済み。戦略相談・レビューに使う。

```bash
/Users/studio/.local/bin/hermes chat -Q --max-turns 1 -q "質問内容"
```

| 用途 | 推奨ツール |
|------|----------|
| 大量SNS分類 | Ollama |
| UI・スクリプト実装 | Claude / Codex |
| 戦略・企画相談 | Hermes |
| 分類設計レビュー | Hermes |
| トレンド調査 | Hermes |

注意: Hermesは外部API経由のため、SNS投稿本文などの生データは渡さない。一般化した質問にする。

---

## 13. 絶対ルール

- SNS投稿の分類結果は「世論」ではなく「収集サンプル内の傾向」として扱う。
- 政治的立場をAIが決めつけているように見せない。
- 攻撃的表現は記事では中和して要約する。
- 被害者・未成年・事故関連は特に慎重に扱う。
- 公開前に代表投稿は必ず人間が確認する。
- UIでは「AI分類の限界」と「収集範囲」を明記する。
- 投票ラベルは一般ユーザー向けの平易な日本語にする（分析用語を使わない）。
- 投票UIは「まず投票→結果表示」の順にし、チャートで先入観を与えない。
- SNS投稿の全文転載は避け、要約とリンク中心にする。

---

## 14. 次にやること（優先順）

1. ~~非政治トピック1件を作成して汎用性を証明する~~ ✅ 完了（あだ名禁止 2026-06-22）
2. ~~分類率を改善するためのクエリ設計見直し~~ ✅ 完了（生成AI著作権トピックで71%達成 2026-06-23）
3. GitHub Pagesでサイトを正式公開する
4. Buy Me a CoffeeのURLを正式登録して差し替える
5. X投稿テンプレートで初回投稿する（生成AI著作権ページが最もバズりやすい）
6. 週3ペース（月水金）で運用を開始する

---

## 15. 2026-06-22 セッション運用記録

### 実施内容

**目的**: 非政治トピック第1号の作成・公開準備

**トピック選定プロセス:**
1. Yahoo検索で複数候補の件数を同時取得して比較
2. `ライブ 撮影`が1,131件で最多 → 実際に収集すると117件中102件（87%）が「撮影した写真のシェア」「撮影可公演の告知」で分類不能
3. `学校 あだ名`（369件）に変更 → 意見系投稿の比率がより高く、分類率が改善

**確立した運用ノウハウ:**

| 知見 | 内容 |
|------|------|
| 検索ヒット数 ≠ 分類可能数 | 「1,131件」でも意見投稿は数十件のことがある。「ヒット数の多さ」よりも「論争性の高さ」を重視してキーワード選定する |
| 10クエリ展開戦略 | 1キーワードで40件取得するより、10種のキーワードで各40件→重複排除した方が多様な意見層をカバーできる |
| `networkidle`タイムアウト問題 | `fetch_yahoo_realtime_node.mjs`の`waitUntil: "networkidle"`は広告など非同期リクエストの影響でタイムアウトしやすい。`"domcontentloaded"`に変更（55行目）で解決 |
| 分類不能80%超でも公開可 | 「その他の相対値が増えてもよい」（ユーザー確認済み）。勢力図の絶対数が賛成10件・反対15件以上あれば掲載に耐える |
| Ollamaの`--avoid-hold`フラグ | 保留になりやすい投稿を積極的に再分類させる。分類率5〜10%程度の改善効果あり |

**スクリプト修正履歴:**
- `scripts/fetch_yahoo_realtime_node.mjs` L55: `waitUntil: "networkidle"` → `"domcontentloaded"`、タイムアウト60s → 90s

**生成ファイル:**
- `configs/topics/school-nickname-ban.yaml`
- `configs/school-nickname-ban-reaction-map.json`
- `social-samples/school-nickname-ban_samples_v2.json`（201件、10クエリ収集・重複排除）
- `social-samples/school-nickname-ban_classified_v2.json`（分類済み、賛成13/反対20/その他166）
- `docs/school-nickname-ban-reaction-map.html`
