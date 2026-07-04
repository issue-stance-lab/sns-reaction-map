# トピックページ標準フォーマット v3

この仕様は、SNS反応まっぷの各トピックページを「漫画 -> 投票 -> 2Dスタンスマップ」に接続するための正典です。Phase B以降のテーマ展開では、原則としてこの順序、セクションID、CSSクラス名、折りたたみ仕様を維持します。

## 1. ヒーロー

- セクション: `<section class="hero">`
- 主要要素:
  - `.top-nav`: トップページなど最低限の戻り導線
  - トピック種別バッジ
  - `<h1>`: ページタイトル
  - `.question-line`: テーマの問いを1行で提示
  - `.lead`: データ取得方法とページの前提
  - `.thirty-summary`: 「30秒サマリー」3点箇条書き
- 30秒サマリーは、SNS分布の要点を3行で書く。推奨順は「最多勢力」「対立勢力」「接点・保留」。

## 2. 漫画で読む対立

- セクションID: `manga-section`
- クラス:
  - `.manga-intro`
  - `.manga-grid`
  - `.manga-page-card`
  - `.manga-modal`
- 現行漫画画像をそのまま使い、画像には必ず `loading="lazy"` を付ける。
- モーダル拡大、前後移動、Escキーで閉じる挙動を維持する。

## 3. 投票

- セクションID: `vote-section`
- 投票質問・選択肢文言はテーマconfigの確定文言を変更しない。
- 投票カード:
  - コンテナ: `#vote-buttons.vote-card-grid`
  - ボタン: `.vote-image-card`
  - ラベル: `.vote-card-label`
- 投票後は `#vote-result` を表示し、次を即時表示する。
  - `#vote-position-label`: あなたの選択
  - `#vote-position-text`: SNS分布との比較案内
  - `#vote-comparison.vote-comparison`: 「あなたの選択 vs SNS分布」の2カード比較
  - `#vote-bars`: 全選択肢の投票割合
- Supabase投票ロジックは維持する。重複投票は `err.code === "23505"` と既存メッセージ判定の両方で扱う。

## 4. 2Dスタンスマップ

- セクションID: `stance-map-section`
- 内側ラッパー: `#stance-map-inner`
- 正典canvas ID:
  - ヒートマップ: `smCanvasHeat`
  - 点・軸・マーカー: `smCanvasMain`
- `ctx.filter` は描画アニメーション中に使わない。Safariで重くなるため、ヒートマップはフィルターなしまたは事前描画にする。
- 投票後は `window.setStanceMapVoteMarker(choiceIndex)` を呼び、マップ上に「あなたはこのあたり」マーカーを表示する。
- ai-copyright の投票選択肢と象限対応:
  - 0: 「クリエイターを守るためAI規制を強化すべき」 -> 右上。規制賛成、クリエイター個人優先。座標目安 `(1.45, 1.45)`。
  - 1: 「技術革新を止めないよう規制は最小限に」 -> 左下。規制反対、AI産業・社会全体優先。座標目安 `(-1.45, -1.35)`。
  - 2: 「オプトアウトや対価支払いなど条件付きで共存」 -> 左上寄り。規制反対を基調に、クリエイター個人優先も残す。座標目安 `(-0.85, 0.95)`。
  - 3: 「よくわからない・まだ判断できない」 -> 右下寄り。制度整備への期待は残しつつ、産業・社会全体優先側の保留。座標目安 `(0.85, -0.95)`。

## 5. 象限別の代表的な声

- セクション見出し: 「象限別の代表的な声」
- 推奨クラス:
  - `.quadrant-nav`: 象限・立場別のページ内ナビ
  - `.sample-grid`
  - `.sample-card`
  - `.sample`
- 既存の代表サンプルを削除せず、象限ナビから該当カードへ移動できるようにする。
- X埋め込みは現行の `blockquote.twitter-tweet` を維持する。

## 6. 争点カード

- セクション見出し: 「争点カード」
- 推奨クラス:
  - `.conflict-panel`
  - `.axis-grid`
  - `.axis-card`
  - `.axis-kicker`
  - `.axis-count`
  - `.axis-tags`
- 旧「対立軸」テーブルはカード形式にし、各カードは立場、件数、短い説明、関連カテゴリタグを含める。

## 7. 回遊セクション

- セクションID: `related-topics`
- 推奨クラス:
  - `.related-grid`
  - `.related-card`
- 他テーマへのカードを2-3枚置く。各カードはリンク、既存ヒーロー画像、テーマ名、短い説明を持つ。
- 画像は `docs/images/` 既存資産のみを使い、必ず `loading="lazy"` を付ける。

## 8. 詳細データ（折りたたみ）

- セクションID: `detail-data`
- クラス: `.details-panel`
- `<details>` に格下げする対象:
  - 分類別件数
  - カテゴリ × 検索クエリ
  - カテゴリ × スタンス
  - 注意
- 初期表示は「分類別件数」のみ `open` を許容する。他の表は閉じる。
- 表の既存クラス（`.bar-list`, `.heat-table`, `.table-wrap`, `.legend`）は維持し、CSS互換性を保つ。

## 実装上の保持条件

- GA4タグ `G-K10S4YCZFH` を残す。
- AdSenseコード `ca-pub-2542211932832864` を残す。
- Supabase URL/APIキーと投票ロジックを削除しない。未設定ページでは空文字の変数を維持し、ローカルフォールバックを動かす。
- OGPメタタグとcanonicalリンクは `SEO_META_START` / `SEO_META_END` ブロックで管理する。
- 漫画セクションと投票画像カードの既存資産は削除しない。
- CSSは各ページのインラインCSSで完結させる。
