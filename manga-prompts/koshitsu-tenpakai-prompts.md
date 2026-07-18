# 皇室典範改正 — 漫画生成プロンプト

テーマ: 皇室典範改正（女性皇族の皇籍維持・旧宮家養子）SNS反応まっぷ
生成枚数: キャラシート2枚 + 本番ページ3枚 = 計5枚

## 保存先

生成後 WebP に変換、各ファイル≤100KB（リサイズ900px幅、q45目安）で以下に配置:

```
docs/images/
├── koshitsu-infographic-kouseki.webp
├── koshitsu-infographic-yoshi.webp
├── koshitsu-infographic-keisho.webp
├── koshitsu-manga-charsheet-sho.webp
├── koshitsu-manga-charsheet-rin.webp
├── koshitsu-manga-page-1.webp
├── koshitsu-manga-page-2.webp
└── koshitsu-manga-page-3.webp
```

---

## Step 0: 投票前インフォグラフィック生成

用途: 投票前の論点整理カード。副首都ページの `fukushuto-infographic-*.webp` と同じ位置に置く想定。
生成枚数: 3枚
推奨サイズ: 正方形 1:1
共通スタイル: `manga-prompts/infographic-style-guide.md` を使用。副首都ページで作成した `fukushuto-infographic-*.webp` と同じ、明るい civic-tech インフォグラフィックの作風に統一する。
トーン: 白〜淡い水色の背景、濃紺・鮮やかな青の大きな日本語見出し、角丸カード、柔らかい影、小さなドット・スパークル・グラフ風アクセント。かわいすぎず、硬すぎない政策ダッシュボード風。煽らず、中立的。実在の皇族の顔や実在政治家の顔は描かない。

### 図解1「女性皇族の皇籍維持」— 結婚後も皇族に残るとは？

**ファイル名:** `koshitsu-infographic-kouseki.webp`

**画面内に入れたい短い日本語:**

- 女性皇族の皇籍維持
- 結婚後も皇族として活動
- 配偶者・子の扱いは？
- 皇位継承権はどうなる？

```
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「女性皇族の皇籍維持」

Main title:
「女性皇族の皇籍維持」
「結婚後も皇族に残るとは？」

Core message:
今回の改正では、女性皇族が結婚後も皇族として活動できる道が開かれる。一方で、配偶者・子の扱いや皇位継承権との関係が論点になる。

Composition:
Center:
A simplified family tree diagram using neutral silhouette icons only. One female royal silhouette follows a highlighted "marriage" path but remains inside a softly outlined area labeled 「皇族」. Do not depict real royal faces.

Around the center, place 4 rounded check cards:
1. 「結婚後も活動」 「公務の担い手を確保」
2. 「配偶者の扱い」 「皇族になるのか？」
3. 「子の扱い」 「次世代まで残るのか？」
4. 「継承権」 「皇位継承とは別論点」

Bottom conclusion band:
「皇族数の確保と、継承制度の線引きが焦点」

Use the common “SNS反応まっぷ civic-tech infographic style”.

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with green, red, orange, purple, gray, and teal as issue accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no dark scenes,
no clutter, no random extra text, no watermark.
```

### 図解2「旧宮家男系男子の養子制度」— 誰を皇族に迎えるのか？

**ファイル名:** `koshitsu-infographic-yoshi.webp`

**画面内に入れたい短い日本語:**

- 旧宮家男系男子の養子制度
- 戦後に皇籍離脱
- 男系男子を養子に
- 正統性・合憲性が論点

```
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「旧宮家男系男子の養子制度」

Main title:
「旧宮家男系男子の養子制度」
「誰を皇族に迎えるのか？」

Core message:
旧宮家の男系男子を養子として皇族に迎える制度は、男系維持の手段として評価される一方、正統性や合憲性をめぐって意見が分かれる。

Composition:
Center:
Two clean family-tree blocks. Left block labeled 「旧宮家」 with a small timeline marker 「戦後に皇籍離脱」. Right block labeled 「皇室」. A highlighted arrow labeled 「養子」 connects a male-line descendant silhouette from the former branch to the current imperial household block. Add a balance scale icon and a document icon to show legal debate.

Around the center, place 4 rounded check cards:
1. 「戦後に離脱」 「現在は皇族ではない」
2. 「男系男子」 「男系維持の候補」
3. 「養子で復帰」 「制度設計が必要」
4. 「法的論点」 「正統性・合憲性」

Bottom conclusion band:
「皇統維持の手段か、制度上の無理筋か」

Use the common “SNS反応まっぷ civic-tech infographic style”.

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with green, red, orange, purple, gray, and teal as issue accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no nationalist symbols,
no flags, no clutter, no random extra text, no watermark.
```

### 図解3「男系維持 vs 女系容認」— 何が対立しているのか？

**ファイル名:** `koshitsu-infographic-keisho.webp`

**画面内に入れたい短い日本語:**

- 男系維持 vs 女系容認
- 女性天皇と女系天皇は別論点
- 伝統の継続
- 安定継承

```
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「男系維持 vs 女系容認」

Main title:
「男系維持 vs 女系容認」
「何が対立しているのか？」

Core message:
対立は単純な賛否ではなく、皇位継承を男系に限るのか、女系も認めるのかという制度設計の違い。女性天皇と女系天皇の区別も重要な論点になる。

Composition:
Center:
A balanced two-column comparison chart. Left side shows a simple vertical patrilineal family line with male-line markers, labeled 「男系維持」 and a small historical-scroll icon. Right side shows a gender-neutral succession line with both male and female silhouette icons, labeled 「女系容認」 and a modern policy-document icon. In the middle, place a neutral mini card labeled 「女性天皇と女系天皇は別論点」.

Around the center, place 4 rounded check cards:
1. 「男系維持」 「父方の血筋を重視」
2. 「女系容認」 「性別にかかわらず継承」
3. 「女性天皇」 「男系の女性が即位」
4. 「安定継承」 「将来世代まで続くか」

Bottom conclusion band:
「伝統の継続と安定継承をどう両立するか」

Use the common “SNS反応まっぷ civic-tech infographic style”.

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with green, red, orange, purple, gray, and teal as issue accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no emotional crowd imagery,
no crown-heavy fantasy decoration, no clutter, no random extra text, no watermark.
```

---

## Step 1: キャラクターシート生成（Character Lock用）

### キャラシート① 宮本 翔（みやもと しょう）

- 役割: 内閣府・皇室制度準備室の若手職員（35歳）
- 立場: 改正を現実的な一歩として支持。まず皇族数を確保すべきと考える
- 恐れ: 議論を続けている間に皇族がいなくなること
- 望み: 制度の安定を確保してから、次のステップを議論したい
- 外見: 短めの黒髪、スクエア型の黒縁メガネ、チャコールグレーのスーツに白シャツ、ノータイ。生真面目で実直な印象

```
Character design reference sheet, white background, multiple expressions (earnest, frustrated, relieved, determined, conflicted), full body and close-up face views. Japanese male government official, age 35, short neat black hair, square black-rimmed glasses, charcoal gray suit with white dress shirt and no tie, holding a clipboard with policy documents. Medium build, serious and conscientious posture. Anime-inspired semi-realistic manga style, clean line art, muted gray-blue palette.
```

### キャラシート② 森山 凛（もりやま りん）

- 役割: 憲法学の大学院生・ジェンダー政策の市民団体でも活動（28歳）
- 立場: 改正は不十分。女性天皇・女系天皇の議論を避けた改正に反対
- 恐れ: 男系限定を制度として固定し、議論の扉が閉じること
- 望み: 性別にかかわらず皇位を継承できる制度への道を開きたい
- 外見: 肩下のストレート黒髪、丸メガネ、ネイビーのカーディガンにクリーム色のブラウス、憲法の教科書を抱えている。知的で芯が強い印象

```
Character design reference sheet, white background, multiple expressions (passionate, skeptical, thoughtful, surprised, quietly determined), full body and close-up face views. Japanese female graduate student, age 28, shoulder-length straight black hair, round thin-frame glasses, navy cardigan over a cream blouse, holding a constitutional law textbook. Slim build, intellectual and quietly strong-willed demeanor. Anime-inspired semi-realistic manga style, clean line art, warm navy and cream palette.
```

---

## Step 2: 本番ページ生成

**重要:** 生成時に Step 1 で作成したキャラクターシート2枚を参照画像として添付すること。

---

### ページ1【導入】「可決の瞬間、二人の反応」

**ファイル名:** `koshitsu-manga-page-1.webp`
**構成:** 上段1コマ大 + 下段2コマ
**タイトルバナー:** 「男系か、女系か。」（1ページ目のみ）

**ストーリー:** 参議院で改正皇室典範が可決された瞬間。テレビ速報を見る二人の反応は正反対。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・大 | 国会議事堂のテレビ中継。「改正皇室典範　可決・成立」の速報テロップが表示されている。画面手前にスマホを握る手 | ナレーション「2026年7月17日——」 |
| 下段・左 | 内閣府のオフィス。翔がパソコンの前で拳を握り、静かに安堵している。机には「皇族数推移」の資料 | 翔「……間に合った。あと10年遅れていたら、取り返しがつかなかった」 |
| 下段・右 | 大学の研究室。凛がテレビを見て唇を噛んでいる。手元の憲法の教科書が開かれている | 凛「女性天皇も、女系天皇も……結局、議論すらしなかった」 |

```
A vertical manga page with 3 panels layout (one large panel on top, two smaller panels on the bottom row). Anime-inspired semi-realistic manga style, clean line art, dramatic political atmosphere. At the top of the page, a bold manga-style title banner with the Japanese text "男系か、女系か。" in large, dynamic handwritten-style lettering with a subtle dark red background accent.

[TOP LARGE PANEL] A close-up of a TV screen showing a live broadcast from the Japanese Diet chamber. A large red news ticker banner across the bottom reads "改正皇室典範　可決・成立". Politicians are visible in the chamber background. In the foreground, a hand grips a smartphone tightly. A narration box in the corner containing the Japanese text "2026年7月17日——"

[BOTTOM LEFT PANEL] A Japanese government office. A young male official (short neat black hair, square black-rimmed glasses, charcoal gray suit, white shirt, no tie) sits at his desk. He clenches his fist on the desk with quiet relief. Documents titled "皇族数推移" are visible on his desk. A speech bubble containing the Japanese text "……間に合った。あと10年遅れていたら、取り返しがつかなかった"

[BOTTOM RIGHT PANEL] A university research office. A young woman (shoulder-length straight black hair, round thin-frame glasses, navy cardigan over cream blouse) watches a small TV with a pained expression, biting her lower lip. An open constitutional law textbook sits on the desk beside her. A speech bubble containing the Japanese text "女性天皇も、女系天皇も……結局、議論すらしなかった"
```

---

### ページ2【対立】「養子制度か、女系容認か」

**ファイル名:** `koshitsu-manga-page-2.webp`
**構成:** 上段2コマ + 下段1コマ大

**ストーリー:** 市民フォーラムで偶然同じテーブルについた二人。養子制度の是非を巡って意見がぶつかる。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・左 | 市民フォーラム会場。翔が資料を見せながら説明している。資料には皇族の家系図と「現在の皇族数：17名」の数字 | 翔「皇族は今17名。このまま何もしなければ、悠仁親王の次の世代で皇族がゼロになる可能性がある」 |
| 上段・右 | 凛が手を挙げて反論する。背景に「憲法14条　法の下の平等」のスライドが見える | 凛「だからといって、80年前に離脱した家系から養子を迎えるのが答えですか？　憲法14条はどうなるんです？」 |
| 下段・大 | テーブルを挟んで向かい合う二人。翔は資料を指さし、凛は憲法の条文を示す。二人の間に緊張感 | 翔「完璧を求めて何もしないより、今できることを積み上げるべきだ」 / 凛「"今できること"の範囲から女性を除外したのは、政治の選択でしょう？」 |

```
A vertical manga page with 3 panels layout (two smaller panels on top row, one large panel on the bottom). Anime-inspired semi-realistic manga style, clean line art, tense debate atmosphere in a civic forum setting.

[TOP LEFT PANEL] A public civic forum hall. The young male official (short neat black hair, square black-rimmed glasses, charcoal gray suit, white shirt) holds up a printed document showing an imperial family tree diagram with the number "現在の皇族数：17名" circled. He speaks with earnest urgency. A speech bubble containing the Japanese text "皇族は今17名。このまま何もしなければ、悠仁親王の次の世代で皇族がゼロになる可能性がある"

[TOP RIGHT PANEL] The young woman (shoulder-length straight black hair, round thin-frame glasses, navy cardigan, cream blouse) raises her hand to challenge. Behind her, a projected slide is partially visible showing "憲法14条　法の下の平等". Her expression is sharp and determined. A speech bubble containing the Japanese text "だからといって、80年前に離脱した家系から養子を迎えるのが答えですか？　憲法14条はどうなるんです？"

[BOTTOM LARGE PANEL] Both sit across a table, leaning forward. The man points at his policy documents; the woman holds open a booklet showing constitutional articles. Tension fills the space between them. Other forum attendees watch in the background. Two speech bubbles: one from the man containing the Japanese text "完璧を求めて何もしないより、今できることを積み上げるべきだ" and one from the woman containing the Japanese text ""今できること"の範囲から女性を除外したのは、政治の選択でしょう？"
```

---

### ページ3【余韻】「皇室を想う気持ちは、同じだった」

**ファイル名:** `koshitsu-manga-page-3.webp`
**構成:** 上段2コマ + 下段1コマ大（ワイド）

**ストーリー:** フォーラム後、ロビーで二人が少し歩み寄る。根っこにある「皇室への想い」は同じだと気づく。

| コマ | 内容 | セリフ |
|------|------|--------|
| 上段・左 | フォーラム後のロビー。凛が自販機でお茶を買っている。翔が隣に立つ | 凛「……あなたも、皇室がなくなっていいとは思ってないんですよね」 |
| 上段・右 | 翔が窓の外を見ながら答える。夕暮れの国会議事堂のシルエットが見える | 翔「もちろん。だからこそ、今の法案でも前に進めたかった。……でも、君の言う"除外"は、確かに説明が足りない」 |
| 下段・大 | ロビーの窓際に並んで立つ二人の後ろ姿。夕焼けの中に国会議事堂。二人の間にわずかな距離、しかし同じ方向を見ている | 凛「次の議論が、ちゃんと開かれますように」 / 翔「……そのときは、同じテーブルで話しましょう」 |

```
A vertical manga page with 3 panels layout (two panels on top row, one large wide panel on bottom). Anime-inspired semi-realistic manga style, clean line art, reflective and warm evening atmosphere.

[TOP LEFT PANEL] A lobby area after the forum. The young woman (shoulder-length straight black hair, round thin-frame glasses, navy cardigan) buys tea from a vending machine. The young man (short neat black hair, square glasses, charcoal suit) stands nearby, slightly hesitant. A speech bubble from the woman containing the Japanese text "……あなたも、皇室がなくなっていいとは思ってないんですよね"

[TOP RIGHT PANEL] The man looks out a window. Through the glass, the silhouette of the National Diet Building is visible against an orange sunset sky. His expression is thoughtful and slightly softened. A speech bubble containing the Japanese text "もちろん。だからこそ、今の法案でも前に進めたかった。……でも、君の言う"除外"は、確かに説明が足りない"

[BOTTOM LARGE PANEL] Wide cinematic shot from behind. Both stand side by side at the large lobby window, looking out at the sunset over the Diet Building. A small but meaningful gap between them — not yet allies, but no longer adversaries. Evening light bathes the scene in warm orange. Two speech bubbles: one from the woman containing the Japanese text "次の議論が、ちゃんと開かれますように" and one from the man containing the Japanese text "……そのときは、同じテーブルで話しましょう"
```

---

## 生成時の注意事項

- **キャラクターシートを必ず参照**してからページを生成すること（ChatGPT/DALL-Eに添付）
- 各ページは **縦長（2:3比率）** で統一する
- セリフは日本語のまま画像内に入れること
- 実在の皇族の顔は描かない（シルエットやニュース映像として処理）
- 政党ロゴ・実在政治家の顔は描かない
- 生成後は `cwebp -q 45 -resize 900 0 input.png -o output.webp` で変換
