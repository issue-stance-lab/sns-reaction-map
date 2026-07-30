# 投票ボタン画像 — Gptimage2プロンプト

テーマ: 生成AIと著作権問題
生成枚数: 4枚
生成サイズ: 512 x 512px（正方形）
保存形式: WebP、1枚20KB以下に圧縮

**重要:** 生成時にキャラクターシート2枚を参照画像として添付すること。

---

## 画像1: 規制強化すべき（澪 — 決意の表情）

立場: クリエイターの権利を守るためAI規制を強化すべき
キャラ: 藤原澪（イラストレーター）
感情: 怒りと決意、自分の作品を守る強い意志

```
Square portrait illustration, 512x512px, white/light gradient background. A young Japanese female illustrator (short black bob hair, round glasses, dark beret, beige cardigan) looking directly at the viewer with a determined, fierce expression. She holds a stylus pen like a weapon, clutching it tightly. Her eyes are sharp and resolute, with a hint of tears. A faint silhouette of her artwork glows behind her. Warm orange-red accent lighting from the left side. Anime-inspired semi-realistic manga style, clean line art, bust shot, centered composition.
```

---

## 画像2: 規制は最小限に（颯太 — 信念の表情）

立場: 技術革新を止めないよう規制は最小限にすべき
キャラ: 桐谷颯太（AIエンジニア）
感情: 信念と情熱、テクノロジーの未来を信じる

```
Square portrait illustration, 512x512px, white/light gradient background. A young Japanese male AI engineer (short brown hair, light stubble, dark navy hoodie, black t-shirt) looking directly at the viewer with a confident, passionate expression. He holds his laptop under one arm, the other hand slightly raised as if explaining his vision. His eyes are calm but burning with conviction. A faint holographic neural network pattern glows behind him. Cool blue accent lighting from the right side. Anime-inspired semi-realistic manga style, clean line art, bust shot, centered composition.
```

---

## 画像3: 条件付きで共存（澪と颯太 — 歩み寄り）

立場: オプトアウトや対価支払いなど条件付きで共存
キャラ: 両方
感情: 慎重だが前向き、対話の姿勢

```
Square illustration, 512x512px, white/light gradient background. Two characters side by side facing the viewer. Left: a young Japanese woman (short black bob, glasses, beret, beige cardigan) with a cautious but hopeful expression. Right: a young Japanese man (brown hair, stubble, navy hoodie) with an empathetic, open expression. Between them, a subtle warm golden glow suggests a bridge or connection forming. Both have their hands slightly extended toward each other but not quite touching. Balanced warm and cool lighting merging in the center. Anime-inspired semi-realistic manga style, clean line art, centered composition.
```

---

## 画像4: まだ判断できない（考え込むシルエット風）

立場: よくわからない・まだ判断できない
キャラ: 汎用（特定キャラではない）
感情: 迷い、考え中

```
Square illustration, 512x512px, white/light gradient background. A single figure shown from behind, slightly translucent/silhouette style, looking at a crossroads or forked path ahead. The left path glows warm orange (representing creators), the right path glows cool blue (representing technology). The figure has a question mark subtly formed in the light above their head. Soft, dreamy atmosphere with muted colors. The overall mood is contemplative and undecided. Anime-inspired semi-realistic manga style, clean line art, centered composition.
```

---

## 保存先

生成後 WebP に変換、20KB以下に圧縮して以下に配置:

```
docs/images/topics/ai-copyright/
├── ai-copyright-vote-1-regulate.webp
├── ai-copyright-vote-2-innovate.webp
├── ai-copyright-vote-3-coexist.webp
└── ai-copyright-vote-4-unsure.webp
```

## HTML側の変更

画像表示サイズを現在の56x56px丸型から **120x120px角丸16px** に変更する。
モバイルでは100x100pxに縮小（メディアクエリで対応）。
