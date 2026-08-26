# 辺野古高校生死亡事故 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `creative/manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: `docs/images/topics/ai-copyright/ai-copyright-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影、整理された左→中央→右の情報フローを使う。

データ基準: X投稿403件から重複を除いた363件をHermesで再分類し、記事利用可と判定した265件。画像内で件数を示す場合は、必ず「公開対象SNSサンプル265件中」と併記し、世論調査や支持率に見せない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**

AIテーマのwide画像と同一サイズを指定すること。

## 保存先・変換コマンド

```text
docs/images/topics/henoko-student-accident/
├── henoko-student-accident-infographic-wide-churitsu.webp （論点1: 政治的中立性）
├── henoko-student-accident-infographic-wide-anzen.webp    （論点2: 安全管理・事故原因）
├── henoko-student-accident-infographic-wide-tsuito.webp   （論点3: 追悼・被害者の尊厳）
├── henoko-student-accident-infographic-wide-heiwa.webp    （論点4: 平和教育の萎縮）
├── henoko-student-accident-infographic-wide-seiji.webp    （論点5: 政治利用・基地問題）
└── henoko-student-accident-infographic-wide-houdou.webp   （論点6: 報道・行政対応）
```

```bash
cwebp -q 82 input.png -o docs/images/topics/henoko-student-accident/henoko-student-accident-infographic-wide-XXX.webp
```

## 全画像共通の安全指定

- 事故・転覆・溺水・負傷・遺体・救助場面を描かない。
- 亡くなった生徒、遺族、船長、教員、活動家、行政担当者など、実在人物を描かない。
- 政党ロゴ、団体ロゴ、政府・自治体の公式エンブレム、学校章、実在SNSロゴを描かない。
- 特定の人物・団体を犯人、加害者、違法行為者と断定する表現を入れない。
- 反基地側・文科省側のどちらかを善悪で決めつけず、論点の分岐を可視化する。
- 「53件」などの件数はSNS投稿サンプル内の分類件数であり、世論比率ではない。

---

## 1. 政治的中立性 — 学びと政治活動の境界はどこか

**ファイル名:** `henoko-student-accident-infographic-wide-churitsu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「政治的中立性」

Main title (top-left area, large bold Japanese text):
「政治的中立性」
「現地学習と政治活動の境界はどこか」

Core message:
公開対象SNSサンプル265件中53件。修学旅行中の活動が、社会問題を学ぶ教育の範囲だったのか、特定の政治活動への参加に近づいていたのかが争点。文科省判断を支持する23件、反発する15件、切り分け・中立15件に分かれ、6論点で最も明示的な賛否が表れた。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 明るい教室アイコンから「現地学習」と書かれたフィールドワーク用ノートへ向かう矢印。人物の顔は描かず、生徒を示す抽象的な3つのシルエットと、地図・ノート・吹き出しの教育アイコンを使う。「社会問題を学ぶ」の青ラベル。
CENTER ZONE: 大きな境界線と天秤。「教育としての学び」（青・開いた本）と「政治活動への参加」（橙・プラカード形だが団体名なし）を左右に置く。中央に「どこで線を引く？」の大きな問い。下に「文科省判断」の文書アイコンを置くが、官印や政府エンブレムは使わない。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「判断を支持 23件」「学校教育の中立性を守るべき」
  「判断に反発 15件」「教育への介入や萎縮を警戒」
  「切り分け 7件」「事故検証と教育評価は別の問い」
  「中立・情報 8件」「認定内容や資料を共有」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「問われているのは、社会問題を学ぶことと政治活動へ参加することの境界」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Blue for education, amber for boundary caution, cyan for information, red-orange only for concerns. Friendly but professional, neutral and nonpartisan.

Avoid:
No real students or teachers, no school logo, no politicians, no party or activist logos, no government emblem, no real SNS logo, no protest crowd, no accident scene, no boats in distress, no random extra text, no watermark.
```

---

## 2. 安全管理・事故原因 — 教育内容より先に何を検証するか

**ファイル名:** `henoko-student-accident-infographic-wide-anzen.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「安全管理・事故原因」

Main title (top-left area, large bold Japanese text):
「安全管理・事故原因」
「教育内容とは分けて、何を検証するか」

Core message:
公開対象SNSサンプル265件中75件で最多。乗船判断、事前確認、運航体制、引率責任、事故原因、再発防止を問う声が中心。52件は文科省判断への賛否を示さず「事故検証と教育評価を切り分ける」立場で、23件は中立的な情報共有だった。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「事前確認」のチェックリスト。救命胴衣、天候確認、運航資格、引率計画を示す4つの安全アイコン。海や船は穏やかな記号として小さく描き、事故や転覆は描かない。
CENTER ZONE: 大きな虫眼鏡が「安全管理プロセス」を確認する図。横方向に「計画 → 実施 → 記録 → 検証 → 再発防止」の5ステップ。教育内容を示す本のアイコンは別レーンに置き、「別々に検証」の分岐線を引く。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「切り分け 52件」「文科省判断に触れず安全面を重視」
  「中立・情報 23件」「事故経緯や安全対策を共有」
  「確認項目」「乗船判断・運航体制・引率責任」
  「到達点」「原因究明と同じ事故を防ぐ仕組み」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「事故の検証と教育内容の評価を混ぜず、再発防止につなげる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Navy and vivid blue headline typography. Green and teal for safety and prevention, amber for unresolved checks. Rounded cards, soft shadows, clear process arrows, subtle checklist graphics.

Avoid:
No capsized boat, no drowning, no rescue scene, no injured person, no victim depiction, no named organization, no blame labels, no politicians, no party logos, no government emblems, no real SNS logos, no dark disaster imagery, no watermark.
```

---

## 3. 追悼・被害者の尊厳 — 政治的対立より先に置くもの

**ファイル名:** `henoko-student-accident-infographic-wide-tsuito.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「追悼・被害者の尊厳」

Main title (top-left area, large bold Japanese text):
「追悼・被害者の尊厳」
「政治的対立より先に置くものは何か」

Core message:
公開対象SNSサンプル265件中25件。亡くなった生徒への追悼、遺族への配慮、謝罪や説明のあり方を重く見る論点。22件は文科省判断と切り分け、2件は中立的な情報共有、1件のみ文科省判断支持を伴っていた。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 白い花、静かな光、空の椅子、手を合わせる抽象アイコンを控えめに配置。実在人物や遺影は描かない。「追悼」「遺族への配慮」の2つの柔らかなラベル。
CENTER ZONE: 大きな保護円の中に「尊厳」の文字。周囲から入る政治・報道・責任追及の矢印を、円の手前で一度止める構図。「まず立ち止まる」の短いキャプション。感情を煽らず、静かな余白を多く取る。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「切り分け 22件」「追悼と政治評価を混ぜない」
  「中立・情報 2件」「追悼行事や経過を共有」
  「配慮」「遺族の意思とプライバシーを尊重」
  「説明」「追悼と原因究明を両立する」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「立場が違っても、被害者の尊厳と遺族への配慮を議論の土台にする」

Style:
Bright, gentle Japanese civic-tech infographic. White and pale blue background with soft lavender and teal accents. Navy headline typography. Rounded cards, generous whitespace, subtle light particles, calm and respectful atmosphere. Professional, neutral, never sentimental or dramatic.

Avoid:
No portrait, no photograph frame, no coffin, no accident scene, no crying family, no named victim, no political symbols, no protest signs, no politicians, no party logos, no government emblems, no real SNS logos, no dark memorial imagery, no watermark.
```

---

## 4. 平和教育の萎縮 — 認定は学びを狭めるのか

**ファイル名:** `henoko-student-accident-infographic-wide-heiwa.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「平和教育の萎縮」

Main title (top-left area, large bold Japanese text):
「平和教育の萎縮」
「認定によって、扱える学びは狭まるのか」

Core message:
公開対象SNSサンプル265件中21件。教育基本法違反の認定が、沖縄戦・基地問題・平和学習を扱う教育現場の萎縮につながるのかが争点。反発1件、支持4件、切り分け10件、中立・情報共有6件で、懸念そのものへの評価も分かれた。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 開いた教科書に「沖縄戦」「基地問題」「平和学習」の3つの抽象ページタブ。文字を消そうとする表現ではなく、ページの上に小さな「扱いを控える？」の灰色クエスチョンカードを置く。
CENTER ZONE: 教室の黒板アイコンと法令文書アイコンを向かい合わせる。「教育の自由」と「政治的中立性」の二方向矢印。中央に「両立できるか？」の問い。人物は描かず、教育空間を示す机・本・吹き出しのみ。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「判断に反発 1件」「教育への圧力や萎縮を懸念」
  「判断を支持 4件」「中立性と平和教育は両立可能」
  「切り分け 10件」「事故・教育・運動を別々に考える」
  「中立・情報 6件」「抗議声明や認定内容を共有」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「平和を学ぶ機会を守りながら、教育の中立性をどう担保するか」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Navy and vivid blue headline typography. Teal for education, purple for freedom of learning, amber for institutional caution. Rounded cards, soft shadows, subtle book and dialogue graphics.

Avoid:
No war scene, no military weapons, no real base photograph, no protest crowd, no politicians, no party logos, no government emblems, no real SNS logos, no student faces, no dark or fearful classroom, no watermark.
```

---

## 5. 政治利用・基地問題 — 現地学習と運動参加をどう分けるか

**ファイル名:** `henoko-student-accident-infographic-wide-seiji.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「政治利用・基地問題」

Main title (top-left area, large bold Japanese text):
「政治利用・基地問題」
「現地学習と運動参加をどう分けるか」

Core message:
公開対象SNSサンプル265件中21件。生徒が地域の現実を学ぶフィールドワークだったのか、特定の基地反対運動へ巻き込まれたのかが争点。18件は文科省判断と切り分けて政治利用・運動側を論じ、1件は文科省判断支持、2件は中立的な情報共有だった。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 地図、ノート、案内ピンの「現地学習」セット。右側に抽象的な市民運動の吹き出しと無地のプラカードを置く。実在の基地、旗、団体名、スローガンは描かない。
CENTER ZONE: 「見る・聞く・考える」の教育フローが、「参加する」の手前で分岐する図。「学習」と「運動参加」の境界を太い点線で示し、中央に「本人の選択と学校の責任」のカード。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「切り分け 18件」「運動側への批判と文科省評価は別」
  「判断支持 1件」「政治活動への接近を問題視」
  「中立・情報 2件」「団体関係や経緯を確認」
  「確認点」「目的・説明・同意・参加方法」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「地域の現実を学ぶことと、特定の運動に参加することの境界を確認する」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Navy headline typography. Cyan for field learning, amber and purple for participation and choice. Rounded cards, soft shadows, map-pin and decision-flow accents. Neutral, nonpartisan.

Avoid:
No real military base, no aircraft or weapons, no party or activist logos, no real slogans, no national flags, no protest crowd, no politicians, no student likeness, no accident scene, no hostile confrontation, no watermark.
```

---

## 6. 報道・行政対応 — 事実と説明は十分だったか

**ファイル名:** `henoko-student-accident-infographic-wide-houdou.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
辺野古高校生死亡事故 の個別論点「報道・行政対応」

Main title (top-left area, large bold Japanese text):
「報道・行政対応」
「事実と説明は十分だったか」

Core message:
公開対象SNSサンプル265件中70件で2番目に多い論点。報道量や見出し、行政の説明、調査・会見・責任者の対応を問う投稿が集まった。41件は中立的な情報共有、23件は文科省判断と切り分けた説明責任の追及、支持5件、反発1件だった。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 抽象的なニュースカード、記者会見マイク、行政文書、調査チェックリストの4アイコン。「報道」「説明」「調査」「公開」のラベル。実在メディア名やロゴは使わない。
CENTER ZONE: 「出来事 → 一次資料 → 行政説明 → 報道 → 読者」の5段階情報フロー。各段階に小さな確認マーク。「どこで情報が欠けた？」の大きな虫眼鏡。文科省判断はフロー内の行政文書の1つとして中立的に示す。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「中立・情報 41件」「会見・記事・資料を共有」
  「切り分け 23件」「事故対応や説明責任を追及」
  「判断支持 5件」「報道批判と認定支持を併記」
  「判断反発 1件」「行政介入の妥当性に疑問」

Small data note:
「公開対象SNSサンプル265件中／世論調査ではありません」

Bottom conclusion band (full width):
「見出しだけで判断せず、一次資料・説明・調査経過をつなげて読む」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Navy and vivid blue headline typography. Cyan for information flow, teal for verified material, amber for missing explanations, gray for neutral sharing. Rounded cards, soft shadows, subtle document and chart accents.

Avoid:
No real media logos, no broadcaster names, no politicians, no party logos, no government emblems, no named officials, no real press photograph, no accident scene, no sensational breaking-news styling, no red alarm graphics, no watermark.
```

---

## 生成後の確認

- 6枚すべてが `1916×821px` で、AIテーマのwide版と同じ構図密度になっている。
- 大見出し、短い問い、中央図解、4カード、下部結論帯が揃っている。
- 「公開対象SNSサンプル265件中／世論調査ではありません」が読める。
- 件数がHermes再分類の公開対象データと一致している。
- 事故や被害者を直接描写していない。
- 政治家、政党、活動団体、学校、行政の公式ロゴに見えるものがない。
- 日本語文字が崩れていない。
- WebP変換後もスマホ幅で大見出しと問いが判読できる。
