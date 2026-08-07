# vote2d.js 統合チェックリスト — 2026-07-11 現在

作成日: 2026-07-11  
対象: Claude Code（ハブAI）

---

## このプロンプトの用途

1. **残検証タスク** — モバイル375px確認 & git push
2. **新規テーマページへの vote2d.js 組み込み** — 手順と必須チェックリスト

---

## 現在の状態（2026-07-11 時点）

### コミット状況

mainブランチが origin/main より **3コミット先行中（未push）**:

```
b449772 fix: 新規訪問者へのスタンスマップブラーが全テーマで未適用だった問題を修正
97f99fc Merge task/growth-2d-vote-canvas: 2Dキャンバス投票UI全8テーマに実装
3cc678b feat: 2Dキャンバス投票UI（vote2d.js）を全8テーマに実装
```

### このセッションで修正した問題（b449772）

**1. 新規訪問者へのスタンスマップブラーが全テーマで効いていなかった**

- `Vote2D.init` の `<script>` タグ（行793）が `#stance-map-inner` 要素（行807）より前に実行される
- コンストラクタ内で `_applyBlur()` を同期呼び出し → 要素が存在せず黙って終了
- **修正**: `onReady` ヘルパー（`DOMContentLoaded` 待機 + `readyState` フォールバック）でラップ

**2. 再訪者のマーカー復元タイミングバグ**

- `setTimeout(fn, 0)` は `window.setStanceMapVoteMarker` 定義前に発火する（大容量スタンスマップスクリプトの解析に~30ms かかる）
- **修正**: 同じく `onReady` ヘルパーで DOMContentLoaded 後に遅延実行

**3. ブラウザキャッシュによる古い vote2d.js の配信**

- **修正**: 全8テーマの `<script src="vote2d.js">` → `<script src="vote2d.js?v=2">` に変更

**4. VOTE_MARKERS の象限順序・ラベルのずれ**

- 旧4択ボタン時代の配列が残っており、vote2d.js の象限インデックス（TL=0/TR=1/BL=2/BR=3）と不一致
- **修正**: 全5テーマ（ai-copyright, bike, bukatsu, constitutional, elderly）の VOTE_MARKERS を再構築

### デスクトップ検証結果（実Chrome、全8テーマ）

| テーマ | 新規訪問ブラー | 投票 | リロード復元 |
|--------|-------------|------|------------|
| ai-copyright | ✓ | ✓（TL） | ✓ |
| elderly-license | ✓ | ✓（TR qi:1） | ✓ |
| takaichi | ✓ | ✓（BL） | ✓ |
| bike / bukatsu / constitutional / henoko / school | ✓ | ✓ | ✓ |

コンソールエラー: **全テーマでゼロ**

---

## 残タスク

### Task A：モバイル375px検証 → git push

**手順:**

```bash
# ローカルサーバー起動（既に起動中なら不要）
python3 -m http.server 8124 -d docs
```

Chrome DevTools > Responsive Device > 375px 幅で各テーマページを確認:

- `#vote-buttons` 内の2Dキャンバスが横スクロールなしで表示される
- キャンバス幅が最低 200px 以上あること
- 投票フロー（タップ→確定→結果）が動作する

問題があれば `docs/vote2d.js` の CSS を修正してコミット。
問題なければ:

```bash
git push origin main
```

**コミット後にやること:**
- GROWTH.yaml の `vote-2d-canvas` エントリの notes に「モバイル375px確認済み」を追記
- GROWTH.yaml の `judge_at: 2026-07-24` は投票転換率の計測判定日。変更不要

---

## vote2d.js の背景知識

`docs/vote2d.js` は2Dキャンバス投票UIコンポーネント（2026-07-10 実装・main マージ済み）。
4択ボタン方式を廃止し、XY軸マップ上でタップ／クリックして立場を選ぶ仕組み。

```
投票データ保存キー: sns_vote2d_v1_{topic}_my    → { qi, sx, sy }
集計データ保存キー: sns_vote2d_v1_{topic}_counts → { "0":N, "1":N, … }
```

象限インデックス（全テーマ共通）:
- 0 = TL（negX & posY）  色: #dc2626（赤）
- 1 = TR（posX & posY）  色: #2563eb（青）
- 2 = BL（negX & negY）  色: #059669（緑）
- 3 = BR（posX & negY）  色: #d97706（琥珀）

**今後 vote2d.js を更新するときは `?v=2` の数字を上げること（→ `?v=3`）**

---

## Task B：新規テーマページへの vote2d.js 組み込み

ブランチ: `task/{theme}-vote2d`

### B-1. configs/{theme}.json に map_axes を追加

```json
"map_axes": {
  "xAxis": { "neg": "←方向の軸ラベル", "pos": "→方向の軸ラベル" },
  "yAxis": { "neg": "↓方向の軸ラベル", "pos": "↑方向の軸ラベル" },
  "quadrants": [
    { "label": "TL象限名（negX & posY）", "desc": "説明文" },
    { "label": "TR象限名（posX & posY）", "desc": "説明文" },
    { "label": "BL象限名（negX & negY）", "desc": "説明文" },
    { "label": "BR象限名（posX & negY）", "desc": "説明文" }
  ]
}
```

象限の順番は **TL/TR/BL/BR = 0/1/2/3** で固定（vote2d.js の stanceToQuad 関数と一致させる）。

### B-2. HTMLに vote2d.js を組み込む

#### 2-1. スクリプト追加

投票ボタンセクションより直前に挿入:

```html
<script src="vote2d.js"></script>
<script>
(function(){
  var supabaseUrl="";
  var supabaseAnonKey="";
  Vote2D.init({
    containerId: 'vote-buttons',
    resultId: 'vote-result',
    topic: '{TOPIC_ID}',
    title: '{ページタイトル}',
    xAxis: { neg: '←軸ラベル', pos: '→軸ラベル' },
    yAxis: { neg: '↓軸ラベル', pos: '↑軸ラベル' },
    quadrants: [
      {"label": "TL象限名", "desc": "説明"},
      {"label": "TR象限名", "desc": "説明"},
      {"label": "BL象限名", "desc": "説明"},
      {"label": "BR象限名", "desc": "説明"}
    ],
    supabaseUrl: supabaseUrl,
    supabaseAnonKey: supabaseAnonKey
  });
})();
</script>
```

#### 2-2. `#vote-result` div の確認

```html
<div id="vote-result" style="display:none;margin-top:12px;"></div>
```

### B-3. スタンスマップ側の setStanceMapVoteMarker を更新

#### VOTE_MARKERS 形式（ai-copyright 等）

```javascript
const VOTE_MARKERS = [
  { x: -1.45, y:  1.45, label: 'あなた: TL象限名', color: '#dc2626' },  // 0=TL
  { x:  1.45, y:  1.45, label: 'あなた: TR象限名', color: '#2563eb' },  // 1=TR
  { x: -1.45, y: -1.45, label: 'あなた: BL象限名', color: '#059669' },  // 2=BL
  { x:  1.45, y: -1.45, label: 'あなた: BR象限名', color: '#d97706' },  // 3=BR
];

window.setStanceMapVoteMarker = function(idx, sx, sy) {
  myVoteMarker = idx;
  if (sx !== undefined) myVoteSX = sx;
  if (sy !== undefined) myVoteSY = sy;
  const note = document.getElementById('your-marker-note');
  if (note) note.style.display = 'block';
  redraw();
};
```

#### VOTE_COORDS / px() / py() 形式（henoko 等のミニファイ版）

```javascript
window.setStanceMapVoteMarker=function(i,sx,sy){marker=i;if(sx!==undefined)markerSX=sx;if(sy!==undefined)markerSY=sy;draw()}
```

### B-4. よくあるバグと対処法

| バグ | 原因 | 対処 |
|------|------|------|
| キャンバスが 2px 幅になる | `#vote-buttons` に `display:flex` が残っている | vote2d.js が自動で `display:block` にリセット済みなので通常不要 |
| 再訪時にマーカーが出ない | 旧コード: `setTimeout(fn, 0)` が大容量スクリプト解析前に発火 | 現 vote2d.js は DOMContentLoaded を使う。修正済み |
| 新規訪問時ブラーが効かない | `#stance-map-inner` がまだ未解析の状態で `_applyBlur()` が実行された | 現 vote2d.js は DOMContentLoaded を使う。修正済み |
| マーカーが象限中心に表示 | `setStanceMapVoteMarker` が `sx, sy` を受け取らない旧署名 | `function(idx, sx, sy)` に更新し `myVoteSX/myVoteSY` を使って描画 |

---

## 保護タグ確認（コミット前に必ずgrep）

```bash
grep -n "G-K10S4YCZFH\|ca-pub-2542211932832864\|supabase\|og:image" docs/{theme}-reaction-map.html
```

GA4・AdSense・Supabase・OGPがすべて存在することを確認する。

---

## コミット規則

```
feat: {theme}に vote2d.js 2D投票UIを組み込み
```

マージ後に THEMES.yaml の該当テーマに `vote2d: done` フィールドを追加すること。
