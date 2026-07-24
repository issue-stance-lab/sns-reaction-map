# 高齢者免許返納 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 副首都ページの `docs/images/fukushuto-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
副首都 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/
├── elderly-license-revocation-infographic-wide-gizuka.webp   （論点1: 義務化・事故防止）
├── elderly-license-revocation-infographic-wide-chiho.webp    （論点2: 地方の足・移動権）
├── elderly-license-revocation-infographic-wide-tekisei.webp  （論点3: 適性検査強化）
├── elderly-license-revocation-infographic-wide-infra.webp    （論点4: 代替交通整備）
├── elderly-license-revocation-infographic-wide-jishu.webp    （論点5: 自主返納支援）
└── elderly-license-revocation-infographic-wide-sonota.webp   （論点6: その他・複合）
```

```bash
cwebp -q 82 input.png -o docs/images/elderly-license-revocation-infographic-wide-XXX.webp
```

---

## 1. 義務化・事故防止 — 「年齢で強制返納、命を守れるか」

**ファイル名:** `elderly-license-revocation-infographic-wide-gizuka.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「義務化・事故防止」

Main title (top-left area, large bold Japanese text):
「義務化・事故防止」
「年齢で強制返納、命を守れるか」

Core message:
全6論点中最多139件。高齢ドライバーの死亡事故報道が引き金となり、「75〜85歳で一律に法的義務化すべき」という声が93%を占める。感情強度が最も高い論点で「未来ある命を守るために」という切実な訴えが集中する。義務化支持129件 / 中立9件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「事故ニュース報道」をイメージしたアイコン群。車とブレーキ痕のミニイラスト。「被害者の声」ラベル付きの吹き出しアイコン2〜3個。下に「高齢ドライバーによる死亡事故」の短い見出し帯。赤い警告ラベル「繰り返される悲劇」。
CENTER ZONE: 大きな「年齢制限」サインボード（「75歳」「80歳」「85歳」の数字が段階的に並ぶシルエット）。左から右へ「事故報道」→「世論の怒り」→「法的義務化」の3ステップ矢印。中央下に「義務化賛成 93%」の短い赤バー。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「義務化支持 93%」「139件中129件が義務化を支持」
  「年齢で一律に」「個人差より年齢線引きを求める声」
  「感情強度が最高」「事故報道への怒り・恐怖が原動力」
  「命を守る論」「未来ある命を守るための必要悪」

Bottom conclusion band (full width):
「事故報道を受けた怒りと恐怖が、義務化への圧倒的な賛同を生む最大論点」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Friendly but professional, neutral, nonpartisan. Large bold readable Japanese text. Red accent for the "mandatory return" call, amber for the accident/warning elements, blue for the neutral policy side.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no dark disaster scenes, no graphic accident depictions, no clutter, no random extra text, no watermark.
```

---

## 2. 地方の足・移動権 — 「田舎で免許返納は死活問題」

**ファイル名:** `elderly-license-revocation-infographic-wide-chiho.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「地方の足・移動権」

Main title (top-left area, large bold Japanese text):
「地方の足・移動権」
「田舎で免許返納は死活問題」

Core message:
24件。「車がなければ病院にも買い物にも行けない」「東京の感覚で義務化を語るな」という地方在住者の切実な声。義務化反対が90%超。件数は少ないが訴えの強度は高く、都市と地方で論点の見え方が全く異なる。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 対比を示す2エリア。上段「都市」：バス・電車・タクシーのミニアイコンが密集。下段「地方・農村」：バス停1つと長い道路、周囲に何もない風景の抽象アイコン。「路線バス：1日2本」のキャプション。
CENTER ZONE: 大きな地図形シルエット（日本列島ではなく抽象的な島形）を2色に分割。都市エリア（青・交通充実）と地方エリア（橙・交通空白）。中央に「車＝唯一の移動手段」というラベル付きの車アイコン。矢印で「返納したら？」の問いを指す。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「義務化反対 90%超」「24件中21件が一律義務化に反対」
  「通院・買い物」「車なしに日常生活が成り立たない」
  「地方の格差」「公共交通のない地域では返納＝孤立」
  「東京ルール批判」「都市基準の政策を地方に押しつけるな」

Bottom conclusion band (full width):
「移動手段のない地方では、免許返納は生活からの強制退場を意味する」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Orange/amber for the "rural hardship" accent, teal/green for the "urban mobility" side. Contrasting but balanced.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 3. 適性検査強化 — 「年齢より個人の能力で判断すべき」

**ファイル名:** `elderly-license-revocation-infographic-wide-tekisei.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「適性検査強化」

Main title (top-left area, large bold Japanese text):
「適性検査強化」
「年齢より個人の能力で判断すべき」

Core message:
20件。「年齢で一律に区切るのは不合理。認知機能検査・実車試験をもっと厳格化して、実際に危険な人だけを排除すべき」という立場。反対寄り60% / 中立40%。サポートカー限定免許や自動運転限定など技術的対応を求める声も。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「年齢で一律」の問題点を示すアイコン。75歳マーク付きの禁止サイン。その横に「？」マーク。下に「個人差がある」「能力の高低」を示す棒グラフ（匿名のシルエット群）。
CENTER ZONE: 検査書類アイコンを中心に、3つの矢印が放射状に伸びる:
  「認知機能検査」→書類・脳のシンプルアイコン
  「実車試験」→ハンドルアイコン
  「サポートカー限定」→車＋シールドのミニアイコン
  中央に「能力で判断」の大きなラベル。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「反対寄り 60%」「年齢より能力で判断すべき派」
  「認知機能検査」「厳格化して危険な人だけ排除を」
  「実車試験見直し」「ペーパー試験から実走確認へ」
  「技術的対応」「自動ブレーキ義務化・自動運転限定」

Bottom conclusion band (full width):
「年齢で一律に区切るより、実力で線引きすべきという代替案」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Purple/indigo accent for the "individual assessment" theme, blue for the "policy design" side, red for the blanket-age-rule rejection.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 4. 代替交通整備 — 「インフラ整備が義務化の前提」

**ファイル名:** `elderly-license-revocation-infographic-wide-infra.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「代替交通整備」

Main title (top-left area, large bold Japanese text):
「代替交通整備」
「インフラ整備が義務化の前提」

Core message:
9件。「返納させるなら、まず代わりの交通手段を整えるべきだ」という立場。整備優先派80%。デマンド交通・コミュニティバス・ライドシェアの拡大など、移動の代替手段なき義務化は「生活破壊」と批判する。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「現在の問題」として、車アイコンに×印。その下に空のバス停（バスが来ない）、「タクシー：高額」ラベル、「デマンド交通：未整備」ラベルの3アイコン。赤い「代替なし」ラベル。
CENTER ZONE: 「義務化」と「インフラ整備」の2本の矢印が天秤に乗る構図。整備なし＝天秤が義務化側に傾き「生活破壊」。整備あり＝均衡して「安心して返納」。中央キャプション「どちらが先か？」
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「整備優先 80%」「9件中7件がインフラ先行を要求」
  「デマンド交通」「予約制の乗り合いバスで柔軟移動」
  「ライドシェア」「需要に応じた民間移動サービス」
  「義務化は後から」「移動手段を保障してから返納を求めよ」

Bottom conclusion band (full width):
「移動手段の代替なき義務化は生活破壊——まずインフラが先」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Teal/green for the "infrastructure solution" elements, amber/orange for the "current gap/problem" side. Clean and hopeful tone.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 5. 自主返納支援 — 「特典と支援で自発的な返納を促す」

**ファイル名:** `elderly-license-revocation-infographic-wide-jishu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「自主返納支援」

Main title (top-left area, large bold Japanese text):
「自主返納支援」
「特典と支援で自発的な返納を促す」

Core message:
7件。「強制するのではなく、返納したら生活が便利になる制度を作れば、自然に返納者が増えるはずだ」という立場。バス・電車の割引、タクシーチケット、買い物支援など返納のメリットを実感できる制度設計を求める。特典強化支持75%。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「現在の自主返納」フロー。免許証アイコン→「自主返納」→「運転経歴証明書」。下にバス運賃割引・タクシー割引カードの小アイコン。「一部の自治体のみ対応」の注記ラベル。
CENTER ZONE: プレゼントボックスまたはギフトカードのアイコンを中心に、4本の矢印が放射状に伸びる:
  「バス・電車 割引」
  「タクシーチケット」
  「買い物配送サービス」
  「医療・介護連携」
  中央キャプション「返納したら生活が豊かになる」
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「特典強化支持 75%」「強制ではなく動機付けを求める声」
  「宇和島バスの例」「自主返納でバス運賃が半額に」
  「自発的返納増」「メリット実感で自然に返納者が増える」
  「地方でも選べる」「地域に合った支援制度の多様化を」

Bottom conclusion band (full width):
「義務化より先に、返納を選びやすくするメリット設計を」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Green/teal for the "benefit/incentive" elements, blue for the "policy design" side. Warm and positive, encouraging tone.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 6. その他・複合 — 「複数論点の混在と感情的反応」

**ファイル名:** `elderly-license-revocation-infographic-wide-sonota.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
高齢者の運転免許返納 の個別論点「その他・複合的な反応」

Main title (top-left area, large bold Japanese text):
「その他・複合的な反応」
「5つの論点に収まらないSNSの声」

Core message:
12件。「政治家にも年齢制限を」「若者の事故も多い——高齢者だけ問題視するのはおかしい」など、免許返納そのものへの賛否より別の論点を持ち出す投稿や、感情的な怒りの発露が中心。SNSならではの生の声が集まる。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「主な反応パターン」として3アイコン:
  吹き出し＋「政治家にも年齢制限を」（紫ラベル）
  天秤＋「なぜ高齢者だけ？」（橙ラベル）
  怒りの吹き出し＋「感情表出・怒り」（赤ラベル）
CENTER ZONE: 中央に「その他 12件」の円グラフ（灰色100%）。周囲に5つの論点（義務化・地方・適性検査・インフラ・自主返納）の小アイコンが配置され、その外側に「その他」が位置することを示す構図。「どの論点にも収まらない」のキャプション。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「政治批判 複数」「国会議員にも定年制・年齢制限を」
  「比較論 複数」「若者の事故率も高い、高齢者だけ問題視？」
  「感情表出」「具体的政策より怒り・不満の発露」
  「SNSらしい声」「複数論点を混在させた複合反応」

Bottom conclusion band (full width):
「怒りと比較論が交差する——定型の論点を超えたSNSの生の声」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles. Gray/silver as the primary accent for the "uncategorized/mixed" theme, purple for the political criticism, orange for the comparison arguments. Neutral and analytical tone.

Avoid:
No politicians, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```
