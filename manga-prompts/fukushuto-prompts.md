# 副首都法案 — ホバー漫画プロンプト（論点別・全7枚）

テーマ: 副首都法案・副首都構想 SNS反応まっぷ
用途: 投票ボタンのホバーポップアップ（各論点1枚・縦型3コマ）
生成枚数: キャラシート2枚 + 論点ページ7枚 = 計9枚

## 保存先

生成後 WebP に変換、各ファイル≤100KB（リサイズ900px幅、q45目安）で以下に配置:

```
docs/images/
├── fukushuto-manga-charsheet-yui.webp      ← キャラシートA
├── fukushuto-manga-charsheet-nobuko.webp   ← キャラシートB
├── fukushuto-manga-teigi.webp              ← 定義・中身
├── fukushuto-manga-kouhochi.webp           ← 候補地
├── fukushuto-manga-tokoso.webp             ← 都構想・維新
├── fukushuto-manga-bousai.webp             ← 防災・災害
├── fukushuto-manga-hiyou.webp              ← 費用・財源
├── fukushuto-manga-yusen.webp              ← 優先順位
└── fukushuto-manga-sonota.webp             ← その他
```

---

## Step 1: キャラクターシート生成（Character Lock用）

### キャラシート① 田村 結衣（たむら ゆい）

- 役割: 都市政策シンクタンクの研究員（32歳）
- 立場: 副首都構想に前向き。東京一極集中のリスクに問題意識を持つ
- 恐れ: このまま何も変えずに大規模災害が起きること
- 望み: 機能分散と多極成長型の国家設計を進めてほしい

```
Character design reference sheet, white background, multiple expressions (confident, thoughtful, earnest, surprised, determined), full body and close-up face views. Japanese female urban policy researcher, age 32, straight black hair in a low bun, black-rimmed rectangular glasses, light gray blazer over a white turtleneck, carrying a tablet with city planning maps. Slim and energetic build, slightly optimistic and forward-looking demeanor. Anime-inspired semi-realistic manga style, clean line art, cool blue-gray palette.
```

### キャラシート② 大野 信子（おおの のぶこ）

- 役割: 元市役所職員・地域市民活動家（52歳）
- 立場: 副首都構想に慎重。中身が決まらないまま進む進め方を問題視
- 恐れ: 「生煮え」のまま決まり、後から取り返しのつかないことになること
- 望み: 議論を尽くしてから制度の枠組みを決めてほしい

```
Character design reference sheet, white background, multiple expressions (skeptical, firm, concerned, thoughtful, occasionally surprised), full body and close-up face views. Japanese woman, former city hall employee, now a community activist, age 52, short wavy salt-and-pepper hair, round glasses, navy cardigan over a light blue blouse, holding a printed document full of highlighted notes. Composed and experienced posture, watchful and sharp expression. Anime-inspired semi-realistic manga style, clean line art, warm earth-tone palette.
```

---

## Step 2: 論点別ページ生成

**重要:** 生成時に Step 1 で作成したキャラクターシート2枚を参照画像として添付すること。
各ページは縦型3コマ（上1コマ大 + 下2コマ）で統一する。

---

### ページ1「定義・中身」— 副首都って、何？

**ファイル名:** `fukushuto-manga-teigi.webp`

**ストーリー:** 結衣が法案を読んでいる。しかし信子の指摘で「定義がない」ことに気づく。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 結衣と信子が法案の印刷物を広げて読んでいる | 結衣「副首都を政令で指定できる枠組みを先に作る。理念はいいと思う」 |
| 下段・左 | 信子が法案のページを指さしてじっと見る | 信子「ねえ、この法案……副首都の定義、どこに書いてある？」 |
| 下段・右 | 二人が法案を見て顔を見合わせる。法案文書に「定義：（空欄）」の文字 | 結衣「……書いてない」 信子「家の設計もせずに、契約だけ先にするようなものじゃない？」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, quiet indoor atmosphere.

[TOP LARGE PANEL] Two Japanese women sit at a table covered with printed government bill documents. The younger woman (black hair in a low bun, rectangular glasses, gray blazer) leans forward reading the papers with interest. The older woman (short wavy graying hair, round glasses, navy cardigan) reads calmly beside her. A speech bubble from the younger woman containing the Japanese text "副首都を政令で指定できる枠組みを先に作る。理念はいいと思う"

[BOTTOM LEFT PANEL] Close-up of the older woman pointing firmly at a specific line in the document with her finger. Her expression is sharp and questioning. A speech bubble containing the Japanese text "ねえ、この法案……副首都の定義、どこに書いてある？"

[BOTTOM RIGHT PANEL] Both women stare at each other over the document, a moment of realization. The document visible on the table shows a section with the text "定義：" followed by empty space. Two speech bubbles: one from the younger woman containing "……書いてない" and one from the older woman containing "家の設計もせずに、契約だけ先にするようなものじゃない？"
```

---

### ページ2「候補地」— 大阪？どこがいいの？

**ファイル名:** `fukushuto-manga-kouhochi.webp`

**ストーリー:** 地図を囲んで副首都の場所を議論する二人。南海トラフの問題が浮上する。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 二人が大きな日本地図を囲んでいる。大阪・福岡・新潟・北海道に付箋が貼られている | 結衣「法案の想定は大阪が軸。関西は経済規模も大きいし、実現可能性がある」 |
| 下段・左 | 信子が地図の南海トラフ想定域を指さす | 信子「でも大阪って、南海トラフの被災想定域に入ってるよね？東京と同時に被災したら……」 |
| 下段・右 | 結衣が新潟・福岡のあたりを指さしながら考え込む | 結衣「日本海側か北部に分散した方が、リスク分散にはなる……でも、その議論が聞こえてこない」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, focused research atmosphere.

[TOP LARGE PANEL] Two Japanese women stand around a large printed map of Japan spread on a table. The map has sticky notes on Osaka, Fukuoka, Niigata, and Hokkaido. The younger woman (black hair bun, glasses, gray blazer) points at Osaka with a confident posture. The older woman (wavy graying hair, glasses, navy cardigan) looks at the map thoughtfully. Speech bubble from the younger woman: "法案の想定は大阪が軸。関西は経済規模も大きいし、実現可能性がある"

[BOTTOM LEFT PANEL] Close-up of the older woman's hand pointing at the Nankai Trough zone shaded on the map with a worried expression. A speech bubble: "でも大阪って、南海トラフの被災想定域に入ってるよね？東京と同時に被災したら……"

[BOTTOM RIGHT PANEL] The younger woman leans over the map, touching the Sea of Japan coastline (Niigata/Fukuoka area) with a thoughtful, conflicted look. A speech bubble: "日本海側か北部に分散した方が、リスク分散にはなる……でも、その議論が聞こえてこない"
```

---

### ページ3「都構想・維新」— 副首都が目的？それとも……

**ファイル名:** `fukushuto-manga-tokoso.webp`

**ストーリー:** ニュースの附則条項を見た信子が「都構想の隠れ蓑」疑惑を指摘する。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 二人がテレビのニュース速報を見ている。画面には「副首都法案 附則に『大阪市の名称変更』条項」の字幕 | 信子「……この附則、見た？」 |
| 下段・左 | 信子が手元のメモを見ながら説明する | 信子「住民投票で二度否決された都構想。その名称変更が、なぜ副首都法案の附則に入ってるの？」 |
| 下段・右 | 結衣が腕を組んで真剣に考え込む | 結衣「副首都の整備が目的なのか、大阪再編が目的なのか……切り分けて議論すべきだと思う」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, tense living-room atmosphere.

[TOP LARGE PANEL] Both women sit on a sofa watching a TV news broadcast. The TV screen shows a Japanese news ticker at the bottom: "副首都法案 附則に『大阪市の名称変更』条項". The younger woman leans forward with wide eyes; the older woman's expression sharpens. Speech bubble from the older woman: "……この附則、見た？"

[BOTTOM LEFT PANEL] The older woman (round glasses, navy cardigan) holds handwritten notes and explains with a serious tone. A speech bubble: "住民投票で二度否決された都構想。その名称変更が、なぜ副首都法案の附則に入ってるの？"

[BOTTOM RIGHT PANEL] The younger woman (gray blazer, glasses) crosses her arms and stares at the floor, thinking deeply. A speech bubble: "副首都の整備が目的なのか、大阪再編が目的なのか……切り分けて議論すべきだと思う"
```

---

### ページ4「防災・災害」— 同じ防災で、正反対の答え

**ファイル名:** `fukushuto-manga-bousai.webp`

**ストーリー:** 「防災のため」という同じ根拠から、二人が正反対の結論を導く。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 防災シミュレーションの画面を二人で見ている。画面に首都直下地震の被害想定が表示されている | 結衣「首都直下が来たら、東京だけに機能が集中している今の状態は危険すぎる」 |
| 下段・左 | 結衣が力強く語る。背景に「今すぐ機能分散を」のイメージ | 結衣「だから副首都で機能を分散させる。防災のためにこそ、早く進めるべきなんだ」 |
| 下段・右 | 信子が別の資料を示す。「南海トラフ＋首都直下 連動リスク」の図が見える | 信子「でも南海トラフと首都直下は連動する可能性がある。大阪に置いたら共倒れじゃない？」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, research-lab atmosphere with an air of urgency.

[TOP LARGE PANEL] Both women stand in front of a large monitor showing a disaster simulation. The screen shows a map of Japan with earthquake impact zones around Tokyo highlighted. Both look serious. Speech bubble from the younger woman (gray blazer, glasses, black hair bun): "首都直下が来たら、東京だけに機能が集中している今の状態は危険すぎる"

[BOTTOM LEFT PANEL] The younger woman gestures with passion, a simple diagram showing city decentralization visible behind her. A speech bubble: "だから副首都で機能を分散させる。防災のためにこそ、早く進めるべきなんだ"

[BOTTOM RIGHT PANEL] The older woman (navy cardigan, wavy graying hair) holds up a separate research document. The document visible has a diagram showing overlapping disaster zones labeled "南海トラフ＋首都直下 連動リスク". Her expression is firm. A speech bubble: "でも南海トラフと首都直下は連動する可能性がある。大阪に置いたら共倒れじゃない？"
```

---

### ページ5「費用・財源」— いくらかかるか、誰も知らない

**ファイル名:** `fukushuto-manga-hiyou.webp`

**ストーリー:** 国会中継を見ていたら「費用は現時点では分かりません」の答弁が流れる。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 二人が国会中継を見ている。テレビ画面には「副首都整備にかかる費用は？」という質問が表示されている | 信子「費用の試算、出てたっけ？」 結衣「4兆円とも7.5兆円とも言われてて……国会でも聞かれてたんだ」 |
| 下段・左 | テレビから大写しになる答弁画面。答弁者の字幕に「現時点では分かりません」 | （ト書き）テレビからの答弁音声 |
| 下段・右 | 信子が呆然とした顔。結衣も困惑気味 | 信子「…兆円単位の事業なのに、費用が『分からない』って何？」 結衣「物価が上がってる今、これは説明が足りないよ」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, living room watching parliament broadcast.

[TOP LARGE PANEL] Both women sit watching a live Diet session on TV. The screen shows a parliamentary committee. The younger woman (glasses, gray blazer) holds a tablet with news articles open. The older woman (navy cardigan, round glasses) holds a printed document. Two speech bubbles: the older woman asking "費用の試算、出てたっけ？" and the younger replying "4兆円とも7.5兆円とも言われてて……国会でも聞かれてたんだ"

[BOTTOM LEFT PANEL] Close-up of the TV screen showing the parliament member at the podium. A subtitle banner overlaid on the TV image contains the Japanese text "現時点では分かりません". The screen takes up most of the panel.

[BOTTOM RIGHT PANEL] Both women stare at the TV with disbelief. The older woman's mouth is open in shock. Two speech bubbles: the older woman saying "…兆円単位の事業なのに、費用が『分からない』って何？" and the younger (looking conflicted) saying "物価が上がってる今、これは説明が足りないよ"
```

---

### ページ6「優先順位」— 今やることなの？

**ファイル名:** `fukushuto-manga-yusen.webp`

**ストーリー:** スーパーの値上がりに驚く信子。帰宅してニュースをつけると、副首都法案が会期延長で今国会成立へ。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | スーパーで信子が値段のついた野菜やパンを見てため息をついている。隣で結衣も表情が曇る | 信子「また値上がりしてる……生活、本当に苦しいよ」 |
| 下段・左 | 帰宅後、テレビをつけた二人。ニュース速報「副首都法案、会期延長して今国会成立へ」 | 信子「え……」 |
| 下段・右 | 信子が腰に手を当ててテレビに向かう。結衣は複雑な表情 | 信子「消費税減税は先送りで、副首都は会期延長？今やることじゃないでしょ！」 結衣「……タイミングの問題は、正直あると思う」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, everyday life atmosphere.

[TOP LARGE PANEL] A Japanese supermarket aisle. The older woman (navy cardigan, wavy graying hair, round glasses) holds a basket and stares at a price tag on bread with a tired sigh. The younger woman (gray blazer) stands beside her looking troubled. Price tags on shelves show noticeably high numbers. Speech bubble from the older woman: "また値上がりしてる……生活、本当に苦しいよ"

[BOTTOM LEFT PANEL] Back at home. Both women sit on the sofa as the younger woman turns on the TV remote. The TV screen shows a breaking news banner: "副首都法案、会期延長して今国会成立へ". The older woman stares at the screen with a blank expression. A minimal speech bubble: "え……"

[BOTTOM RIGHT PANEL] The older woman stands facing the TV with hands on her hips, frustrated. The younger woman sits on the couch with a conflicted, complicated expression. Two speech bubbles: the older woman saying "消費税減税は先送りで、副首都は会期延長？今やることじゃないでしょ！" and the younger saying "……タイミングの問題は、正直あると思う"
```

---

### ページ7「その他・わからない」— 難しくて、正直よくわからない

**ファイル名:** `fukushuto-manga-sonota.webp`

**ストーリー:** SNSを眺める二人。意見が飛び交っているが「副首都って何？」という根本的な疑問が残る。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 二人がスマホを見ながらソファに座っている。画面にはSNSの意見が次々流れている（「賛成」「反対」「意味不明」が入り乱れる） | 結衣「SNS見てると、みんな言ってることが全然違う……」 |
| 下段・左 | 信子がスマホをテーブルに置いて首をひねる | 信子「そもそも副首都って……実際、何をする場所なの？」 |
| 下段・右 | 結衣も腕を組んで黙り込む。窓の外は夕暮れ | 結衣「……それが決まってないのが、この法案の問題なんだよね」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, casual evening home atmosphere.

[TOP LARGE PANEL] Both women sit side by side on a sofa, each scrolling their smartphones. The phone screens show a stream of social media posts with contrasting opinions — some in green showing support, some in red showing opposition, some in gray showing confusion. Mixed Japanese text fragments like "賛成", "反対", "意味不明" float around the screens stylistically. Speech bubble from the younger woman (gray blazer, glasses): "SNS見てると、みんな言ってることが全然違う……"

[BOTTOM LEFT PANEL] The older woman (navy cardigan, round glasses) sets her phone down on the coffee table and tilts her head thoughtfully. A speech bubble: "そもそも副首都って……実際、何をする場所なの？"

[BOTTOM RIGHT PANEL] Wide shot of both women in the room. The younger woman crosses her arms and goes quiet. Warm evening light comes through the window. A speech bubble from the younger woman: "……それが決まってないのが、この法案の問題なんだよね"
```

---

## 生成時の注意事項

- **キャラクターシートを必ず参照**してからページを生成すること（ChatGPT/DALL-Eに添付）
- 各ページは **縦長（2:3比率）** で統一する
- セリフは日本語のまま画像内に入れること
- 暴力・危険シーン・政党ロゴ等は描かない
- 生成後は `cwebp -q 45 -resize 900 0 input.png -o output.webp` で変換
