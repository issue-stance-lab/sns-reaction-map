# 高市文春問題 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `creative/manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 副首都ページの `docs/images/topics/fukushuto/fukushuto-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**

## 保存先・変換コマンド

```
docs/images/topics/takaichi/
├── takaichi-infographic-wide-setsumei.webp  （論点1: 中傷動画・説明責任）
├── takaichi-infographic-wide-bunshun.webp   （論点2: 文春報道の真偽）
├── takaichi-infographic-wide-token.webp     （論点3: サナエトークン疑惑）
├── takaichi-infographic-wide-matsui.webp    （論点4: 松井健氏・工作の実態）
└── takaichi-infographic-wide-hikaku.webp    （論点5: 比較・政治倫理）
```

```bash
cwebp -q 82 input.png -o docs/images/topics/takaichi/takaichi-infographic-wide-XXX.webp
```

---

## 1. 中傷動画・説明責任 — 陣営が依頼したのか、本人に責任はあるか

**ファイル名:** `takaichi-infographic-wide-setsumei.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高市文春問題 の個別論点「中傷動画・説明責任」

Main title (top-left area, large bold Japanese text):
「中傷動画・説明責任」
「陣営が依頼したのか、本人に責任はあるか」

Core message:
最多97件・高熱量（high 34%）。批判・追及が60%を占め、陣営が対立候補への中傷動画制作をネット業者に依頼したとされる疑惑と、国会での答弁が二転三転したことへの説明責任要求が中心。擁護・懐疑側28%は「本人の直接指示が未確認」と断定を拒む。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
スマートフォンの画面にモザイク処理された動画プレイヤーアイコン（実在人物の映像は描かない）。秘書アイコン→制作業者アイコン→拡散アイコンを矢印でつなぐ「工作フロー図」。各ステップに「依頼？」「制作？」「拡散？」の吹き出し。「未確認」の赤スタンプを重ねる。

CENTER ZONE:
国会を象徴するシンプルな議事堂シルエット（実写ではなくアイコン）。演壇のマイクアイコンと「答弁が二転三転」のテキスト。赤い「説明責任」ラベルと青い「本人無関与」ラベルを天秤に乗せる構図。下部に「批判 60% vs 擁護 28%」の横バーグラフ。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「批判・追及 60%」「陣営・秘書の関与が事実なら本人も説明を」
  「擁護・懐疑 28%」「直接指示が未確認の段階で断定は早い」
  「熱量 high 34%」「5論点で最も熱く荒れた議論」
  「答弁の二転三転」「説明のブレ自体が不信感を呼ぶ」

Bottom conclusion band (full width):
「最多97件・最高熱量——中傷動画疑惑と国会答弁のブレが最大の対立軸」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Red accent for the accountability-demand side, blue for the defend/doubt side.

Avoid:
No politicians' faces or likenesses, no party logos, no government emblems, no real SNS logos, no manga characters, no real person names in large type, no dark disaster scenes, no clutter, no watermark.
```

---

## 2. 文春報道の真偽 — 捏造か事実か、メディアを信じるか

**ファイル名:** `takaichi-infographic-wide-bunshun.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高市文春問題 の個別論点「文春報道の真偽」

Main title (top-left area, large bold Japanese text):
「文春報道の真偽」
「捏造か事実か——メディアを信じるか」

Core message:
59件。5論点で唯一「擁護・懐疑」が93%を占める逆転論点。週刊文春の証拠動画にタイムスタンプの時間的矛盾が指摘され、「捏造・印象操作」と断じる声が圧倒的多数。批判・追及はわずか3%にとどまる。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
週刊誌を象徴するシンプルな雑誌アイコン（実在誌名・ロゴは描かない）。証拠書類の上に「？」の大きな吹き出し。タイムライン図に「報道日」と「証拠映像の撮影日」を並べ、「時系列の矛盾」の赤ラベルを重ねる。「捏造の疑い」と「事実の可能性」の対立矢印。

CENTER ZONE:
大きな天秤アイコン。左皿に「捏造・印象操作」（赤、重い・傾く）、右皿に「事実の報道」（青、軽い）。明確に左に傾いた天秤で「擁護 93%」の圧倒的優位を視覚化する。下部に「5論点唯一の逆転」のバナー。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「擁護・懐疑 93%」「5論点唯一の逆転——最大の特徴」
  「時系列の矛盾」「証拠映像の撮影日に疑問符」
  「メディア不信」「週刊誌・共同通信の報道姿勢を批判」
  「批判は3%のみ」「報道を信頼して追及する声が最小」

Bottom conclusion band (full width):
「唯一の逆転論点——擁護93%、文春報道への強い不信が支配する」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue dominant for the defend/skeptical 93% majority, small red accent for the minority who trust the reporting. The tilted scale is the central visual motif.

Avoid:
No politicians' faces or likenesses, no party logos, no government emblems, no real SNS or magazine logos, no manga characters, no real person names in large type, no clutter, no watermark.
```

---

## 3. サナエトークン疑惑 — 被害6億円、関与の範囲はどこまで

**ファイル名:** `takaichi-infographic-wide-token.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高市文春問題 の個別論点「サナエトークン疑惑」

Main title (top-left area, large bold Japanese text):
「サナエトークン疑惑」
「被害6億円、関与の範囲はどこまで」

Core message:
31件。仮想通貨「サナエトークン」の暴落と被害者補償問題。批判・追及61%は「SNSリポストが関与の証拠」と主張し、擁護・懐疑32%は「第三者事業であり直接責任はない」と反論する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
金色のコインアイコン（実在仮想通貨ロゴは描かない）と下落グラフ。「6億円の被害」の赤テキスト。コインから被害者シルエットへ向かう破線矢印。「リポスト・宣伝」ラベルのSNS投稿アイコン（実在SNSロゴは描かない）。

CENTER ZONE:
「直接関与」と「第三者事業」の2択比較図。左に赤い「批判側：リポストは関与の証」のカード、右に青い「擁護側：第三者が独自運営」のカード。中央に「線引きはどこか」の問いと、スマートフォン＋再投稿アイコンを置く。下部に批判61%・擁護32%の横バー。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「批判・追及 61%」「SNSリポストが関与の証拠とみる」
  「擁護・懐疑 32%」「第三者事業で本人に直接責任なし」
  「被害6億円」「補償問題が追及の出発点」
  「熱量は中程度」「他論点より冷静な議論が多い」

Bottom conclusion band (full width):
「SNSリポストを『関与の証拠』とみるか『無関係の拡散』とみるかで評価が割れる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Gold/amber accent for the cryptocurrency token motif, red for the victim/damage side, blue for the defend side. Falling graph visible but not catastrophic.

Avoid:
No politicians' faces or likenesses, no party logos, no government emblems, no real cryptocurrency logos (no Bitcoin, no coin names), no real SNS logos, no manga characters, no real person names in large type, no clutter, no watermark.
```

---

## 4. 松井健氏・工作の実態 — ネットワークの全体像とは

**ファイル名:** `takaichi-infographic-wide-matsui.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高市文春問題 の個別論点「松井健氏・工作の実態」

Main title (top-left area, large bold Japanese text):
「松井健氏・工作の実態」
「ネットワークの全体像とは」

Core message:
19件。松井健氏を軸にした情報工作ネットワークの実態と、高市陣営との接触の深さが焦点。批判・追及63%は「秘書を通じた依頼が事実なら陣営の関与は明白」と主張。擁護・懐疑21%は「松井氏の証言の信頼性自体に疑問」と反論。慎重・保留15%は証拠待ちの立場。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
抽象的な人物ネットワーク図（顔・実名は描かない）。中心に「工作者（松井）」のシルエット、周囲に「陣営秘書」「動画制作業者」「SNS拡散ルート」の3ノードを点線でつなぐ。各接続点に「確認済み？」「未確認？」のラベル。

CENTER ZONE:
「接触ルート」の時系列フロー図。書類アイコンの「依頼？」→スマホアイコンの「制作？」→再生ボタンアイコンの「拡散？」の3段ステップ。各ステップに「事実」（青チェック）と「未確認」（赤クエスチョン）の2列を並べる。下部に「証言の信頼性が争点」のカード。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「批判・追及 63%」「秘書経由の依頼が事実なら陣営の責任は明白」
  「擁護・懐疑 21%」「松井氏証言の信頼性自体に疑問」
  「慎重・保留 15%」「証拠が出そろうまで判断保留」
  「ネットワーク図」「誰が誰に何を依頼したかの全体像が焦点」

Bottom conclusion band (full width):
「接触・依頼・拡散の各段階で『事実か未確認か』が決定的に分かれる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Navy/dark blue for the network diagram lines, red for the confirmed-accusation side, blue for the skeptical side, amber for the undecided nodes.

Avoid:
No politicians' faces or likenesses, no real person names in large type, no party logos, no government emblems, no real SNS logos, no manga characters, no dark conspiracy visuals, no clutter, no watermark.
```

---

## 5. 比較・政治倫理 — 他の政治家スキャンダルと同じ基準で問えるか

**ファイル名:** `takaichi-infographic-wide-hikaku.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高市文春問題 の個別論点「比較・政治倫理」

Main title (top-left area, large bold Japanese text):
「比較・政治倫理」
「他の政治家スキャンダルと同じ基準で問えるか」

Core message:
17件。玉木氏・石丸氏ら他の政治家スキャンダルとの比較から政治家の説明責任を問う横断的な論点。批判・追及58%は「党派を問わず同じ基準で追及すべき」と主張。擁護・懐疑29%は「比較対象が違う、二重基準だ」と反論する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE:
「政治家スキャンダル比較」のシンプルな比較表（実名・政党名の大きな表示は避け、「政治家A」「政治家B」「政治家C」などの中立ラベルを使う）。各ケースに「メディア報道量」「追及の強度」「解決の有無」の3行を並べ、バラつきを示す。「同じ基準？」の吹き出し。

CENTER ZONE:
大きな天秤アイコン。左皿に「情報工作・虚偽答弁」（赤、今回のケース）、右皿に「他のスキャンダル」（青、比較対象）。どちらの皿も似た重さで水平に示し「本当に同じ基準か」を問う。中央下に「政治家の説明責任」の大見出しカード。批判58%・擁護29%の横バーも小さく添える。

RIGHT ZONE:
4つの角丸カードを2×2グリッドで配置:
  「批判・追及 58%」「党派を問わず同じ基準で説明責任を問うべき」
  「擁護・懐疑 29%」「比較対象が違う、フェアな比較ではない」
  「選挙・情報工作」「選挙への組織的介入は別次元の問題」
  「メディアの姿勢」「報道量のバラつきへの不信感も論点に」

Bottom conclusion band (full width):
「政治倫理は党派を超えた横断論点——比較の公平性が問われる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Balanced blue/red palette for the comparison motif — neither side dominates visually. The level scale is the central motif. Professional and nonpartisan.

Avoid:
No politicians' faces or likenesses, no real person names in large type, no party logos or colors, no government emblems, no real SNS logos, no manga characters, no clutter, no watermark.
```
