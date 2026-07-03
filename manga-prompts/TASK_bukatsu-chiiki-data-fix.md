# 課題20: 部活動の地域移行 — SNS反応マップのデータ修正

課題管理: `TASK_BOARD.md`（課題7・課題9の延長）

## リポジトリ
https://github.com/issue-stance-lab/sns-reaction-map.git
ブランチ: `main` から `task/20-bukatsu-chiiki-data-fix` を切って作業

## 問題の概要

「部活動の地域移行の是非」SNS反応マップページ (`docs/bukatsu-chiiki-reaction-map.html`) のデータが不十分で、表示に複数の不具合がある。

## 具体的な問題 (3件)

### 問題 #20-1: 「その他・分類保留」が113件/180件 (63%) と多すぎる

`social-samples/bukatsu-chiiki_classified.json` の分類結果:
- 教員の長時間労働解消や持続可能性の観点から地域移行に賛成: 35件
- 保護者の費用負担増や受け皿不足を懸念し地域移行に反対: 20件
- 部活動の教育的価値や学校文化の喪失を理由に地域移行に反対: 7件
- 少子化による部活動の維持困難を理由に地域移行を支持: 4件
- 段階的導入や条件整備を前提に地域移行を条件付きで支持: 1件
- **その他・分類保留: 113件** ← ここが問題

「保留」の中身を見ると、実際には立場を含んでいるツイートも多い。分類のconfidenceが低すぎて保留に回されたものを再分類すべき。

**対応:** `bukatsu-chiiki_classified.json` の113件の「その他・分類保留」を再分類する。分類カテゴリは `configs/bukatsu-chiiki-reaction-map.json` の `category_order` を参照。本当に分類不能なもの（ニュース記事のリンクだけ、立場不明のつぶやき）のみ「その他・分類保留」に残す。

### 問題 #20-2: 半円チャートが全件「その他」1グループに集約されている

`docs/bukatsu-chiiki-reaction-map.html` 790行目:
```js
var data=[{"label": "その他", "count": 180, "color": "#cbd5e1", "cats": "その他・分類保留, 少子化による..."}];
```
本来は ai-copyright のように対立軸ごとにグループ化されるべき:
```js
// ai-copyright の正しい例 (846行目):
var data=[
  {"label": "クリエイターの著作権を最優先に守る", "count": 181, "color": "#e07040", "cats": "著作権厳格保護..."},
  {"label": "条件付きで共存の仕組みを作る", "count": 36, "color": "#0f7490", "cats": "条件付き容認..."},
  ...
];
```

**対応:** 再分類後の件数をもとに、半円チャートの `var data=[...]` を対立軸グループ別に再構成する。
- 賛成グループ (教員負担軽減 + 少子化対応): 青系 `#1769d1`
- 反対グループ (費用負担 + 教育的価値): オレンジ系 `#b54708`
- 条件付き: グレー系 `#667085`
- その他: `#cbd5e1`

### 問題 #20-3: 対立軸セクションが空

`docs/bukatsu-chiiki-reaction-map.html` 853行目:
```html
<article class="axis-card" data-tone="neutral">
  <div class="axis-kicker">対立軸</div>
  <h3></h3>                    ← 空
  <div class="axis-count">0<span>件</span></div>  ← 0件
  <p></p>                      ← 空
  <div class="axis-tags"></div> ← 空
</article>
```

**対応:** ai-copyright の対立軸セクション (909行目) を参考に、以下の構造で埋める:

```
対立軸1 (data-tone="positive"):
  kicker: 教員負担軽減
  h3: 教員の働き方改革と持続可能な部活動
  count: (再分類後の賛成系合計)
  p: 教員の長時間労働解消と少子化対応のため、地域との役割分担を進めるべきとする立場。
  tags: 教員の長時間労働解消〜, 少子化による〜

対立軸2 (data-tone="negative"):
  kicker: 保護者負担・教育価値
  h3: 費用増と学校文化喪失への懸念
  count: (再分類後の反対系合計)
  p: 地域移行による保護者の費用負担増、受け皿不足、部活動の教育的価値の喪失を懸念する立場。
  tags: 保護者の費用負担増〜, 部活動の教育的価値〜
```
タグには代表サンプルセクションへのアンカーリンク (`<a href="#sample-...">`) も付ける。

## 作業手順

1. `main` から `task/20-bukatsu-chiiki-data-fix` ブランチを作成
2. `social-samples/bukatsu-chiiki_classified.json` の「その他・分類保留」113件を再分類
3. 再分類結果をもとに `docs/bukatsu-chiiki-reaction-map.html` を更新:
   - 半円チャート `var data=[...]` (790行目付近)
   - 対立軸セクション (853行目付近)
   - 分類別件数のバーチャート (856-861行目付近)
   - ヒートマップの件数 (868行目以降)
4. コミット & PR作成 (タイトルに `課題20対応` を含める) → main へマージ

## 参考ファイル

- 正しく動作している例: `docs/ai-copyright-reaction-map.html`
- 設定ファイル: `configs/bukatsu-chiiki-reaction-map.json`
- 分類データ: `social-samples/bukatsu-chiiki_classified.json`
- 分類カテゴリ定義: `configs/bukatsu-chiiki-reaction-map.json` の `category_order`
