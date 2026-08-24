# 部活動の地域移行 note第1回｜画像作成プロンプト（Codex用）v2

作成日: 2026-08-23（v2で人物写真＋インフォグラフィックのハイブリッド方式に変更）
対象記事: 「部活動の地域移行、賛成44%が17%に落ちる理由」（note第1回）
作るもの: 見出し画像1点＋本文図解4点＝計5点

---

## 0. 方式：AI生成は「人物と情景」だけ、文字はHTMLで重ねる

画像生成モデルの日本語描画はかなり良くなりましたが、**この記事に限っては数字をAIに描かせません。**
理由は3つあります。

1. **数字が1文字でも崩れたら記事が死ぬ。** この記事の価値は「59.9%と16.7%」という具体的な数値そのものです。「59.9%」が「59.8%」や「5g.9%」になった画像を出した時点で、中立の集計サイトとしての信頼が崩れます
2. **修正コストが違う。** 数値が更新されたとき（データは今後も追加収集されます）、HTMLなら数字を1行書き換えて再レンダリングするだけです。生成画像は作り直しになります
3. **リサーチの推奨どおり。** アップロードいただいた資料にも「実用的：背景のみ生成させ、文字はCanva等で重ねる」「『テキストは入れないで』と指示すると英語文字の混入を防げる」とあります

そのうえで、**人物写真の効果（スキ率14%→19%、カメラ目線が効く）はきちんと取りに行きます。**

```
【最終的な構造】

  レイヤー1（AI生成）  人物・情景の写真         ← 文字は一切入れない
  レイヤー2（CSS）     暗色グラデーションの帯   ← 文字を読ませるための「ざぶとん」
  レイヤー3（HTML/CSS） 数字・ラベル・グラフ     ← ここは完全に制御下に置く
```

---

## 1. 人物描写の方針（全画像共通）

### 主役は「大人」にします

この記事の主題は **大人どうしの負担の受け渡し** です。先生が渡したい、保護者が受け取れない、自治体が用意しきれない。子どもを主役にすると、論旨とズレます。

したがって:

- **写す人物は、先生・保護者・自治体職員（すべて成人）**
- **子どもは、背景に小さく、後ろ姿またはシルエットのみ**。顔は写さない
- これは配慮であると同時に、**編集上そのほうが正しい**という判断です

### 避けること（プロンプトに毎回明記）

- 実在の人物に似せない（架空の人物であること）
- 実在の学校・自治体が特定できる要素を入れない（校章、校名、看板、市章）
- 企業ロゴ、ブランド名、ユニフォームのメーカーロゴ
- 画像内のあらゆる文字（日本語・英語・数字すべて）
- 特定のクリエイターの画風を模倣する指示

### スタイル・ロック（毎回この英文を先頭に貼る）

```
STYLE LOCK — paste this block at the top of every image prompt:

Editorial documentary photograph. Japan, present day. Natural available light,
soft overcast daylight. Muted, desaturated color grading with cool blue-teal
shadows and a slightly dark overall exposure. Shallow depth of field, 50mm lens,
f/2.0. Calm, respectful, understated tone — no drama, no exaggerated emotion,
no stock-photo smiling.

Fictional people who do not resemble any real person. All people shown are
adults. Any children in frame are distant, small, out of focus, and seen only
from behind — never their faces.

Absolutely no text of any kind anywhere in the image: no Japanese characters,
no English letters, no numbers, no signage, no captions, no watermarks,
no school crests, no company logos, no brand marks.

Composition must leave the specified area of the frame visually quiet
(low detail, low contrast) so that graphics can be overlaid there later.
```

このブロックを固定することで、**シリーズ4本すべてで写真のトーンが揃います。**

---

## 2. 画像生成プロンプト（3点）

### 生成A｜見出し画像用の人物（第1回）

```
[STYLE LOCK を貼る]

Subject: A Japanese schoolteacher in their late 30s, wearing a plain navy
track jacket of the kind Japanese school staff wear for club supervision.
Waist-up. Standing just inside the doorway of an empty school gymnasium in
late afternoon. Looking directly into the camera with a calm, composed,
slightly tired expression — someone at the end of a long day, not unhappy,
not smiling for the camera.

Placement: The person occupies the RIGHT side of the frame, with their face
positioned roughly 60-65% across the frame from the left. The LEFT 45% of the
frame must be visually quiet — the dim, out-of-focus gymnasium interior,
low contrast, no distracting detail.

Background: gymnasium floor lines, folded-away goals, high windows with
low afternoon light. Two or three students far in the background, small,
blurred, seen from behind, packing up equipment.

Aspect ratio: 1.91:1 (wide). Output at the highest resolution available.
```

生成後の確認: 手指の破綻／顔の左右非対称／画像内に紛れ込んだ文字／実在しそうな校章。1つでもあれば再生成。

### 生成B｜図3用の2枚（渡す側／受け取る側）

**B-1（渡す側・先生）**

```
[STYLE LOCK を貼る]

Subject: A Japanese schoolteacher in their 40s, plain track jacket, sitting
alone at a desk in a school staff room after hours. Looking slightly to the
right of camera, thinking. Papers and a laptop on the desk, but no readable
text on them. The room is dim except for one desk lamp.

Placement: Person centered. Upper third of the frame kept quiet for an
overlay label.

Aspect ratio: 4:3.
```

**B-2（受け取る側・保護者）**

```
[STYLE LOCK を貼る]

Subject: A Japanese parent in their 40s in the driver's seat of an ordinary
family car at dusk, parked, hands resting on the steering wheel, looking
straight ahead through the windshield with a tired, thoughtful expression.
A child's sports bag visible on the back seat. No child in the car.

Placement: Person centered. Upper third of the frame kept quiet for an
overlay label.

Aspect ratio: 4:3.
```

### 生成C｜図4用の3枚（三すくみ）

3枚は**同じ構図・同じ距離・同じ光**で揃えてください。並べたときに条件が同じに見えることが、この図の説得力です。

```
[STYLE LOCK を貼る]

Produce three separate images with IDENTICAL framing, camera distance,
lighting and color grading. Each is a waist-up portrait, centered,
person looking directly into the camera with a neutral, composed expression.
Plain, softly blurred interior background.

Image 1 — a Japanese schoolteacher in their 40s, plain navy track jacket,
          background: blurred school corridor.
Image 2 — a Japanese parent in their 40s, everyday casual clothing,
          background: blurred home interior.
Image 3 — a Japanese local-government office worker in their 50s,
          plain shirt with a lanyard (no readable card, no logo),
          background: blurred office interior.

Aspect ratio: 1:1 for all three.
```

---

## 3. 合成・作図プロンプト（Codexに渡す）

### 3-0. 共通仕様（最初にこれを渡す）

```
これから note 記事用の画像を5点つくります。まず共通仕様を渡します。
以降の指示はすべてこの共通仕様に従ってください。

## 方式
人物・情景の写真はすでに生成済みで note-drafts/photos/ に置いてあります。
あなたの仕事は、その写真の上に HTML/CSS で数字・ラベル・グラフを重ね、
PNGとして書き出すことです。写真そのものを加工したり、
文字を画像として生成したりはしないでください。

## 実装方法
- 1画像 = 1つの自己完結したHTMLファイル（CSSはインライン、外部JSなし）
- 写真は <img> または background-image で読み込む
- レンダリングは Playwright（Chromium）で該当要素をスクリーンショットしてPNG化
- フォントは Google Fonts の Noto Sans JP（weight 400/500/700/900）
- 数字には font-variant-numeric: tabular-nums を必ず指定
- 写真入力: note-drafts/photos/
- HTML出力: note-drafts/figures/<名前>.html
- PNG出力:  note-drafts/images/<名前>.png
- note-drafts/figures/render.mjs にまとめ、全図を一括再生成できるようにする

## カラートークン（既存のSNS反応まっぷのテーマ。変更しないこと）
--page:    #07111E
--card-1:  #0C1E35
--card-2:  #0A1928
--card-3:  #071522
--ink:     #F0F4FF
--ink-70:  rgba(240,244,255,0.70)
--ink-45:  rgba(240,244,255,0.45)
--teal:    #2DD4BF   /* 主役アクセント／移行支持 */
--red:     #F87171   /* 慎重・反対 */
--amber:   #FBBF24   /* 条件付き・改善要求 */
--gray:    #64748B   /* 中立・情報 */

## 写真の上に文字を置くときの必須処理（「ざぶとん」）
写真に直接文字を置くと必ず読みにくくなります。次のどちらかを必ず入れてください。
- 文字側に、写真から文字方向へ効く線形グラデーションの帯
  例: linear-gradient(90deg, rgba(7,17,30,0.92) 0%, rgba(7,17,30,0.82) 45%, rgba(7,17,30,0) 78%)
- または半透明の暗色パネル（rgba(7,17,30,0.78)、backdrop-filter: blur(6px)）
そのうえで、実際のコントラスト比を計算し、
大きな文字（24px以上）は3:1以上、小さな文字は4.5:1以上を満たすことを確認して報告してください。
写真は場所によって明るさが変わるので、最も明るい画素を基準に判定してください。

## グラフ作図のルール（厳守）
1. 塗り面どうしは必ず 2px の隙間を空ける（背景色で抜く）
2. データ端の角丸は 4px。ベースライン側は角を丸めない
3. 目盛線・軸線は控えめに（rgba(255,255,255,0.06) 以下、1px）
4. 数値ラベルは棒の中か直後に直接置く
5. 系列が2つ以上あるときは凡例を置く。1系列なら凡例なし
6. 数値・ラベルのテキストは白系トークンで書く。系列色をテキストに使わない
   （例外: 記事の主役である「59.9%」と「16.7%」の2つだけ）
7. 2軸グラフは禁止
8. 情報を詰め込まない。余白を十分に取る

## どの図に人物を入れるか（重要）
- 見出し画像 …… 人物あり
- 図1 立場の内訳 …… 人物なし
- 図2 論点別支持率 …… 人物なし
- 図3 渡す側／受け取る側 …… 人物あり
- 図4 三すくみ …… 人物あり
データそのものを見せる図（図1・図2）に人物を入れると、
数字への集中が削がれます。「誰の話か」を示す図にだけ人物を使います。

## 検収（各図つくるたびに必ず）
- PNGを実際に開いて目視し、ラベルの重なり・はみ出し・切れがないか確認する
- 幅375pxに縮小した状態でも主要な数字が読めるか確認する
- 写真の上の文字のコントラスト比を計算して報告する
- 何をどう直したかを具体的に報告する

質問があれば聞いてください。なければ「了解」とだけ返してください。
```

---

### 3-1. 見出し画像

```
見出し画像を1点つくってください。

## 出力
- ファイル: note-drafts/images/bukatsu-chiiki_note-header.png
- 論理サイズ 1280×670px を deviceScaleFactor: 1.5 で描画し、
  実ピクセル 1920×1006px のPNGとして書き出す
- 比率は厳密に 1.91:1

## 素材
- 写真: note-drafts/photos/teacher-gym.png（体育館の入口に立つ先生、カメラ目線、右寄り）
- 写真は object-fit: cover で全面に敷き、顔が中央やや右（x≈62%）に来るよう位置調整する

## レイヤー構成
1. 写真（全面）
2. 左から効く暗色グラデーション
   linear-gradient(90deg, rgba(7,17,30,0.94) 0%, rgba(7,17,30,0.86) 42%, rgba(7,17,30,0.15) 72%, rgba(7,17,30,0) 100%)
   ＋全面に rgba(7,17,30,0.25) を1枚重ねて全体を沈める
3. 文字レイヤー（左寄せ、左端から約90pxの位置に配置）

## 文字レイヤーの中身（これだけ。増やさない）

  部活動の地域移行            26px / weight 500 / --ink-70 / letter-spacing .08em

  44%  →  17%               ← 主役

  SNS公開投稿 754件を論点別に分析   20px / weight 400 / --ink-45

「44% → 17%」の指定:
- フォントサイズ 150px 前後、weight 900、1行に収める
- 「44%」は --teal、「→」は --ink-45（細め）、「17%」は --red
- letter-spacing は -0.02em 程度で詰める

## 配置の絶対条件（最重要）
noteは一覧表示で左右を切り、右側サムネイルや音声記事では
「中央の正方形」だけを切り出します。1280×670の中央正方形は x=305〜975 です。

- 「44% → 17%」の全体が x=305〜975 の内側に完全に収まること
- 先生の顔も x=305〜975 の内側に収まること（＝中央正方形に切っても、
  数字と人物が両方残る構図にする）
- 画像の端から100px以内には意味のある要素を置かない
  （右下の「SNS反応まっぷ」クレジット 12px --ink-45 のみ例外）

## 検収に追加
- 1280×670の全体像と、中央670×670を切り出した正方形の両方をPNGで出し、
  どちらでも「44% → 17%」と先生の顔が成立していることを確認して報告
- 幅300pxに縮小した状態（note一覧の実表示サイズ相当）でも
  「44%」「17%」が判読できるか確認
- 文字が乗っている領域の写真の最も明るい画素を基準に、
  コントラスト比を計算して報告
```

---

### 3-2. 図1｜立場の内訳（帯グラフ・人物なし）

```
本文用の図解を1点つくってください。写真は使いません。

## 出力
- note-drafts/images/bukatsu-chiiki_fig1-stance.png
- 論理サイズ 1200×380px、deviceScaleFactor: 2
- 背景は共通仕様のカードスタイル
  （linear-gradient(145deg, #0C1E35 0%, #0A1928 60%, #071522 100%)、
   border-radius 16px、48px間隔の微細グリッドテクスチャ）

## データ（合計754件）
移行支持          332件  44.0%   --teal
慎重・反対        243件  32.2%   --red
条件付き・改善要求 143件  19.0%   --amber
中立・情報         36件   4.8%   --gray

## レイアウト
- 見出し「SNS公開投稿 754件の立場」（22px / weight 700 / --ink）
- 横1本の積み上げ帯グラフ（高さ56px、border-radius 8px）
  - 比率どおりに配置、区分どうしは2pxの隙間
  - 帯の中に「44.0%」「32.2%」「19.0%」を直接置く（13px / weight 700 / 濃い文字色）
  - 4.8%は帯が細いので帯内に置かず、凡例側にのみ表示
- 帯の下に凡例を横1列（10×10pxの角丸ドット＋ラベル＋件数）

## 注意
この図は「まあそうだよね」と頷かせる図です。派手にしないでください。
記事の山は次の図2なので、意図的に静かに作ります。
```

---

### 3-3. 図2｜論点別の支持率（★記事の山・人物なし）

```
本文用の図解を1点つくってください。この記事で最も重要な図です。写真は使いません。

## 出力
- note-drafts/images/bukatsu-chiiki_fig2-issue-support.png
- 論理サイズ 1200×760px、deviceScaleFactor: 2
- 背景は図1と同じカードスタイル

## データ（横棒グラフ。値は「その論点の投稿のうち、移行支持だった割合」）
教員の働き方         227件   59.9%
制度・移行プロセス    171件   45.0%
教育的意義・機会      144件   41.7%
受け皿・指導者        100件   30.0%
費用・家庭負担         72件   16.7%

## 色の決め方（重要）
量の大小を見せる図なので、色は1色（teal）の濃淡だけを使います。
- 59.9% → #2DD4BF（最も濃い）
- 45.0% → #2DD4BF 不透明度78%
- 41.7% → 同72%
- 30.0% → 同52%
- 16.7% → 同30%（最も薄い）

複数の色相を使わないでください。
費用・家庭負担を赤で「悪い」と表現しないでください。
編集上の評価ではなく、数値の大小だけを見せます。

## レイアウト
- 見出し「論点別に見た『移行支持』の割合」（22px / weight 700 / --ink）
- 小見出し「母集団はすべて同じ754件。分け方を変えただけです」（15px / --ink-70）
- 横棒5本、棒の高さ48px、間隔16px、すべて同じ左端から開始
- 左に論点名（16px / --ink）とその下に件数（13px / --ink-45）
- 棒の右端の角丸4px、左端は角丸なし
- 棒の右隣に数値を直接（20px / weight 900 / tabular-nums）
  - 最上段の59.9%だけ --teal、最下段の16.7%だけ --red、残り3つは --ink-70
- x軸目盛は 0/20/40/60% の4本だけ、rgba(255,255,255,0.06) の細線
- 凡例なし（1系列のため）

## 記事の核心を伝える注記（必須）
最上段と最下段をつなぐ縦のブラケットを引き、脇に置く:

    3.6倍
    同じ754件の中での開き

（「3.6倍」は28px / weight 900 / --amber、説明文は14px / --ink-70）

このブラケットが図の主役です。読者が最初に目を留めるべきは
個々の棒ではなく「上と下の落差」であることが伝わるようにしてください。

## 注記（最下部・12px / --ink-45）
※このほか「その他」35件、「地域格差」5件があります
```

---

### 3-4. 図3｜渡す側と受け取る側（★人物あり）

```
本文用の概念図を1点つくってください。写真を2枚使います。

## 出力
- note-drafts/images/bukatsu-chiiki_fig3-give-receive.png
- 論理サイズ 1200×680px、deviceScaleFactor: 2

## 素材
- 左パネル: note-drafts/photos/teacher-staffroom.png
- 右パネル: note-drafts/photos/parent-car.png

## 伝えたいこと
同じ「部活動の地域移行」について、負担を手放す側の話をしている人と
受け取る側の話をしている人がいて、その間で受け渡しがまだ成立していない、という構造。

## レイアウト（左右2パネル＋中央の断絶）
2つのパネルは完全に同じサイズ・同じ構造にしてください。対比が一目で分かることが命です。

各パネル:
- 写真を上半分に敷き（高さ約240px、object-fit: cover）、
  下端から上へ効く暗色グラデーションで下半分の文字領域へつなぐ
- パネル全体の背景 rgba(255,255,255,0.05)、border-radius 12px
- 左端に3pxのアクセントライン（左パネル=--teal、右パネル=--red）

左パネル（--teal）:
  ラベル小: 負担を手放す側        13px / --ink-45 / letter-spacing .1em
  見出し:   教員の働き方          20px / weight 700 / --ink
  数値:     支持 59.9%            36px / weight 900 / --teal
  補足:     227件の投稿           14px / --ink-45
  一言:     「学校の中だけでは、もう支えきれない」  15px / --ink-70

右パネル（--red）:
  ラベル小: 負担を受け取る側
  見出し:   費用・家庭負担
  数値:     支持 16.7%            36px / weight 900 / --red
  補足:     72件の投稿
  一言:     「月額8000円、子ども3人で年28万8000円」

中央（この図の主役）:
- 左パネルから右へ向かう矢印（--teal、線幅3px、実線）
- 右パネルから左へ向かう矢印（--red、線幅3px、実線）
- 2本は向き合うが、中央で40pxほどの隙間を空けて途切れさせる
- 隙間に点線の縦線を引き、その脇に:
      まだ受け渡しが
      成立していない
  （16px / weight 700 / --amber）

## 注意
- 「一言」は投稿の直接引用ではなく編集部の要約です。鉤括弧付きで小さめに
- 矢印は太くしすぎない。中央の断絶が主役です
- 写真の上に文字を置く場合は、必ずグラデーションのざぶとんを敷く
```

---

### 3-5. 図4｜先生・保護者・自治体の三すくみ（★人物あり）

```
本文用の概念図を1点つくってください。写真を3枚使います。

## 出力
- note-drafts/images/bukatsu-chiiki_fig4-standoff.png
- 論理サイズ 1200×820px、deviceScaleFactor: 2

## 素材（すべて1:1）
- note-drafts/photos/person-teacher.png
- note-drafts/photos/person-parent.png
- note-drafts/photos/person-official.png

## 伝えたいこと
3者とも部活をなくしたいとは言っていないのに前へ進まない。
賛否が割れているからではなく、引き取り手が決まっていないから。

## レイアウト（正三角形の配置）
上の頂点=先生／左下=保護者／右下=自治体

各頂点のカード（3枚とも完全に同じサイズ・同じ構造）:
- 写真を直径96pxの円形にクロップして上部に配置
  （border: 2px solid、色はそのカードのアクセント色）
- カード本体: 角丸12px、背景 rgba(255,255,255,0.06)、上端に3pxのアクセントライン
- 円の下に3行:

  先生    ／ --teal
    渡したい                    24px / weight 900 / --teal
    土日の指導と引率を、これ以上は担えない   15px / --ink-70

  保護者  ／ --red
    受け取れない                24px / weight 900 / --red
    会費と送迎を、家庭では引き受けきれない

  自治体  ／ --amber
    用意しきれない              24px / weight 900 / --amber
    指導者も予算も、まだ揃っていない

## 三角形の辺
3枚のカードを結ぶ辺を双方向矢印で描く。
線は rgba(255,255,255,0.18)、線幅2px。各辺の中央に小さく「?」（--ink-45）。

## 中央
三角形の中心に角丸の領域を置き、中に:

    引き取り手が
    決まっていない

（26px / weight 900 / --ink、背景 rgba(251,191,36,0.10)、
 border 1px solid rgba(251,191,36,0.35)）

## 注意
- どれか1者を悪者に見せる表現にしないこと。
  線の太さ・色の強さ・写真の大きさを3者で完全に揃えてください
- 中央の領域が三角形の辺と重ならないよう十分な余白を取る
```

---

## 4. 最後にまとめて確認してもらうこと

```
5点すべて完成したら、以下を確認して報告してください。

1. 5枚を並べたコンタクトシート（1枚のPNG）をつくり、
   写真のトーン・フォント・余白の取り方が揃っているか目視確認する
2. 各PNGのファイルサイズを報告（10MB以内。超えるものは画質を落とさず圧縮）
3. 見出し画像は1920×1006px、本文図解は横1200px（実ピクセル2400px）か確認
4. 幅375pxのモバイル表示を想定して縮小し、読めなくなる文字がないか確認。
   あれば文字を大きくして作り直す
5. 写真の上に置いたすべての文字について、コントラスト比を計算して一覧で報告
6. 生成写真に文字（日本語・英語・数字）が紛れ込んでいないか、
   5枚すべてを拡大して確認する
7. note-drafts/figures/render.mjs で5枚すべて再生成できる状態か確認
```

---

## 5. シリーズ4本の写真プラン

同じ人物ばかりだと4本が単調になります。回ごとに主役を変えます。

| 回 | 見出し画像の人物 | 情景 |
|---|---|---|
| 第1回 総論 | 先生（カメラ目線） | 夕方の体育館の入口 |
| 第2回 先生編 | 先生（横顔・別カット） | 夜の職員室 |
| 第3回 お金と送迎編 | 保護者（カメラ目線） | 夕暮れの車内 |
| 第4回 子どもと自治体編 | 自治体職員＋子どもの後ろ姿 | 市役所の窓口／校門 |

写真のトーン（スタイル・ロック）は4本とも同一にして、**マイページで並んだときにシリーズと分かる**ようにします。

---

## 付記1｜配色の検査結果（正直な注記）

カラートークンは既存の SNS反応まっぷ のテーマをそのまま使っています。標準的なパレット検査の結果はこうでした。

| 検査項目 | 結果 |
|---|---|
| 色覚多様性での識別（隣接ペア） | PASS（最悪ペアで ΔE 10.7） |
| 通常視力での識別 | PASS（ΔE 21.2） |
| 背景とのコントラスト | PASS（4色すべて 3:1 以上） |
| 明度バンド | FAIL（暗い背景に対して明るすぎる） |
| 彩度の下限 | FAIL（#64748B が灰色に見える） |

**この2つのFAILは今回は許容します。**

- 明度バンドのFAILは「暗い背景に明るい色を置く」という既存テーマの設計そのもので、ここだけ変えるとシリーズ4本とサイト本体で見た目が割れます
- #64748B のFAILは「中立・情報」というグレーであるべき区分に当てているためで、意図どおりです

そのうえで識別を色だけに頼らないよう、全図で **数値の直接ラベル** と **2pxの塗り分け隙間** を必須にしています。

## 付記2｜AI生成画像の扱い

- 日本ではAI生成物に著作権が認められないケースが多く、**この画像に独占的な権利は主張できない**前提で使います
- 特定のクリエイターの画風を指示していないこと、実在の人物・学校・ブランドを含まないことを、生成のたびに確認してください
- 記事末のデータ注記に、1行だけ添えることを推奨します:
  「※記事中の写真はAIで生成した架空の人物・情景です」
  中立の集計サイトとして、写真が実際の取材ではないことを明示しておくほうが安全です

## 付記3｜暖色パターンのA/Bテスト（あとで）

リサーチには「オレンジ・黄など暖色背景のほうがクリック率が高い」というデザイナー分析がありましたが、少数サンプルで、シンプル志向のnoteにそのまま当てはまるとは限りません。

**第3回（お金と送迎編）だけ暖色版の見出し画像**を試し、スキ率（スキ÷ビュー）で比較するのが安全な検証方法です。第1回はシリーズの基準として、既存テーマの紺＋tealで作ります。

## 付記4｜元データの出典

すべての数値は正典 `social-samples/bukatsu-chiiki_hermes_classified.json` の754件（is_opinion かつ is_relevant）を論点×立場でクロス集計した結果です。図の数値を変更する場合は、必ずこのファイルから数え直してください。
