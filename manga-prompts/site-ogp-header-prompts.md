# サイトOGP画像・Xヘッダー画像 生成プロンプト

対応課題: `TASK_BOARD.md` 課題32
作成: 2026-08-02

---

## 差し替えの背景

現行の `docs/ogp/default.png`（2026-06-27作成）には、サイトから削除済みの要素が残っている。

| 現在入っているもの | 状態 |
|---|---|
| 「その話題、SNSでは実はどっちが多い？」 | S2でトップから削除した旧コピー |
| 賛成42% / 保留18% / 中立20% / 反対20% | **根拠のないダミー値** |
| 「トレンド上昇中」「12.5K」「話題沸騰中」 | 実データではない演出値 |

X固定ポストの本文が「世論調査ではありません」と明記しているのに、
同じ投稿のOGPカードが円グラフで割合を出しているため、**投稿内で矛盾している**。

---

## 絶対に入れてはいけない要素

**新しい画像でも、以下は1つも入れないこと。** 課題32の再発になる。

- ❌ **数値・割合・パーセント**（42%、20% など。実データでも入れない — 画像は更新されないため必ず古くなる）
- ❌ **円グラフ・棒グラフで割合を示す表現**
- ❌ 「どっちが多い」「意見が真っ二つ」「どっち派？」
- ❌ 「トレンド上昇中」「話題沸騰中」「12.5K」などの演出値
- ❌ 「リアルタイム」「世論」「世論調査」

**画像に数字を入れない**のがこの課題の核心。画像はコードから生成されず更新もされないため、
どんな数字も時間とともに嘘になる。

## 入れるべき要素

- ✅ サイト名「SNS反応まっぷ」
- ✅ コピー「**その話題を、数ではなく問いから読む。**」（トップページ h1 と統一）
- ✅ **鮮やかな色数**。旧画像の華やかさは維持する（地味にしない）
- ✅ **多数の色付きドット**＝スタンスマップのモチーフ。サイトの視覚的な看板であり、
  「たくさんの声が立場ごとに散らばっている」ことを表す（数量を主張しないので問題ない）
- ✅ 賛成と反対の「理由」が並んでいることを示す視覚表現（数値なし）
- ✅ 現行サイトの配色（青 `#075ef2` / 橙 `#ff5426` / 緑 `#36b8a3` / 紫 `#9358e8` / 紺 `#071a3d`）

---

## サイトの画風（必ず守る）

**参照するのはトップページの初画面（ヒーロー）。**
`docs/index.html` を開いた最初の画面がサイトの顔であり、この雰囲気に合わせる。

> ⚠️ 注意: トップページ下部の「HOW IT WORKS」セクション（`docs/images/site/*.webp`）は
> 水彩タッチのイラストだが、**あれは物語部分の演出であり、サイトの基調ではない。**
> OGP・ヘッダーはヒーローの画風に合わせる。

### ヒーローの画風

| 要素 | 内容 |
|---|---|
| 画材 | **クリーンなデジタルベクター**。水彩でも手描きでもない |
| 背景 | ほぼ白（`#f8faff`）。うっすらとした方眼グリッドが極薄で入る |
| 主役の図 | **4つのドット群（ネットワーク図）**。点を細い線で結んだ星座・分子構造のような塊 |
| 色 | 鮮明だが上品。青 `#075ef2` / 橙 `#ff5426` / 緑 `#36b8a3` / 紫 `#9358e8` |
| ラベル | **角丸のピル**。単色の塗りに白文字。小さく、影は控えめ |
| 文字 | 太いゴシック（Noto Sans JP Black）。濃紺 `#071a3d`。一部に青→紫のグラデーション |
| 影 | やわらかく薄い。`0 12px 32px rgba(16,47,91,.09)` |
| 印象 | 現代的で清潔・知的・SaaSのランディングページに近い。落ち着いているが古びていない |

### ロゴマークの正確な仕様（`docs/index.html` の実装）

**必ずこの通りに描く。** 生成AIは勝手に簡略化するので、毎回確認すること。

```css
.logo-mark i { width:11px; height:11px; border-radius:50%; box-shadow:0 0 0 3px #fff }
  1個目 上           #075ef2  青
  2個目 右上         #2786ff  明るい青
  3個目 右下         #ff5426  橙
  4個目 下           #36b8a3  緑
  5個目 左下         #9358e8  紫
  6個目 左上         #ff5426  橙
.logo-mark:before / :after {
  border: 2px solid #b8cbeb; border-radius:50%;
  transform: rotate(35deg) / rotate(-35deg);   ← 2本を交差させる
}
```

- **ドットは6個**（4個ではない）。各ドットに白い縁が付く
- **楕円リングは2本**（1本ではない）。＋35°と−35°で交差させる。色は淡い青灰 `#b8cbeb`
- リングはドットより内側（inset 8px）を通る

### ロゴタイプ（サイト名）の仕様

```css
.logo-text { font-weight: 900; letter-spacing: -.04em }
font-family: "Noto Sans JP"
```

**Noto Sans JP の最も太いウェイト（Black / 900）**、字間をやや詰める。濃紺 `#071a3d`。

### サイトの視覚的な看板：4つのドット群

ヒーロー中央にある、**点を線で結んだ4つの塊**がサイトの象徴。

```
青の群れ   ← 賛成寄りの意見
橙の群れ   ← 反対寄りの意見
緑の群れ   ← 条件付きの意見
紫の群れ   ← 中立・保留
```

各群れの脇に、その色の角丸ピルラベルが付く。
**数量を主張せず、「立場ごとに意見が集まっている」ことだけを示す。**
OGP・ヘッダーの両方でこのモチーフを主役にする。

### 避けるもの

- ❌ 水彩・色鉛筆・紙の質感・手描きの揺れた線
- ❌ ポスター調、ネオン、太い白フチ、濃いグラデーション背景、紙吹雪
- ❌ 単色ミニマル、グレースケール、要素が少なすぎる絵
- ❌ **数字・割合・円グラフ・棒グラフ**（課題32の再発）

### 豊かさの出し方

彩度を上げるのではなく、**ドットの数と線の密度**で豊かさを出す。
ヒーローの4群は合計で100個以上の点が線で結ばれており、それが画面の華やかさを作っている。

---

## 1. OGP画像（1200×630）

出力先: `docs/ogp/default.png`

### プロンプト（英語・画像生成AI用）

**主役は「SNS反応まっぷ」というサイト名。** キャッチコピーは脇役。

```
A clean, modern digital illustration for a Japanese website's Open Graph card,
in the visual language of a well-designed SaaS product landing page.
Crisp, intelligent, calm and contemporary. Vector-clean, NOT hand-drawn.

Layout: horizontal, 1200x630 pixels.
Background: near-white with the faintest cool blue tint (#f8faff), overlaid with an
extremely subtle square grid pattern in pale blue at about 3% opacity,
fading out toward the bottom. Clean and airy.

=== MAIN SUBJECT: the site name (MUST DOMINATE) ===
The site name 「SNS反応まっぷ」 in VERY LARGE, ultra-heavy Japanese gothic type
(Noto Sans JP Black, weight 900), placed upper-left, with slightly tightened letter
spacing, solid deep navy (#071a3d). No outline, no heavy shadow.

SIZE IS CRITICAL: the site name must span roughly 45% of the total canvas width
and be by far the largest element in the image. Make it noticeably bigger than
feels comfortable — it is the primary subject.

Immediately left of the name, the logo mark, drawn EXACTLY as follows:
- SIX small solid circles of equal size arranged evenly around a circle
  (like the six points of a hexagon), each with a crisp white ring around it:
  top = blue (#075ef2), upper-right = bright blue (#2786ff),
  lower-right = orange (#ff5426), bottom = green (#36b8a3),
  lower-left = purple (#9358e8), upper-left = orange (#ff5426).
- TWO thin ellipse outlines in pale blue-gray (#b8cbeb), 2px stroke,
  drawn INSIDE the ring of dots and CROSSING each other in an X,
  one tilted +35 degrees, the other -35 degrees, like two orbital rings.
Exactly six dots and exactly two crossing ellipses. Do not simplify.

=== SUBTITLE (clearly secondary) ===
Below the site name, on ONE line, at roughly one-third its height:
「その話題を、数ではなく問いから読む。」
Same typeface, bold, deep navy, noticeably smaller.
Apply a blue-to-purple gradient (#075ef2 → #2853d8) to the phrase 「問いから読む」 only.

=== LOWER-LEFT: balance and emotion motif (fills the empty space) ===
Below the subtitle, in the lower-left area, a simple flat-vector illustration:
- A balance scale (天秤) drawn with thin clean lines in deep navy, PERFECTLY LEVEL
  and evenly balanced — neither side tipping.
- On the left pan, a small rounded blue (#075ef2) speech bubble;
  on the right pan, a small rounded orange (#ff5426) speech bubble.
  Each bubble contains two or three short white horizontal lines
  suggesting written reasons. NO numbers.
- Floating lightly around the scale, three or four small rounded speech bubbles
  in green (#36b8a3) and purple (#9358e8), each containing a single simple mark:
  a question mark 「？」, an exclamation mark 「！」, and an ellipsis 「…」.
  These suggest questioning, strong feeling, and hesitation.
- A few tiny scattered dots in the four palette colors around them.

The scale communicates that both sides are weighed equally.
Keep it small and light — supporting, not competing with the site name.

=== HERO GRAPHIC (right side, the visual signature) ===
Four distinct constellation-like clusters of dots, floating and slightly overlapping,
occupying the right half of the canvas:

- A BLUE cluster (#075ef2) upper-left of the group
- An ORANGE cluster (#ff5426) upper-right
- A GREEN cluster (#36b8a3) lower-left
- A PURPLE cluster (#9358e8) lower-right

Each cluster contains 20-35 small filled circles of varying sizes (3-10px),
connected by thin 1px lines of the same color at low opacity, forming an organic
network / molecular / star-map structure. Dots are crisp with clean edges,
scattered naturally rather than in a regular pattern.
Behind each cluster, a very soft radial glow in its own color.

Beside each cluster, a small rounded pill-shaped label with solid color fill
and white text, with a soft subtle shadow:
- blue pill: 「賛成寄りの意見」
- orange pill: 「反対寄りの意見」
- green pill: 「条件付きの意見」
- purple pill: 「中立・保留」

Do NOT add any other label, caption, or pill above or around this graphic.
The four stance pills are the only labels on the right side.

=== FINISHING ===
Soft, light shadows only (like 0 12px 32px rgba(16,47,91,.09)).
Generous white space. Rounded corners on any card-like element.
Richness comes from the NUMBER of dots and connecting lines, not from saturation
or decoration.

Style: clean flat vector, crisp edges, modern tech-editorial, calm and trustworthy.
NOT watercolor. NOT hand-drawn. NOT paper texture. NOT poster art. NOT neon.
NO thick outlines, NO confetti, NO sparkles.

ABSOLUTELY NO numbers, percentages, pie charts, donut charts, bar charts, gauges,
trend arrows, or any metric readouts anywhere in the image.

Output image: landscape, exactly 1200x630 pixels.
```

### 確認事項

- [ ] 画像内に数字が1つも無いこと
- [ ] 「どっちが多い」等の旧コピーが無いこと
- [ ] 1200×630 であること
- [ ] X・Facebook・LINE のカードで文字が切れないこと（安全域: 中央1000×520）
- [ ] ファイルサイズを1MB以下に圧縮（現行は1.4MB）

---

## 2. Xヘッダー画像（1500×500）

X プロフィール上部のバナー。現行は「その話題、SNSでは実はどっちが多い？」入り。

### プロンプト（英語・画像生成AI用）

**主役は「SNS反応まっぷ」というサイト名。** キャッチコピーは脇役。

```
A clean, modern digital banner for a Japanese website's social media header,
in the visual language of a well-designed SaaS product landing page.
Crisp, intelligent, calm and contemporary. Vector-clean, NOT hand-drawn.

Layout: very wide horizontal, 1500x500 pixels.
Background: near-white with the faintest cool blue tint (#f8faff), overlaid with an
extremely subtle square grid pattern in pale blue at about 3% opacity.
Clean and airy.

=== MAIN SUBJECT: the site name (MUST DOMINATE) ===
The site name 「SNS反応まっぷ」 in VERY LARGE, ultra-heavy Japanese gothic type
(Noto Sans JP Black, weight 900), placed left of center, slightly tightened letter
spacing, solid deep navy (#071a3d). No outline, no heavy shadow.

SIZE IS CRITICAL: the site name must span roughly 40% of the total banner width
and be by far the largest element. Make it noticeably bigger than feels comfortable.

Immediately left of the name, the logo mark, drawn EXACTLY as follows:
- SIX small solid circles of equal size arranged evenly around a circle
  (like the six points of a hexagon), each with a crisp white ring around it:
  top = blue (#075ef2), upper-right = bright blue (#2786ff),
  lower-right = orange (#ff5426), bottom = green (#36b8a3),
  lower-left = purple (#9358e8), upper-left = orange (#ff5426).
- TWO thin ellipse outlines in pale blue-gray (#b8cbeb), 2px stroke,
  drawn INSIDE the ring of dots and CROSSING each other in an X,
  one tilted +35 degrees, the other -35 degrees, like two orbital rings.
Exactly six dots and exactly two crossing ellipses. Do not simplify.

=== SUBTITLE (clearly secondary) ===
Directly below the site name, on ONE line, at roughly one-third its height:
「その話題を、数ではなく問いから読む。」
Same typeface, bold, deep navy, noticeably smaller, with a blue-to-purple gradient
(#075ef2 → #2853d8) applied to the phrase 「問いから読む」 only.

=== BALANCE AND EMOTION MOTIF (fills empty space near the type) ===
Beside or just below the subtitle, a small flat-vector illustration:
- A balance scale (天秤) in thin clean deep-navy lines, PERFECTLY LEVEL and
  evenly balanced — neither side tipping.
- On the left pan a small blue (#075ef2) speech bubble, on the right pan a small
  orange (#ff5426) one, each holding two or three short white horizontal lines
  suggesting written reasons. NO numbers.
- Three or four small rounded speech bubbles floating nearby in green (#36b8a3)
  and purple (#9358e8), each containing one simple mark: 「？」「！」「…」.
- A few tiny scattered dots in the four palette colors.

Keep it small and light — supporting, not competing with the site name.

=== HERO GRAPHIC (right half, the visual signature) ===
Four distinct constellation-like clusters of dots, floating and slightly overlapping,
spread horizontally across the right portion of the banner:

- A BLUE cluster (#075ef2)
- An ORANGE cluster (#ff5426)
- A GREEN cluster (#36b8a3)
- A PURPLE cluster (#9358e8)

Each cluster contains 20-35 small filled circles of varying sizes (3-10px),
connected by thin 1px lines of the same color at low opacity, forming an organic
network / molecular / star-map structure. Crisp clean edges, natural scatter.
Behind each cluster, a very soft radial glow in its own color.

Beside each cluster, a small rounded pill-shaped label with solid color fill and
white text, with a soft subtle shadow:
- blue pill: 「賛成寄りの意見」
- orange pill: 「反対寄りの意見」
- green pill: 「条件付きの意見」
- purple pill: 「中立・保留」

Do NOT add any other label, caption, or pill above or around this graphic.
The four stance pills are the only labels on the right side.

The very wide format suits the four clusters spread out horizontally
rather than stacked.

=== SAFE AREA (critical for X) ===
On X, the profile picture overlaps the lower-left corner (a ~300x300 pixel circle)
and the bottom edge is cropped on mobile.
Keep the site name, logo mark and subtitle within the central horizontal band,
clear of the left 350 pixels and the bottom 100 pixels.
Faint background grid and stray dots MAY extend into those areas.

=== FINISHING ===
Soft, light shadows only. Generous white space. Rounded corners on any card-like
element. Richness comes from the NUMBER of dots and connecting lines,
not from saturation or decoration.

Style: clean flat vector, crisp edges, modern tech-editorial, calm and trustworthy.
NOT watercolor. NOT hand-drawn. NOT paper texture. NOT poster art. NOT neon.
NO thick outlines, NO confetti, NO sparkles.

ABSOLUTELY NO numbers, percentages, pie charts, donut charts, bar charts, gauges,
trend arrows, or any metric readouts anywhere in the image.

Output image: landscape, exactly 1500x500 pixels.
```

### 確認事項

- [ ] 画像内に数字が1つも無いこと
- [ ] 左下300×300（プロフィール画像の重なり）に文字が無いこと
- [ ] 下端100pxに重要要素が無いこと（モバイルで切れる）
- [ ] 1500×500 であること
- [ ] PC・モバイル両方で表示確認

---

## 3. 差し替え後の作業

### ファイルの配置

```
docs/ogp/default.png   ← 新しいOGP画像で上書き
```

Xヘッダーは X の「プロフィールを編集」から直接アップロード（リポジトリには入れない。
参照用に `docs/images/site/` へ置いてもよい）。

### OGPキャッシュの更新

画像を差し替えても、X側のキャッシュが残ると古い画像が表示され続ける。

1. https://cards-dev.twitter.com/validator を開く
2. `https://issue-stance-lab.github.io/sns-reaction-map/` を入力
3. 新しい画像が表示されることを確認

Facebook のキャッシュは https://developers.facebook.com/tools/debug/ で更新できる。

### 記録

- `TASK_BOARD.md` 課題32 を完了に更新
- `THEMES.yaml` には影響しない（サイト共通画像のため）

---

## 4. 余力があれば：テーマ別OGP 9枚の点検

`docs/ogp/` に9枚（2026-07-02作成）。同様のダミー数値が入っていないか確認する。

```
ai-copyright.png / bike-blue-ticket.png / bukatsu-chiiki.png
constitutional-amendment.png / elderly-license-revocation.png
henoko-student-accident.png / school-nickname-ban.png / takaichi.png
```

数字が入っているものがあれば、上記と同じ方針（数値を入れない）で作り直す。
`consumption-tax-cut` `fukushuto` `koshitsu-tenpakai` はテーマのhero画像を
OGPに流用しているため、こちらも合わせて確認する。
