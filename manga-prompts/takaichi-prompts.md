# 高市文春問題 — 漫画生成プロンプト

テーマ: 高市文春問題 SNS反応まっぷ
生成枚数: キャラシート2枚 + 本番ページ3枚 = 計5枚

**注意:** 実在の政治家（高市早苗氏）の顔を描かない。架空の「総理秘書」と「記者」の対立構図で描く。

## 保存先

生成後 WebP に変換、漫画≤100KB（リサイズ900px、q45目安）で以下に配置:

```
docs/images/
├── takaichi-manga-charsheet-reiko.webp
├── takaichi-manga-charsheet-shota.webp
├── takaichi-manga-page-1.webp
├── takaichi-manga-page-2.webp
└── takaichi-manga-page-3.webp
```

---

## Step 1: キャラクターシート生成（Character Lock用）

### キャラシート① 桐山 玲子（きりやま れいこ）

- 役割: 週刊誌記者・政治部デスク（38歳）
- 立場: 中傷動画の組織的拡散に関する取材を進め、説明責任を求める
- 恐れ: 証拠不十分のまま報じれば信頼を失うこと
- 望み: ネット選挙の透明性を社会に問いたい

```
Character design reference sheet, white background, multiple expressions (determined, doubtful, surprised, focused, satisfied), full body and close-up face views. Japanese female journalist, age 38, chin-length bob haircut in dark brown, no glasses, beige trench coat over black turtleneck, press badge on a lanyard, holding a reporter's notebook and pen. Athletic build, sharp and perceptive demeanor. Anime-inspired semi-realistic manga style, clean line art, urban newsroom color palette.
```

### キャラシート② 長谷川 翔太（はせがわ しょうた）

- 役割: 与党議員の政策秘書（34歳）
- 立場: 報道は裏取り不足の印象操作であり、党の立場を守る
- 恐れ: 根拠のない報道で議員のキャリアが潰されること
- 望み: ネット戦略は合法的な選挙活動であると証明したい

```
Character design reference sheet, white background, multiple expressions (confident, defensive, frustrated, composed, calculating), full body and close-up face views. Japanese male political secretary, age 34, short neat black hair swept to the side, slim rectangular glasses, navy blue suit with thin stripe, light blue shirt, no tie, smartphone always in hand. Lean build, polished and strategic demeanor. Anime-inspired semi-realistic manga style, clean line art, political office color palette.
```

---

## Step 2: 本番ページ生成

**重要:** 生成時に Step 1 で作成したキャラクターシート2枚を参照画像として添付すること。

---

### ページ1「文春砲、波紋広がる」

**構成:** 上段1コマ大 + 下段2コマ

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 週刊誌の編集部。玲子がデスクでパソコン画面に映る「中傷動画が組織的に拡散」の記事原稿を確認。同僚記者たちが周囲で作業中 | 玲子「これだけの証拠がある。出すべきだ。」 |
| 下段・左 | 議員会館の秘書室。翔太がスマホで速報ニュースを見ている。画面に「週刊誌が中傷動画疑惑を報道」の通知 | 翔太「……また週刊誌か。裏を取ってから書けよ。」 |
| 下段・右 | SNSのタイムラインのモンタージュ。「説明責任！」「捏造だろ」「証拠は？」と様々な反応 | ナレーション「ネット上では即座に賛否が分かれた。」 |

```
A manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, tense media/political atmosphere.

[TOP LARGE PANEL] A busy weekly magazine editorial office at night. A female journalist (chin-length dark brown bob, beige trench coat draped on chair, black turtleneck, press badge) sits at her desk reviewing a draft article on a large monitor. The screen shows headlines about "organized distribution of attack videos." Colleagues work at nearby desks under fluorescent lights. A speech bubble containing the Japanese text "これだけの証拠がある。出すべきだ。"

[BOTTOM LEFT PANEL] A political secretary's office in the Diet Members' Building. A young male secretary (short neat black hair, slim rectangular glasses, navy striped suit, light blue shirt) looks at his smartphone with a tense expression. The phone screen shows a news alert about "weekly magazine reports attack video allegations." A speech bubble containing the Japanese text "……また週刊誌か。裏を取ってから書けよ。"

[BOTTOM RIGHT PANEL] A collage of smartphone screens showing social media reactions. Various posts visible: "説明責任を果たせ", "また捏造報道か", "証拠を出せ", "ネット選挙の闇". Likes, retweets, and angry emoji reactions. A narration box containing the Japanese text "ネット上では即座に賛否が分かれた。"
```

---

### ページ2「証拠と反論」

**構成:** 上段2コマ + 下段1コマ大

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・左 | 記者会見場。玲子が手を挙げて質問。フラッシュが光る | 玲子「動画制作を外部に委託した事実はありますか？ YES か NO でお答えください。」 |
| 上段・右 | 翔太が記者会見の控室で、弁護士と対策を練っている。ホワイトボードに「反論ポイント」の箇条書き | 翔太「勝手連の活動と陣営は無関係だ。法的に何の問題もない。」 |
| 下段・大 | 玲子と翔太がカフェで偶然出くわし、テーブルを挟んで向かい合う | 玲子「有権者が知る権利がある。隠すほど疑惑は深まる。」/ 翔太「根拠のない疑惑で人を裁くのは、それこそ中傷じゃないですか。」 |

```
A manga page with 3 panels layout (two smaller panels on top row, one large panel on the bottom). Anime-inspired semi-realistic manga style, clean line art, confrontational political atmosphere.

[TOP LEFT PANEL] A press conference room. The female journalist (chin-length dark brown bob, black turtleneck, press badge on lanyard) stands among reporters, raising her hand to ask a question. Camera flashes illuminate the scene. Microphones and recorders point toward an unseen podium. A speech bubble containing the Japanese text "動画制作を外部に委託した事実はありますか？ YES か NO でお答えください。"

[TOP RIGHT PANEL] A backroom behind the press conference. The male political secretary (short neat black hair, slim rectangular glasses, navy striped suit) discusses strategy with a lawyer. A whiteboard behind them lists "反論ポイント" with bullet points. His expression is focused and strategic. A speech bubble containing the Japanese text "勝手連の活動と陣営は無関係だ。法的に何の問題もない。"

[BOTTOM LARGE PANEL] A quiet café near the Diet building. The journalist and the secretary sit across from each other at a small table. Coffee cups between them. She leans forward with determination. He sits back with arms crossed defensively. Tension fills the air but the conversation is civil. Two speech bubbles: one from the journalist containing the Japanese text "有権者が知る権利がある。隠すほど疑惑は深まる。" and one from the secretary containing the Japanese text "根拠のない疑惑で人を裁くのは、それこそ中傷じゃないですか。"
```

---

### ページ3「透明性への問い」

**構成:** 上段2コマ + 下段1コマ大

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・左 | 国会答弁シーン。議員（後ろ姿のみ）が答弁修正を読み上げている。傍聴席の翔太が目を閉じている | ナレーション「答弁は訂正された。だが疑問は消えなかった。」 |
| 上段・右 | 玲子が編集部で次の記事を書いている。画面に「ネット選挙の透明性」の見出し | 玲子「事実を積み重ねるしかない。読者が判断する。」 |
| 下段・大 | 二分割構図。左に玲子がノートPCに向かう横顔、右に翔太がスマホを見つめる横顔。二人の間にSNSの投稿が浮かぶ | 玲子「民主主義のコストは、知ることだ。」/ 翔太「……正しい情報が何かを決めるのは、誰なんだ。」 |

```
A manga page with 3 panels layout (two panels on top row, one large panel on bottom). Anime-inspired semi-realistic manga style, clean line art, reflective and contemplative tone.

[TOP LEFT PANEL] The Diet chamber during an answer session. A politician (shown only from behind, face not visible) reads a corrected statement at the podium. In the spectator gallery, the male secretary (short neat black hair, slim rectangular glasses, navy suit) sits with eyes closed, conflicted. A narration box containing the Japanese text "答弁は訂正された。だが疑問は消えなかった。"

[TOP RIGHT PANEL] The magazine editorial office. The female journalist (chin-length dark brown bob, black turtleneck) types at her desk. Her monitor shows a new article draft with the headline "ネット選挙の透明性を問う". Her expression is determined but weary. A speech bubble containing the Japanese text "事実を積み重ねるしかない。読者が判断する。"

[BOTTOM LARGE PANEL] Split composition: on the left, the journalist at her laptop in profile view, illuminated by the screen's glow. On the right, the secretary looking at his smartphone in profile view, the light casting shadows on his face. Between them, floating social media posts with various opinions ("説明しろ", "証拠不十分", "有権者をなめるな", "報道の自由"). Both scenes share the same twilight sky through their respective windows. Two speech bubbles: one from the journalist containing the Japanese text "民主主義のコストは、知ることだ。" and one from the secretary containing the Japanese text "……正しい情報が何かを決めるのは、誰なんだ。"
```
