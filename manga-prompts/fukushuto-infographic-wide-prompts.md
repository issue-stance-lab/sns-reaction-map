# 副首都法案 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 皇室典範ページの `docs/images/koshitsu-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
皇室典範 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/
├── fukushuto-infographic-wide-teigi.webp
├── fukushuto-infographic-wide-kouhochi.webp
├── fukushuto-infographic-wide-tokoso.webp
├── fukushuto-infographic-wide-bousai.webp
├── fukushuto-infographic-wide-hiyou.webp
└── fukushuto-infographic-wide-yusen.webp
```

```bash
cwebp -q 82 input.png -o docs/images/fukushuto-infographic-wide-XXX.webp
```

---

## 1. 定義・中身 — 「生煮え」のまま通していいのか

**ファイル名:** `fukushuto-infographic-wide-teigi.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「定義・中身」

Main title (top-left area, large bold Japanese text):
「定義・中身」
「副首都、何をする場所か、書いてある？」

Core message:
副首都法案は「副首都を政令で指定できる枠組み」を先行立法する構造だが、何の機能を移すのか、誰が統治するのか、費用はいくらか——定義も体制も法案に書かれていない。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 青い法案文書アイコン。文書の中に「定義：（空欄）」「統治体制：（空欄）」「費用：（空欄）」の3行を縦に表示。
CENTER ZONE: 大きな「先行立法」矢印と、骨格だけの建物アイコン（設計なしに建設中イメージ）。「中身はこれから」の吹き出し。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「定義がない」「何が副首都になるのか？」
  「統治体制」「誰が決め、誰が動かす？」
  「先に枠組み」「中身は後から」
  「生煮え？」「批判と擁護が拮抗」

Bottom conclusion band (full width):
「定義・体制・費用が決まる前に、枠組みだけ先行した法案」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with orange accent for the empty blanks.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark disaster scenes, no clutter, no random extra text, no watermark.
```

---

## 2. 候補地 — 大阪？福岡？新潟？

**ファイル名:** `fukushuto-infographic-wide-kouhochi.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「候補地」

Main title (top-left area, large bold Japanese text):
「候補地」
「副首都は、どこに置く？」

Core message:
「大阪を副首都に」が前提だが、南海トラフ巨大地震の被災想定域にバックアップ拠点を置くことへの疑問が大きい。SNS上では新潟・福岡・北海道など日本海側を推す対案が多く、「どこがいい？」と地図を広げる建設的な議論が最多。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「同時被災リスク」の赤い警告アイコンと「東京と同じ被災想定域？」の問いカード。
CENTER ZONE: 抽象化した日本列島のシルエット地図（ラベル最小限）。太平洋岸に「南海トラフ想定域」を赤い波線ゾーンで表示。大阪位置に「？」アイコン、日本海側に青い星マーク複数。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「大阪は？」「南海トラフの想定域にある」
  「同時被災」「東京と共倒れになる？」
  「日本海側」「新潟・北海道・福岡など」
  「分散の原則」「距離と安全性が鍵」

Bottom conclusion band (full width):
「バックアップの意味をなすか、候補地の地理条件が焦点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with red for risk zones and purple for alternative locations.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark disaster scenes, no actual city name labels on the map, no clutter, no watermark.
```

---

## 3. 都構想・維新 — 「大阪ありき」への不信

**ファイル名:** `fukushuto-infographic-wide-tokoso.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「都構想・維新」

Main title (top-left area, large bold Japanese text):
「都構想・維新」
「副首都法案は大阪都構想の隠れ蓑？」

Core message:
副首都法案の附則に「都」への名称変更規定があることから、「住民投票で2度否決された大阪都構想を国政経由で実現しようとしている」という疑念が広がる。一方で「提唱し続けてきた政党が大阪を軸に進めるのは当然」という反論もある。感情温度が最も高い論点。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 投票箱アイコン2つに「×」マーク（2度否決）と「住民投票」ラベル。政党名・ロゴは描かない。
CENTER ZONE: 「住民投票×2否決」→「国会」→「法案」→「副首都指定」のフロー矢印。法案文書カードに「附則：都への改称」を貼り付け、大きな「？」吹き出しを重ねる。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「住民投票」「2度否決された都構想」
  「附則の改称」「都への名称変更規定」
  「政治不信」「利益誘導との批判」
  「推進論」「提唱者が進めるのは当然」

Bottom conclusion band (full width):
「維新への評価が、そのまま賛否を分ける最も感情的な論点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with amber/orange for the distrust/suspicion element.

Avoid:
No politicians, no party logos (including any political party), no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 4. 防災・災害 — 同じ「防災」で正反対の結論

**ファイル名:** `fukushuto-infographic-wide-bousai.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「防災・災害」

Main title (top-left area, large bold Japanese text):
「防災・災害」
「同じ『防災』から、なぜ正反対の結論が出る？」

Core message:
賛成側は「首都直下地震に備えた機能分散が急務」、反対側は「南海トラフは首都直下地震と連動する。大阪では共倒れだ」——同じ防災を根拠に正反対の結論が出る。賛成・反対・中立の三すくみになっている唯一の論点。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「機能分散」側。都市アイコンを複数に分散させる矢印図（green accent）と「首都直下 → 分散で対応」のラベル。
CENTER ZONE: 大きな天秤アイコン。左皿に「機能分散：一極集中リスクを減らす」（green）、右皿に「共倒れリスク：南海トラフ連動」（red）。台座に「防災」の共通ラベル。「同じ根拠から逆の結論」のキャプション。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「機能分散」「東京一極集中のリスク」
  「南海トラフ」「大阪も太平洋岸の被災想定域」
  「連動リスク」「2大災害が同時に起きたら」
  「三すくみ」「賛否が正面衝突する唯一の論点」

Bottom conclusion band (full width):
「賛成も反対も『防災』を根拠にする——このテーマ唯一の激戦区」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with green for pro-decentralization and red for co-disaster risk.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark disaster scenes (no collapsed buildings, no victims), no clutter, no watermark.
```

---

## 5. 費用・財源 — 「4兆円とも7.5兆円とも」

**ファイル名:** `fukushuto-infographic-wide-hiyou.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「費用・財源」

Main title (top-left area, large bold Japanese text):
「費用・財源」
「総額も財源も、まだ分からない？」

Core message:
副首都整備の費用は民間試算で4兆円〜7.5兆円超の幅があり、政府は国会答弁で「現時点では分からない」と回答。物価高で家計が苦しい中、費用・財源が不明なまま巨大事業を走らせることへの不信が論点の中心。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 大きな「？兆円」テキスト（濃紺・極太）。下に「4兆円 〜 7.5兆円超」のレンジバー（グラデーション）。コインや電卓・グラフのミニアイコン。
CENTER ZONE: 抽象的な書類・法案アイコン（議事堂は描かない）。「法案可決」→「副首都指定」の矢印フローに「費用？」の大きな疑問符を重ねる。「答弁：現時点では分からない」カード。物価上昇を示す小さな上向き矢印グラフ。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「試算なし」「政府：現時点では不明」
  「4〜7.5兆」「民間推計の幅が大きい」
  「財源は？」「国費か、地方か、増税か」
  「大型事業」「方針先行は普通との反論」

Bottom conclusion band (full width):
「物価高の今、費用・財源不明のまま走らせていいのか」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with amber/orange for the "cost unknown / caution" accent.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 6. 優先順位 — 「物価対策どこ行った」

**ファイル名:** `fukushuto-infographic-wide-yusen.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
副首都法案 の個別論点「優先順位」

Main title (top-left area, large bold Japanese text):
「優先順位」
「なぜ今、これを最優先にするのか？」

Core message:
「消費税減税は先送りなのに、副首都法案のために会期を延長するのか」——法案の中身より「なぜ今これなのか」を問う怒りが中心。件数は最少だが感情温度は2番目に高い。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「今の優先課題（生活実感）」として食費・光熱費・物価の生活費アイコン（食材・電球・カートのミニアイコン）リスト。各アイコンに赤い上昇矢印。「後回し」スタンプラベルを重ねる。
CENTER ZONE: 横に並んだ2枚の優先度比較カード。左「物価対策」に「↓ 先送り」赤ラベル、右「副首都法案」に「↑ 会期延長」青ラベル。両カードの上に「なぜ今？」の問いと大きな「？」。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「会期延長」「副首都法案を通すために」
  「物価対策」「先送りされたとの声が多い」
  「国民感情」「日常と政治の乖離」
  「長期視点」「国家設計は別の話との反論」

Bottom conclusion band (full width):
「内容より『なぜ今か』——生活実感からの怒りが最も熱い」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with red for "delayed" items and amber for the "why now" tension.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```
