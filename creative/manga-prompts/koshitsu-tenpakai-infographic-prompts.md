# 皇室典範改正 — 個別論点インフォグラフィック生成プロンプト

共通スタイル: `creative/manga-prompts/infographic-style-guide.md` の **7. 個別論点画像テンプレ** を使用する。

基準テイスト: 副首都ページの `docs/images/topics/fukushuto/fukushuto-infographic-*.webp` と同じ、明るい civic-tech インフォグラフィック。白〜淡い水色背景、濃紺・鮮やかな青の見出し、角丸カード、柔らかい影、ドット・スパークル・グラフ風アクセントを使う。実在の皇族・政治家・政党ロゴ・政府エンブレムは描かない。

## 保存先

生成後 WebP に変換、各ファイルは `900x900` 目安、100KB以下を目標にする。

```
docs/images/topics/koshitsu-tenpakai/
├── koshitsu-infographic-kouseki.webp
├── koshitsu-infographic-yoshi.webp
└── koshitsu-infographic-keisho.webp
```

---

## 1. 女性皇族の皇籍維持

**ファイル名:** `koshitsu-infographic-kouseki.webp`

```text
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「女性皇族の皇籍維持」

Main title:
「女性皇族の皇籍維持」
「結婚後も皇族に残るとは？」

Core message:
女性皇族が結婚後も皇族として活動できる道を開く改正。皇族数の確保につながる一方で、配偶者・子の扱いと皇位継承権の線引きが論点になる。

Composition:
Center:
簡略化した家系図。実在人物の顔ではなく、男女の中立的なシルエットアイコンを使う。女性皇族のシルエットが「結婚」の矢印を通っても、淡い青の枠「皇族」の中に残る構図。配偶者・子のアイコンには小さな「？」マークを付ける。

Around the center, place 4 rounded check cards:
1. 「結婚後も活動」 「公務の担い手を確保」
2. 「配偶者の扱い」 「皇族になるのか？」
3. 「子の扱い」 「次世代まで残るのか？」
4. 「継承権」 「皇位継承とは別論点」

Bottom conclusion band:
「皇族数の確保と、継承制度の線引きが焦点」

Use the common “SNS反応まっぷ civic-tech infographic style”.
```

---

## 2. 旧宮家男系男子の養子制度

**ファイル名:** `koshitsu-infographic-yoshi.webp`

```text
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「旧宮家男系男子の養子制度」

Main title:
「旧宮家男系男子の養子制度」
「誰を皇族に迎えるのか？」

Core message:
旧宮家の男系男子を養子として皇族に迎える制度。男系維持の手段として評価される一方、戦後に皇籍を離れた家系をどう位置づけるか、正統性や合憲性が争点になる。

Composition:
Center:
左右に2つの家系図ブロックを置く。左は「旧宮家」、小さなタイムラインで「戦後に皇籍離脱」。右は「皇室」。左の男系男子シルエットから右の皇室ブロックへ、青い矢印「養子」でつなぐ。中央下に書類アイコンと天秤アイコンを置き、制度設計・法的論点を示す。

Around the center, place 4 rounded check cards:
1. 「戦後に離脱」 「現在は皇族ではない」
2. 「男系男子」 「男系維持の候補」
3. 「養子で復帰」 「制度設計が必要」
4. 「法的論点」 「正統性・合憲性」

Bottom conclusion band:
「皇統維持の手段か、制度上の無理筋か」

Use the common “SNS反応まっぷ civic-tech infographic style”.
```

---

## 3. 男系維持 vs 女系容認

**ファイル名:** `koshitsu-infographic-keisho.webp`

```text
Create a polished 1:1 square Japanese infographic.

Theme:
皇室典範改正 の個別論点「男系維持 vs 女系容認」

Main title:
「男系維持 vs 女系容認」
「何が対立しているのか？」

Core message:
対立は単純な賛否ではなく、皇位継承を男系に限るのか、女系も認めるのかという制度設計の違い。女性天皇と女系天皇の区別も、議論の入口になる。

Composition:
Center:
左右比較の図解。左側は「男系維持」として、父方の線が続くシンプルな縦型家系ラインと巻物アイコン。右側は「女系容認」として、男女両方のシルエットが並ぶ継承ラインと政策文書アイコン。中央に小さな中立カード「女性天皇と女系天皇は別論点」を置く。

Around the center, place 4 rounded check cards:
1. 「男系維持」 「父方の血筋を重視」
2. 「女系容認」 「性別にかかわらず継承」
3. 「女性天皇」 「男系の女性が即位」
4. 「安定継承」 「将来世代まで続くか」

Bottom conclusion band:
「伝統の継続と安定継承をどう両立するか」

Use the common “SNS反応まっぷ civic-tech infographic style”.
```

---

## 【生成済み 2026-08-02】争点⑤ 愛子さま・皇族の地位（wide 21:9）

`docs/images/topics/koshitsu-tenpakai/koshitsu-infographic-wide-aiko.webp`（1916×821px・140KB）
PNGから `cwebp -q 80` で変換（同フォルダのwide図解は133〜141KB）。

初版は中央下の注記カードに「サンプル17件」と件数を焼き込んでいたため、同日中に修正版へ差し替えた。
現行版は画像内に数値を一切持たない。

**ファイル名:** `koshitsu-infographic-wide-aiko.webp`

```text
Create a polished Japanese infographic.

Theme:
皇室典範改正 の個別論点「愛子さま・皇族の地位」

Main title:
「愛子さま・皇族の地位」
「制度と国民感情のあいだ」

Core message:
皇族個人の地位や将来をめぐる議論。継承順位は制度が定めるものだが、国民感情との隔たりも指摘される。

Composition:
Center:
天秤の図解。左の皿に「制度・法の定め」を表す巻物と条文アイコン、右の皿に「国民感情・世論」を表す人々のシルエット群。天秤はわずかに傾き、どちらにも振り切れていないことを示す。中央下に小さな注記カード「継承順位は制度が定める」。

Around the center, place 4 rounded check cards:
1. 「制度が定める」 「継承順位は法の問題」
2. 「世論の支持」 「人気は制度を変えない」
3. 「皇籍の維持」 「結婚後も皇族に残るか」
4. 「次世代の扱い」 「子の身分は未確定」

Bottom conclusion band:
「制度の線引きと国民感情の距離をどう扱うか」

IMPORTANT: Do not render any number, count, percentage, or sample size in the image.
件数・サンプル数・割合は画像に一切入れないこと（ページ側が分類結果から自動表示するため）。

Use the common “SNS反応まっぷ civic-tech infographic style”.
Output image: wide, 21:9 aspect ratio (e.g. 1916×821px).
```

---

### 納品後の手順

1. PNGを `docs/images/topics/koshitsu-tenpakai/` に置く
2. WebP変換: `cwebp -q 80 <入力>.png -o <出力>.webp`（q=80で136〜140KB、既存と揃う）
3. PNGを削除（このフォルダはWebPのみ）
4. `python3 scripts/build_koshitsu_arena.py --check` と
   `python3 scripts/verify_theme_page.py koshitsu-tenpakai` が exit 0

---

## 図解を作るときの共通ルール

**件数・パーセント・サンプル数を画像に焼き込まない。**
数字は分類結果から `scripts/sync_issue_counts.py` が生成し、
論点カードの `explainer-count` バッジとして表示される。
画像に入れると、データ補充のたびに画像だけが取り残される。

「最多の論点」「件数は少ない」といった**程度を表す言い回しも、できるだけ画像に入れない**。
数値ほど壊れやすくはないが、データが動けば同じように嘘になる。

---

### 参考: 争点④の図解タイトルとのズレ（別件・未対応）

争点④のカード名は `女性天皇と女系天皇の違い`（正典ラベル `女性天皇・女系天皇`）に変わったが、
流用している `koshitsu-infographic-wide-josei-tenno.webp` の焼き込みタイトルは「女性天皇・愛子天皇」のまま。
争点⑤で愛子さまを別カードに分けたので、余裕があれば争点④の図解も
「女性天皇と女系天皇の違い」のタイトルで作り直すと、カードと図解の呼称が揃う。
