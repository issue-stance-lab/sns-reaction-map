# 自転車の青切符導入 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 副首都ページの `docs/images/fukushuto-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
副首都 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/
├── bike-blue-ticket-infographic-wide-torishimari.webp  （論点1: 取締り強化賛成）
├── bike-blue-ticket-infographic-wide-infra.webp        （論点2: インフラ整備優先）
├── bike-blue-ticket-infographic-wide-sharido.webp      （論点3: 車道走行への不安）
├── bike-blue-ticket-infographic-wide-menkyo.webp       （論点4: 免許制要求）
└── bike-blue-ticket-infographic-wide-ambiguity.webp    （論点5: ルール曖昧・不信）
```

```bash
cwebp -q 82 input.png -o docs/images/bike-blue-ticket-infographic-wide-XXX.webp
```

---

## 1. 取締り強化賛成 — 危険自転車への「青切符」は当然か

**ファイル名:** `bike-blue-ticket-infographic-wide-torishimari.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
自転車の青切符導入 の個別論点「取締り強化賛成」

Main title (top-left area, large bold Japanese text):
「取締り強化賛成」
「危険な自転車に「青切符」は当然か」

Core message:
最多37件、全員が取締り強化を支持。信号無視・ながらスマホ・歩道の無謀走行など、自転車の危険行為が社会問題化している。「事故が起きてからでは遅い」「歩行者が毎日怖い思いをしている」という実体験の訴えが主軸で、青切符（反則金制度）による抑止力に期待する声が全体の100%を占める唯一の論点。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 危険な自転車の行動パターンを3つのアイコンで列挙。①スマホを持つ自転車シルエット＋「ながらスマホ」赤ラベル。②歩道を疾走する自転車シルエット＋「歩道の無謀走行」赤ラベル。③「STOP」標識を無視する自転車＋「信号無視」赤ラベル。
CENTER ZONE: 大きな「青切符」文書アイコン（反則金の金額例「5,000〜12,000円」を一行表示）。上から「警告なし → 即・反則金」の赤い因果矢印。「SNS上では100%が取締り支持」の赤いバー（細いが幅いっぱい）を中央下部に配置。「抑止力」のキャプション。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「歩行者の恐怖」「毎日危ない思いをしている」
  「事後では遅い」「事故が起きてからでは意味がない」
  「即効性」「反則金が行動を変える唯一の手段」
  「悪質違反」「信号無視・逆走・スマホ運転が標的」

Bottom conclusion band (full width):
「SNSの声は一致——危険行為への抑止力として青切符を歓迎」

Style:
Bright, clean Japanese civic-tech infographic. White and very light teal background (#f0fdf4). Vivid navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Red and teal are the main accent colors. Red dominates for the dangerous behavior side. Teal for the civic safety angle.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no watermark.
```

---

## 2. インフラ整備優先 — 自転車レーンなしに取り締まれるか

**ファイル名:** `bike-blue-ticket-infographic-wide-infra.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
自転車の青切符導入 の個別論点「インフラ整備優先」

Main title (top-left area, large bold Japanese text):
「インフラ整備優先」
「自転車レーンがないのに取り締まれるのか」

Core message:
33件中30件（91%）がインフラ優先の立場。「安全に走れる専用レーンがない状態で車道走行を義務付けた上で罰則を科すのは理不尽だ」というのが共通の訴え。取り締まり自体には反対していない場合も多く、「整備が先、罰則は後」という順番論が中心。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「現実の道路」の断面図イラスト（簡略化）。車線が2本あり、自転車専用レーンがゼロ。「自転車レーン：なし」の赤いバッジ。路駐車アイコンが道路端をふさいでいる。「ここを走れと言われても…」の吹き出し。
CENTER ZONE: 天秤アイコン。左皿に「罰則・取締り」（赤・切符アイコン）、右皿に「自転車レーン整備」（青・道路アイコン）。右皿のほうがわずかに重い。「どちらを先にすべきか」のキャプション。中央下部に「反対91%」の青バー（幅いっぱい）。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「レーンなし罰則」「専用レーンがない状態での取締りは理不尽」
  「整備が先」「まず走れる環境を作ることが先決」
  「地方の実情」「田舎では歩道しかない道が大半」
  「本末転倒」「危険な環境を作り出したのはインフラ側」

Bottom conclusion band (full width):
「インフラが追いつかない道路で、罰則だけが先走る——それが問題の核心」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid navy headline typography. Blue dominates (91% anti-enforcement stance). Rounded cards, soft shadows, small dots, sparkles. Blue for the infrastructure side, orange/amber for the "problem" alert accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 3. 車道走行への不安 — 「車道を走れ」は安全なのか

**ファイル名:** `bike-blue-ticket-infographic-wide-sharido.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
自転車の青切符導入 の個別論点「車道走行への不安」

Main title (top-left area, large bold Japanese text):
「車道走行への不安」
「「車道を走れ」というルールは本当に安全か」

Core message:
14件中12件（86%）が車道走行への不安を訴える。青切符導入と合わせて「自転車は原則車道」というルールが強調されることへの恐怖が中心。「路駐の車があって走れない」「子どもや高齢者は車道を走れない」という生活実感の訴え。一方で「歩道を飛ばす自転車のほうが歩行者には危険」という視点も存在する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「車道の現実」を示す簡略断面図。大型トラックのアイコンが自転車の横すれすれを走る構図。路駐の乗用車アイコンが自転車の行く手をふさぐ。「ここを走れ？」の赤い疑問符。子ども・高齢者シルエットに「参加困難」ラベル。
CENTER ZONE: 「原則車道」という標識アイコンの中央配置。左下に「危険！車道」の赤カード、右下に「歩道も危険」の橙カード。「どちらが安全か」の問いを吹き出しで。中央下部に「車道不安派86%」の青バー。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「路駐問題」「路駐車があると車道から弾き出される」
  「子ども・高齢者」「弱者には車道走行は無理なルール」
  「地方格差」「片側1車線の幹線道路が怖い」
  「歩道も危険」「飛ばす自転車が歩行者にとって脅威」

Bottom conclusion band (full width):
「車道の危険と歩道の危険——どちらを優先するかで立場が分かれる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light amber background (#fffbeb). Vivid navy headline typography. Orange and red accents for the danger zones, blue for the "pedestrian perspective" side. Rounded cards, soft shadows, small dots, sparkles.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no crash scenes, no injured people, no clutter, no watermark.
```

---

## 4. 免許制要求 — 罰則より先に教育が必要か

**ファイル名:** `bike-blue-ticket-infographic-wide-menkyo.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
自転車の青切符導入 の個別論点「免許制要求」

Main title (top-left area, large bold Japanese text):
「免許制要求」
「青切符の前に、ルールを教えるべきでは？」

Core message:
16件。取締り支持12%・中立44%・反対44%と最も拮抗した論点。「罰則より先にルールを学ぶ機会がなければ不公平」という訴えが中心。「原付のように免許か事前講習を義務付けるべき」という提案型の意見と、「免許制は自転車利用の障壁になる」という現実論が対立している。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「免許取得フロー」の簡略図。「学科試験」→「技能講習」→「免許証」の3ステップ矢印。下部に「現在の自転車：ゼロ」の赤いバッジ。「ルールを知らずに走っている？」の吹き出し。
CENTER ZONE: 免許証アイコン（個人情報なし・抽象的なデザイン）vs 青切符アイコンの対比。「どちらが先か」の天秤。中央下部に3色の横バー:「取締り支持12%（赤）/ 中立44%（グレー）/ 教育優先44%（青）」と等分割。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「知識なき罰則」「ルールを知らないまま取り締まるのは理不尽」
  「原付モデル」「原付のように事前講習・免許制を導入すべき」
  「利便性の壁」「免許制は自転車通勤・通学を困難にする」
  「教育優先」「まず学校・職場での交通教育を義務化すべき」

Bottom conclusion band (full width):
「賛否がほぼ均等——「教育か罰則か」は答えが出ていない論点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light purple background (#faf5ff). Vivid navy headline typography. Purple/indigo for the education/knowledge side, amber/gold for the "license system" proposal, gray for the balanced neutral block. Rounded cards, soft shadows, small dots, sparkles.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 5. ルール曖昧・不信 — 違反基準が複雑すぎる

**ファイル名:** `bike-blue-ticket-infographic-wide-ambiguity.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
自転車の青切符導入 の個別論点「ルール曖昧・不信」

Main title (top-left area, large bold Japanese text):
「ルール曖昧・不信」
「113種類の違反基準——誰が全部わかるのか」

Core message:
19件中13件（68%）がルールへの不信・反対。「何が違反かわからない」「警察が恣意的に取り締まるのではないか」という不信感が中心。「113種類の違反対象は多すぎて周知できない」「正直者だけが損をする運用になる」という批判が主軸。基準の整理と周知なしでの取り締まりには反対という立場。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「113種類の違反リスト」を模した小さいテキスト箇条書きアイコン（読めなくてOK、量の多さを見せる）。「あなたは何件知っていますか？」の問いかけ吹き出し。「一般の認知：ほぼ0」の赤いバッジ。
CENTER ZONE: 大きな「？」アイコンを中央に。左に「警察の裁量」（赤・警告アイコン）、右に「基準の整理」（青・チェックリストアイコン）が向き合う構図。中央下部に「反対68%・中立32%」の青＋グレーの2色バー（赤はほぼゼロ）。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「基準が多すぎ」「113種類は覚えられない、周知不可能」
  「恣意的運用」「警察の判断次第で誰でも捕まる可能性」
  「正直者損」「知らなかった人と知っている人で不公平に」
  「先に周知を」「取締り前に広報・教育が必要」

Bottom conclusion band (full width):
「ルールが複雑すぎて誰も知らない——「知らなかった」は免罪符にならないのに」

Style:
Bright, clean Japanese civic-tech infographic. White and very light gray background (#f8fafc). Vivid navy headline typography. Gray and deep purple for the "ambiguity" theme. Red accent for the "arbitrary enforcement" risk. Blue for the "let's fix the rules" side. Rounded cards, soft shadows, small dots, sparkles.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```
