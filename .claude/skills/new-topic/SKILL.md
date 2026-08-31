---
name: new-topic
description: 新しいテーマ（トピック）を1本、選定から公開まで追加するための手順。「新テーマを追加して」「◯◯のページを作って」「次のトピックを選んで収集して」「テーマを増やしたい」「トレンドから話題を拾ってページにして」といった作業では必ずこのスキルを読むこと。公開後に人が画面を見るまで気づけない壊れ方（ヒートマップが隠れる／投票のやり直しボタンが無い／モバイルでヘッダーが崩れる／AdSense審査対象のルートに載らない）が毎回同じ場所で起きている。新テーマのページ更新スクリプトは「同じ入力で2回実行しても差分が出ない」adapter形式で作ること（課題34、`THEMES.yaml` の `page_update_mode` で確認する）。会社の理念・権限・CEO承認範囲は `company/COMPANY.md` と `AI_HANDOFF.md` に従うこと。既存テーマへのデータ追加は対象外で、そちらは DATA_REFRESH.md を見ること。
---

# 新テーマの追加

## この作業で本当に危ないこと

新テーマは「作れた」ことが分かりやすい作業なので、公開までは順調に見える。
問題は**公開したあとに現れて、しかも検査に映らない**。

過去11テーマで実際に起きたのは次の2種類。

**① 一度きりのページを作ってしまう（最も高くつく）**

ページ生成スクリプトを「今回のHTMLを出す」ためだけに書くと、次の更新で再実行できない。
`build_consumption_tax_page.py` は生成済みページに再実行すると `ValueError: substring not found` で落ちる。
結果、11テーマ中**adapter（自動更新できる）は4本だけ**で、残り7本は更新のたびに
`DATA_REFRESH.md`「更新後の画面チェックリスト」の約30項目を人が手で追っている。新テーマを足すたびにこの負債が1本増える。

→ **⑥で「同じ入力で2回実行して差分ゼロ」を確認するまで公開しない。**

**② 人が画面を見るまで気づかない壊れ方**

| 壊れ方 | どこで起きたか |
|---|---|
| ヒートマップが真っ白なキャンバスに隠れる | CSS特異度。`#stance-map-section canvas`(101) が `#canvasMain`(100) に勝つ |
| 別タブから戻るとヒートマップが永久に出ない | `drawHeatmap()` にアニメーション状態のフィルターを入れた |
| 投票後に「やり直す」「シェア」が出ない | constitutional-amendment（2026-07-26発覚）。カスタム投票UIで欠落 |
| ヒーロー画像が生成AI著作権テーマの絵になる | `--topic-hero-image` 未指定時のCSSフォールバック |
| 375px でヘッダーのボタンがはみ出す | ロゴ+gap+Xアイコン+ボタンが375pxを超える |
| 審査対象のトップに新テーマが載らない | AdSenseが見ているのは**別リポジトリのルート**（課題15） |

検査スクリプトはどれも通る。だから⑦の実機確認を省かない。

---

## 進め方

### ⓪ 作業場所を用意する

```sh
git worktree add ../isa-wt-{slug} -b task/{slug}
cd ../isa-wt-{slug}

# 非公開の正典（gitignore対象なので worktree には入らない）
tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" \
  -C . --exclude=manifest.json

# 収集ツール（node_modules も gitignore 対象）
cp -R ../issue-stance-aggregator/node_modules .
```

この2つは**入っていないことが `git status` に出ない**。
`node_modules` が無いと収集が最初の疎通確認で `Cannot find package 'playwright'` で止まる。
正典が無いとテストが落ちて、自分の変更のせいだと誤診する。

着手前のベースラインを取っておく（後で「自分が壊したのか元からか」を切り分けるため）。

```sh
python3 -m unittest discover -s tests ; echo "exit=$?"
python3 scripts/verify_top_page.py ; echo "exit=$?"
```

### ① テーマを選ぶ（収集の前に3分で捨てる）

**向くもの**: 規制・権利・ルールのトレードオフがあり、好き嫌いではなく賛成/反対の構造がある話題。
**向かないもの**: 推し活、味覚・趣味、感想が主の話題。**戦争関連は除外**（課題13）。

小さく1回引いて、機械に判定させる。

```sh
node scripts/fetch_yahoo_realtime_node.mjs --query "候補キーワード" --output /tmp/judge.json
python3 scripts/trend_judge.py --input /tmp/judge.json
```

`total_available` が100件未満なら**即見送り**。ここで粘らない。
消費税減税は trend_judge スコア 9/10 で通した（意見率100%・投稿量2・対立性2・SEO需要2・広告安全性1）。

### ② 検索クエリを設計する（ここの出来で分類成功率が4倍変わる）

**最大の罠は「キーワードが日常会話でも使われる」こと。**

| ❌ | ✅ |
|---|---|
| 「学校 あだ名」→ 思い出話が混入 | 「あだ名禁止 賛成 OR 反対 OR やりすぎ」 |
| 「ライブ スマホ 撮影」→ 写真シェアが混入 | 「ライブ 撮影禁止 賛否」 |

- 意見誘発語を入れる（賛成 OR 反対 OR やりすぎ OR おかしい）
- 制度語を入れる（禁止・規制・義務化・廃止）
- **賛成側と反対側の両方のクエリを作る**（偏り防止）
- 合計8〜20クエリ

実績: あだ名禁止（旧方式）112件中17件分類成功=**15%**、生成AI著作権（改善版）475件中339件=**71%**。
消費税減税は20クエリで667件・意見率91.8%。

確定したクエリは `configs/topics/{slug}.yaml` の `fetch_queries` に**そのまま**書く。
潮目ウィジェットは次回以降これと同じ条件で引いた結果と比較するので、**後から変えない**。

### ③ 収集する

```sh
node scripts/fetch_yahoo_realtime_node.mjs \
  --query "..." --query "..." \
  --output social-samples/{slug}_raw.json --dedupe --wait-ms 6000
```

重複判定は tweet_id → URL内status ID → URL → 本文ハッシュの順。除外した件数を控える（THEMES.yaml の `notes` に書く）。

**`fetched_at` が全件に入っていることを確認する。** ここが欠けると `sample_period`（取得期間）を
後から復元できず `unknown` のまま残る。現在5テーマが `unknown` で埋められないままになっている（課題28）。
**推測で埋めない。** 分からないものは `unknown` のまま、ページに「取得期間: 記録なし」と正直に出す。

### ④ 論点体系を決めて分類する

`scripts/{slug}_taxonomy.py` を作る。**これが論点の唯一の定義**で、ページもテストもここを見る。

- 論点（`main_issue`）は6〜7個 + その他。多すぎると投票の選択肢が爆発する
- 立場（stance）は3つか4つ。**「賛成だが政府案には不満」のような中間が出る話題は4つにする**
  （消費税減税は3スタンスでは表現できず4スタンスにした。アリーナの点の色も
  x座標ベースではなく立場インデックスベースに変えている）

分類器は既存テーマのものを写して作る（`scripts/classify_{既存}_arena_hermes.py`）。

**全件を流す前に必ず10〜12件で試す。** 1件5〜6秒なので、600件なら1時間。
綴りミスで1時間を捨てないための工程。

```sh
python3 scripts/classify_{slug}_arena_hermes.py \
  --input social-samples/{slug}_raw.json \
  --output social-samples/{slug}_hermes_arena_classified.json --limit 12
```

出力の `main_issue` が**自分の決めたラベルだけ**になっているか見る。
1つでも体系外が出たらプロンプト（`ISSUE_DEFS` の説明文）を直してやり直す。
問題なければ `--resume` で続きを流す（12件は無駄にならない）。

長時間かかるので裏で流すことになるが、**終わったら即コミットする。**
未追跡のまま置いた分類結果は worktree の掃除で消える（fukushuto で1ヶ月放置され、
危うく「不要ファイル」として消されかけた）。

### ⑤ ページを作る

**先に既存テーマを1つ選んでテンプレートにする。** ゼロから書かない。
消費税減税は副首都ページを元に生成した。

必ず入れるもの:

- **保護タグ** — GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase投票 / OGP meta
- **ヒーロー画像を `body` の inline style で指定する** — `--topic-hero-image` を書かないと
  `topic-modern.css:111` のフォールバックで生成AI著作権のヒーロー画像が出る
- **投票の完了画面に「𝕏 でシェア」と「投票をやり直す」** — `vote2d.js` を使うテーマは
  `vote-result` div の中に `<a id="share-x">` と `<button id="vote-redo-btn">` があれば
  vote2d.js が動的生成する。カスタムUIを書く場合は自分で `r.innerHTML` に入れる
- **2Dスタンスマップ**を載せるなら下の「2Dスタンスマップの実装」を読んでから書く
- **背景解説セクション**（`configs/{slug}-reaction-map.json` の `background`）— AdSense審査で
  「有用性の低いコンテンツ」と判定された過去があるので省かない

**件数をHTMLに直接書かない。** トップの数値は `THEMES.yaml` の `sample_file` の実レコード数から
生成される。論点カードの件数は `python3 scripts/sync_issue_counts.py {slug}` で入れる。

### ⑥ 生成スクリプトを「2回実行して差分ゼロ」にする ⛔

**ここを通らないうちは公開しない。** 上の①「一度きりのページ」を作らないための関門。

```sh
python3 scripts/build_{slug}_page.py --output /tmp/a.html
python3 scripts/build_{slug}_page.py --output /tmp/b.html
diff /tmp/a.html /tmp/b.html && echo "冪等OK"
# さらに、生成済みページに対してもう一度流して落ちないこと
python3 scripts/build_{slug}_page.py && git diff --stat docs/{slug}-reaction-map.html
```

- 入力ファイルと出力ファイルを**引数で受け取る**（staging候補の生成に必要）
- 生成後の自己検証をスクリプトに埋める（タイトル・h1・canonical・保護タグ・件数・
  テンプレート元テーマの残留参照・賛否バー合計100%）。消費税減税のスクリプトはこれをやっている
- 通ったら `scripts/refresh_adapters/{slug}.py` として登録し、`THEMES.yaml` に
  `page_update_mode: adapter` を書く。既存の `koshitsu.py` が参考になる

2回目に落ちる／差分が出る場合は `migration` 止まりになる。**そのときは公開前に
オーナーへ「このテーマは当面手動更新になります」と伝える**（黙って増やさない）。

### ⑦ 実機で確認する（検査スクリプトでは映らない）

ブラウザで開いて、次を自分の目で確認する。人に頼まない。

- [ ] コンソールエラーなし
- [ ] 375px幅で横スクロールなし、ヘッダーの「テーマを見る」が1行で収まる
- [ ] ヒートマップのチェックを入れると色が出る／外すと消える
- [ ] **別タブに移ってから戻ってもヒートマップが出ている**（`requestAnimationFrame` はバックグラウンドで止まる）
- [ ] 投票 → 完了画面に「シェア」と「投票をやり直す」が出る
- [ ] ヒーロー画像が自テーマのものになっている

### ⑧ 公開の登録（忘れやすい5か所）

```sh
python3 .claude/skills/new-topic/scripts/check_launch.py {slug}
```

このスクリプトが見るのは、過去に実際に抜けた項目だけ。中身は次のとおり。

1. `THEMES.yaml` にテーマを追加（`page_update_mode` と `collect_at` を必ず入れる）
2. `configs/site-cases.json` と `configs/theme-seo.json` の**両方**に登録
   — **URL集合が一致しないと `apply_theme_trust.py` が落ちる**
3. `docs/sitemap.xml` に追加
4. `docs/index.html` にトピックカードを追加 → `python3 scripts/sync_portal_stats.py` で数値を生成
5. `supabase/functions/cast-vote/index.ts` の `TOPIC_CHOICES` に
   `{slug}-issue-stance-v1: 論点数×立場数` を追加 → **オーナーに `supabase functions deploy cast-vote --no-verify-jwt` を依頼**
   （これを忘れると投票が `invalid_topic` で全部弾かれる。ページ側は無言で失敗する）

続けて既存の検査を通す。

```sh
python3 scripts/verify_theme_page.py {slug} ; echo "exit=$?"
python3 scripts/verify_top_page.py ; echo "exit=$?"
python3 scripts/seo/validate_theme_seo.py ; echo "exit=$?"
python3 -m unittest discover -s tests
```

`validate_theme_seo.py` は着手前から1件落ちている（課題37）。⓪のベースラインと比べて、
**新しく落ちた分だけ**が自分の責任範囲。

### ⑨ 画像

漫画・図解プロンプトは `creative/manga-prompts/{slug}-prompts.md` に書く。生成はオーナーがGPTimage2で行う。

- **本番ページ生成プロンプトの末尾に必ず比率を書く**:
  `Output image: portrait, 3:4 aspect ratio (e.g. 900×1200px).`
  HTMLの `.manga-page-card img` は `aspect-ratio:3/4` 固定なので、正方形で作ると上下が切れる
- 図解（インフォグラフィック）は wide 1915×821px 前後
- キャラシートは比率指定不要（HTMLに出さない）
- 保存は WebP、漫画は ≤100KB / 900px

---

## 2Dスタンスマップの実装

載せる場合のみ。過去に2回とも同じ場所で壊れている。

### CSS（特異度に注意）

```css
/* ❌ 汎用ルールに background を書くと個別ルールに勝ってしまう */
#stance-map-section canvas { background:#fafafa; }   /* 特異度101 */
#canvasMain { background:transparent; }              /* 特異度100 → 負ける */
```

```css
/* ✅ 汎用ルールには background を書かない */
#stance-map-section canvas { display:block; width:100%; border:1px solid #e0e0e0; border-radius:8px; }
#canvasMain { cursor:crosshair; position:relative; z-index:2; background:transparent; }
#canvasHeat { position:absolute; top:0; left:0; width:100%; height:100%;
              border-radius:8px; pointer-events:none; z-index:1; background:#fafafa; }
```

負けると main キャンバスが白く不透明になり、下のヒートマップを完全に隠す。

### JS（アニメーション状態を混ぜない）

既存ページでの関数名は `drawHeat()`（henoko のみ `drawHeatmap()` も併存）。

```js
// ❌ 背景タブで animating=true, animFrame=0 のまま止まり vis=[] になる
const vis = RAW.filter((p,i) => visible(p) && (animating ? i < animFrame : true));

// ✅ ヒートマップはアニメーション状態を見ない
function drawHeat(){
  hCtx.clearRect(0,0,W,H);
  if(!showHeat) return;
  const vis = RAW.filter(p => visible(p));
  if(!vis.length) return;
  ...
}
function redraw(){ drawHeatmap(); drawBase(); }   // 順序も固定
```

### 確認方法

後期のページはスクリプトを `(function(){...})()` で包んでいるので、コンソールから
`drawHeatmap` や `RAW` に触れない。キャンバスのピクセルを直接見る。

```js
document.getElementById('smCanvasHeat').getContext('2d').getImageData(300,300,1,1).data
```

- `getComputedStyle(canvasMain).backgroundColor` が `rgba(0,0,0,0)`
- `getComputedStyle(canvasHeat).backgroundColor` が `rgb(250,250,250)`

---

## 落とし穴

**`inject_tide_widget.py` は引数を取らず全テーマを書き換える。** 一部を古いデータへ巻き戻す
（2026-08-08 に ai-copyright と takaichi が公開中のまま後退した）。実行したら
`git status --porcelain` を見て、対象外の `docs/*.html` が出ていたら `git restore` する。

**`THEMES.yaml` の `notes` は長くていい。** 次に触るAIが読む唯一の経緯なので、
使ったクエリ数・重複除外件数・スタンス構成を選んだ理由・テンプレート元のテーマを書く。

**pytest は入っていない。** `python3 -m unittest discover -s tests` で動かす。

**公開したら作業ツリーを片付ける。** `git worktree remove` の前に、そのツリーにしかない
非公開ファイル（`social-samples/` の未追跡分）を共有ツリーへ複製してバックアップを取り直す。
放置した3本が事故の温床になった（課題36）。

---

## 完了条件

- [ ] `check_launch.py {slug}` が exit 0
- [ ] `verify_theme_page.py {slug}` / `verify_top_page.py` が exit 0
- [ ] ページ生成スクリプトを2回実行して差分ゼロ（`page_update_mode: adapter`）
      — 通らない場合はオーナーに手動更新になる旨を伝えた
- [ ] ⑦の実機確認6項目を自分で見た
- [ ] `supabase functions deploy` をオーナーに依頼した
- [ ] ルートリポジトリの一覧に追記した
- [ ] `THEMES.yaml` に `collect_at`（次回収集予定）を入れた
- [ ] 作業ツリーを片付けた

## 完了報告に含めること

1. `git diff --stat`
2. 収集・分類の実数（総件数／重複除外／意見率／論点別の内訳）
3. 検査スクリプトの出力をそのまま貼る
4. 冪等性の確認結果（2回実行の diff）
5. オーナーにやってもらうこと（画像生成／supabaseデプロイ／ルートリポジトリ）
6. 確認していないこと・判断に迷った点

オーナーはエンジニアではない。専門用語には初出で一言そえ、結論を先に書く（`CLAUDE.md` 参照）。
