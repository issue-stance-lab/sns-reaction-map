# 部活動の地域移行 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 皇室典範・副首都ページの wide 画像と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
副首都 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/
├── bukatsu-chiiki-infographic-wide-hiyou.png/webp      （費用・家庭負担）
├── bukatsu-chiiki-infographic-wide-ukesara.png/webp    （受け皿・指導者）
├── bukatsu-chiiki-infographic-wide-kyoin.png/webp      （教員の働き方）
├── bukatsu-chiiki-infographic-wide-kyoiku.png/webp     （教育的意義・機会）
├── bukatsu-chiiki-infographic-wide-kousa.png/webp      （地域格差）
└── bukatsu-chiiki-infographic-wide-seido.png/webp      （制度・移行プロセス）
```

```bash
cwebp -q 82 input.png -o docs/images/bukatsu-chiiki-infographic-wide-XXX.webp
```

---

## 1. 費用・家庭負担 — 「月8000円×3人、年間30万円近く」

**ファイル名:** `bukatsu-chiiki-infographic-wide-hiyou.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「費用・家庭負担」

Main title (top-left area, large bold Japanese text):
「費用・家庭負担」
「月謝が増えたら、続けられる家庭と続けられない家庭が生まれる」

Core message:
移行後の月会費が公立部活の頃より大幅に上がるケースが続出。3人きょうだいでは年間30万円近くになる家庭も。低所得家庭への補助の有無で地域差も生まれる。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 家計簿アプリ風のスマートフォン画面。「部活費」の行が赤字で「月8,000円」と表示。下に「×3人 = 月24,000円 / 年間288,000円」の計算式テキスト。電卓と財布のミニアイコン。
CENTER ZONE: 左右に対比する2枚の大きなカード。左カード（青）「公立部活（移行前）」に「月500〜2,000円程度」のラベル。右カード（amber）「地域クラブ（移行後）」に「月5,000〜12,000円」のラベル。中央に太い上昇矢印と「平均X倍」の吹き出し。下部に「補助制度の有無で格差が拡大」の注釈。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「家計直撃」「3人きょうだいで年間30万円近く」
  「地域格差」「補助の有無で差が生まれる」
  「やめざるを得ない」「費用で夢を奪われる子」
  「公的補助」「市税で一律化できるとの声も」

Bottom conclusion band (full width):
「費用を誰がどう補填するか、制度設計が追いついていない」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with amber/orange for the cost increase accent, red for the "can't continue" warning.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no random extra text, no watermark.
```

---

## 2. 受け皿・指導者 — 「ボランティア頼みは限界」

**ファイル名:** `bukatsu-chiiki-infographic-wide-ukesara.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「受け皿・指導者」

Main title (top-left area, large bold Japanese text):
「受け皿・指導者」
「報酬が安ければ、指導者は集まらない」

Core message:
地域クラブの指導者がいない・報酬が最低賃金レベル・責任は重い。「タイミーで探した方が時給が高い」という声も。人材確保ができなければ地域移行自体が空洞化する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 大きな「指導者募集」求人票のアイコン（空白のシルエット）。下に「時給1,000円」の赤文字ラベルと「責任：大」のサブテキスト。「応募ゼロ」スタンプ風の表示。
CENTER ZONE: 悪循環のサイクル図（矢印でループ）:「低報酬 → 人材が集まらない → クラブが成立しない → 子どもが参加できない → 低報酬（に留まり続ける）」。ループの中心に「空洞化リスク」のラベル。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「指導者不足」「地方では人材自体がいない」
  「低報酬」「最低賃金レベル、責任は重い」
  「タイミー比較」「短期バイトより安い時給」
  「生活できる報酬」「社会全体で保障すべき声」

Bottom conclusion band (full width):
「受け皿となる人材と組織がなければ、移行は絵に描いた餅になる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with red for "shortage" and "risk" accents, green for the "livable wage" solution card.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no random extra text, no watermark.
```

---

## 3. 教員の働き方 — 「ブラック部活の解消」が最大動機

**ファイル名:** `bukatsu-chiiki-infographic-wide-kyoin.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「教員の働き方」

Main title (top-left area, large bold Japanese text):
「教員の働き方」
「土日も部活指導——この構造を変えられるか」

Core message:
教員が土日に無償で指導する構造が長時間労働の温床に。地域移行の最大の動機は教員の働き方改革。ただし「義務がなくなっても続ける教員が多い」という現実もある。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 月間カレンダーのアイコン。土曜・日曜のマスに赤い「部活」タグが並ぶ。下に「残業：月60〜100時間超」のバー付きグラフ。「無償」の赤スタンプ。
CENTER ZONE: 「移行前」と「移行後」の対比フロー。移行前：教員アイコンから学校・部活・授業・事務の4本矢印が伸びて「過負荷」ラベル。大きな矢印で移行後：教員アイコンから授業・事務のみ（2本）に絞られ、部活は地域クラブアイコンへ分岐。「役割分担」のラベル。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「土日出勤」「無償で指導する構造」
  「働き方改革」「移行の最大の動機」
  「強制解消」「義務がなくなるメリット」
  「自発継続」「やめられない現実も残る」

Bottom conclusion band (full width):
「教員の過負荷が、地域移行を生み出した最大の根拠」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with red for the "overwork" side and green for the "reformed" post-transition side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no random extra text, no watermark.
```

---

## 4. 教育的意義・機会 — 「子どもの夢と居場所」

**ファイル名:** `bukatsu-chiiki-infographic-wide-kyoiku.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「教育的意義・機会」

Main title (top-left area, large bold Japanese text):
「教育的意義・機会」
「部活は競技だけでなく、人間形成の場でもある」

Core message:
部活動は競技だけでなく人間形成・チームワーク・居場所の場でもある。地域移行で不登校の子も参加しやすくなる可能性がある一方、「費用や距離で夢を奪われる子がいる」という怒りも。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 子どもたちのアクティビティアイコン（バスケットボール・吹奏楽・美術・サッカーのミニアイコン群）。「チームワーク・成長・居場所」の3つのキーワードラベル。明るく活気ある配色（green accent）。
CENTER ZONE: 天秤アイコン。左皿（green）「地域移行で広がる機会」——「不登校でも参加しやすい」「多様な子どもが集まれる」の2行。右皿（amber）「費用と距離の壁」——「月謝が払えない」「遠くて通えない」の2行。中央台座に「機会の平等」ラベル。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「人間形成」「チームワーク・継続・礼儀」
  「不登校の子」「参加しやすくなる可能性」
  「費用の壁」「払えなければ諦めるしかない」
  「距離の壁」「送迎できない家庭の問題」

Bottom conclusion band (full width):
「全ての子どもに機会が届くかどうか——地域移行の本質はここにある」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with green for "opportunity expanding" and amber/orange for "barriers" accents.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no random extra text, no watermark.
```

---

## 5. 地域格差 — 「都市はできるが地方は無理」

**ファイル名:** `bukatsu-chiiki-infographic-wide-kousa.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「地域格差」

Main title (top-left area, large bold Japanese text):
「地域格差」
「都市に代替クラブはあるが、地方には受け皿がない」

Core message:
都市部は代替クラブや交通手段があるが、地方では受け皿となる団体自体が存在しない。少子化で単独チームが組めない学校も増えており、移行の実現可能性が地域によって大きく異なる。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 都市エリアのイメージ。スポーツクラブ・地域クラブのアイコンが複数並ぶ。「選択肢：多」のラベル（green）。公共交通アイコン（電車・バス）も配置。
CENTER ZONE: 抽象化された日本のシルエット地図（ラベル最小限）。都市エリアに緑のチェックマーク複数、地方エリアに赤いバツマークや「？」アイコン。中央に「同じ政策、違う現実」のキャプション。少子化を示す小さな下降矢印グラフ。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「都市」「クラブも交通も選択肢がある」
  「地方」「受け皿自体が存在しない」
  「少子化」「チームが成立しない学校も」
  「柔軟設計」「地域の実情に合わせた制度を」

Bottom conclusion band (full width):
「一律政策が、地域によっては実現不可能な要求になる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with green for urban "options available" and red/amber for rural "no infrastructure" accents, purple for the regional disparity comparison.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no actual city name labels on the map, no dark scenes, no clutter, no random extra text, no watermark.
```

---

## 6. 制度・移行プロセス — 「手探りのまま進んでいる」

**ファイル名:** `bukatsu-chiiki-infographic-wide-seido.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
部活動の地域移行 の個別論点「制度・移行プロセス」

Main title (top-left area, large bold Japanese text):
「制度・移行プロセス」
「方針は出たが、現場は手探りのまま」

Core message:
国の方針は出たが、担い手・費用負担のルールは自治体ごとの手探り。「クラブ化と言っているのにチームしか作っていない」という本質的な批判も。プロセス設計の問題を問う声が最多論点（投稿件数51件）。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 大きな法令文書アイコン（「国の方針」ラベル付き）から太い矢印が下に伸びる。矢印の途中で破線になり「現場へ届かない」の吹き出し。矢印の先に「？」マークだけが置かれた空のボックス。
CENTER ZONE: 左右に並ぶ2枚の大きな対比カード。左カード（blue）「国が決めたこと」——「地域移行を推進」「休日から段階的に」の2行のみ。右カード（amber）「現場で起きていること」——「担い手がいない」「費用ルールが決まらない」の2行のみ。両カードの中央に大きな「≠」記号（イコールではない）。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「方針先行」「中身はこれから決まる構造」
  「自治体格差」「対応スピードがバラバラ」
  「本質批判」「チームではなくクラブを作れ」
  「段階移行」「休日→平日の順序は当然との声」

Bottom conclusion band (full width):
「国の方針と現場の実装に大きなギャップがある——最多投稿の論点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Blue/navy base with amber/orange for the "unclear / unresolved" elements, and red for the "gap between policy and reality" accent.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark scenes, no clutter, no random extra text, no watermark.
```
