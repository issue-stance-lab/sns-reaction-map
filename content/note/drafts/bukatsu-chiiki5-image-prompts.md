# note第5回「学習指導要領を読む」｜画像作成プロンプト（ChatGPT / Codex 用）

作成日: 2026-09-08
対象記事: `content/note/drafts/bukatsu-chiiki-note5-FINAL.md`
第1回のプロンプト集は `content/note/drafts/bukatsu-chiiki-image-prompts.md`、
第2回は `content/note/drafts/bukatsu-chiiki2-image-prompts.md`、
第3回は `content/note/drafts/bukatsu-chiiki3-image-prompts.md`。
共通仕様（配色トークン・文字サイズ・幅800pxのルール）はそこから引き写している。
**共通仕様を直すときは4ファイルとも直すこと。**

第4回（`bukatsu4_*`）はプロンプト集を残さずに作った。図のHTMLは
`content/note/drafts/figures/bukatsu4_fig2-kyoto-kobe.html` が見た目の見本になる。

---

## 今回作るもの（3点）

| ファイル | 内容 | 人物 |
|---|---|---|
| `content/note/drafts/images/bukatsu5_note-header.png` | 見出し画像。主役は「消えません」 | あり（教員） |
| `content/note/drafts/images/bukatsu5_fig1-history.png` | 学習指導要領における部活動の記載の変遷（昭和33年〜令和8年度末） | なし |
| `content/note/drafts/images/bukatsu5_fig2-schedule.png` | 次期学習指導要領に向けた工程 | なし |

写真の主役はシリーズで一巡している（第1回=先生・夕方の体育館、第2回=先生・土曜の朝、
第3回=保護者・送迎、第4回=自治体職員）。**第5回は先生に戻す。**
ただし場面は体育館ではなく、職員室で分厚い冊子を開いている場面にする。
記事が扱うのが「文書」だから。

---

## この回だけの重大な注意（最初に読むこと）

**この記事にはSNS投稿の集計が1件も出てきません。** 第1〜4回と決定的に違う点です。
図に載る数字は、年号・西暦・年度だけです。

- **年号・西暦・年度を、勝手に足さない。勝手に変えない。丸めない。**
  下の表に書いてある値だけを使うこと。「たぶん昭和43年頃」のような補完は禁止
- 件数・パーセント・グラフの棒は**一切登場しません**。棒グラフを作らないこと
- 「予定」「素案」と書いてある行は、**確定した事実と見分けがつく描き分け**にする
  （破線・淡い色・「予定」ラベルのいずれか。第1〜4回の `--amber` を使う）

理由: この記事は一次資料（学習指導要領・国の会議資料・国会答弁）だけで組んでいます。
本文は2026-09-07に原文照合まで済ませてあります。図の年号が1つでもずれると、
記事全体の裏づけが崩れます。

---

## 0. 共通仕様（最初にこれを渡してから、各プロンプトを渡す）

```
これから note 記事用の画像を3点つくります。まず共通仕様を渡します。
以降の指示はすべてこの共通仕様に従ってください。

## いちばん重要なルール（この回だけ第1〜4回と違います）

この記事にSNS投稿の集計は出てきません。図に入る数字は年号・西暦・年度だけです。
渡した表に書いてある値だけを使ってください。書いていない年を補完しないでください。
件数・パーセント・棒グラフは作りません。

「予定」「素案」の行は、確定した行と見分けがつくように描き分けてください
（破線の枠、または amber 系の色、または「予定」ラベル）。

## 方式
人物の写真は生成し、その上に HTML/CSS で文字を重ねます。
図1・図2は写真を使わず、HTML/CSS だけで組みます。
写真そのものを加工したり、文字を画像として生成したりはしないでください。

## 実装方法
- 1画像 = 1つの自己完結したHTMLファイル（CSSはインライン、外部JSなし）
- 写真は <img> または background-image で読み込む
- レンダリングは Playwright（Chromium）で該当要素をスクリーンショットしてPNG化
- フォントは Google Fonts の Noto Sans JP（weight 400/500/700/900）
- 数字には font-variant-numeric: tabular-nums を必ず指定
- 写真入力: content/note/drafts/photos/
- HTML出力: content/note/drafts/figures/<名前>.html
- PNG出力:  content/note/drafts/images/<名前>.png
- content/note/drafts/figures/render5.mjs にまとめ、3点を一括再生成できるようにする
  （render.mjs / render2.mjs / render3.mjs / render4.mjs は上書きしないこと）

## カラートークン（既存のSNS反応まっぷのテーマ。変更しないこと）
--page:    #07111E
--card-1:  #0C1E35
--card-2:  #0A1928
--card-3:  #071522
--ink:     #F0F4FF
--ink-70:  rgba(240,244,255,0.70)
--ink-45:  rgba(240,244,255,0.45)
--teal:    #2DD4BF   /* 主役アクセント／記載がある期間 */
--red:     #F87171   /* 平成10年の全削除だけに使う */
--amber:   #FBBF24   /* 予定・素案 */
--gray:    #64748B   /* 記載なしの期間 */

カード共通スタイル:
- background: linear-gradient(145deg, var(--card-1) 0%, var(--card-2) 60%, var(--card-3) 100%)
- border: 1px solid rgba(255,255,255,0.08)
- border-radius: 16px
- 48px間隔の微細グリッドテクスチャ: rgba(255,255,255,0.025) の1px線を縦横に
- 右上に teal のごく淡いグロー: radial-gradient(circle, rgba(45,212,191,0.12) 0%, transparent 70%)
- 右下に小さく「SNS反応まっぷ」（見出し画像は20px、本文の図は24px。--ink-45, letter-spacing .08em）

## 写真の上に文字を置くときの必須処理（「ざぶとん」）
四角い半透明パネルは使わないでください。人物の顔にかかると目隠しに見えます。
必ず線形グラデーションを使います。
  linear-gradient(90deg, rgba(7,17,30,0.94) 0%, rgba(7,17,30,0.86) 42%,
                  rgba(7,17,30,0.15) 72%, rgba(7,17,30,0) 100%)
そのうえで実際のコントラスト比を計算し、大きな文字（24px以上）は3:1以上、
小さな文字は4.5:1以上を満たすことを確認して報告してください。
写真は場所によって明るさが変わるので、最も明るい画素を基準に判定します。

## 文字の大きさ（第2回から引き継ぎ・厳守）

**図の論理幅は 800px に固定します。1200pxで作らないでください。**
noteは本文の図を最大620px幅（スマホ375px）で表示するため、幅1200pxで作ると
中の文字が半分以下に縮み、スマホでは読めなくなります。

- キャンバスの論理幅: **800px**（高さは内容に合わせて伸ばしてよい。縦長は問題ない）
- 書き出し: deviceScaleFactor 3（実ピクセル 2400px幅）
- **図の中で使う最小の文字は 24px**。これより小さい文字を1つも置かない
- 役割ごとの最小サイズ

  | 役割 | 論理サイズ | スマホ375pxでの実寸 |
  |---|---|---|
  | 図の見出し | 44px / weight 700 | 20.6px |
  | 年号（見出しになる数字） | 48px / weight 900 | 22.5px |
  | 項目名・出来事 | 30px / weight 500 | 14.1px |
  | 説明・補足 | 26px | 12.2px |
  | 注記・出典 | 24px | 11.2px |

大きくするために字を小さくせず、内容を削ってください（説明文を短く、縦に伸ばす）。
**入りきらないから24pxを下回る、という判断は禁止です。**

## 作図のルール（厳守）
1. 情報を詰め込まない。余白を十分に取る
2. 罫線・区切り線は控えめに（rgba(255,255,255,0.06) 以下、1px）
3. 年号と出来事は必ず同じ行の中で対応づける。離して置かない
4. 「予定」「素案」の行は破線または amber で、確定行と描き分ける
5. テキストは白系トークンで書く。強調色を長い文章に使わない
6. コンテンツの高さに合わせてキャンバス高さを詰める（下部に大きな空白を残さない）
7. 横スクロールが要る形にしない。縦に伸ばす

## 検収（各図つくるたびに必ず）
- **図の中の最小フォントを調べ、スマホ実寸を計算して報告する。**
  計算式: 実寸 = 論理px × 375 ÷ 図の論理幅。**11pxを下回るものが1つでもあれば作り直す**
- PNGを375px幅に縮小して実際に開き、すべての文字が読めるか目で確かめる
- ラベルの重なり・はみ出し・切れがないか確認する
- 写真の上の文字のコントラスト比を計算して報告する
- **渡した表に無い年号・西暦・年度が図に入っていないことを、1つずつ照合して報告する**
- 「予定」「素案」の行が、確定行と見分けがつくことを確認する
- 何をどう直したかを具体的に報告する

質問があれば聞いてください。なければ「了解」とだけ返してください。
```

---

## 1. 人物写真の生成（1枚）

第1〜4回と**同じスタイル・ロック**を使う。シリーズ5本で写真のトーンを揃えるため。

### スタイル・ロック（プロンプトの先頭に貼る）

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

### 生成｜見出し画像用の人物（第5回・教員・書類を読む場面）

第1回は「夕方の体育館の先生」、第2回は「土曜の朝の体育館の先生」、第3回は「送迎の保護者」、
第4回は「自治体職員」。第5回は先生に戻し、**場所を職員室に、対象を分厚い冊子にする。**
記事が扱うのが文書だから。

```
[STYLE LOCK を貼る]

Subject: A Japanese schoolteacher in their 40s, seated at a desk in a middle
school staff room in the late afternoon, holding open a thick paperback
government booklet with both hands and reading it closely. The booklet is
plain, matte, unmarked — its cover and pages must be completely blank with no
readable text, no printed characters, no page numbers. The teacher's
expression is quiet and concentrated — neither worried nor pleased. Simply
reading.

Placement: The person occupies the RIGHT side of the frame, with their face
positioned roughly 60-65% across the frame from the left. The LEFT 45% of the
frame must be visually quiet — the dim staff room interior behind them, low
contrast, no distracting detail, no readable signage, no whiteboard writing.

Background: an ordinary Japanese school staff room, desks and shelves out of
focus, late afternoon light through a window on the far side. No other adults
in focus. No children in frame.

Output file name: teacher-reading-booklet.png
Aspect ratio: 1.91:1 (wide). Output at the highest resolution available.
```

生成後の確認: 手指の破綻／顔の左右非対称／**冊子の表紙や紙面に文字が写り込んでいないか**／
実在しそうな校名・ロゴ。1つでもあれば再生成してください。
冊子への文字の写り込みは、この回でいちばん起きやすい失敗です。

---

## 2. 見出し画像 `bukatsu5_note-header.png`

記事の書き出しは「部活動が学習指導要領から消える、という話をSNSで見かけます。
答えは、消えません。」です。**主役の言葉は「消えません」。**

```
[共通仕様を渡したあとに]

見出し画像を1点つくってください。

- 出力: content/note/drafts/images/bukatsu5_note-header.png
- HTML: content/note/drafts/figures/bukatsu5_note-header.html
- 写真: content/note/drafts/photos/teacher-reading-booklet.png
- 論理サイズ 1280x670 で作り、deviceScaleFactor 1.5 で撮る。
  そのあと ImageMagick で下方向に余白を足して 1920x1006 に拡張する
  （背景色 #07111E、-gravity south）。noteの見出し画像の推奨比に合わせるため
- 同じHTMLから、square（670x670）と 375px幅・300px幅の縮小版も書き出す

写真の左45%に「ざぶとん」を敷き、その上に次の3つを置く。

1. 小さく上に: 部活動の地域移行を読む 第5回
2. 主役（いちばん大きく）: 部活動は、学習指導要領から消えるのか
3. 答えとして、主役より少し小さく、teal で: 消えません

右下に「SNS反応まっぷ」。

主役の文字は weight 900。「消えません」だけを --teal にし、
ほかの文字はすべて白系トークンで書く。
パーセント・件数は一切置かない。
```

---

## 3. 図1 `bukatsu5_fig1-history.png`｜記載の変遷

本文中の位置: 「▼［図1：学習指導要領における部活動の記載の変遷］」の行を置き換える。

**縦の年表にすること。** 横一本の時間軸にすると、8つの年号がスマホで潰れて読めなくなる。

```
[共通仕様を渡したあとに]

図を1点つくってください。学習指導要領で部活動がどう書かれてきたかの年表です。

- 出力: content/note/drafts/images/bukatsu5_fig1-history.png
- HTML: content/note/drafts/figures/bukatsu5_fig1-history.html
- 論理幅 800px の縦長。高さは内容に合わせる
- 縦に流れる年表。左に年号、右に出来事。1行1改訂
- 見出し: 部活動は、学習指導要領にこう書かれてきた

行はこの8つだけ。ここに無い年を足さないこと。

| 年 | 西暦 | 何が起きたか | 色 |
|---|---|---|---|
| 昭和33年 | 1958 | 部活動の記載なし。全員参加の「クラブ活動」があった | gray |
| 昭和44年 | 1969 | 部活動の記載なし | gray |
| 昭和52年 | 1977 | 部活動を想定した記載が入る | teal |
| 平成元年 | 1989 | 「部活動」の語が初めて載る。クラブ活動の代わりに実施してよい、という条件つき | teal |
| 平成10年 | 1998 | クラブ活動の廃止に伴い、部活動の記載も一旦すべて消える | red |
| 平成20年 | 2008 | 独立した記載として復活 | teal |
| 平成29年 | 2017 | 「持続可能な運営体制」を追加（現行の要領） | teal |
| 令和8年度末 | 2026年度末 | 告示の予定。部活動と地域クラブ活動の双方を記載する方向（素案段階） | amber・破線 |

描き分け:
- gray の2行は、記載が無かった期間だと分かるように、他より落とす
- 平成10年の行だけ red。この記事でいちばん重い1行なので、少し目立たせてよい
- 令和8年度末の行は破線の枠にし、行末に「予定」ラベルを置く。確定と読ませない
- 「現行の要領」は平成29年の行にだけ書く

注記（24px、--ink-45）:
※令和8年度末は予定。中央教育審議会の審議まとめは2026年9月時点で素案であり、
答申・告示までに文言が変わる可能性があります。

右下に「SNS反応まっぷ」。
```

---

## 4. 図2 `bukatsu5_fig2-schedule.png`｜次の改訂の工程

本文中の位置: 「▼［図2：次期学習指導要領に向けた工程］」の行を置き換える。

```
[共通仕様を渡したあとに]

図を1点つくってください。次の学習指導要領が実際に使われるまでの工程です。

- 出力: content/note/drafts/images/bukatsu5_fig2-schedule.png
- HTML: content/note/drafts/figures/bukatsu5_fig2-schedule.html
- 論理幅 800px の縦長。上から下へ流れる工程図
- 見出し: 次の学習指導要領が中学校で使われるまで

段はこの6つだけ。ここに無い工程・年を足さないこと。

| 段 | 時期 | 状態 |
|---|---|---|
| 審議まとめ（素案） | 令和8年8月31日 | 済。ただし素案 |
| 答申 | 令和8年冬頃 | 予定 |
| 告示 | 令和8年度末 | 予定 |
| 周知 | 告示のあと | 予定 |
| 先行実施 | 周知のあと | 予定 |
| 全面実施（中学校） | 令和13年度（2031年度） | 予定 |

描き分け:
- 「審議まとめ（素案）」の段だけ teal。ここまでは実際に起きたこと
- 残り5段はすべて amber の破線。全部まだ予定である、と一目で分かるようにする
- いちばん下の「全面実施（中学校）令和13年度（2031年度）」は、
  この図でいちばん大きい数字として置く。読者がいちばん知りたいのは「いつからか」なので
- 段と段は細い縦線でつなぐ。矢印は1本の細い線で十分。装飾しない

注記（24px、--ink-45）:
※中央教育審議会教育課程企画特別部会「改訂スケジュール（イメージ）」（令和8年7月8日）、
同「次期学習指導要領等に向けた審議まとめ（素案）」（令和8年8月31日）より。
審議まとめは素案段階で、答申・告示までに変わる可能性があります。

右下に「SNS反応まっぷ」。
```

---

## 5. 貼り付け（人がやる）

図が出来上がったら、note の下書き（`https://editor.note.com/notes/n6ec8c2a71ef0/edit/`）で
次の2行を置き換える。

| 本文中の目印 | 置き換えるPNG |
|---|---|
| `▼［図1：学習指導要領における部活動の記載の変遷］` | `images/bukatsu5_fig1-history.png` |
| `▼［図2：次期学習指導要領に向けた工程］` | `images/bukatsu5_fig2-schedule.png` |

見出し画像は note の記事上部（アイキャッチ）に `bukatsu5_note-header.png` を設定する。

図を貼ったあと、**スマホ幅で1回読み返すこと。** 第2回で、図の文字が小さすぎて
読めない状態のまま公開しかけている。
