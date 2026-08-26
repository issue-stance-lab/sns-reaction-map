# 学校でのあだ名禁止 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `creative/manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 「生成AIと著作権」ページの
`docs/images/topics/ai-copyright/ai-copyright-infographic-wide-*.webp` と同じ、明るい
civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の
見出し、角丸カード、柔らかい影、ドット・スパークル・小さなグラフ風
アクセントを使う。

人物ドラマや漫画表現ではなく、学校・名札・吹き出し・盾・天秤・チェック
リストなどの抽象アイコンを中心にする。実在する学校名、校章、自治体ロゴ、
制服、SNSロゴ、実在人物は描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**

「生成AIと著作権」のwide版と同一サイズを指定すること。

## 分類データ

Yahooリアルタイム検索で取得した374件をHermesで再分類。
関連投稿106件のうち、関連する意見投稿63件を論点アリーナへ使用。

| 論点 | 件数 | スタンス内訳 |
|---|---:|---|
| いじめ・心理的安全 | 17 | 禁止支持6 / 反対1 / 中立10 |
| 一律禁止の実効性 | 16 | 反対13 / 条件付き2 / 中立1 |
| 親しさ・呼称文化 | 13 | 反対10 / 支持1 / 条件付き1 / 中立1 |
| 学校運用・現場体験 | 8 | 中立6 / 支持1 / 反対1 |
| さん付け・ジェンダー配慮 | 5 | 反対4 / 中立1 |
| 本人意思・柔軟運用 | 4 | 条件付き4 |

注意: 上記は取得したSNS投稿サンプルの構成であり、世論比率ではない。

## 保存先・変換コマンド

```text
docs/images/topics/school-nickname-ban/
├── school-nickname-ban-infographic-wide-safety.webp
├── school-nickname-ban-infographic-wide-effectiveness.webp
├── school-nickname-ban-infographic-wide-culture.webp
├── school-nickname-ban-infographic-wide-field.webp
├── school-nickname-ban-infographic-wide-gender.webp
└── school-nickname-ban-infographic-wide-choice.webp
```

```bash
cwebp -q 82 input.png -o docs/images/topics/school-nickname-ban/school-nickname-ban-infographic-wide-XXX.webp
```

---

## 1. いじめ・心理的安全 — 呼び方のルールで傷つく子を守れるか

**ファイル名:** `school-nickname-ban-infographic-wide-safety.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「いじめ・心理的安全」

Main title (top-left area, large bold Japanese text):
「いじめ・心理的安全」
「呼び方のルールで、傷つく子を守れるか」

Core message:
17件で最多の論点。禁止支持6件、中立・体験10件、反対1件。
嫌なあだ名やからかいの入口を減らしたいという考えと、
呼び方だけを禁止しても人間関係への教育は残るという見方がある。
取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
教室を表す抽象的な机・名札・吹き出しのアイコン。
赤いギザギザ吹き出し「嫌なあだ名」が、緑の盾
「安心できる呼び方」で遮られるシンプルな図。
小さなラベルは「からかいの入口を減らす」。

CENTER ZONE:
大きな盾アイコンの中央に「心理的安全」。
左側に緑のカード「予防ルール」、右側に青いカード「対話・教育」。
両方から盾へ矢印を伸ばし、
「ルールだけか、教育も必要か」の問いを置く。
下部に3色の短い横バー:
「支持 6」「中立・体験 10」「反対 1」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「被害を予防」「嫌な呼び方の入口を減らす」
  「言いにくい子」「拒否を伝えにくい子を守る」
  「対話も必要」「相手の気持ちを考える教育」
  「禁止の限界」「別の言葉による攻撃は残る」

Bottom conclusion band (full width):
「守るための共通ルールと、関係を育てる教育をどう組み合わせるか」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light mint-blue background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Green/teal for safety and support, red only for harmful-name warnings,
blue for dialogue and education, gray for neutral experiences.
Friendly but professional, calm, balanced, nonjudgmental.
All Japanese text must be accurate, large, and readable.

Avoid:
No crying or injured children, no bullying reenactment, no threatening faces,
no real school uniforms, no school emblems, no teachers or children as identifiable
real people, no real SNS logos, no manga panels, no sensational fear imagery,
no random extra text, no watermark.
```

---

## 2. 一律禁止の実効性 — 禁止すればいじめは減るのか

**ファイル名:** `school-nickname-ban-infographic-wide-effectiveness.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「一律禁止の実効性」

Main title (top-left area, large bold Japanese text):
「一律禁止の実効性」
「禁止すれば、いじめは減るのか」

Core message:
16件。13件が一律禁止に反対、2件が条件付き・個別対応、
1件が中立。表面的な呼称規制ではいじめの本質は変わらないという
批判が中心だが、からかいの入口を減らす予防効果も検討点になる。
取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
「あだ名禁止」という学校ルールの書類アイコン。
書類から「呼び方を統一」へ進む青い矢印。
その先で矢印が「いじめ減少？」という大きな疑問符にぶつかる。
赤い小ラベル「表面的では？」。

CENTER ZONE:
原因と対策を比べる二層の因果図。
上段は「呼び方」→「ルールで制御」。
下段は「関係性・悪意」→「対話・個別対応」。
中央に天秤を置き「どこまで効果があるか」。
下部の短い横バー:
「反対 13」「条件付き 2」「中立 1」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「入口を減らす」「からかいのきっかけを予防」
  「本質は残る」「悪意や排除は別の形でも起こる」
  「過剰管理」「子どもの関係へ学校が介入しすぎる懸念」
  「個別対応」「問題のある呼び方を具体的に止める」

Bottom conclusion band (full width):
「ルールの分かりやすさと、いじめ対策の実効性は同じではない」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue-gray background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle flow-chart accents.
Blue for rules, red for effectiveness concerns, amber for conditional approaches,
gray for neutral information. Balanced and analytical, not anti-school.
All Japanese text must be accurate, large, and readable.

Avoid:
No politicians, no government emblems, no school emblems, no real SNS logos,
no identifiable children or teachers, no manga characters, no angry crowd,
no broken-school imagery, no random extra text, no watermark.
```

---

## 3. 親しさ・呼称文化 — あだ名は個性か、押しつけか

**ファイル名:** `school-nickname-ban-infographic-wide-culture.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「親しさ・呼称文化」

Main title (top-left area, large bold Japanese text):
「親しさ・呼称文化」
「あだ名は個性か、押しつけか」

Core message:
13件。10件が一律禁止に反対し、支持・条件付き・中立が各1件。
愛称は親しさや個性を生むという声が多い一方、
呼ぶ側の親しさと呼ばれる側の受け止めは一致しないことがある。
取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
3つの丸い名札アイコン。
「名字＋さん」「下の名前」「愛称」の3種類を並べる。
名札同士を柔らかい線でつなぎ「関係性で変わる呼び方」。
赤い小さな注意マークで「本人はどう感じる？」。

CENTER ZONE:
大きな2つの吹き出しを向かい合わせる。
緑の吹き出し「親しみ・個性」と、
赤紫の吹き出し「押しつけ・不快」。
中央に耳のアイコンと「受け手の気持ち」。
下部の短い横バー:
「反対 10」「支持 1」「条件付き 1」「中立 1」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「親近感」「自然な交流を生む愛称」
  「個性」「同じ名前でも呼び方で区別できる」
  「距離感」「さん付けでよそよそしく感じる場合」
  「受け手基準」「親しみでも嫌なら止める」

Bottom conclusion band (full width):
「呼ぶ側の親しさより、呼ばれる側の受け止めをどう確かめるか」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light lavender-blue background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles.
Teal/green for warmth and connection, purple for individuality,
red only for unwanted-name caution, blue for neutral naming choices.
Warm but neutral, never nostalgic or moralizing.
All Japanese text must be accurate, large, and readable.

Avoid:
No real children, no school uniforms, no identifiable classroom,
no mocking facial expressions, no speech bubbles with insults,
no real SNS logos, no manga panels, no random extra text, no watermark.
```

---

## 4. 学校運用・現場体験 — 学校ごとにルールが違う

**ファイル名:** `school-nickname-ban-infographic-wide-field.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「学校運用・現場体験」

Main title (top-left area, large bold Japanese text):
「学校運用・現場体験」
「学校ごとに、呼び方のルールが違う」

Core message:
8件。中立・体験6件、禁止支持1件、反対1件。
「昔から禁止だった」「今は下の名前で呼ぶ」「家庭と学校で違う」など、
同じ制度名でも時代・学校・先生によって運用が異なることを示す論点。
取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
3つの抽象的な学校建物アイコンを横並びにする。
学校A「名字＋さん」、学校B「下の名前」、学校C「愛称は本人同意」。
建物や校章は架空で、文字はこの3項目だけ。

CENTER ZONE:
「家庭」「友達同士」「先生」の3つの円を重ねたベン図。
重なる中央に「同じ子でも呼び方が違う」。
その下に小さなタイムライン:
「昔」→「現在」→「学校ごとの差」。
下部の短い横バー:
「中立・体験 6」「支持 1」「反対 1」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「学校差」「同じ地域でも運用が異なる」
  「世代差」「昔からあった学校もある」
  「家庭との違い」「家では呼び捨て、学校ではさん付け」
  「目的の共有」「なぜそのルールか説明できるか」

Bottom conclusion band (full width):
「制度名だけでなく、誰が・どこで・なぜ運用しているかを見る」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light cyan background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle timeline accents.
Cyan/blue for school operations, purple for generation differences,
gray for neutral experiences, small green and red accents for support/opposition.
Calm, observational, data-oriented.
All Japanese text must be accurate, large, and readable.

Avoid:
No real school names, no school emblems, no municipal logos,
no real uniforms, no identifiable people, no ranking of schools,
no real SNS logos, no manga characters, no random extra text, no watermark.
```

---

## 5. さん付け・ジェンダー配慮 — 呼び方を統一すれば対等になるか

**ファイル名:** `school-nickname-ban-infographic-wide-gender.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「さん付け・ジェンダー配慮」

Main title (top-left area, large bold Japanese text):
「さん付け・ジェンダー配慮」
「呼び方を統一すれば、対等になるか」

Core message:
5件。4件が一律禁止に反対、1件が中立。
「くん・ちゃん」の性差や上下関係をなくす狙いがある一方、
さん付けの形式だけを統一しても、対等さや人権尊重には直結しないという
批判が見られる。取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
「くん」「ちゃん」という2つの名札が、
一本の矢印で共通の「さん」名札へまとまる図。
上に「呼称を統一」、下に「性別で分けない」。
人物の性別を固定するイラストは使わず、名札だけで表現する。

CENTER ZONE:
大きな天秤アイコン。
左皿に「形式の統一」、右皿に「実質的な対等さ」。
中央の問いは「呼び方だけで変わる？」。
下部の短い横バー:
「反対 4」「中立 1」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「性差をなくす」「くん・ちゃんで分けない」
  「対等な敬称」「全員を同じ呼び方にする」
  「形式化の懸念」「さん付けだけが目的になる」
  「本人の希望」「敬称も関係性に合わせられるか」

Bottom conclusion band (full width):
「呼称の統一を、実質的な尊重へどうつなげるか」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light purple-blue background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles.
Purple/indigo for equality and naming systems, teal for inclusion,
amber for formalism cautions, gray for neutral information.
Inclusive, calm, nonpartisan, never stereotypical.
All Japanese text must be accurate, large, and readable.

Avoid:
No gender stereotypes, no pink-for-girls or blue-for-boys coding,
no binary-only human silhouettes, no ideological symbols,
no real schools or uniforms, no real SNS logos, no manga characters,
no random extra text, no watermark.
```

---

## 6. 本人意思・柔軟運用 — 嫌な呼び方だけ止めればよいか

**ファイル名:** `school-nickname-ban-infographic-wide-choice.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
学校でのあだ名禁止 の個別論点「本人意思・柔軟運用」

Main title (top-left area, large bold Japanese text):
「本人意思・柔軟運用」
「嫌な呼び方だけ、止めればよいか」

Core message:
4件すべてが条件付き・個別対応。
全面自由でも一律禁止でもなく、本人が望む愛称は認め、
嫌な呼び方や悪意あるあだ名は止めるという中間案。
ただし、嫌だと言いにくい子をどう守るかが運用上の課題になる。
取得したSNS投稿サンプルの整理であり、世論調査ではない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
3つの呼び方カードを縦に配置:
  緑「本人が望む愛称」チェックマーク
  青「名字＋さん」選択可能マーク
  赤「嫌な呼び方」停止マーク
上部に「本人が選べる？」。

CENTER ZONE:
シンプルな3ステップフロー:
「本人に確認」→「希望を共有」→「嫌なら止める」。
その下に小さな注意カード:
「嫌だと言いにくい場合は？」
右側に教師・保護者・子どもを人物ではなく
3つの抽象アイコンで結ぶ「相談ルート」。
下部の単色バー:
「条件付き・個別対応 4」。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「本人同意」「呼ばれる側の意思を確認」
  「選択肢」「愛称・名前・さん付けから選べる」
  「撤回可能」「途中で嫌になったら変えられる」
  「支援役」「言いにくい時は大人が介入」

Bottom conclusion band (full width):
「自由か禁止かではなく、本人が安心して選び直せる仕組みへ」

Style:
Bright, clean Japanese civic-tech infographic.
White and very light green-blue background.
Vivid navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, simple step-flow accents.
Green for consent and accepted names, blue for available choices,
red only for stop/unwanted names, amber for support-needed cautions.
Warm, practical, child-centered but not childish.
All Japanese text must be accurate, large, and readable.

Avoid:
No identifiable children, no crying faces, no teacher authority imagery,
no checkbox implying forced consent, no real school logos or uniforms,
no real SNS logos, no manga characters, no random extra text, no watermark.
```

---

## 共通の生成後チェック

- 1916×821pxの横長比率になっている
- 日本語タイトルとカード文言が正確に読める
- 右側4カードが2×2で整理され、スマホ幅でも要点が判別できる
- 件数とスタンス内訳が上記のHermes分類結果と一致する
- 「SNS投稿サンプルであり世論調査ではない」という前提と矛盾しない
- 支持・反対のどちらかを悪者として描いていない
- 人物ドラマではなく、アイコン・フロー・比較図を中心にしている
- 実在学校、制服、校章、自治体、SNSのロゴが入っていない
- ランダムな文字、読めない小文字、ウォーターマークがない
