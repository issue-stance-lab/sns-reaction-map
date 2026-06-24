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

入力形式は `templates/reaction-map-input.schema.md` に合わせる。

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
cp templates/reaction-map-config.template.json configs/<topic>-reaction-map.json
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
