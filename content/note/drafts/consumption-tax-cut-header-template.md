# note見出し画像テンプレート｜消費税減税シリーズ

第1回で確立した型。第2〜4回はこれに写真とテキストを差し替えるだけで、
シリーズとしての統一感を保ったまま作れる。

## 経緯（2026-09-21）

1. 当初はGPTimage2で「写真1枚に文字まで焼き込む」想定だったが、部活動シリーズの実例
   （`bukatsu-chiiki-image-prompts.md`）を見ると、実際は**①GPTimage2で背景写真だけ作る
   →②HTML/CSSで文字を別途合成**という2段階だった。文字合成はAI側の作業にできる。
2. v1（ラベル・数字・サブタイトル・件数・ブランド名の5段）はオーナーから
   「インパクトが弱い」と指摘。
3. note公式・実践者の記事をWeb調査した結果（出典は末尾）、
   「文字を減らす勇気」「太いゴシック体」「具体的な数字はCTRに効く」が共通見解と判明。
   ただし文字を大きく太くしすぎると「情報商材感」が出るという注意点もあった。
4. v2で文字を「数字→転換ワード」の1行だけに削ったところ大幅に改善。
   ただしテーマ名が画像から読み取れなくなったため、v3で小さいラベルを1行だけ復活。
   **v3（ラベル＋数字の2段構成）が確定版。**

## 色のルール（固定・4回とも変えない）

読者が「この配色＝どんでん返しの合図」と覚えられるよう、意味を統一する。

| 役割 | 色 | 用途 |
|---|---|---|
| 前提の数字 | ティール `#1f5c4d` | 一見そう見える数字（例: 賛成60%） |
| 転換後のキーワード | テラコッタ `#9c3c1a` | 実際の中身・どんでん返し（例: 政治不信） |
| 矢印 | `#9c8d6c` | 前提→転換をつなぐ |
| ラベル文字 | `#6b5d44` | シリーズ名・回数 |
| ブランド名 | `#5c5340` | 右下の「SNS反応まっぷ」 |
| 背景スクリム | クリーム `#faf7f1` 系グラデーション | 写真の上に敷いて文字を読みやすくする |

サイト本体のティール（`--accent:#2d6a5a`）と完全一致はしていないが近似色。
記事プレビューHTML（`consumption-tax-cut-note1-preview.html`）とは別に、
見出し画像だけの色調整のため、あえて少し濃い `#1f5c4d` を採用している。

## レイアウトの型

1. **左上: ラベル**「[テーマ名]シリーズ　第[N]回」34px / weight 700 / letter-spacing .08em
2. **中央: 大きい数字＋矢印＋転換ワード** 190px / weight 900 / Noto Sans JP（明朝体は不可、
   ゴシック体の方が視認性・強さで勝る）。2行に収まらなければ`<br>`で改行する
3. **右下: ブランド名**「SNS反応まっぷ」24px / weight 700
4. **背景**: 写真を全面に敷き、左から効くクリーム色グラデーションのスクリムを重ねて
   左側の文字を読みやすくする

**文字はこの3要素だけ。サブタイトルや件数は足さない**（v1の反省点）。

## 素材の作り方（3ステップ）

### ステップ1: 各回の「数字→転換ワード」を決める

その回の本文の主張を、数字1つ＋短いキーワードに要約する。本文を書き終えてから決める
（本文がまだなら、この画像も作れない）。

### ステップ2: 背景写真をGPTimage2で作ってもらう（オーナー担当）

下記のプロンプト雛形を使う。**左40%程度に模様の少ない余白を残す**よう明示すること
（第1回のv1はこの指定が無く、右側に寄せられた図表と文字が近すぎた）。

```
[この回のテーマ]をテーマにしたSNS意見分析記事の見出し画像用の背景写真を作成してください。

【構図】画面の右60%程度に、[この回の内容に合うモチーフ]を配置する。
画面の左40%程度は、太い文字を重ねられるよう、模様の少ない平坦な背景のみにする
(余白として確保し、文字の視認性を最優先する)。

【スタイル】写実的すぎない、落ち着いたフラットイラスト〜半立体的な質感。
ジャーナリスティックで上品な雰囲気。派手なアニメ調・広告調は避ける。

【配色】背景は温かみのあるクリーム色(#faf7f1系)。差し色にディープティール(#2d6a5a系)を使う。

【禁止事項】実在の政治家・著名人を想起させる人物は描かない。特定の政党を連想させる
配色(赤と青の対比など)やロゴ・シンボルは使わない。文字・ロゴ・ウォーターマークは入れない。

【サイズ】横長、1920×1006px目安(比率およそ1.9:1)。

【保存】
ファイル名: consumption-tax-cut[N]-[モチーフ名].png
保存先フォルダ: /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/content/note/drafts/photos/
```

モチーフの案（内容に応じて選ぶ・変えてよい）:
- 第2回（対象範囲と財源）: 食品が並ぶ棚で一部だけ枠で囲まれている、または天秤・電卓
- 第3回（SNSの賛否そのもの）: スマートフォンの通知・吹き出しが重なる様子
- 第4回（現金給付の設計）: 封筒・振込明細・条件を示すチェックリストのようなモチーフ

### ステップ3: 私がHTML/CSSで文字を合成する

下のテンプレートの `{{...}}` を差し替えてPlaywrightでレンダリングする。

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&display=swap" rel="stylesheet">
<style>
  html,body{margin:0;padding:0;width:1920px;height:1006px;overflow:hidden;}
  .canvas{position:relative;width:1920px;height:1006px;background:#faf7f1;font-family:'Noto Sans JP',sans-serif;}
  .photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:62% 50%;}
  .scrim{position:absolute;inset:0;background:linear-gradient(90deg,
    rgba(250,247,241,0.98) 0%, rgba(250,247,241,0.96) 44%,
    rgba(250,247,241,0.62) 60%, rgba(250,247,241,0.10) 75%, rgba(250,247,241,0) 88%);}
  .text{position:absolute;left:100px;top:0;bottom:0;width:1150px;display:flex;flex-direction:column;justify-content:center;}
  .eyebrow{font-size:34px;font-weight:700;letter-spacing:.08em;color:#6b5d44;margin-bottom:20px;}
  .stat{font-weight:900;font-size:190px;line-height:1.05;white-space:nowrap;letter-spacing:-.02em;}
  .stat .n1{color:#1f5c4d;}
  .stat .arrow{color:#9c8d6c;font-size:115px;margin:0 8px;font-weight:700;}
  .stat .n2{color:#9c3c1a;}
  .brand{position:absolute;right:44px;bottom:36px;font-size:24px;font-weight:700;letter-spacing:.06em;color:#5c5340;}
</style>
</head>
<body>
  <div class="canvas">
    <img class="photo" src="{{PHOTO_FILENAME}}">
    <div class="scrim"></div>
    <div class="text">
      <div class="eyebrow">消費税減税シリーズ　第{{N}}回</div>
      <div class="stat"><span class="n1">{{STAT_1}}</span><br><span class="arrow">→</span><span class="n2">{{STAT_2}}</span></div>
    </div>
    <div class="brand">SNS反応まっぷ</div>
  </div>
</body>
</html>
```

レンダー用スクリプト（Playwright、`node_modules`はリポジトリのものを使う）:

```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1006 } });
  await page.goto('http://localhost:PORT/index.html', { waitUntil: 'networkidle' });
  await page.screenshot({ path: 'header-vN.png' });
  await browser.close();
})();
```

HTMLと写真を同じフォルダに置き、`python3 -m http.server PORT` で配信してから実行する
（file://直読みだと相対パスで失敗することがある）。

## サイズ

1920×1006px（論理サイズ1280×670pxをdeviceScaleFactor 1.5相当で描画したのと同じ比率）。
noteの公式推奨サイズ1280×670px・比率1.91:1と一致する。

## 出典（Web調査、2026-09-21）

- [タイトルと見出し画像のコツ – noteヘルプセンター](https://www.help-note.com/hc/ja/articles/360012426353-%E3%82%BF%E3%82%A4%E3%83%88%E3%83%AB%E3%81%A8%E8%A6%8B%E5%87%BA%E3%81%97%E7%94%BB%E5%83%8F%E3%81%AE%E3%82%B3%E3%83%84)
- [noteアイキャッチ画像の作り方｜サイズ1280×670・おしゃれなデザインのコツ【2026年】](https://www.samune-ai.jp/blog/note-eyecatch-tsukurikata)
- [バナー改善に効果的な「数字」がもたらすインパクトとは？｜B-SOKU公式note](https://note.com/bsoku/n/n80b964e9147d)
- [noteのサムネイルには文字入れをするべきか問題｜いしかわゆき（ゆぴ）](https://note.com/milkprincess17/n/nb9ed56940b51)

## 確定版ファイル（第1回）

- 背景写真: `content/note/drafts/photos/consumption-tax-cut1-receipt-magnifier.png`
- 合成後の見出し画像: `content/note/drafts/images/consumption-tax-cut1_note-header.png`

## 確定版ファイル（第2回）

- 背景写真: `content/note/drafts/photos/consumption-tax-cut2-shelf-frame.png`（モチーフ: 食品棚の一部を枠で囲む）
- 合成後の見出し画像: `content/note/drafts/images/consumption-tax-cut2_note-header.png`
- 数字→転換ワード: 「331件」（ティール）→「変えない」（テラコッタ）※初版「拡大37%」から改訂
- 写真がすでに1920×1006ぴったりだったため、`object-position`の調整（62% 50%等のシフト）は不要だった。
  `object-position: 50% 50%`のままで十分。写真自体に左40%の余白が作り込まれている場合は毎回この点を確認すること

## 回ごとに数字の「型」を変える（2026-09-22 追加）

第2回の初版「拡大37%→変えない」は、第1回「賛成60%→政治不信」と**◯◯%＋4文字**という
文字の並びがほぼ同型で、オーナーから「回によって変わり映えがしない」と指摘された。

**同じテンプレートを使い回しても、数字の種類と文字数は回ごとに変えること。**
候補: 件数（331件）、年（2027年）、差額（◯兆円）、順位・個数など。%を毎回使わない。
決めるときは、直前の回で使った数字の種類・語尾の記号（%/件/年/兆円など）を
`git log`かこのファイルの「確定版ファイル」一覧で確認してから選ぶ。
