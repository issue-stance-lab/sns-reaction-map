# 課題37: validate_theme_seo.py が1件落ちている

**状態**: 未着手（2026-08-07 の棚卸しで検出。棚卸し前から存在する既存の不整合）
**発見**: 2026-08-07

```
FAILED: 1 validation error(s)
- ai-copyright-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

**概要**: `docs/ai-copyright-reaction-map.html` の JSON-LD `dateModified` と `THEMES.yaml` の `updated_at` がずれている。データ更新時にページ側のSEO日付を戻し忘れたと思われる。

**やること**: どちらが正しいか（最後に実際に公開更新した日）を確認して片方へ揃える。ai-copyright は `page_update_mode: adapter` なので、adapter 側で `dateModified` を更新していない可能性も調べる。
