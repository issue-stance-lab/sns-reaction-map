# Q2投票設問 再設計 — 残り3テーマ

作成日: 2026-07-12  
対象: Claude Code（ハブAI）

---

## 背景

SNS反応まっぷの投票UIは2問構成：
- **Q1**: 賛成/反対を問う（X軸）
- **Q2**: 価値観・優先事項を問う（Y軸）

2026-07-12 のセッションで、全8テーマの Q2 を「賛成/反対調」から「Y軸の価値対立を問う問い」に改善した。5テーマはコミット・プッシュ済み（commit `b3c9f0f`）。

以下の3テーマは **Y軸の定義またはQ2のラベルに根本的な問題があり保留**。

---

## 保留テーマの現状と問題点

### 1. 部活動の地域移行 (`docs/bukatsu-chiiki-reaction-map.html`)

**現在のQ2（作業ディレクトリに変更中・未コミット）**
```
text:     '部活動改革で守りたいのはどちら？'
negLabel: '教員の持続可能な働き方'
posLabel: '子どもの活動の質・教育機会'
```

**Y軸定義**
```
neg: '教員の負担軽減を最優先'
pos: '競技力・教育的価値を最優先'
```

**問題**  
「先生 vs 子ども」の対立構造になっており、どちらを選んでも「もう一方を犠牲にする気がある？」と読まれてしまう。  
「両方大事」と感じて答えにくい二択。

**検討した代替案**
- 「部活動は今後、主に誰が担うべき？」neg: 学校・教育行政（公的教育として）/ pos: 地域・保護者・民間クラブ  
  → **問題**: Y軸の軸意味（教員負担 vs 競技価値）と合わなくなる

**論点**  
Y軸ラベル自体（教員の負担軽減 vs 競技力・教育価値）を変えるか、  
この対立のまま問いの言い方だけを改善するか？

---

### 2. 辺野古高校生死亡事故 (`docs/henoko-student-accident-reaction-map.html`)

**現在のQ2（作業ディレクトリに変更中・未コミット）**
```
text:     '再発防止のため、最も力を入れるべきことは？'
negLabel: '現場・学校・地域の安全管理強化'
posLabel: '国・制度・政策レベルの見直し'
```

**Y軸定義**
```
neg: '事故・安全・追悼を中心に議論'
pos: '政治・制度・思想の問題として議論'
```

**問題**  
前セッションの旧Q2「この問題の本質はどこ？」はフレーム選択型で答えにくかった。  
変更後の問いはY軸に合っており改善されているが、  
「現場の安全管理」と「国・制度の見直し」は**排他的ではなく、両方必要**と感じやすい。

**確認事項**  
現状の変更で問題なければそのままコミットして良い。  
もしラベルをさらに改善するなら：  
- neg: `事故の背景より安全対策・追悼を優先`  
- pos: `安全対策より政治・制度的な問題提起を優先`  
のような「立場の差」をより明示する書き方も検討できる。

---

### 3. 高市文春問題 (`docs/takaichi-reaction-map-standard.html`)

**現在のQ2（作業ディレクトリに変更中・未コミット）**
```
text:     'この件で最も重要な問題は？'
negLabel: 'SNS・メディアのフェイク問題'
posLabel: '政治家の説明責任・情報倫理'
```

**Y軸定義（現状）**
```
neg: '派生論点・サナエトークン中心'
pos: '中傷動画・政治責任の本筋を重視'
```

**問題**  
Y軸 neg ラベルの「派生論点・サナエトークン中心」が：
1. 蔑称的（擁護派を「派生論点を見ている人」と揶揄する）
2. 「サナエトークン」はそもそも一般に通じない
3. **積極的に選べる立場として成立しない**

Q2の neg「SNS・メディアのフェイク問題」は、X軸 neg（擁護・報道批判）の人が選ぶ立場として自然。  
しかし**Y軸ラベルもあわせて書き換えないと、スタンスマップの軸表示と乖離する**。

**必要な作業**  
Y軸ラベルを書き換える場合、すでに分類済みのデータ（140件）との整合性確認が必要。  
Y軸の意味を変えずにラベルだけ言い換えるのか、軸の定義から見直すかを判断すること。

---

## 作業手順

### Step 1: 検討・決定
各テーマについて上記の論点を整理し、Q2テキスト・ラベルの最終案を決定する。  
高市については Y軸ラベルも同時に変更するか判断する。

### Step 2: 実装

HTML直接編集。以下のキーを変更：
- `questions[1].text`
- `questions[1].negLabel`
- `questions[1].posLabel`

Y軸も変える場合は `yAxis.neg` / `yAxis.pos` も変更。

### Step 3: 保護タグ確認

```bash
grep -n "G-K10S4YCZFH\|ca-pub-2542211932832864\|supabase\|og:image" \
  docs/bukatsu-chiiki-reaction-map.html \
  docs/henoko-student-accident-reaction-map.html \
  docs/takaichi-reaction-map-standard.html
```

### Step 4: コミット＆プッシュ

```bash
git add docs/bukatsu-chiiki-reaction-map.html \
        docs/henoko-student-accident-reaction-map.html \
        docs/images/henoko-student-accident-manga-page-1.webp \
        docs/images/henoko-student-accident-manga-page-2.webp \
        docs/images/takaichi-manga-page-3.webp \
        docs/takaichi-reaction-map-standard.html

git commit -m "feat(vote): Q2投票設問を改善（部活・辺野古・高市）"
git push origin main
```

---

## 参照ファイル

- `THEMES.yaml` — テーマ台帳と工程状態
- `docs/vote2d.js` — 投票UIコンポーネント（questions配列の仕様はここを確認）
- 各テーマHTMLの `Vote2D.init({...})` 内 `questions`, `xAxis`, `yAxis`, `quadrants`
