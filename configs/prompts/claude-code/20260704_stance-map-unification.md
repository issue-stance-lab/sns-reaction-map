# 課題25: スタンスマップ統一 — 半円図→4象限2Dマップへの一括移行

最終更新: 2026-07-04

## 背景

各テーマの reaction-map.html に「半円チャート（反応の勢力図）」として表示していた分類結果を、2軸スコアを使った「2Dスタンスマップ（十字散布図）」に置き換える作業を進めてきたが、テーマごとに異なるセッションが異なるやり方で実装したため、以下の問題が発生している:

1. **ページの重複**: constitutional は reaction-map.html 内にスタンスマップを埋め込んだ上に、独立した stance-map.html も存在。index.html から両方にリンクあり
2. **セクション消失**: ai-copyright はスタンスマップに置換した際、対立軸セクション・分類別件数・ヒートマップ（カテゴリ×クエリ / カテゴリ×スタンス）が消えた
3. **独立ページの孤立**: bike / bukatsu / elderly の独立 stance-map.html は reaction-map.html からリンクされておらず、GA4/AdSense/Supabase 投票もない
4. **CSS/JSのバグ**: 過去に毎回発生（CSS特異度バグ、drawHeatmapのアニメーションフィルター等）。チェックリストが守られない

## ゴール

**全テーマの reaction-map.html に、統一構造でスタンスマップを埋め込む。独立 stance-map.html は削除する。**

完成状態:
- 全8テーマの reaction-map.html が同じセクション構造を持つ
- 既存セクション（対立軸・分類別件数・ヒートマップ・代表サンプル）は保持
- スタンスマップは「対立軸」セクションの直前に配置
- 独立 stance-map.html は削除し、index.html からのリンクも reaction-map.html に統一
- GA4 / AdSense / Supabase タグは一切触らない

---

## 現状マトリクス

| テーマ | slug | reaction-map 内スタンスマップ | 独立 stance-map.html | 対立軸セクション | 分類別件数 | ヒートマップ(×クエリ/×スタンス) | 2D分類JSON | 2D件数 |
|--------|------|------|------|------|------|------|------|------|
| 生成AI著作権 | ai-copyright | ✅ あり | なし | ❌ CSSのみ残存(中身なし) | ❌ 消失 | ❌ 消失 | `ai-copyright_2d_classified.json` | 339件 |
| 自転車青切符 | bike-blue-ticket | ❌ なし | ✅ 孤立 | ✅ あり | ✅ あり | ✅ あり | `bike-blue-ticket_2d_classified.json` | 116件 |
| 部活地域移行 | bukatsu-chiiki | ❌ なし | ✅ 孤立 | ✅ あり | ✅ あり | ✅ あり | `bukatsu-chiiki_2d_classified.json` | 148件 |
| 憲法改正 | constitutional | ✅ あり | ⚠️ 重複 | ✅ あり | ✅ あり | ✅ あり | `constitutional_amendment_2d_classified.json` | 366件 |
| 高齢者免許返納 | elderly | ✅ あり | ⚠️ 重複 | ❌ 消失 | ❌ 消失 | ❌ 消失 | `elderly-license_2d_classified.json` | 117件 |
| 辺野古 | henoko | ❌ なし | ❌ なし | ✅ あり | ✅ あり | ✅ あり | **なし（2D未分類）** | — |
| あだ名禁止 | school-nickname-ban | ❌ なし | ❌ なし | ✅ あり | ✅ あり | ✅ あり | `school-nickname-ban_2d_classified.json` | 103件(70%エラー→要再実行) |
| 高市早苗 | takaichi | ❌ なし | ❌ なし | ✅ あり | ✅ あり | ✅ あり | **なし（2D未分類）** | — |

### 2D JSON の軸フィールド名

各テーマの `social-samples/*_2d_classified.json` で使われているフィールド名:

| テーマ | X軸フィールド | Y軸フィールド |
|--------|--------------|--------------|
| ai-copyright | `stance_regulation` | `stance_beneficiary` |
| bike-blue-ticket | `stance_enforcement` | `stance_priority` |
| bukatsu-chiiki | `stance_transfer` | `stance_priority` |
| constitutional | `stance_amendment` | `stance_priority` |
| elderly-license | `stance_restriction` | `stance_priority` |
| school-nickname-ban | `stance_ban` | `stance_culture` |

共通フィールド: `emotional_intensity`, `confidence`, `summary`, `url`, `text`

---

## 正典とするセクション構造

各 reaction-map.html のセクション配置順（上から下）:

```
1. ヒーロー（テーマ名・リード文）
2. 漫画セクション（あるテーマのみ）
3. 投票セクション
4. ★ SNS意見スタンスマップ（2Dマップ） ← 新規追加 or 統一
5. 対立軸（conflict-panel）
6. 分類別件数（バーチャート）
7. カテゴリ × 検索クエリ（ヒートマップ）
8. カテゴリ × スタンス（ヒートマップ）
9. 代表サンプル
10. フッター
```

**ルール**:
- セクション4（スタンスマップ）以外は**既存を保持**する。消さない
- 2D分類JSONがないテーマ（henoko / takaichi）は、スタンスマップ追加をスキップし、既存の半円チャート（反応の勢力図）をそのまま残す
- school-nickname-ban は2D分類の品質が低い（70%エラー）ため、再分類が完了するまでスキップ

---

## 正典テンプレート: スタンスマップHTML/CSS/JS

### 参考実装

**constitutional-amendment-reaction-map.html** を正典とする。理由:
- reaction-map 内に埋め込み済み
- 対立軸・分類別件数・ヒートマップも全部残っている
- CSS特異度バグの修正済みパターンを使用
- ガイドツアー・引用テキスト即時表示も実装済み

### CSS（`</style>` の直前に追記）

```css
/* === 2D Stance Map (embedded) === */
#stance-map-section { position: relative; }
#stance-map-inner { transition: filter .6s ease; }
#sm-wrap { position:relative; width:100%; max-width:660px; margin:0 auto; }

/* ⚠️ 重要: canvas の汎用ルールに background を書くな（特異度101が個別ID100に勝ってしまう） */
#stance-map-section canvas { display:block; width:100%; border:1px solid #e0e0e0; border-radius:8px; }
#smCanvasMain { cursor:crosshair; position:relative; z-index:2; background:transparent; }
#smCanvasHeat { position:absolute; top:0; left:0; width:100%; height:100%; border-radius:8px; pointer-events:none; z-index:1; background:#fafafa; }

.sm-ax { position:absolute; font-size:10px; font-weight:600; color:#444; background:rgba(255,255,255,.85); padding:2px 6px; border-radius:4px; pointer-events:none; z-index:3; line-height:1.4; }
#sm-tooltip { position:fixed; background:#111; color:#fff; font-size:12px; padding:8px 12px; border-radius:8px; pointer-events:none; z-index:9999; max-width:280px; opacity:0; transition:opacity .15s; line-height:1.5; }

/* Tour panel */
#smTourPanel { background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); color:#e0e0e0; border-radius:12px; padding:16px; margin-top:10px; display:none; }
#smTourPanel.active { display:block; }
#smTourStep { font-size:10px; color:#888; margin-bottom:4px; }
#smTourTitle { font-size:16px; font-weight:800; color:#fff; margin-bottom:8px; }
#smTourDesc { font-size:13px; line-height:1.6; color:#ccc; margin-bottom:12px; }
#smTourEmbedLoading { font-size:12px; color:#888; display:none; margin-bottom:8px; }
#smTourEmbed { margin-bottom:8px; display:none; }
#smTourQuoteFallback { background:#0d1117; border-left:3px solid #1d9bf0; border-radius:6px; padding:10px 12px; margin-bottom:8px; font-size:13px; line-height:1.5; display:none; cursor:pointer; }
#smTourQuoteLink { color:#1d9bf0; margin-left:8px; }
.sm-tour-nav { display:flex; align-items:center; gap:8px; margin-top:10px; }
.sm-tnav { background:none; border:1px solid #444; color:#ccc; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:13px; }
.sm-tnav.primary { background:#1d9bf0; border-color:#1d9bf0; color:#fff; }
.sm-tnav:hover { opacity:.8; }
#smTourProgress { flex:1; height:4px; background:#333; border-radius:2px; }
#smTourProgressBar { height:4px; background:#1d9bf0; border-radius:2px; transition:width .3s; }

/* Controls */
.sm-controls { margin-top:10px; display:flex; flex-direction:column; gap:8px; }
.sm-view-row { display:flex; align-items:center; gap:16px; flex-wrap:wrap; font-size:13px; }
.sm-filters { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.sm-fbtn { font-size:11px; padding:4px 10px; border:1px solid #ccc; border-radius:20px; background:#fff; cursor:pointer; color:#555; }
.sm-fbtn.active { background:var(--accent,#2563eb); color:#fff; border-color:var(--accent,#2563eb); }
.sm-stat-cards { display:grid; grid-template-columns:repeat(2,1fr); gap:6px; margin-top:10px; }
.sm-sbox { background:#f8f9fa; border-radius:8px; padding:10px 12px; }
.sm-slabel { font-size:11px; color:#666; margin-bottom:2px; }
.sm-sval { font-size:22px; font-weight:800; line-height:1.2; }
.sm-sdesc { font-size:11px; color:#888; margin-top:2px; }
.sm-legend-emo { display:flex; align-items:center; gap:6px; font-size:12px; }
.sm-emo-bar { width:60px; height:8px; border-radius:4px; background:linear-gradient(to right,#3498db,#e74c3c); }
#smStartTour { font-size:12px; padding:6px 14px; border:1px solid var(--accent,#2563eb); border-radius:6px; background:none; color:var(--accent,#2563eb); cursor:pointer; font-weight:600; }
#smStartTour:hover { background:var(--accent,#2563eb); color:#fff; }
```

### HTML構造（投票セクションの直後、対立軸セクションの直前に挿入）

```html
<section class="panel" id="stance-map-section">
<div id="stance-map-inner">
<div class="panel-title"><h2>SNS意見スタンスマップ</h2><span>{{件数}}件{{除外注記}} | 点の色＝感情強度（青:冷静 → 赤:激怒）| ホバーで詳細 / クリックでXへ</span></div>
<div id="sm-wrap">
  <canvas id="smCanvasHeat" width="600" height="600"></canvas>
  <canvas id="smCanvasMain" width="600" height="600"></canvas>
  <div class="sm-ax" style="top:3px;left:50%;transform:translateX(-50%)">{{Y軸+ラベル}} ▲</div>
  <div class="sm-ax" style="bottom:3px;left:50%;transform:translateX(-50%)">▼ {{Y軸-ラベル}}</div>
  <div class="sm-ax" style="top:50%;left:2px;transform:translateY(-50%);writing-mode:vertical-rl">◀ {{X軸-ラベル}}</div>
  <div class="sm-ax" style="top:50%;right:2px;transform:translateY(-50%);writing-mode:vertical-rl">{{X軸+ラベル}} ▶</div>
</div>
<!-- ガイドツアーパネル -->
<div id="smTourPanel">
  <div id="smTourStep"></div>
  <div id="smTourTitle"></div>
  <div id="smTourDesc"></div>
  <div id="smTourEmbedLoading">投稿を読み込み中…</div>
  <div id="smTourEmbed"></div>
  <div id="smTourQuoteFallback"><span id="smTourQuoteText"></span><small id="smTourQuoteLink">↗ Xで見る</small></div>
  <div class="sm-tour-nav">
    <button class="sm-tnav" id="smBtnPrev">← 前へ</button>
    <div id="smTourProgress"><div id="smTourProgressBar"></div></div>
    <button class="sm-tnav primary" id="smBtnNext">次へ →</button>
    <button class="sm-tnav" id="smBtnClose" style="border-color:#666;color:#aaa">✕</button>
  </div>
</div>
<!-- コントロール -->
<div class="sm-controls">
  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <div class="sm-legend-emo">
      <span style="color:#555">感情強度:</span>
      <span>冷静</span>
      <div class="sm-emo-bar"></div>
      <span>激怒</span>
    </div>
    <button id="smStartTour">▶ ガイドツアーで読む</button>
  </div>
  <div class="sm-view-row">
    <label><input type="checkbox" id="smChkHeat" checked> ヒートマップ</label>
    <label><input type="checkbox" id="smChkDots" checked> ドット</label>
    <label style="color:#888">強度: <input type="range" id="smHeatIntensity" min="10" max="60" value="40" style="width:80px;vertical-align:middle"></label>
  </div>
  <div class="sm-filters">
    <span style="font-size:10px;color:#888">絞り込み:</span>
    <!-- テーマごとにボタンをカスタマイズ -->
    <button class="sm-fbtn active" data-q="all">全件 ({{N}})</button>
    <button class="sm-fbtn" data-q="q1">{{象限1ラベル}} ({{n1}})</button>
    <button class="sm-fbtn" data-q="q3">{{象限3ラベル}} ({{n3}})</button>
    <button class="sm-fbtn" data-q="q4">高感情 e≥1.5 ({{nHigh}})</button>
    <button class="sm-fbtn" data-q="calm">冷静 e≤0 ({{nCalm}})</button>
  </div>
</div>
<!-- 象限サマリーカード -->
<div class="sm-stat-cards">
  <div class="sm-sbox"><div class="sm-slabel">{{象限1名称}} (右上)</div><div class="sm-sval" style="color:#2980b9">{{n1}}件</div><div class="sm-sdesc">{{象限1の一行説明}}</div></div>
  <div class="sm-sbox"><div class="sm-slabel">{{象限3名称}} (左下)</div><div class="sm-sval" style="color:#c0392b">{{n3}}件</div><div class="sm-sdesc">{{象限3の一行説明}}</div></div>
  <div class="sm-sbox"><div class="sm-slabel">中立含む（X=0またはY=0）</div><div class="sm-sval" style="color:#7f8c8d">{{nMid}}件</div><div class="sm-sdesc">{{中間帯の一行説明}}</div></div>
  <div class="sm-sbox"><div class="sm-slabel">高感情 (e ≥ 1.5)</div><div class="sm-sval" style="color:#e67e22">{{nHigh}}件</div><div class="sm-sdesc">強い怒り・感情的な訴え（両陣営）</div></div>
</div>
<div id="sm-tooltip"></div>
</div><!-- /stance-map-inner -->
</section>
```

### JS（`</section>` の直後に `<script>` ブロック）

constitutional-amendment-reaction-map.html の行1109〜1815 をそのままコピーし、以下の5箇所のみ差し替える:

1. **`const RAW = [...]`** — テーマの2D JSONから生成。各要素のフォーマット:
   ```json
   {"x": stance_X値, "y": stance_Y値, "e": emotional_intensity, "c": confidence, "s": "summary", "u": "url"}
   ```

2. **`const TOUR = [...]`** — ガイドツアーのステップ定義。各象限から代表的な投稿を2〜3件選んでストーリーを構成

3. **フィルターボタンのロジック** — `data-q` の値に応じた絞り込み条件を定義

4. **象限の件数計算** — RAWデータから象限ごとの件数を集計

5. **軸ラベルのテキスト** — HTML側の `.sm-ax` テキストと整合させる

### ⚠️ 実装時の必須チェックリスト（過去バグ再発防止）

- [ ] **CSS特異度**: `#stance-map-section canvas { ... }` に `background` を**絶対に書かない**。`background` は `#smCanvasHeat` と `#smCanvasMain` 個別にのみ指定
- [ ] **drawHeatmap()**: アニメーション状態でフィルターしない。`const vis = RAW.filter(p => visible(p))` のみ
- [ ] **IIFE**: メインスクリプトを `(function(){ ... })()` でラップし、グローバル汚染を防ぐ
- [ ] **canvas ID**: `smCanvasMain` / `smCanvasHeat`（`sm` プレフィックス付き）。既存ページの他のcanvasと衝突しない
- [ ] **`getComputedStyle` 確認**: ブラウザで開いた後、以下を検証
  - `getComputedStyle(document.getElementById('smCanvasMain')).backgroundColor` → `rgba(0, 0, 0, 0)`
  - `getComputedStyle(document.getElementById('smCanvasHeat')).backgroundColor` → `rgb(250, 250, 250)`
- [ ] **既存セクションの保持**: 対立軸(conflict-panel)・分類別件数・ヒートマップ(×クエリ/×スタンス)・代表サンプルが消えていないこと

---

## 作業手順

### Phase 1: 正典テンプレート抽出（準備）

1. `constitutional-amendment-reaction-map.html` からスタンスマップセクション（CSS + HTML + JS）を抽出し、テンプレートとして理解する
2. テンプレートの `{{変数}}` 部分をテーマごとに差し替える仕組みを把握する

### Phase 2: 既存の修正（ai-copyright / elderly / constitutional）

#### ai-copyright — セクション復旧 + 統一

**問題**: 対立軸・分類別件数・ヒートマップが消失。スタンスマップは存在する
**作業**:
1. git log で消失前のバージョンを特定し、対立軸・分類別件数・ヒートマップセクションを復旧
2. スタンスマップのCSS/JSを正典パターンに合わせる
3. GA4(`G-K10S4YCZFH`) / AdSense(`ca-pub-2542211932832864`) / Supabase タグが維持されていることを確認

#### elderly — セクション復旧

**問題**: 対立軸・分類別件数・ヒートマップが消失。スタンスマップは存在する
**作業**:
1. git log で消失前のバージョンを特定し、対立軸・分類別件数・ヒートマップセクションを復旧
2. スタンスマップのCSS/JSを正典パターンに合わせる
3. 独立版 `docs/elderly-license-stance-map.html` を削除

#### constitutional — 重複ページ解消

**問題**: reaction-map + 独立 stance-map の2ページが存在
**作業**:
1. reaction-map.html のスタンスマップが正常動作していることを確認
2. 独立版 `docs/constitutional-amendment-stance-map.html` を削除
3. `docs/index.html` の独立版へのリンク（トピックカード + フッターリンク）を削除
4. `docs/index.html` の reaction-map へのリンクに「2Dスタンスマップ」のタグを追加

### Phase 3: 新規追加（bike / bukatsu）

#### bike-blue-ticket

**データ**: `social-samples/bike-blue-ticket_2d_classified.json` (116件)
**2軸**: `stance_enforcement` (X軸: 取締り反対↔賛成) / `stance_priority` (Y軸: ライダー利便性↔安全・秩序優先)
**作業**:
1. `docs/bike-blue-ticket-reaction-map.html` に正典テンプレートのCSS/HTML/JSを挿入
2. 2D JSONからRAWデータを生成し埋め込む
3. 軸ラベル・象限サマリー・フィルターボタンをテーマに合わせてカスタマイズ
4. ガイドツアーを構成（各象限から代表投稿を選出）
5. 既存の「反応の勢力図」（半円チャート）セクションを削除
6. 独立版 `docs/bike-blue-ticket-stance-map.html` を削除

#### bukatsu-chiiki

**データ**: `social-samples/bukatsu-chiiki_2d_classified.json` (148件)
**2軸**: `stance_transfer` (X軸: 移行反対↔移行推進) / `stance_priority` (Y軸: 教員負担軽減↔教育的価値重視)
**作業**: bike と同じパターン
**独立版**: `docs/bukatsu-chiiki-stance-map.html` を削除

### Phase 4: スキップ対象の確認

- **henoko** / **takaichi**: 2D分類JSONが存在しないため、半円チャートを維持。将来2D分類を実行した際にこのプロンプトに従ってスタンスマップを追加する
- **school-nickname-ban**: 2D分類が70%エラー（103件中）。再分類完了後にこのプロンプトに従って追加する

### Phase 5: index.html の整理

1. constitutional-amendment-stance-map.html へのトピックカードを削除（重複解消）
2. フッターリンクから stance-map.html 系を削除
3. 各テーマカードの `card-axes` タグに「2Dスタンスマップ」を追加（実装済みテーマのみ）

---

## 検証チェックリスト（全テーマ共通）

各テーマの作業完了後、以下を全て確認:

### ブラウザ検証
- [ ] ページが正常に表示される（白画面にならない）
- [ ] スタンスマップのドットが表示される
- [ ] ヒートマップのon/offが動作する
- [ ] ドットのon/offが動作する
- [ ] フィルターボタンで絞り込みが動作する
- [ ] ドットにホバーでツールチップが表示される
- [ ] ドットクリックでXの投稿URLに遷移する
- [ ] ガイドツアーが開始・進行・終了する
- [ ] 引用テキストが即時表示される
- [ ] 対立軸セクションが表示される
- [ ] 分類別件数が表示される
- [ ] ヒートマップテーブル（×クエリ / ×スタンス）が表示される
- [ ] 代表サンプルが表示される
- [ ] 投票ボタンが動作する

### コンソール検証（DevToolsまたは preview_eval）
- [ ] `getComputedStyle(document.getElementById('smCanvasMain')).backgroundColor` → `rgba(0, 0, 0, 0)`
- [ ] `getComputedStyle(document.getElementById('smCanvasHeat')).backgroundColor` → `rgb(250, 250, 250)`
- [ ] JSコンソールにエラーがないこと

### タグ検証
- [ ] GA4タグ (`G-K10S4YCZFH`) が存在すること
- [ ] AdSenseタグ (`ca-pub-2542211932832864`) が存在すること
- [ ] Supabase URL/APIキーが維持されていること

---

## RAW データ変換スクリプト（参考）

2D分類JSONからHTMLに埋め込むRAW配列を生成するPythonスニペット:

```python
import json, sys

input_file = sys.argv[1]  # e.g. social-samples/bike-blue-ticket_2d_classified.json
x_key = sys.argv[2]       # e.g. stance_enforcement
y_key = sys.argv[3]       # e.g. stance_priority

with open(input_file) as f:
    data = json.load(f)

raw = []
for item in data:
    x = item.get(x_key, 0)
    y = item.get(y_key, 0)
    e = item.get('emotional_intensity', 0)
    c = item.get('confidence', 0.5)
    s = item.get('summary', '')
    u = item.get('url', '')
    if x is not None and y is not None:
        raw.append({"x": x, "y": y, "e": e, "c": c, "s": s, "u": u})

print(f"const RAW = {json.dumps(raw, ensure_ascii=False)};")
print(f"// Total: {len(raw)} items")
```

使い方:
```bash
python3 generate_raw.py social-samples/bike-blue-ticket_2d_classified.json stance_enforcement stance_priority
```

---

## 参照ファイル

- 正典実装: `docs/constitutional-amendment-reaction-map.html` (行691〜728: CSS, 行1051〜1107: HTML, 行1109〜1815: JS)
- CSSバグチェックリスト: メモリ `reference_stancemap_impl.md`
- 2D分類データ: `social-samples/*_2d_classified.json`
- ワークフロー: `templates/reaction-map-workflow.md`
- 漫画データスキーマ: `templates/manga-content.schema.md`
- TASK_BOARD: 課題23（ai-copyright 2Dマップ）、課題24（漫画コンテンツ）
