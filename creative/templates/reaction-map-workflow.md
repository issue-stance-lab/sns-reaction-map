# SNS反応まっぷ 標準ワークフロー

## 目的

別テーマでも同じ画面構成で、SNS反応の分類結果を可視化する。

基本の見せ方:

- 分類別件数
- カテゴリ × 検索クエリ
- カテゴリ × スタンス
- 代表サンプル
- 注意書き

## 1. 分類済みJSONを用意

入力形式は `creative/templates/reaction-map-input.schema.md` に合わせる。

分類基盤はOpenCode Go APIの `minimax-m2.7`。テーマ固有の2D分類スクリプトで
10件テストを行い、合格後に全量実行する。Ollamaはローカル予備として使用する。

最低限必要な項目:

- `query`
- `text`
- `url`
- `classification.category`
- `classification.stance`
- `classification.summary`

## 0. 事前判定

本収集の前に、少量サンプルで「SNS反応まっぷ」として成立するかを判定する。

まず検索クエリ案を出す。

```bash
python3 scripts/trend_judge.py \
  --topic "ライブ中のスマホ撮影OK？" \
  --print-queries
```

Yahooリアルタイム検索で少量サンプルを取得する。

```bash
node scripts/fetch_yahoo_realtime_node.mjs \
  --query "ライブ中のスマホ撮影OK" \
  --query "ライブ スマホ撮影 迷惑" \
  --query "ライブ 撮影禁止 おかしい" \
  --dedupe \
  --output social-samples/<topic>_judge_samples.json \
  --markdown social-samples/<topic>_judge_samples.md
```

Trend Judgeで GO / HOLD / NG を判定する。

```bash
python3 scripts/trend_judge.py \
  --topic "ライブ中のスマホ撮影OK？" \
  --slug live-smartphone-ok \
  --input social-samples/<topic>_judge_samples.json \
  --output social-samples/<topic>_trend_judge.json \
  --markdown social-samples/<topic>_trend_judge.md
```

判定基準:

- `GO`: 本収集してページ化する
- `HOLD`: クエリ変更、続報待ち、別角度で再調査
- `NG`: ページ化しない

## 2. テーマ設定を作る

テンプレートをコピーする。

```bash
cp creative/templates/reaction-map-config.template.json configs/<topic>-reaction-map.json
```

変更する項目:

- `title`
- `subtitle`
- `category_order`
- `stance_order`
- `notes`

## 3. HTMLを生成

```bash
python3 scripts/build_reaction_map.py \
  --input social-samples/<topic>_classified.json \
  --config configs/<topic>-reaction-map.json \
  --output docs/<topic>-reaction-map.html
```

## 3.1. 共通テーマUIを適用

生成後は `creative/templates/topic-page-v3.md` を正典として、既存テーマと同じヒーロー・要約・注目指標を適用する。

必須項目:

- `site-tokens.css?v=2`、`topic-modern.css?v=23`、`topic-modern.js?v=8` を読み込む
- `<body class="summary-on-light">` に `--topic-hero-image` を設定
- 題名下の分析方法を次の共通文にする

```text
収集したSNS投稿のうち、分析対象となった意見{分析対象件数}件をAIが{論点数}つの論点に整理しました。世論調査ではなく、SNS反応サンプルの論点比較です。
```

- `.thirty-summary` は「まず結論 / 今回の分析で見えたこと」と3つの要点
- ヒーロー直下は `.stats.insight-stats` を使い、「分析対象の意見」とテーマ固有の重要な発見を表示
- 論点解説の見出しは「このテーマを読み解く、{論点数}つの論点」
- 収集件数、重複除去、使用モデルなどの工程詳細は「調査概要」へ置く

公開前に `configs/theme-seo.json` へ、検索タイトル、description、根拠のある公開日・更新日、収集方法を登録し、共通の信頼性情報とArticle構造化データを適用する。

```bash
python3 scripts/seo/apply_theme_trust.py --check
python3 scripts/seo/apply_theme_trust.py
```

- `datePublished` / `dateModified` は `THEMES.yaml` の `published_at` / `updated_at` など、リポジトリ内で確認できる日付だけを使う
- 技術的な再生成だけで、分析内容の最終更新日を新しくしない
- 編集・分析主体は個人名を推測せず、個人運営プロジェクトの編集名義 `SNS反応まっぷ編集部` と `about.html` を使用する
- 既存の「データの集め方」は共通の信頼性情報欄へ統合し、重複表示しない

注目指標は4枚を基本とするが、テーマに必要な場合は追加できる。候補と選定基準は `creative/templates/topic-page-v3.md` の「1.3 ヒーロー直下の注目指標」を参照する。

## 3.5. 漫画コンテンツを生成

分類データの対立軸が確定した後、ショートコミック（4コマ）のデータを生成する。

### 手順

1. `configs/<topic>-reaction-map.json` の `conflict_axes` と分類済みデータから対立構造を把握
2. 対立する2名の当事者キャラクターを設定
3. キャラクターシート生成用プロンプト（Step 1）を作成
4. Gptimage2でキャラクターシートを生成（手動）
5. 4コマの構成・セリフ・画像生成プロンプト（Step 2）を作成
6. Gptimage2でコマ画像を生成（手動、キャラクターシートを参照画像として添付）
7. 生成画像をWebP形式に変換・圧縮（1枚100KB以下）
8. `configs/<topic>-reaction-map.json` の `manga` フィールドにデータを格納

### 出力先

- 画像: `docs/images/topics/<topic>/<topic>-manga-panel-{1-4}.webp`
- データ: `configs/<topic>-reaction-map.json` の `manga` フィールド

### スキーマ

`creative/templates/manga-content.schema.md` を参照。

### 注意

- 画像生成（Step 1, 2）は手動操作。それ以外は自動化可能。
- 漫画セクションには「※ この漫画はSNS上の代表的な意見をもとに構成したフィクションです」の注記を必ず含める。
- 実在の個人が特定できるキャラクター設定は禁止。

## 4. Substack用PNGを生成

Playwrightが入ったPython環境で実行する。

```bash
python3 scripts/capture_reaction_map_png.py \
  --html docs/<topic>-reaction-map.html \
  --output-dir docs \
  --prefix <topic>-reaction-map
```

出力:

- `<topic>-reaction-map-full.png`
- `<topic>-reaction-map-category-counts.png`
- `<topic>-reaction-map-by-query.png`
- `<topic>-reaction-map-by-stance.png`
- `<topic>-reaction-map-samples.png`

## 5. Substackでの使い分け

無料版:

- `<topic>-reaction-map-by-query.png`
- 簡易スコアカード
- 判定のみ

有料版:

- `<topic>-reaction-map-by-stance.png`
- 代表反応要旨
- 投稿URL
- 採点理由
- 危ない論点

## 注意

- この画面は世論調査ではなく、取得サンプルの反応整理。
- 公開記事では投稿本文を大量転載しない。
- 代表投稿は「要旨 + URL」を基本にする。
- 分類結果はAI出力なので、記事に使う代表例は人間が確認する。

## 公開前UIチェック

- 全テーマ共通のヘッダー、白いヒーロー、右側フェード画像になっている
- 分析方法は数字以外が共通文と一致している
- 「まず結論」と注目指標の件数が分類データと一致している
- 「このテーマを読み解く、○つの論点」の数と実際の論点数が一致している
- 論点インフォグラフィックがパネル内幅いっぱい・比率1915:821で統一され、文字や数値が見切れていない
- 投票2問目の補足が「選ぶと結果を表示します」で統一され、「← 論点を選び直す」が全テーマで同じ位置に表示される
- 投票2問目の回答ボタンがPCで等幅・等高、720px以下で1列になり、「選ぶ」が各カード下端に揃う
- 戻るボタンから未送信のまま1問目へ戻れる
- 3000px以上スクロールしても共通ヘッダーが画面上端に固定される
- 1280pxと390pxでヒーロー高、折り返し、横スクロールを確認する
- コンソールのerror/warnがない
