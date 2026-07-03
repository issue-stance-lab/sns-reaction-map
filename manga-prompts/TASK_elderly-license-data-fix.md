# 課題21（後半）: 高齢者免許返納 — 保留63件の再分類 & HTML修正

**担当**: Hermes (Kimi K2.6)

## 作業の前に
- `Agent.md` と `TASK_BOARD.md` を読んでください
- 再分類はOllamaではなく、あなた（Hermes）が投稿テキストを直接読んでカテゴリを判定してください

## リポジトリ
https://github.com/issue-stance-lab/sns-reaction-map.git
ブランチ: `task/21-nickname-elderly-data-fix`（既存ブランチを使用）

## 背景
課題21の前半（school-nickname-ban）は完了済み。後半の高齢者免許返納が未対応のため、この作業をお願いします。

---

## 現状データ

**ファイル**: `social-samples/elderly-license-revocation_classified.json`（183件）

| カテゴリ | 件数 |
|---------|------|
| 免許返納義務化に賛成（高齢運転手の事故防止を最優先） | 68件 |
| **その他・分類保留** | **63件** ← これを減らす |
| 免許返納義務化に反対（地方の生活維持や移動手段確保を重視） | 19件 |
| 自主返納のインセンティブ強化（特典や支援）を進めるべき | 15件 |
| 適性検査や技術的制限の強化で対応（年齢一律の義務化は避けるべき） | 11件 |
| 代替移動手段や公共交通機関の整備を優先すべき | 7件 |

保留63件を確認したところ、大半はテーマに関連しており、既存カテゴリに再分類できるはずです（school-nickname-banとは違い、無関係な雑談は少ない）。

---

## やること

### Step 1: 保留63件の再分類

`social-samples/elderly-license-revocation_classified.json` の `"category": "その他・分類保留"` の63件について：

1. 各投稿の `text` を読む
2. 以下の5カテゴリのいずれかに分類できるか判定する：
   - `免許返納義務化に賛成（高齢運転手の事故防止を最優先）`
   - `免許返納義務化に反対（地方の生活維持や移動手段確保を重視）`
   - `適性検査や技術的制限の強化で対応（年齢一律の義務化は避けるべき）`
   - `代替移動手段や公共交通機関の整備を優先すべき`
   - `自主返納のインセンティブ強化（特典や支援）を進めるべき`
3. 分類できるものは `category`、`stance`、`summary`、`reason` を更新する
4. 本当にどのカテゴリにも当てはまらないもの（テーマ無関係、意味不明等）は `その他・分類保留` のまま残す

**stance の対応表**（`configs/elderly-license-revocation-reaction-map.json` の `stance_order` 参照）：

| category | stance |
|----------|--------|
| 免許返納義務化に賛成（...） | 義務化賛成 |
| 免許返納義務化に反対（...） | 義務化反対 |
| 適性検査や技術的制限の強化で対応（...） | 適性検査強化 |
| 代替移動手段や公共交通機関の整備を優先すべき | インフラ優先 |
| 自主返納のインセンティブ強化（...） | 自主返納促進 |
| その他・分類保留 | その他 |

### Step 2: HTML更新

`docs/elderly-license-revocation-reaction-map.html` を再分類後の件数で更新する。

#### 2-1. 統計セクション（`<section class="stats">`）
- `最多カテゴリ` と `最多スタンス` の表示を更新（再分類後の最多に合わせる）

#### 2-2. 半円チャート（790行目付近）
```
var data=[{"label": "事故防止のため義務化すべき", "count": 68, ...}, ...]
```
- 各グループの `count` を再分類後の件数に更新
- グループ構成（`configs/elderly-license-revocation-reaction-map.json` の `conflict_axes` 参照）：
  - 「事故防止のため義務化すべき」→ 免許返納義務化に賛成
  - 「一律義務化には反対・地方の死活問題」→ 免許返納義務化に反対
  - 「適性検査や技術、インフラでカバーすべき」→ 適性検査 + 代替移動手段 + 自主返納インセンティブ
  - 「未確認・過激化した反応」→ その他・分類保留（再分類後に残った件数）

#### 2-3. 対立軸カード（`<section class="panel conflict-panel">`）
- 各 `axis-count` の件数を更新

#### 2-4. 分類別件数バーチャート（`<div class="bar-list">`）
- 各 `<strong>` の件数と `width:XX%` を更新

#### 2-5. ヒートマップ（`<table class="heat-table">`）
- 各セルの件数を再分類後の値に更新
- `その他・分類保留` 行の件数が大幅に減るはず

#### 2-6. 勢力図の数字
- 半円チャート上部の対立軸ラベルと件数
- 中央の総サンプル数（183件のまま変わらないはず。school-nickname-banと違い除外はしない方針）

---

## 注意事項

1. **GA/AdSenseのマーカーコメントを消さないでください**
   - `<!-- GA_TAG_START -->` 〜 `<!-- GA_TAG_END -->`
   - `<!-- ADSENSE_TAG_START -->` 〜 `<!-- ADSENSE_TAG_END -->`
   - これらは自動挿入スクリプトが使うマーカーです。前回のschool-nickname-ban作業で消してしまったので、今回は必ず残してください

2. **総サンプル数は183件のまま**
   - このテーマは school-nickname-ban と違い、テーマ無関係な雑談は少ないため、除外ではなく再分類が主な作業です
   - 本当に無関係なものがあれば除外してもOKですが、その場合は `vote_method` に除外理由を追記してください

3. **コミットメッセージ**: `fix: 課題21 高齢者免許返納の保留63件を再分類・チャート更新` のような形式で

4. **変更するファイルは2つだけ**:
   - `social-samples/elderly-license-revocation_classified.json`
   - `docs/elderly-license-revocation-reaction-map.html`

## 参考
- 正しく動作している例: `docs/ai-copyright-reaction-map.html`
- 設定ファイル: `configs/elderly-license-revocation-reaction-map.json`
- 前半（school-nickname-ban）の作業結果を参考にしてもOK
