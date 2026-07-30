# 消費税減税 — 論点別インフォグラフィック（wide版）生成プロンプト

共通スタイル: `manga-prompts/infographic-style-guide.md` を参照。

基準テイスト: 副首都ページの `docs/images/topics/fukushuto/fukushuto-infographic-wide-*.webp` と同じ明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影。実在の政治家・政党ロゴ・政府エンブレムは描かない。

**このテーマ固有の注意:** 最大論点が「公約と政治不信」で政党の動きが話題の中心だが、**画像内に実在の政党名・政治家名・省庁名は入れない**。「公約を掲げた各党」「与党」「野党」のような一般名詞に置き換える。特定政党の支持・批判に読める配色（政党カラー）も避ける。

## 生成サイズ

**1916×821px（21:9 ultra-wide）**
副首都 wide と同一サイズを指定すること。

## 保存先・変換コマンド

```
docs/images/topics/consumption-tax-cut/
├── consumption-tax-cut-infographic-wide-kouyaku.webp    （論点1: 公約と政治不信 267件）
├── consumption-tax-cut-infographic-wide-kouka.webp      （論点2: 減税の効果 114件）
├── consumption-tax-cut-infographic-wide-taishou.webp    （論点3: 減税の対象範囲 96件）
├── consumption-tax-cut-infographic-wide-zaigen.webp     （論点4: 財源と社会保障 64件）
├── consumption-tax-cut-infographic-wide-kyufu.webp      （論点5: 給付など他策との比較 46件）
└── consumption-tax-cut-infographic-wide-jigyousha.webp  （論点6: 事業者の実務負担 19件）
```

```bash
cwebp -q 82 input.png -o docs/images/topics/consumption-tax-cut/consumption-tax-cut-infographic-wide-XXX.webp
```

分類の母数: Yahooリアルタイム検索667件 → 関連666件 → 意見612件（Hermes / kimi-k2.6、2026-07-28）。
立場は4分類（減税推進 / 条件付き賛成・政府案に不満 / 減税反対・慎重 / 中立・情報）。

---

## 1. 公約と政治不信 — 「公約はどこへ行ったのか」

**ファイル名:** `consumption-tax-cut-infographic-wide-kouyaku.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「公約と政治不信」

Main title (top-left area, large bold Japanese text):
「公約と政治不信」
「公約はどこへ行ったのか」

Core message:
全6論点中最多の267件、意見全体の43.6%を占める最大論点。税制の中身ではなく「選挙で減税を掲げた党が採決でどう動いたか」を問う声が中心。減税推進167件（63%）が「公約を実行しない政治は信用できない」と訴える一方、減税に反対の立場からも「公約を掲げた以上は説明すべき」という批判が32件あり、賛否を越えて政治の姿勢そのものが問われている。減税推進167件 / 条件付き賛成35件 / 反対・慎重32件 / 中立33件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「選挙のとき」と「採決のとき」の対比を上下2段で。上段：演説台のシルエットと公約ビラのアイコン、「減税します」と読める吹き出し（政党名は入れない）。下段：投票ボタンが並ぶ議場の抽象アイコンと、色の変わった票のマーク。間に赤い下向き矢印と「言ったことと、やったこと」の短いラベル。
CENTER ZONE: 大きな「公約」の紙アイコンが中央に置かれ、そこから左右にひび割れが走る構図。左半分に「実行」、右半分に「先送り」のラベル。紙の下に「政治不信」と書かれた濃紺のバーを幅いっぱいに配置し、その上に4色の帯グラフ（緑63% / 橙13% / 赤12% / 灰12%）を重ねる。キャプション「賛否を越えて広がる不信」。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「最大論点 267件」「意見全体の43.6%が政治の姿勢を問う」
  「実行を求める声 63%」「掲げた減税を実行しない党は信用できない」
  「反対派からも批判」「減税に反対でも公約の説明責任は問う」
  「中身より姿勢」「税率の議論より政治への信頼が争点化」

Bottom conclusion band (full width):
「税制の中身ではなく『言ったことを守るか』が最大の争点になった」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Navy as the dominant color for the "trust in politics" theme, with a red accent for the broken-promise crack and green for the majority demanding execution. Serious but not angry, analytical tone.

Avoid:
No politicians, no party names, no party logos, no government emblems, no ministry names, no real SNS logos, no manga characters, no real person likeness, no national flags, no party color coding, no clutter, no random extra text, no watermark.
```

---

## 2. 減税の効果 — 「本当に生活は楽になるのか」

**ファイル名:** `consumption-tax-cut-infographic-wide-kouka.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「減税の効果」

Main title (top-left area, large bold Japanese text):
「減税の効果」
「本当に生活は楽になるのか」

Core message:
114件。6論点で唯一、反対・慎重が最多になった論点。「減税分が値下げに反映されず事業者の利益になる」「供給が追いつかないなかで需要を刺激すればインフレが加速する」という懐疑が61件（54%）を占める。一方で「物価高対策として最も早く広く効く」「申請不要でその場に効く」という即効性を評価する声も37件あり、同じ物価高を根拠に正反対の結論が出ている。反対・慎重61件 / 減税推進37件 / 条件付き賛成12件 / 中立4件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「減税分はどこへ行く？」の分岐図。棚に並んだ商品と値札のアイコンから矢印が2本に分かれる。上の矢印→財布アイコン＋「家計に届く」緑ラベル。下の矢印→店舗・企業の抽象アイコン＋「価格に反映されない」赤ラベル。分岐点に大きな「？」マーク。
CENTER ZONE: 中央に折れ線グラフのフレーム。同じ「物価高」の山から2本の線が伸び、上向きの赤線に「需要刺激でインフレ加速」、下向きの緑線に「可処分所得が増える」のラベル。グラフの下に「同じ物価高から、正反対の結論」というキャプション帯。左下に「反対・慎重 54%」の赤いバー。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「唯一の慎重多数 54%」「6論点で反対・慎重が最多になった論点」
  「価格転嫁の疑問」「値下げされず事業者の利益になるのでは」
  「インフレ懸念」「供給不足の中で需要を刺激する危うさ」
  「即効性の評価 32%」「申請不要で全員にすぐ届く手段」

Bottom conclusion band (full width):
「同じ物価高を根拠に、効くという声と効かないという声が正面からぶつかる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, chart accents. Red for the skeptical side and green for the effectiveness side, balanced so neither dominates visually. Analytical, evidence-weighing tone.

Avoid:
No politicians, no party names, no party logos, no government emblems, no real SNS logos, no store brand logos, no manga characters, no real person likeness, no real banknotes or portraits on money, no clutter, no random extra text, no watermark.
```

---

## 3. 減税の対象範囲 — 「食料品だけか、一律か」

**ファイル名:** `consumption-tax-cut-infographic-wide-taishou.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「減税の対象範囲」

Main title (top-left area, large bold Japanese text):
「減税の対象範囲」
「食料品だけか、一律か」

Core message:
96件。減税に前向きな声が93%を占めるが、その中身が真っ二つに割れる論点。減税推進47件（49%）が「一律減税、さらに廃止まで」を求め、条件付き賛成42件（44%）が「減税自体は歓迎だが食料品限定・期限付きでは中途半端」と政府案に不満を示す。反対・慎重は7件と最少で、「反対だから食料品限定で済んでよかった」という逆向きの評価も含まれる。減税推進47件 / 条件付き賛成42件 / 反対・慎重7件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 買い物カゴを2つ並べる対比。左のカゴ＝パン・野菜・牛乳など食料品、下向き矢印の橙ラベル「対象」。右のカゴ＝日用品・電球・衣類など、イコール記号の青ラベル「対象外」。2つのカゴの間に点線の境界線を縦に引き、「この線をどこに引くか」の短いキャプション。
CENTER ZONE: 横一直線のスライダー（ゲージ）を大きく配置。左端「食料品のみ」、中央「一律5%」、右端「廃止」の3つの目盛り。つまみは左端寄りに置き、そこから右向きの矢印が複数伸びて「もっと踏み込め」を表現。ゲージの下に「前向きが93%、でも着地点が割れる」のキャプション帯。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「前向きが93%」「96件中89件が減税そのものには賛成」
  「一律・廃止まで 49%」「対象を絞らず税率全体を下げよ」
  「政府案に不満 44%」「食料品限定・期限付きでは中途半端」
  「線引きの難しさ」「どこまでを食料品とするかで実務が複雑化」

Bottom conclusion band (full width):
「賛成が9割でも一枚岩ではない——どこまで下げるかで意見が割れる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, subtle chart accents. Green for the "full cut" side and amber/orange for the "government plan is not enough" side, with blue for the neutral policy framing. Two accent colors dominate, showing a split inside the pro side.

Avoid:
No politicians, no party names, no party logos, no government emblems, no real SNS logos, no store brand logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 4. 財源と社会保障 — 「減った分は誰が払うのか」

**ファイル名:** `consumption-tax-cut-infographic-wide-zaigen.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「財源と社会保障」

Main title (top-left area, large bold Japanese text):
「財源と社会保障」
「減った分は誰が払うのか」

Core message:
64件。賛否がほぼ拮抗する論点。反対・慎重30件（47%）が「年金・医療の財源が細る」「代替財源を示さない減税は無責任」と警告し、減税推進28件（44%）が「財源論は増税のための口実」「歳出の組み替えと経済成長で賄える」と反論する。件数差はわずか2件で、6論点の中で最も評価が割れている。反対・慎重30件 / 減税推進28件 / 条件付き賛成5件 / 中立1件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 「消費税が支えているもの」を示す3アイコン縦並び。年金（通帳と高齢者の抽象シルエット）、医療（十字と聴診器）、介護（手を添えるシンプルなピクトグラム）。それぞれに細い青いバーを添える。下に赤ラベル「減れば、どこかが細る」。
CENTER ZONE: 中央に大きな天秤。左皿に「減税分」の欠けたコインの山、右皿に「社会保障」のアイコン群。天秤の支柱に「代替財源」というラベルの支え棒が斜めに描かれ、それが太いか細いかで結論が変わることを示す。天秤の下に赤28%対緑27%の拮抗バーと「わずか2件差」のキャプション。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「最も拮抗 30 vs 28」「6論点で最も評価が割れた論点」
  「無責任論 47%」「代替財源を示さない減税は無責任」
  「口実論 44%」「財源論は増税を通すための言い訳」
  「歳出の組み替え」「他の支出を見直せば財源は作れるという主張」

Bottom conclusion band (full width):
「財源をどう埋めるかではなく、財源論そのものを信じるかで割れている」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, chart accents. Red and green used in near-equal weight to express the almost even split, with amber for the funding-source element. Balanced, no side visually favored.

Avoid:
No politicians, no party names, no party logos, no government emblems, no ministry names, no real SNS logos, no manga characters, no real person likeness, no real banknotes or portraits on money, no clutter, no random extra text, no watermark.
```

---

## 5. 給付など他策との比較 — 「減税か、給付付き税額控除か」

**ファイル名:** `consumption-tax-cut-infographic-wide-kyufu.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「給付など他策との比較」

Main title (top-left area, large bold Japanese text):
「給付など他策との比較」
「減税か、給付付き税額控除か」

Core message:
46件。「消費税減税」以外の手段と比べる論点。反対・慎重21件（46%）が「逆進性の是正が目的なら給付付き税額控除の方が的を絞れる」「社会保障費の見直しが先」と主張し、条件付き賛成13件（28%）は「減税と給付を組み合わせないと低所得層に届かない」と両立を求める。減税推進12件（26%）は「配るなら取るな」「一度きりの給付より継続して効く減税を」と反論する。反対・慎重21件 / 条件付き賛成13件 / 減税推進12件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 3つの手段を縦に並べたカード。①「消費税減税」＝レシートと下向き矢印。②「給付付き税額控除」＝申請書類と封筒。③「現金給付」＝振込通帳。各カードの横に「全員に継続」「対象を絞る」「一度きり」の短いラベル。
CENTER ZONE: 中央に「どちらが届くか」と題した比較図。左に「広く薄く」を表す横に広い浅い皿、右に「狭く厚く」を表す縦に深い皿。皿の間を人型ピクトグラムの列が行き来する。下に「手続きの重さ」を示す矢印スケール（減税＝軽い / 給付＝重い）。キャプション「速さと的の絞りやすさは両立しない」。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「他策を推す 46%」「逆進性の是正なら控除の方が的を絞れる」
  「両立を求める 28%」「減税と給付を組み合わせないと届かない」
  「減税を推す 26%」「一度きりの給付より継続する減税を」
  「手続きの壁」「申請が要る制度は届かない層が出る」

Bottom conclusion band (full width):
「速く広く効かせるか、対象を絞って厚く配るか——手段の選び方で割れる」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, chart accents. Purple/indigo as the main accent for the "comparing options" theme, with teal for the benefit/allowance side and green for the tax-cut side. Comparative, calm tone.

Avoid:
No politicians, no party names, no party logos, no government emblems, no real SNS logos, no manga characters, no real person likeness, no real banknotes or portraits on money, no clutter, no random extra text, no watermark.
```

---

## 6. 事業者の実務負担 — 「レジ改修とインボイスの現場」

**ファイル名:** `consumption-tax-cut-infographic-wide-jigyousha.webp`

```text
Create a polished ultra-wide 21:9 Japanese infographic at 1916×821 pixels.

Theme:
消費税減税 の個別論点「事業者の実務負担」

Main title (top-left area, large bold Japanese text):
「事業者の実務負担」
「レジ改修とインボイスの現場」

Core message:
19件と最少ながら、実務の観点から減税に最も懐疑的な論点。反対・慎重11件（58%）が「レジ・システム改修の負担が中小事業者に集中する」「短期の税率変更では現場が回らない」「免税・簡易課税事業者の負担増で廃業を招く」と指摘する。一方で減税推進5件（26%）は「改修費は公費で持てばいい」「増税のときはシステム問題が議論されなかった」と、実務論を減税を見送る口実とみている。反対・慎重11件 / 減税推進5件 / 中立2件 / 条件付き賛成1件。

Ultra-wide horizontal composition (left → center → right flow):
LEFT ZONE: 小さな商店のカウンターとレジ端末のアイコン。レジから伸びる設定画面の吹き出しに「税率の切り替え」を表す歯車マーク。下に3つの負担ラベルを縦に並べる：「レジ・システム改修」「区分経理の手間」「インボイス対応」。赤い「中小に集中」の帯。
CENTER ZONE: 中央に「税率変更」の歯車を大きく配置し、そこから2方向へ矢印。上向き矢印→「準備期間があれば回る」緑ラベル。下向き矢印→「短期の変更では回らない」赤ラベル。歯車の脇に、大きな企業アイコンと小さな商店アイコンを並べ、負担の大きさの違いを棒の高さで表す。キャプション「同じ改修でも、体力差で重さが変わる」。
RIGHT ZONE: 4つの角丸カードを2×2グリッドで配置:
  「最も慎重 58%」「19件中11件が実務面から慎重・反対」
  「中小に集中」「改修コストを吸収できる体力に差がある」
  「準備期間の要求」「短期の税率変更では現場が対応できない」
  「口実論 26%」「増税時に議論されない負担論は言い訳では」

Bottom conclusion band (full width):
「最少の論点だが、実務の重さを理由にした慎重論が最も濃く出る」

Style:
Bright, clean Japanese civic-tech infographic. White and very light blue background. Vivid blue and navy headline typography. Rounded cards, soft shadows, small dots, sparkles, chart accents. Amber/orange as the main accent for the "operational burden" theme, red for the small-business concentration, green for the counterargument. Practical, on-the-ground tone.

Avoid:
No politicians, no party names, no party logos, no government emblems, no real SNS logos, no store brand logos, no POS vendor logos, no manga characters, no real person likeness, no clutter, no random extra text, no watermark.
```

---

## 「その他」を作らない理由

`その他` は6件（意見全体の1.0%）と極端に少なく、内容も他論点の言い換えが中心のため、独立したインフォグラフィックは作らない。
ページの論点解説カードも6論点構成にしてある（自転車青切符も同じ理由で `その他` を除外している）。

---

## 生成後の反映手順

**2026-07-29 実施済み**（6枚とも生成・WebP変換・HTML反映・ローカル検証まで完了）。

1. 各PNGをWebP変換して `docs/images/topics/consumption-tax-cut/` に保存する

   ```bash
   cwebp -q 82 input.png -o docs/images/topics/consumption-tax-cut/consumption-tax-cut-infographic-wide-XXX.webp
   ```

2. `scripts/build_consumption_tax_page.py` の explainer セクション生成部を、画像つきカード＋拡大モーダル版に切り替える
   （テンプレート元の副首都ページ `#explainer-section` と同じ構造。現在は画像未生成のためテキストのみ）
3. `python3 scripts/build_consumption_tax_page.py` を再実行する
4. ローカルで画像の読み込みと375px幅の表示を確認する
5. `THEMES.yaml` の `manga_img` を `partial` から更新する

---

## 品質チェック

- 論点名と件数が本文・アリーナの数字と一致している（意見612件が母数）
- 実在の政党名・政治家名・省庁名・政党カラーが入っていない
- 賛成側・反対側のどちらかを勝たせる表現になっていない
- 21:9（1916×821px）で生成されている
- 小さすぎて読めない文字が入っていない
- WebP変換後に1枚あたり200KB以下
