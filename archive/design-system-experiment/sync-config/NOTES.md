# Design Sync ノート

> 2026-08-27に休止実験としてアーカイブ。公開サイトはこのパッケージを使用していない。
> 再開する場合だけ、以下の保存済み手順と現行ツールの仕様を照合する。

## セットアップ情報

- **パッケージ**: `archive/design-system-experiment/package/` (モノレポ内のローカルパッケージ)
- **エントリ**: `./archive/design-system-experiment/package/dist/index.es.js`
- **node_modules**: `archive/design-system-experiment/package/node_modules`
- **ビルドコマンド**: `cd archive/design-system-experiment/package && npm run build`（JS + tsc 型定義）
- **CSS**: `archive/design-system-experiment/package/src/styles.css` を `cfg.cssEntry` で指定（PKG_DIR からの相対パス）
- **Playwright**: `~/.cache/ms-playwright/` に playwright-core、`~/Library/Caches/ms-playwright/` に playwright 本体

## Known render warns

なし（初回全クリーン）

## 注意点

- `cssEntry` は `PKG_DIR` (`archive/design-system-experiment/package/`) からの相対パス。リポジトリルートからではない
- esbuild の WARNING: `package.json` の `exports["."].types` が `import`/`require` の後にあるため unused になるが無害
- tsconfig は `moduleResolution: bundler` を使用（Node16 ではない）
- `archive/design-system-experiment/package/node_modules/` に react がインストール済み（コンバーターが要求）
- `HeatCell` は `<td>` 要素なので必ず `<table>` の中でしか使えない。プレビューは table でラップして書く

## 再同期手順

```bash
# 1. スクリプトを再ステージ
mkdir -p archive/local/design-sync-runtime/.ds-sync && cp -r /path/to/design-sync/skill/{package-build,package-validate,package-capture,resync}.mjs /path/to/design-sync/skill/{lib,storybook} archive/local/design-sync-runtime/.ds-sync/
cd archive/local/design-sync-runtime/.ds-sync && npm i esbuild ts-morph @types/react playwright && cd ..

# 2. DSをリビルド
cd archive/design-system-experiment/package && npm run build && cd ../../..

# 3. ドライバー実行
node archive/local/design-sync-runtime/.ds-sync/resync.mjs \
  --config archive/design-system-experiment/sync-config/config.json \
  --node-modules archive/design-system-experiment/package/node_modules \
  --entry ./archive/design-system-experiment/package/dist/index.es.js \
  --out ./archive/local/design-sync-runtime/ds-bundle \
  --remote archive/design-system-experiment/sync-config/.cache/remote-sync.json
```

## Re-sync risks

- **CSS トークン**: `archive/design-system-experiment/package/src/styles.css` に直書きされているため、既存レポートの CSS と乖離が生じた場合は手動で同期が必要
- **プレビューの日本語テキスト**: 特定のデータ値（192件, 52件など）がハードコードされている。実際のデータが変わっても自動更新されない
- **フロアカード**: BarRow, Chip, NavLinks, StatGrid はプレビューなし（フロアカード）。必要ならいつでも `archive/design-system-experiment/sync-config/previews/` に追加可能
- **esbuild 型定義 WARNING**: package.json の `exports.types` 位置による無害な警告は毎回出る
