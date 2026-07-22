# 生成AIと著作権 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 副首都ページの `docs/images/fukushuto-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
副首都 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/
├── ai-copyright-infographic-wide-gakushu.webp     （論点1: 学習データ・無断利用）
├── ai-copyright-infographic-wide-hoseibi.webp     （論点2: 法制度・規制整備）
├── ai-copyright-infographic-wide-moraru.webp      （論点3: 利用者モラル・倫理）
├── ai-copyright-infographic-wide-creator.webp     （論点4: クリエイター保護・権利）
├── ai-copyright-infographic-wide-gijutsu.webp     （論点5: 技術競争・AI推進）
└── ai-copyright-infographic-wide-seiseibutsu.webp （論点6: AI生成物の権利・創作性）
```

```bash
cwebp -q 82 input.png -o docs/images/ai-copyright-infographic-wide-XXX.webp
```

---

## 1. 学習データ・無断利用 — 「漫画村と同じ」は本当か

**ファイル名:** `ai-copyright-infographic-wide-gakushu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「学習データ・無断利用」

Main title (top-left area, large bold Japanese text):
「学習データ・無断利用」
「AI学習は著作権侵害か、合法か」

Core message:
最多126件。AIが作品を学習データとして取り込む行為の是非が核心の争点。日本の著作権法30条の4は学習行為を原則合法とするが、クリエイターからは「許諾も対価もなく作品を取り込む仕組みは著作権侵害だ」という批判が73%を占める。一方「学習行為は合法、問題は生成・出力段階だ」という反論も根強い。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「著作物」として積み重なったイラスト・小説・楽譜のミニアイコン群。大きな赤い「→」矢印が「AI学習」ラベル付きでAIモデルのアイコンへ向かう。「許諾なし・対価なし」の警告ラベル。
CENTER ZONE: 「著作権法 第30条の4」と書かれた法律文書アイコン（議事堂は描かない）。文書に「学習目的の利用：原則合法」の一行。大きな「？」吹き出しで「ただし…」を示す。左に「侵害だ」（赤ラベル）、右に「合法だ」（青ラベル）の対立矢印を重ねる。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「規制賛成 73%」「対価も許諾もなく取り込む仕組みが問題」
  「合法論 22%」「学習行為は30条の4で保護される」
  「漫画村比較」「違法サイトとの類比が多く用いられる」
  「出力段階規制」「生成・出力が問題であり学習は別」

Bottom conclusion band (full width):
「学習の合法性をめぐる解釈の違いが、すべての対立の出発点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Red accent for the "infringement" side, blue for the "legal/pro-AI" side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark disaster scenes, no clutter, no random extra text, no watermark.
```

---

## 2. 法制度・規制整備 — ライセンス制度で解決できるか

**ファイル名:** `ai-copyright-infographic-wide-hoseibi.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「法制度・規制整備」

Main title (top-left area, large bold Japanese text):
「法制度・規制整備」
「ライセンス制度で解決できるのか？」

Core message:
79件。「許諾なし学習の禁止」「オプトアウト制度」「ライセンス料の徴収」など具体的な法整備を求める声が58%を占める。一方でEUのAI法のような強規制は「産業を萎縮させる」という反論があり、規制の範囲と設計が最大の焦点になっている。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「規制を求める声」。EU旗ではなく「EU型ライセンス制度」の書類アイコン。「オプトアウト制度」「許諾義務化」「ライセンス料」の3つを縦に列挙したチェックリスト形式。各項目に赤い要求マーク。
CENTER ZONE: 天秤アイコン。左皿に「権利者保護」（赤・法律書アイコン）、右皿に「産業振興」（青・ロケットアイコン）。「どこで線を引くか」のキャプション。下部に「政府の対応：検討中」のカード。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「許諾義務化」「学習前に著作者の承諾を得る制度」
  「オプトアウト」「拒否した作品は除外する仕組み」
  「産業萎縮」「過剰規制は日本のAI競争力を削ぐ」
  「対価還元」「利用料を権利者に分配する仕組みを」

Bottom conclusion band (full width):
「規制の範囲と設計次第で、産業と権利者の両方が左右される」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with amber/orange for the "law & regulation" accent, blue for the "pro-innovation" side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 3. 利用者モラル・倫理 — クレジット表記と配慮の欠如

**ファイル名:** `ai-copyright-infographic-wide-moraru.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「利用者モラル・倫理」

Main title (top-left area, large bold Japanese text):
「利用者モラル・倫理」
「法律より先に、使い方が問われている」

Core message:
73件。「AI生成と隠してオリジナルとして投稿する」「クレジット表記すらしない」という個人の使い方への批判が中心。「ルールがないから何でもいい」という態度そのものを問題視する声が64%を占め、法整備の議論より先に利用者のモラルを問う論点。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「問題の行動パターン」として3つのミニアイコン:
  スマホ投稿アイコン＋「AI生成と隠して投稿」（赤ラベル）
  名前タグ＋「クレジット表記なし」（赤ラベル）
  複製アイコン＋「元の作者に無配慮」（赤ラベル）
CENTER ZONE: 大きな「モラル vs ルール」比較図。左に「自主的な配慮・表記」（緑のハートアイコン）、右に「法規制による強制」（青の法律書アイコン）。中央に「どちらが先か」の問い。SNSを象徴する抽象的な投稿アイコン群（実在ロゴは描かない）。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「AI隠し」「生成AIとわかるよう表示すべき」
  「クレジット」「元画像の作者名を明記すべき」
  「自己責任」「嫌なら公開しない、が自衛の基本」
  「法待ち限界」「ルールより先に使い手の倫理が必要」

Bottom conclusion band (full width):
「法律が追いつく前に、使い手の一人ひとりの倫理が問われる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/navy base with purple for the "ethics/morality" accent, red for the problematic behavior.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos (no X/Twitter/Instagram logos), no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 4. クリエイター保護・権利 — 廃業の危機は現実か

**ファイル名:** `ai-copyright-infographic-wide-creator.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「クリエイター保護・権利」

Main title (top-left area, large bold Japanese text):
「クリエイター保護・権利」
「廃業の危機は現実か？」

Core message:
46件。クリエイターの生計への影響を訴える声が72%。「10年かけた作風が一瞬で真似される」という訴えと「技術転換すべき」という反論が対立する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: イラストレーター・作曲家のシルエットアイコン群。右下がりのミニ棒グラフ。「廃業・受注減」の赤ラベル1枚。
CENTER ZONE: 盾アイコン（クリエイター保護）とAIアイコンが向き合う構図。左に赤「生計の危機」、右に青「技術転換」の対比ラベル。下部に規制賛成72%を示す短い赤バー。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「廃業の危機」「仕事が次々と消える」
  「作風の複製」「10年が一瞬で真似される」
  「生計の問題」「権利より先に生活が脅かされる」
  「技術転換」「AIを武器にできるか」

Bottom conclusion band (full width):
「クリエイターの生計と技術の進歩が正面衝突する」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Red accent for the creator crisis side, green for the adapt-and-use-AI side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```

---

## 5. 技術競争・AI推進 — 規制したら日本が負ける

**ファイル名:** `ai-copyright-infographic-wide-gijutsu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「技術競争・AI推進」

Main title (top-left area, large bold Japanese text):
「技術競争・AI推進」
「規制したら日本が負ける？」

Core message:
40件。6論点で唯一AI推進派が68%を占める逆転論点。「規制強化すれば国際競争に遅れる」という産業競争力の主張が中心。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 抽象的なグローバル競争マップ（国旗・国名なし）。3つの国アイコンと上昇矢印。日本アイコンだけ「規制→停滞」の赤ラベル。
CENTER ZONE: ロケット上昇アイコン。「学習規制 → 競争力低下」のシンプルな2ステップ因果矢印。横に「出力段階で規制を」の青カード1枚。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「推進派 68%」「唯一の逆転論点」
  「国際競争」「規制で日本だけ遅れる」
  「出力規制」「問題は生成段階に絞るべき」
  「別の問題」「競争力と著作権は切り離せ」

Bottom conclusion band (full width):
「6論点でここだけ逆転——産業競争力がAI推進の根拠」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Blue/cyan dominant for the pro-AI majority, small red accent for the minority regulation side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no country flags or national emblems, no clutter, no watermark.
```

---

## 6. AI生成物の権利・創作性 — プロンプトに著作権はあるか

**ファイル名:** `ai-copyright-infographic-wide-seiseibutsu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
生成AIと著作権 の個別論点「AI生成物の権利・創作性」

Main title (top-left area, large bold Japanese text):
「AI生成物の権利・創作性」
「プロンプトに著作権はあるか？」

Core message:
31件。中立が32%と6論点最多。「プロンプトだけで著作権が生じるか」という問いに社会的合意がなく、法の空白が広がっている。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: キーボード→AIアイコン→イラスト出力の3ステップ矢印図。「©」マークに大きな「？」を重ねる。文字は「ここに創作性は？」の1行のみ。
CENTER ZONE: 3色の横バー。赤「否定 45%」グレー「中立 32%」青「認定 23%」。下部に「答えが出ていない」の短いキャプション。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「著作権否定」「人の創意がなければ権利なし」
  「プロンプト創作」「指示文にも創作性あり」
  「中立 32%最多」「答えが出ていない論点」
  「法の空白」「既存法では対応できない」

Bottom conclusion band (full width):
「中立最多——創作の定義そのものが宙に浮いている」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Purple/indigo accent for the ambiguous theme, red for no-copyright, blue for yes-copyright, gray for the large neutral block.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no watermark.
```
