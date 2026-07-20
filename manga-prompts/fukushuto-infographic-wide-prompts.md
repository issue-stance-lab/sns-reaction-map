# 副首都法案 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` の **6. 冒頭説明画像テンプレ** を使用する。

基準テイスト: 皇室典範ページの `docs/images/koshitsu-infographic-wide-*.webp` と同じ、明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影、ドット・スパークル・グラフ風アクセントを使う。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 保存先

生成後 WebP に変換、各ファイルは横幅 1800px 目安、150KB以下を目標にする。

```
docs/images/
├── fukushuto-infographic-wide-teigi.webp     ← 論点①定義・中身
├── fukushuto-infographic-wide-kouhochi.webp  ← 論点②候補地
├── fukushuto-infographic-wide-tokoso.webp    ← 論点③都構想・維新
├── fukushuto-infographic-wide-bousai.webp    ← 論点④防災・災害
├── fukushuto-infographic-wide-hiyou.webp     ← 論点⑤費用・財源
└── fukushuto-infographic-wide-yusen.webp     ← 論点⑥優先順位
```

WebP変換コマンド（生成 PNG から）:
```bash
cwebp -q 82 -resize 1800 0 input.png -o docs/images/fukushuto-infographic-wide-XXX.webp
```

---

## 1. 定義・中身 — 「生煮え」のまま通していいのか

**ファイル名:** `fukushuto-infographic-wide-teigi.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「定義・中身」

Main title:
「定義・中身」
「副首都、何をする場所か、書いてある？」

Core message:
副首都法案は「副首都を政令で指定できる枠組み」を先行立法する構造だが、何の機能を移すのか、誰が統治するのか、費用はいくらか——定義も体制も法案に書かれていない。「家の設計前に契約だけ先に結ぶ」という批判と、「大きな方針から決めるのが大型事業の常識」という擁護が対立する。

Visual structure:
Left side: 青い法案文書アイコン（書類）と「副首都指定」の枠。その中に「定義：（空欄）」「統治体制：（空欄）」「費用：（空欄）」の3行を縦に配置する。
Center: 大きな矢印「先行立法」と、工事中フラッグや建物の骨格だけのアイコン（完成前に看板だけ立っているイメージ）。骨格ビルのそばに「中身はこれから」の吹き出し。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「定義がない」 「何が副首都になるのか？」
2. 「統治体制」 「誰が決め、誰が動かす？」
3. 「先に枠組み」 「中身は後から」
4. 「生煮え？」 「批判と擁護が拮抗」

Conclusion band:
「定義・体制・費用が決まる前に、枠組みだけ先行した法案」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with orange as the "caution/unclear" accent for the empty blanks.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no dark disaster scenes,
no clutter, no random extra text, no watermark.
```

---

## 2. 候補地 — 大阪？福岡？新潟？

**ファイル名:** `fukushuto-infographic-wide-kouhochi.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「候補地」

Main title:
「候補地」
「副首都は、どこに置く？」

Core message:
「大阪を副首都に」が前提になっているが、南海トラフ巨大地震の被災想定域にバックアップ拠点を置くことへの疑問は大きい。SNS上では新潟・福岡・北海道など日本海側・遠隔地を推す対案が多く、この論点では「どこがいい？」と地図を広げた建設的な議論が最多。

Visual structure:
Center: 抽象化した日本列島の輪郭地図（シルエット、詳細な地名ラベルは最小限）。右下の太平洋岸エリアに「南海トラフ想定域」を赤い波線または赤いゾーンで示す。大阪の位置に大きな疑問符「？」アイコンを置く。日本海側（新潟・北海道・福岡周辺）に「代替候補」を示す青い星アイコンを散らす。
Left side: 「同時被災リスク」を示す赤い警告アイコンと、「東京と同じ被災想定域？」の問い。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「大阪は？」 「南海トラフの想定域にある」
2. 「同時被災」 「東京と共倒れになる？」
3. 「日本海側」 「新潟・北海道・福岡など」
4. 「分散の原則」 「距離と安全性が鍵」

Conclusion band:
「バックアップの意味をなすか、候補地の地理条件が焦点」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with red for risk zones and purple for alternative locations.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no dark disaster scenes,
no clutter, no random extra text, no watermark.
No actual city name labels on the map — use only colored icons/zones.
```

---

## 3. 都構想・維新 — 「大阪ありき」への不信

**ファイル名:** `fukushuto-infographic-wide-tokoso.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「都構想・維新」

Main title:
「都構想・維新」
「副首都法案は大阪都構想の隠れ蓑？」

Core message:
副首都法案の附則に「都」への名称変更規定があることから、SNS上では「住民投票で2度否決された大阪都構想を、国政経由で実現しようとしている」という疑念が強い。一方で「大阪から提唱し続けてきた政党が大阪を軸に進めるのは当然」という真っ向からの反論もある。このテーマで感情温度が最も高い論点。

Visual structure:
Left side: 投票箱アイコン2つに「×」（2度否決を表現）と「住民投票」のラベル。政党名・ロゴは描かない。
Center: 「国会→法案→副首都指定」のフロー矢印。法案文書の下部に「附則：都への改称」が書かれたカードを貼り付け、その上に大きな疑問符の吹き出し。左側の否決アイコンと右側のフローを点線で結んで「関係？」を示す。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「住民投票」 「2度否決された都構想」
2. 「附則の改称」 「都への名称変更規定」
3. 「政治不信」 「利益誘導との批判」
4. 「推進論」 「提唱者が進めるのは当然」

Conclusion band:
「維新への評価が、そのまま賛否を分ける最も感情的な論点」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with amber/orange to highlight the suspicion/distrust element.

Avoid:
No politicians, no party logos (including Nippon Ishin no Kai logo), no government emblems, no real SNS logos,
no manga characters, no real person likeness,
no clutter, no random extra text, no watermark.
```

---

## 4. 防災・災害 — 同じ「防災」で正反対の結論

**ファイル名:** `fukushuto-infographic-wide-bousai.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「防災・災害」

Main title:
「防災・災害」
「同じ『防災』から、なぜ正反対の結論が出る？」

Core message:
賛成側は「首都直下地震に備えた機能分散が急務」、反対側は「南海トラフは首都直下地震と連動する。大阪では東京と共倒れだ」——同じ防災の言葉から正反対の結論が導かれる。この論点だけが、賛成・反対・中立の三すくみになっている。

Visual structure:
Center: 大きな天秤アイコン。左の皿に「機能分散：一極集中リスクを減らす」（green accent、都市アイコンを複数散らす）、右の皿に「共倒れリスク：同時被災の恐れ」（red accent、波アイコン）。天秤の台座に「防災」という共通ラベルを置き、「同じ根拠から逆の結論」という構図を強調する。
Left side: 首都機能分散を示す、東京から別の都市への矢印アイコン（building→building）。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「機能分散」 「東京一極集中のリスク」
2. 「南海トラフ」 「大阪も太平洋岸の被災想定域」
3. 「連動リスク」 「2大災害が同時に起きたら」
4. 「三すくみ」 「賛否が正面衝突する唯一の論点」

Conclusion band:
「賛成も反対も『防災』を根拠にする——このテーマ唯一の激戦区」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with green for the pro-decentralization side and red for the co-disaster risk side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness, no dark disaster scenes (no collapsed buildings, no victims),
no clutter, no random extra text, no watermark.
```

---

## 5. 費用・財源 — 「4兆円とも7.5兆円とも」

**ファイル名:** `fukushuto-infographic-wide-hiyou.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「費用・財源」

Main title:
「費用・財源」
「総額も財源も、まだ分からない？」

Core message:
副首都整備にかかる費用は民間試算で「4兆円」から「7.5兆円超」まで幅があり、政府は国会答弁で「現時点では分からない」と回答した。物価高で家計が苦しい中、費用も財源も不明確なまま事業を進めることへの不信が論点の中心。少数派からは「大型プロジェクトは方針決定→予算積み上げの順が普通」という擁護もある。

Visual structure:
Left side: 大きな「？兆円」の金額テキスト（濃紺・大文字）。その下に「4兆円〜7.5兆円」のレンジバー（グラジュエントで幅を示す）。コインや電卓・グラフアイコン。
Center: 法案文書アイコン（議事堂ではなく抽象的な書類）と「答弁：現時点では分からない」のカード。「法案可決」→「費用？」の矢印フローに大きな疑問符を重ねる。上昇している物価グラフのミニアイコンを添える。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「試算なし」 「政府：現時点では不明」
2. 「4〜7.5兆」 「民間推計の幅が大きい」
3. 「財源は？」 「国費か、地方か、増税か」
4. 「大型事業」 「方針先行は普通との反論」

Conclusion band:
「物価高の今、費用・財源不明のまま走らせていいのか」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with amber/orange for the "cost unknown / caution" accent.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness,
no clutter, no random extra text, no watermark.
```

---

## 6. 優先順位 — 「物価対策どこ行った」

**ファイル名:** `fukushuto-infographic-wide-yusen.webp`

```text
Create a polished 16:9 wide Japanese infographic.

Theme:
副首都法案 の個別論点「優先順位」

Main title:
「優先順位」
「なぜ今、これを最優先にするのか？」

Core message:
「消費税減税は先送りなのに、副首都法案のために会期を延長するのか」——法案の中身より「なぜ今これなのか」を問う怒りが中心の論点。件数は最少だが感情温度は2番目に高く、生活実感からの怒りが政治への不満に直結している。

Visual structure:
Left side: 「今の優先課題」として、食費・光熱費・物価を示す生活費アイコン（食材・電球・カートのミニアイコン）のリスト。各アイコンに赤い上昇矢印を添える。「後回し」のスタンプ風ラベルを重ねる。
Center: 横に並んだ2枚の優先度カード。左カード「物価対策」に「⬇ 先送り」の赤いラベル、右カード「副首都法案」に「⬆ 会期延長」の青いラベル。両カードの上に「？」と「なぜ今？」の問い。
Right side: 4つの確認ポイントカードを縦に配置。

Key issue cards:
1. 「会期延長」 「副首都法案を通すために」
2. 「物価対策」 「先送りされたとの声が多い」
3. 「国民感情」 「日常と政治の乖離」
4. 「長期視点」 「国家設計は別の話との反論」

Conclusion band:
「内容より『なぜ今か』——生活実感からの怒りが最も熱い」

Use the common "SNS反応まっぷ civic-tech infographic style".

Style:
Bright, clean Japanese civic-tech infographic.
White and very light blue background.
Vivid blue and navy headline typography.
Rounded cards, soft shadows, small dots, sparkles, subtle chart accents.
Friendly but professional, neutral, nonpartisan.
Readable Japanese text, large bold typography.
Use blue/navy as the base, with red for the "delayed" items and amber for the "why now" tension.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos,
no manga characters, no real person likeness,
no clutter, no random extra text, no watermark.
```
