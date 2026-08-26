# SNS反応まっぷ デザインシステム 規約

## セットアップ

コンポーネントにはプロバイダーラッパー不要。スタイルシートの読み込みのみ必要です。

```html
<link rel="stylesheet" href="_ds_bundle.css" />
```

または設計時は `styles.css`（`_ds_bundle.css` を `@import` しています）を使用してください。

## スタイリング

このデザインシステムは **CSS クラス** ベースです。`ds-` プレフィックスの CSS カスタムプロパティ（トークン）と対応するクラスを使います。CSS-in-JS や Tailwind は使用しません。

### デザイントークン（CSS カスタムプロパティ）

| トークン | 値 | 用途 |
|---|---|---|
| `--ds-bg` | `#f4f6f8` | ページ背景 |
| `--ds-panel` | `#ffffff` | カード・パネル面 |
| `--ds-ink` | `#172033` | 本文テキスト |
| `--ds-muted` | `#667085` | 補助テキスト、ラベル |
| `--ds-line` | `#d7dce5` | ボーダー |
| `--ds-accent` | `#1769d1` | リンク、アクション |
| `--ds-accent-soft` | `#e7f1ff` | アクセント背景 |
| `--ds-warn` | `#b54708` | 警告・反対色 |
| `--ds-ok` | `#16885a` | 成功・賛成色 |
| `--ds-purple` | `#7a4cc2` | 手続き・注意色 |
| `--ds-shadow` | `0 10px 28px rgba(16,24,40,.06)` | カード影 |

コンポーネントの色は直接指定せず、必ず `var(--ds-*)` トークンを使ってください。

## コンポーネント構成例

```jsx
// ページの基本構成
import {
  PageHeader, NavLinks, StatGrid, StatCard,
  Panel, BarList, AxisCard, NoticeAlert
} from 'issue-stance-ds';

function ReportPage() {
  return (
    <>
      <PageHeader
        title="憲法改正論議 ダッシュボード"
        lead="SNS反応192件を論点ごとに集計・分類。"
        nav={[
          { href: '/', label: 'トップ' },
          { href: '/map', label: '反応マップ', current: true },
        ]}
      />
      <main style={{ padding: '20px min(5vw,56px) 48px', background: 'var(--ds-bg)' }}>
        <NoticeAlert>
          このデータはサンプルです。世論比率としては扱えません。
        </NoticeAlert>
        <StatGrid>
          <StatCard label="収集件数" value="192" unit="件" />
          <StatCard label="賛成・支持" value="52" unit="件" />
          <StatCard label="反対・慎重" value="61" unit="件" />
        </StatGrid>
      </main>
    </>
  );
}
```

## コンポーネント一覧

| コンポーネント | 用途 |
|---|---|
| `PageHeader` | ページ上部の白いヘッダー（タイトル・リード・ナビ） |
| `NavLinks` | 横並びピル型ナビゲーション |
| `StatCard` + `StatGrid` | 数値メトリクスカード |
| `Panel` | 白いコンテンツコンテナ（タイトル付き） |
| `AxisCard` | スタンス軸カード（variant: positive/negative/ok/warn） |
| `BarList` + `BarRow` | 水平バーチャート |
| `Badge` | インラインラベル（トピック分類など） |
| `StanceBadge` | スタンス表示バッジ（variant: support/oppose/cautious/neutral） |
| `Chip` + `ChipRow` | フィルターチップ（active 状態あり） |
| `PostCard` | SNS投稿カード（要旨・引用・メタ情報） |
| `StatList` | キーバリューリスト |
| `TableWrap` + `HeatCell` | ヒートマップテーブル |
| `VersusGrid` | 賛否対比レイアウト |
| `NoticeAlert` | サンプリング注意書きなどのアラート |
| `Toolbar` | スティッキーフィルターバー |
| `PageLayout` | メイン+サイドバー 2カラムレイアウト |

## スタンス色の規則

| スタンス | 色 | トークン |
|---|---|---|
| 賛成・支持 | 青 | `--ds-accent` |
| 反対・慎重 | オレンジ | `--ds-warn` |
| 手続き重視 | 紫 | `--ds-purple` |
| 中立・不明 | グレー | `--ds-muted` |
| 肯定的・OK | 緑 | `--ds-ok` |

`AxisCard` の `variant` prop と `StanceBadge` の `variant` prop で一貫してこの色を使います。ヒートマップセルの `bgColor` でも同じ色コードを使用してください。
